package br.uf.labsd.ddb.database;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import br.uf.labsd.ddb.config.NodeConfig;

/**
 * Gerenciador de conexão e operações no banco de dados MySQL
 */
public class DatabaseManager {
    private static final Logger logger = LoggerFactory.getLogger(DatabaseManager.class);
    
    private final NodeConfig.DatabaseConfig config;
    private Connection connection;
    
    public DatabaseManager(NodeConfig.DatabaseConfig config) {
        this.config = config;
    }
    
    /**
     * Conecta ao banco de dados
     */
    public void connect() throws SQLException {
        try {
            Class.forName("com.mysql.cj.jdbc.Driver");
            connection = DriverManager.getConnection(
                config.getJdbcUrl(),
                config.getUsername(),
                config.getPassword()
            );
            connection.setAutoCommit(false); // Controle manual de transações
            logger.info("Conectado ao banco de dados: {}", config.getJdbcUrl());
        } catch (ClassNotFoundException e) {
            throw new SQLException("Driver MySQL não encontrado", e);
        }
    }
    
    /**
     * Desconecta do banco de dados
     */
    public void disconnect() {
        if (connection != null) {
            try {
                connection.close();
                logger.info("Desconectado do banco de dados");
            } catch (SQLException e) {
                logger.error("Erro ao desconectar", e);
            }
        }
    }
    
    /**
     * Executa uma query SELECT
     */
    public QueryResult executeQuery(String sql) throws SQLException {
        logger.info("Executando query: {}", sql);
        
        try (Statement stmt = connection.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            
            return buildQueryResult(rs);
        }
    }
    
    /**
     * Executa uma query de modificação (INSERT, UPDATE, DELETE)
     */
    public int executeUpdate(String sql) throws SQLException {
        logger.info("Executando update: {}", sql);
        
        try (Statement stmt = connection.createStatement()) {
            return stmt.executeUpdate(sql);
        }
    }
    
    /**
     * Executa uma query genérica
     */
    public QueryResult execute(String sql) throws SQLException {
        logger.info("Executando SQL: {}", sql);
        
        try (Statement stmt = connection.createStatement()) {
            boolean hasResultSet = stmt.execute(sql);
            
            if (hasResultSet) {
                try (ResultSet rs = stmt.getResultSet()) {
                    return buildQueryResult(rs);
                }
            } else {
                int updateCount = stmt.getUpdateCount();
                QueryResult result = new QueryResult();
                result.setUpdateCount(updateCount);
                return result;
            }
        }
    }
    
    /**
     * Inicia uma transação
     */
    public void beginTransaction() throws SQLException {
        connection.setAutoCommit(false);
        logger.debug("Transação iniciada");
    }
    
    /**
     * Commita uma transação
     */
    public void commit() throws SQLException {
        connection.commit();
        logger.debug("Transação commitada");
    }
    
    /**
     * Faz rollback de uma transação
     */
    public void rollback() {
        try {
            connection.rollback();
            logger.debug("Transação revertida");
        } catch (SQLException e) {
            logger.error("Erro ao fazer rollback", e);
        }
    }
    
    /**
     * Verifica se a conexão está ativa
     */
    public boolean isConnected() {
        try {
            return connection != null && !connection.isClosed() && connection.isValid(5);
        } catch (SQLException e) {
            return false;
        }
    }
    
    /**
     * Constrói resultado da query a partir do ResultSet
     */
    private QueryResult buildQueryResult(ResultSet rs) throws SQLException {
        QueryResult result = new QueryResult();
        ResultSetMetaData metadata = rs.getMetaData();
        int columnCount = metadata.getColumnCount();
        
        // Adiciona nomes das colunas
        List<String> columns = new ArrayList<>();
        for (int i = 1; i <= columnCount; i++) {
            columns.add(metadata.getColumnName(i));
        }
        result.setColumns(columns);
        
        // Adiciona linhas
        List<Map<String, Object>> rows = new ArrayList<>();
        while (rs.next()) {
            Map<String, Object> row = new HashMap<>();
            for (int i = 1; i <= columnCount; i++) {
                row.put(metadata.getColumnName(i), rs.getObject(i));
            }
            rows.add(row);
        }
        result.setRows(rows);
        
        return result;
    }
    
    /**
     * Resultado de uma query
     */
    public static class QueryResult {
        private List<String> columns;
        private List<Map<String, Object>> rows;
        private int updateCount = -1;
        
        public List<String> getColumns() { return columns; }
        public void setColumns(List<String> columns) { this.columns = columns; }
        
        public List<Map<String, Object>> getRows() { return rows; }
        public void setRows(List<Map<String, Object>> rows) { this.rows = rows; }
        
        public int getUpdateCount() { return updateCount; }
        public void setUpdateCount(int updateCount) { this.updateCount = updateCount; }
        
        public boolean hasResultSet() {
            return columns != null && rows != null;
        }
        
        public int getRowCount() {
            return rows != null ? rows.size() : 0;
        }
    }
}
