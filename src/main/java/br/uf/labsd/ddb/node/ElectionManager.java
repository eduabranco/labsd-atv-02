package br.uf.labsd.ddb.node;

import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import br.uf.labsd.ddb.protocol.ChecksumUtil;
import br.uf.labsd.ddb.protocol.Message;

/**
 * Gerencia a eleição de coordenador usando algoritmo Bully
 */
public class ElectionManager {
    private static final Logger logger = LoggerFactory.getLogger(ElectionManager.class);
    
    private final DDBNode node;
    private volatile boolean electionInProgress = false;
    private ScheduledFuture<?> electionTimeout;
    
    public ElectionManager(DDBNode node) {
        this.node = node;
    }
    
    /**
     * Inicia processo de eleição (Algoritmo Bully)
     */
    public void startElection() {
        if (electionInProgress) {
            logger.debug("[{}] Eleição já em progresso", node.getConfig().getNodeId());
            return;
        }
        
        electionInProgress = true;
        logger.info("[{}] Iniciando eleição de coordenador", node.getConfig().getNodeId());
        
        // Envia mensagem de eleição para nós com ID maior
        Message electionMsg = new Message(Message.MessageType.ELECTION, node.getConfig().getNodeId());
        ChecksumUtil.addChecksum(electionMsg);
        
        boolean sentToHigher = false;
        for (var peer : node.getConfig().getPeers()) {
            if (peer.getNodeId().compareTo(node.getConfig().getNodeId()) > 0) {
                node.getNetworkManager().sendToNode(peer.getNodeId(), electionMsg);
                sentToHigher = true;
            }
        }
        
        // Se não há nós com ID maior, este nó se torna coordenador
        if (!sentToHigher) {
            becomeCoordinator();
            return;
        }
        
        // Aguarda respostas por um timeout
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        electionTimeout = scheduler.schedule(() -> {
            // Se não recebeu OK de ninguém, torna-se coordenador
            if (electionInProgress) {
                logger.info("[{}] Timeout de eleição, tornando-se coordenador", 
                           node.getConfig().getNodeId());
                becomeCoordinator();
            }
        }, node.getConfig().getElectionTimeout(), TimeUnit.MILLISECONDS);
    }
    
    /**
     * Trata mensagem de eleição recebida
     */
    public void handleElection(Message message) {
        String sourceNodeId = message.getSourceNodeId();
        logger.info("[{}] Recebida mensagem de eleição de {}", 
                   node.getConfig().getNodeId(), sourceNodeId);
        
        // Envia OK de volta
        Message okMsg = new Message(Message.MessageType.ELECTION_OK, node.getConfig().getNodeId());
        okMsg.setTargetNodeId(sourceNodeId);
        ChecksumUtil.addChecksum(okMsg);
        node.getNetworkManager().sendToNode(sourceNodeId, okMsg);
        
        // Inicia própria eleição se não houver uma em andamento
        if (!electionInProgress) {
            startElection();
        }
    }
    
    /**
     * Trata mensagem OK de eleição
     */
    public void handleElectionOk(Message message) {
        logger.info("[{}] Recebido OK de eleição de {}", 
                   node.getConfig().getNodeId(), message.getSourceNodeId());
        
        // Cancela timeout e para eleição (há um nó com ID maior)
        if (electionTimeout != null) {
            electionTimeout.cancel(false);
        }
        electionInProgress = false;
    }
    
    /**
     * Trata anúncio de coordenador
     */
    public void handleCoordinator(Message message) {
        String newCoordinator = message.getSourceNodeId();
        logger.info("[{}] Novo coordenador anunciado: {}", 
                   node.getConfig().getNodeId(), newCoordinator);
        
        node.setCoordinatorId(newCoordinator);
        electionInProgress = false;
        
        if (electionTimeout != null) {
            electionTimeout.cancel(false);
        }
    }
    
    /**
     * Torna-se coordenador e anuncia para todos
     */
    private void becomeCoordinator() {
        logger.info("[{}] Tornando-se coordenador", node.getConfig().getNodeId());
        
        node.setCoordinatorId(node.getConfig().getNodeId());
        electionInProgress = false;
        
        if (electionTimeout != null) {
            electionTimeout.cancel(false);
        }
        
        // Anuncia que é o novo coordenador
        Message coordinatorMsg = new Message(Message.MessageType.COORDINATOR, 
                                             node.getConfig().getNodeId());
        ChecksumUtil.addChecksum(coordinatorMsg);
        node.getNetworkManager().broadcast(coordinatorMsg);
    }
}
