package br.uf.labsd.ddb;

import br.uf.labsd.ddb.config.NodeConfig;
import br.uf.labsd.ddb.node.DDBNode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Classe principal para iniciar um nó do DDB
 */
public class Main {
    private static final Logger logger = LoggerFactory.getLogger(Main.class);
    
    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Uso: java -jar distributed-database.jar <config-file>");
            System.err.println("Exemplo: java -jar distributed-database.jar config/node1.json");
            System.exit(1);
        }
        
        String configFile = args[0];
        
        try {
            // Carrega configuração
            logger.info("Carregando configuração de: {}", configFile);
            NodeConfig config = NodeConfig.loadFromFile(configFile);
            
            // Cria e inicia o nó
            DDBNode node = new DDBNode(config);
            
            // Hook para shutdown gracioso
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                logger.info("Recebido sinal de shutdown...");
                node.stop();
            }));
            
            // Inicia o nó
            node.start();
            
            logger.info("Nó {} iniciado com sucesso!", config.getNodeId());
            logger.info("Pressione Ctrl+C para parar o nó.");
            
            // Mantém a aplicação rodando
            Thread.currentThread().join();
            
        } catch (Exception e) {
            logger.error("Erro ao iniciar nó", e);
            System.exit(1);
        }
    }
}
