package br.uf.labsd.ddb.node;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import br.uf.labsd.ddb.config.NodeConfig;
import br.uf.labsd.ddb.protocol.Message;

/**
 * Gerencia a comunicação em rede do nó
 */
public class NetworkManager {
    private static final Logger logger = LoggerFactory.getLogger(NetworkManager.class);
    
    private final DDBNode node;
    private ServerSocket serverSocket;
    private ExecutorService executor;
    private volatile boolean running = false;
    
    public NetworkManager(DDBNode node) {
        this.node = node;
    }
    
    /**
     * Inicia o servidor de rede
     */
    public void start() throws IOException {
        NodeConfig config = node.getConfig();
        serverSocket = new ServerSocket(config.getPort());
        executor = Executors.newCachedThreadPool();
        running = true;
        
        // Thread para aceitar conexões
        executor.submit(() -> {
            while (running) {
                try {
                    Socket clientSocket = serverSocket.accept();
                    executor.submit(() -> handleClient(clientSocket));
                } catch (IOException e) {
                    if (running) {
                        logger.error("Erro ao aceitar conexão", e);
                    }
                }
            }
        });
        
        logger.info("Servidor de rede iniciado na porta {}", config.getPort());
    }
    
    /**
     * Para o servidor de rede
     */
    public void stop() {
        running = false;
        
        try {
            if (serverSocket != null && !serverSocket.isClosed()) {
                serverSocket.close();
            }
        } catch (IOException e) {
            logger.error("Erro ao fechar servidor", e);
        }
        
        if (executor != null) {
            executor.shutdownNow();
        }
        
        logger.info("Servidor de rede parado");
    }
    
    /**
     * Trata conexão de cliente
     */
    private void handleClient(Socket socket) {
        try (BufferedReader in = new BufferedReader(
                new InputStreamReader(socket.getInputStream()));
             PrintWriter out = new PrintWriter(socket.getOutputStream(), true)) {
            
            String messageJson = in.readLine();
            if (messageJson != null && !messageJson.isEmpty()) {
                Message message = Message.fromJson(messageJson);
                
                // Ignora mensagens do próprio nó
                if (!message.getSourceNodeId().equals(node.getConfig().getNodeId())) {
                    node.processMessage(message);
                }
            }
            
        } catch (Exception e) {
            logger.error("Erro ao tratar cliente", e);
        } finally {
            try {
                socket.close();
            } catch (IOException e) {
                logger.error("Erro ao fechar socket", e);
            }
        }
    }
    
    /**
     * Envia mensagem para um peer específico
     */
    public boolean sendToPeer(NodeConfig.PeerNode peer, Message message) {
        try (Socket socket = new Socket(peer.getHost(), peer.getPort());
             PrintWriter out = new PrintWriter(socket.getOutputStream(), true)) {
            
            out.println(message.toJson());
            logger.debug("Mensagem {} enviada para {}", message.getType(), peer.getNodeId());
            return true;
            
        } catch (IOException e) {
            logger.warn("Erro ao enviar mensagem para {}: {}", 
                       peer.getNodeId(), e.getMessage());
            return false;
        }
    }
    
    /**
     * Envia mensagem em broadcast para todos os peers
     */
    public void broadcast(Message message) {
        logger.debug("Broadcasting mensagem tipo {} para {} peers", 
                    message.getType(), node.getConfig().getPeers().size());
        
        for (NodeConfig.PeerNode peer : node.getConfig().getPeers()) {
            executor.submit(() -> sendToPeer(peer, message));
        }
    }
    
    /**
     * Envia mensagem para um nó específico por ID
     */
    public boolean sendToNode(String nodeId, Message message) {
        NodeConfig.PeerNode peer = findPeerByNodeId(nodeId);
        if (peer != null) {
            message.setTargetNodeId(nodeId);
            return sendToPeer(peer, message);
        }
        logger.warn("Peer não encontrado: {}", nodeId);
        return false;
    }
    
    /**
     * Encontra peer por ID
     */
    private NodeConfig.PeerNode findPeerByNodeId(String nodeId) {
        for (NodeConfig.PeerNode peer : node.getConfig().getPeers()) {
            if (peer.getNodeId().equals(nodeId)) {
                return peer;
            }
        }
        return null;
    }
}
