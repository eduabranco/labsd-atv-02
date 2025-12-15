package br.uf.labsd.ddb.protocol;

import java.io.Serializable;
import java.util.UUID;

import com.google.gson.Gson;

/**
 * Mensagem do protocolo de comunicação entre nós
 */
public class Message implements Serializable {
    private static final long serialVersionUID = 1L;
    
    public enum MessageType {
        // Eleição de coordenador
        ELECTION,
        ELECTION_OK,
        COORDINATOR,
        
        // Heartbeat
        HEARTBEAT,
        HEARTBEAT_ACK,
        
        // Replicação de queries
        QUERY_EXECUTE,
        QUERY_RESULT,
        QUERY_COMMIT,
        QUERY_ROLLBACK,
        
        // Gerenciamento de transações
        TRANSACTION_BEGIN,
        TRANSACTION_PREPARE,
        TRANSACTION_COMMIT,
        TRANSACTION_ABORT,
        
        // Sincronização
        SYNC_REQUEST,
        SYNC_DATA,
        
        // Status
        NODE_JOIN,
        NODE_LEAVE,
        NODE_STATUS
    }
    
    private String messageId;
    private MessageType type;
    private String sourceNodeId;
    private String targetNodeId; // null para broadcast
    private long timestamp;
    private String payload;
    private String checksum;
    
    public Message() {
        this.messageId = UUID.randomUUID().toString();
        this.timestamp = System.currentTimeMillis();
    }
    
    public Message(MessageType type, String sourceNodeId) {
        this();
        this.type = type;
        this.sourceNodeId = sourceNodeId;
    }
    
    // Getters and Setters
    public String getMessageId() { return messageId; }
    public void setMessageId(String messageId) { this.messageId = messageId; }
    
    public MessageType getType() { return type; }
    public void setType(MessageType type) { this.type = type; }
    
    public String getSourceNodeId() { return sourceNodeId; }
    public void setSourceNodeId(String sourceNodeId) { this.sourceNodeId = sourceNodeId; }
    
    public String getTargetNodeId() { return targetNodeId; }
    public void setTargetNodeId(String targetNodeId) { this.targetNodeId = targetNodeId; }
    
    public long getTimestamp() { return timestamp; }
    public void setTimestamp(long timestamp) { this.timestamp = timestamp; }
    
    public String getPayload() { return payload; }
    public void setPayload(String payload) { this.payload = payload; }
    
    public String getChecksum() { return checksum; }
    public void setChecksum(String checksum) { this.checksum = checksum; }
    
    /**
     * Serializa a mensagem para JSON
     */
    public String toJson() {
        Gson gson = new Gson();
        return gson.toJson(this);
    }
    
    /**
     * Desserializa mensagem de JSON
     */
    public static Message fromJson(String json) {
        Gson gson = new Gson();
        return gson.fromJson(json, Message.class);
    }
    
    /**
     * Verifica se a mensagem é broadcast
     */
    public boolean isBroadcast() {
        return targetNodeId == null;
    }
}
