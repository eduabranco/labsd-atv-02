package br.uf.labsd.ddb.protocol;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/**
 * Utilitário para calcular checksum das mensagens
 */
public class ChecksumUtil {
    
    /**
     * Calcula checksum MD5 de uma string
     */
    public static String calculateChecksum(String data) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] hashBytes = md.digest(data.getBytes(StandardCharsets.UTF_8));
            
            StringBuilder sb = new StringBuilder();
            for (byte b : hashBytes) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("Erro ao calcular checksum", e);
        }
    }
    
    /**
     * Verifica se o checksum está correto
     */
    public static boolean verifyChecksum(String data, String expectedChecksum) {
        String actualChecksum = calculateChecksum(data);
        return actualChecksum.equals(expectedChecksum);
    }
    
    /**
     * Adiciona checksum a uma mensagem
     */
    public static void addChecksum(Message message) {
        String data = message.getMessageId() + 
                     message.getType() + 
                     message.getSourceNodeId() + 
                     message.getTimestamp() + 
                     (message.getPayload() != null ? message.getPayload() : "");
        message.setChecksum(calculateChecksum(data));
    }
    
    /**
     * Verifica checksum de uma mensagem
     */
    public static boolean verifyMessageChecksum(Message message) {
        if (message.getChecksum() == null) {
            return false;
        }
        
        String data = message.getMessageId() + 
                     message.getType() + 
                     message.getSourceNodeId() + 
                     message.getTimestamp() + 
                     (message.getPayload() != null ? message.getPayload() : "");
        
        return verifyChecksum(data, message.getChecksum());
    }
}
