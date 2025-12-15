package br.uf.labsd.ddb.node;

import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import br.uf.labsd.ddb.protocol.ChecksumUtil;
import br.uf.labsd.ddb.protocol.Message;

/**
 * Gerencia o heartbeat entre nós
 */
public class HeartbeatManager {
    private static final Logger logger = LoggerFactory.getLogger(HeartbeatManager.class);
    
    private final DDBNode node;
    private ScheduledExecutorService scheduler;
    private volatile boolean running = false;
    
    public HeartbeatManager(DDBNode node) {
        this.node = node;
    }
    
    /**
     * Inicia o heartbeat
     */
    public void start() {
        scheduler = Executors.newScheduledThreadPool(1);
        running = true;
        
        // Envia heartbeat periodicamente
        scheduler.scheduleAtFixedRate(
            this::sendHeartbeat,
            0,
            node.getConfig().getHeartbeatInterval(),
            TimeUnit.MILLISECONDS
        );
        
        // Verifica status dos peers
        scheduler.scheduleAtFixedRate(
            this::checkPeerStatus,
            node.getConfig().getHeartbeatInterval() * 2,
            node.getConfig().getHeartbeatInterval(),
            TimeUnit.MILLISECONDS
        );
        
        logger.info("Heartbeat iniciado (intervalo: {}ms)", 
                   node.getConfig().getHeartbeatInterval());
    }
    
    /**
     * Para o heartbeat
     */
    public void stop() {
        running = false;
        if (scheduler != null) {
            scheduler.shutdownNow();
        }
        logger.info("Heartbeat parado");
    }
    
    /**
     * Envia heartbeat para todos os peers
     */
    private void sendHeartbeat() {
        if (!running) return;
        
        Message message = new Message(Message.MessageType.HEARTBEAT, node.getConfig().getNodeId());
        ChecksumUtil.addChecksum(message);
        
        node.getNetworkManager().broadcast(message);
        logger.debug("[{}] Heartbeat enviado", node.getConfig().getNodeId());
    }
    
    /**
     * Trata recebimento de heartbeat
     */
    public void handleHeartbeat(Message message) {
        String sourceNodeId = message.getSourceNodeId();
        logger.debug("[{}] Heartbeat recebido de {}", 
                    node.getConfig().getNodeId(), sourceNodeId);
        
        // Atualiza status do peer
        DDBNode.PeerStatus status = node.getPeerStatuses()
            .computeIfAbsent(sourceNodeId, k -> new DDBNode.PeerStatus());
        status.setNodeId(sourceNodeId);
        status.setLastHeartbeat(System.currentTimeMillis());
        status.setActive(true);
        
        // Envia ACK
        Message ack = new Message(Message.MessageType.HEARTBEAT_ACK, node.getConfig().getNodeId());
        ack.setTargetNodeId(sourceNodeId);
        ChecksumUtil.addChecksum(ack);
        
        node.getNetworkManager().sendToNode(sourceNodeId, ack);
    }
    
    /**
     * Trata recebimento de ACK de heartbeat
     */
    public void handleHeartbeatAck(Message message) {
        String sourceNodeId = message.getSourceNodeId();
        logger.debug("[{}] Heartbeat ACK recebido de {}", 
                    node.getConfig().getNodeId(), sourceNodeId);
        
        // Atualiza status do peer
        DDBNode.PeerStatus status = node.getPeerStatuses()
            .computeIfAbsent(sourceNodeId, k -> new DDBNode.PeerStatus());
        status.setLastHeartbeat(System.currentTimeMillis());
        status.setActive(true);
    }
    
    /**
     * Verifica status dos peers e marca inativos se necessário
     */
    private void checkPeerStatus() {
        if (!running) return;
        
        long timeout = node.getConfig().getHeartbeatInterval() * 3;
        long now = System.currentTimeMillis();
        
        for (DDBNode.PeerStatus status : node.getPeerStatuses().values()) {
            if (now - status.getLastHeartbeat() > timeout && status.isActive()) {
                logger.warn("[{}] Peer {} não responde (timeout)", 
                           node.getConfig().getNodeId(), status.getNodeId());
                status.setActive(false);
                
                // Se o coordenador falhou, inicia eleição
                if (status.getNodeId().equals(node.getCoordinatorId())) {
                    logger.warn("[{}] Coordenador falhou, iniciando eleição", 
                               node.getConfig().getNodeId());
                    node.setCoordinatorId(null);
                    // Agenda eleição com pequeno delay
                    scheduler.schedule(
                        () -> {
                            ElectionManager em = new ElectionManager(node);
                            em.startElection();
                        },
                        1000,
                        TimeUnit.MILLISECONDS
                    );
                }
            }
        }
    }
}
