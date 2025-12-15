package br.uf.labsd.ddb.config;

import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import com.google.gson.Gson;

/**
 * Configuração do nó do DDB
 */
public class NodeConfig {
    private String nodeId;
    private String host;
    private int port;
    private DatabaseConfig database;
    private List<PeerNode> peers;
    private int heartbeatInterval = 5000; // ms
    private int electionTimeout = 10000; // ms
    
    public static class DatabaseConfig {
        private String url;
        private String username;
        private String password;
        private String database;
        
        public String getUrl() { return url; }
        public void setUrl(String url) { this.url = url; }
        
        public String getUsername() { return username; }
        public void setUsername(String username) { this.username = username; }
        
        public String getPassword() { return password; }
        public void setPassword(String password) { this.password = password; }
        
        public String getDatabase() { return database; }
        public void setDatabase(String database) { this.database = database; }
        
        public String getJdbcUrl() {
            return "jdbc:mysql://" + url + "/" + database + 
                   "?useSSL=false&serverTimezone=UTC&allowPublicKeyRetrieval=true";
        }
    }
    
    public static class PeerNode {
        private String nodeId;
        private String host;
        private int port;
        
        public PeerNode() {}
        
        public PeerNode(String nodeId, String host, int port) {
            this.nodeId = nodeId;
            this.host = host;
            this.port = port;
        }
        
        public String getNodeId() { return nodeId; }
        public void setNodeId(String nodeId) { this.nodeId = nodeId; }
        
        public String getHost() { return host; }
        public void setHost(String host) { this.host = host; }
        
        public int getPort() { return port; }
        public void setPort(int port) { this.port = port; }
    }
    
    // Getters and Setters
    public String getNodeId() { return nodeId; }
    public void setNodeId(String nodeId) { this.nodeId = nodeId; }
    
    public String getHost() { return host; }
    public void setHost(String host) { this.host = host; }
    
    public int getPort() { return port; }
    public void setPort(int port) { this.port = port; }
    
    public DatabaseConfig getDatabase() { return database; }
    public void setDatabase(DatabaseConfig database) { this.database = database; }
    
    public List<PeerNode> getPeers() { 
        return peers != null ? peers : new ArrayList<>(); 
    }
    public void setPeers(List<PeerNode> peers) { this.peers = peers; }
    
    public int getHeartbeatInterval() { return heartbeatInterval; }
    public void setHeartbeatInterval(int heartbeatInterval) { 
        this.heartbeatInterval = heartbeatInterval; 
    }
    
    public int getElectionTimeout() { return electionTimeout; }
    public void setElectionTimeout(int electionTimeout) { 
        this.electionTimeout = electionTimeout; 
    }
    
    /**
     * Carrega configuração de arquivo JSON
     */
    public static NodeConfig loadFromFile(String filePath) throws IOException {
        try (FileReader reader = new FileReader(filePath)) {
            Gson gson = new Gson();
            return gson.fromJson(reader, NodeConfig.class);
        }
    }
}
