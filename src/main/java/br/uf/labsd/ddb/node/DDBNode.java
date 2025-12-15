package br.uf.labsd.ddb.node;

import java.sql.SQLException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import br.uf.labsd.ddb.config.NodeConfig;
import br.uf.labsd.ddb.database.DatabaseManager;
import br.uf.labsd.ddb.protocol.ChecksumUtil;
import br.uf.labsd.ddb.protocol.Message;

/**
 * Nó do banco de dados distribuído
 */
public class DDBNode {
    private static final Logger logger = LoggerFactory.getLogger(DDBNode.class);
    
    private final NodeConfig config;
    private final DatabaseManager dbManager;
    private final NetworkManager networkManager;
    private final HeartbeatManager heartbeatManager;
    private final ElectionManager electionManager;
    
    private volatile boolean running = false;
    private String coordinatorId;
    private final Map<String, PeerStatus> peerStatuses;
    
    public DDBNode(NodeConfig config) {
        this.config = config;
        this.dbManager = new DatabaseManager(config.getDatabase());
        this.networkManager = new NetworkManager(this);
        this.heartbeatManager = new HeartbeatManager(this);
        this.electionManager = new ElectionManager(this);
        this.peerStatuses = new ConcurrentHashMap<>();
        this.coordinatorId = null;
    }
    
    /**
     * Inicia o nó
     */
    public void start() throws Exception {
        logger.info("Iniciando nó {} na porta {}", config.getNodeId(), config.getPort());
        
        // Conecta ao banco de dados
        dbManager.connect();
        
        // Inicia servidor de rede
        networkManager.start();
        
        // Inicia heartbeat
        heartbeatManager.start();
        
        // Aguarda um pouco e inicia eleição
        Thread.sleep(2000);
        electionManager.startElection();
        
        running = true;
        logger.info("Nó {} iniciado com sucesso", config.getNodeId());
    }
    
    /**
     * Para o nó
     */
    public void stop() {
        logger.info("Parando nó {}", config.getNodeId());
        running = false;
        
        heartbeatManager.stop();
        networkManager.stop();
        dbManager.disconnect();
        
        logger.info("Nó {} parado", config.getNodeId());
    }
    
    /**
     * Processa mensagem recebida
     */
    public void processMessage(Message message) {
        // Verifica checksum
        if (!ChecksumUtil.verifyMessageChecksum(message)) {
            logger.warn("Checksum inválido para mensagem {}", message.getMessageId());
            return;
        }
        
        logger.debug("Processando mensagem tipo {} de {}", 
                    message.getType(), message.getSourceNodeId());
        
        switch (message.getType()) {
            case HEARTBEAT:
                heartbeatManager.handleHeartbeat(message);
                break;
                
            case HEARTBEAT_ACK:
                heartbeatManager.handleHeartbeatAck(message);
                break;
                
            case ELECTION:
                electionManager.handleElection(message);
                break;
                
            case ELECTION_OK:
                electionManager.handleElectionOk(message);
                break;
                
            case COORDINATOR:
                electionManager.handleCoordinator(message);
                break;
                
            case QUERY_EXECUTE:
                handleQueryExecute(message);
                break;
                
            case NODE_JOIN:
                handleNodeJoin(message);
                break;
                
            default:
                logger.warn("Tipo de mensagem não tratado: {}", message.getType());
        }
    }
    
    /**
     * Executa uma query localmente
     */
    public DatabaseManager.QueryResult executeLocalQuery(String sql) throws SQLException {
        logger.info("[{}] Executando query localmente: {}", config.getNodeId(), sql);
        return dbManager.execute(sql);
    }
    
    /**
     * Replica query para todos os nós
     */
    public void replicateQuery(String sql) {
        logger.info("[{}] Replicando query: {}", config.getNodeId(), sql);
        
        Message message = new Message(Message.MessageType.QUERY_EXECUTE, config.getNodeId());
        message.setPayload(sql);
        ChecksumUtil.addChecksum(message);
        
        networkManager.broadcast(message);
    }
    
    /**
     * Trata execução de query recebida de outro nó
     */
    private void handleQueryExecute(Message message) {
        String sql = message.getPayload();
        logger.info("[{}] Recebida query para execução: {}", config.getNodeId(), sql);
        
        try {
            dbManager.execute(sql);
            dbManager.commit();
            logger.info("[{}] Query executada e commitada com sucesso", config.getNodeId());
        } catch (SQLException e) {
            logger.error("[{}] Erro ao executar query", config.getNodeId(), e);
            dbManager.rollback();
        }
    }
    
    /**
     * Trata entrada de novo nó
     */
    private void handleNodeJoin(Message message) {
        String newNodeId = message.getSourceNodeId();
        logger.info("[{}] Novo nó entrou na rede: {}", config.getNodeId(), newNodeId);
        
        PeerStatus status = new PeerStatus();
        status.setNodeId(newNodeId);
        status.setLastHeartbeat(System.currentTimeMillis());
        status.setActive(true);
        peerStatuses.put(newNodeId, status);
    }
    
    // Getters
    public NodeConfig getConfig() { return config; }
    public DatabaseManager getDbManager() { return dbManager; }
    public NetworkManager getNetworkManager() { return networkManager; }
    public boolean isRunning() { return running; }
    public String getCoordinatorId() { return coordinatorId; }
    public void setCoordinatorId(String coordinatorId) { 
        this.coordinatorId = coordinatorId;
        logger.info("[{}] Coordenador definido: {}", config.getNodeId(), coordinatorId);
    }
    public boolean isCoordinator() { 
        return config.getNodeId().equals(coordinatorId); 
    }
    public Map<String, PeerStatus> getPeerStatuses() { return peerStatuses; }
    
    /**
     * Status de um peer
     */
    public static class PeerStatus {
        private String nodeId;
        private long lastHeartbeat;
        private boolean active;
        
        public String getNodeId() { return nodeId; }
        public void setNodeId(String nodeId) { this.nodeId = nodeId; }
        
        public long getLastHeartbeat() { return lastHeartbeat; }
        public void setLastHeartbeat(long lastHeartbeat) { this.lastHeartbeat = lastHeartbeat; }
        
        public boolean isActive() { return active; }
        public void setActive(boolean active) { this.active = active; }
    }
}
