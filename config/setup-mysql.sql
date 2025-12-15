-- Script para configurar o MySQL para o DDB

-- Criar usuário para o DDB
CREATE USER IF NOT EXISTS 'ddb_user'@'%' IDENTIFIED BY 'ddb_pass';

-- Criar banco de dados
CREATE DATABASE IF NOT EXISTS ddb;

-- Conceder privilégios
GRANT ALL PRIVILEGES ON ddb.* TO 'ddb_user'@'%';
FLUSH PRIVILEGES;

-- Usar o banco de dados
USE ddb;

-- Tabela de exemplo para testes
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inserir dados de exemplo
INSERT INTO users (name, email) VALUES 
    ('João Silva', 'joao@example.com'),
    ('Maria Santos', 'maria@example.com'),
    ('Pedro Oliveira', 'pedro@example.com')
ON DUPLICATE KEY UPDATE name=VALUES(name);
