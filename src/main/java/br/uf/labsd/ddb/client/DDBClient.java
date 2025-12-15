package br.uf.labsd.ddb.client;

import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import br.uf.labsd.ddb.config.NodeConfig;
import br.uf.labsd.ddb.database.DatabaseManager;

/**
 * Cliente para acessar o DDB
 */
public class DDBClient {
    private static final Logger logger = LoggerFactory.getLogger(DDBClient.class);
    
    private final List<NodeConfig.PeerNode> nodes;
    private int currentNodeIndex = 0;
    
    public DDBClient(List<NodeConfig.PeerNode> nodes) {
        this.nodes = new ArrayList<>(nodes);
    }
    
    /**
     * Executa uma query no DDB (com balanceamento de carga round-robin)
     */
    public QueryResponse executeQuery(String sql) {
        // Seleciona próximo nó (round-robin)
        NodeConfig.PeerNode node = selectNode();
        
        logger.info("Executando query no nó {}: {}", node.getNodeId(), sql);
        
        try {
            // Conecta diretamente ao MySQL do nó selecionado
            NodeConfig.DatabaseConfig dbConfig = new NodeConfig.DatabaseConfig();
            dbConfig.setUrl(node.getHost() + ":3306");
            dbConfig.setUsername("ddb_user"); // Configurável
            dbConfig.setPassword("ddb_pass"); // Configurável
            dbConfig.setDatabase("ddb"); // Configurável
            
            DatabaseManager dbManager = new DatabaseManager(dbConfig);
            dbManager.connect();
            
            DatabaseManager.QueryResult result = dbManager.execute(sql);
            
            // Se for uma modificação, commita
            if (!sql.trim().toUpperCase().startsWith("SELECT")) {
                dbManager.commit();
            }
            
            dbManager.disconnect();
            
            return new QueryResponse(true, result, node.getNodeId(), null);
            
        } catch (SQLException e) {
            logger.error("Erro ao executar query", e);
            return new QueryResponse(false, null, node.getNodeId(), e.getMessage());
        }
    }
    
    /**
     * Seleciona nó usando round-robin
     */
    private NodeConfig.PeerNode selectNode() {
        if (nodes.isEmpty()) {
            throw new IllegalStateException("Nenhum nó disponível");
        }
        
        NodeConfig.PeerNode node = nodes.get(currentNodeIndex);
        currentNodeIndex = (currentNodeIndex + 1) % nodes.size();
        return node;
    }
    
    /**
     * Exibe resultado formatado
     */
    public void displayResult(QueryResponse response) {
        System.out.println("\n" + "=".repeat(80));
        System.out.println("Nó executado: " + response.getNodeId());
        System.out.println("=".repeat(80));
        
        if (!response.isSuccess()) {
            System.out.println("ERRO: " + response.getErrorMessage());
            return;
        }
        
        DatabaseManager.QueryResult result = response.getResult();
        
        if (result.hasResultSet()) {
            // Exibe tabela de resultados
            List<String> columns = result.getColumns();
            List<Map<String, Object>> rows = result.getRows();
            
            // Calcula largura das colunas
            Map<String, Integer> columnWidths = new HashMap<>();
            for (String col : columns) {
                columnWidths.put(col, col.length());
            }
            
            for (Map<String, Object> row : rows) {
                for (String col : columns) {
                    Object value = row.get(col);
                    String strValue = value != null ? value.toString() : "NULL";
                    columnWidths.put(col, Math.max(columnWidths.get(col), strValue.length()));
                }
            }
            
            // Cabeçalho
            System.out.print("| ");
            for (String col : columns) {
                System.out.printf("%-" + columnWidths.get(col) + "s | ", col);
            }
            System.out.println();
            
            // Separador
            System.out.print("+-");
            for (String col : columns) {
                System.out.print("-".repeat(columnWidths.get(col)) + "-+-");
            }
            System.out.println();
            
            // Linhas
            for (Map<String, Object> row : rows) {
                System.out.print("| ");
                for (String col : columns) {
                    Object value = row.get(col);
                    String strValue = value != null ? value.toString() : "NULL";
                    System.out.printf("%-" + columnWidths.get(col) + "s | ", strValue);
                }
                System.out.println();
            }
            
            System.out.println("\nLinhas retornadas: " + result.getRowCount());
            
        } else {
            System.out.println("Linhas afetadas: " + result.getUpdateCount());
        }
        
        System.out.println("=".repeat(80) + "\n");
    }
    
    /**
     * Resposta de uma query
     */
    public static class QueryResponse {
        private final boolean success;
        private final DatabaseManager.QueryResult result;
        private final String nodeId;
        private final String errorMessage;
        
        public QueryResponse(boolean success, DatabaseManager.QueryResult result, 
                           String nodeId, String errorMessage) {
            this.success = success;
            this.result = result;
            this.nodeId = nodeId;
            this.errorMessage = errorMessage;
        }
        
        public boolean isSuccess() { return success; }
        public DatabaseManager.QueryResult getResult() { return result; }
        public String getNodeId() { return nodeId; }
        public String getErrorMessage() { return errorMessage; }
    }
}
