package br.uf.labsd.ddb.client;

import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;

import br.uf.labsd.ddb.config.NodeConfig;

/**
 * Interface de linha de comando para acessar o DDB
 */
public class ClientCLI {
    
    public static void main(String[] args) {
        System.out.println("=== Cliente DDB - Banco de Dados Distribuído ===\n");
        
        // Configura nós do DDB
        List<NodeConfig.PeerNode> nodes = new ArrayList<>();
        nodes.add(new NodeConfig.PeerNode("node1", "localhost", 5001));
        nodes.add(new NodeConfig.PeerNode("node2", "localhost", 5002));
        nodes.add(new NodeConfig.PeerNode("node3", "localhost", 5003));
        
        DDBClient client = new DDBClient(nodes);
        
        Scanner scanner = new Scanner(System.in);
        boolean running = true;
        
        System.out.println("Nós disponíveis:");
        for (NodeConfig.PeerNode node : nodes) {
            System.out.println("  - " + node.getNodeId() + " (" + node.getHost() + ":" + node.getPort() + ")");
        }
        System.out.println("\nDigite 'help' para ver os comandos disponíveis.\n");
        
        while (running) {
            System.out.print("ddb> ");
            String input = scanner.nextLine().trim();
            
            if (input.isEmpty()) {
                continue;
            }
            
            String[] parts = input.split("\\s+", 2);
            String command = parts[0].toLowerCase();
            
            switch (command) {
                case "help":
                    showHelp();
                    break;
                    
                case "exit":
                case "quit":
                    running = false;
                    System.out.println("Encerrando cliente...");
                    break;
                    
                case "select":
                case "insert":
                case "update":
                case "delete":
                case "create":
                case "drop":
                case "alter":
                    executeSQL(client, input);
                    break;
                    
                default:
                    System.out.println("Comando não reconhecido. Digite 'help' para ajuda.");
            }
        }
        
        scanner.close();
    }
    
    private static void showHelp() {
        System.out.println("\nComandos disponíveis:");
        System.out.println("  SELECT ... - Executa query de seleção");
        System.out.println("  INSERT ... - Insere dados");
        System.out.println("  UPDATE ... - Atualiza dados");
        System.out.println("  DELETE ... - Remove dados");
        System.out.println("  CREATE ... - Cria tabela/banco");
        System.out.println("  DROP ...   - Remove tabela/banco");
        System.out.println("  ALTER ...  - Altera estrutura");
        System.out.println("  help       - Mostra esta ajuda");
        System.out.println("  exit/quit  - Sai do cliente");
        System.out.println("\nExemplos:");
        System.out.println("  SELECT * FROM users;");
        System.out.println("  INSERT INTO users (name, email) VALUES ('João', 'joao@example.com');");
        System.out.println("  UPDATE users SET name = 'Maria' WHERE id = 1;");
        System.out.println();
    }
    
    private static void executeSQL(DDBClient client, String sql) {
        try {
            DDBClient.QueryResponse response = client.executeQuery(sql);
            client.displayResult(response);
        } catch (Exception e) {
            System.out.println("ERRO: " + e.getMessage());
        }
    }
}
