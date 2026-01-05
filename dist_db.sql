-- 1. Cria o banco de dados
CREATE DATABASE IF NOT EXISTS dist_db;

-- 2. Cria um usuário específico para o middleware
-- Substitua 'sua_senha_forte' pela senha que desejar
CREATE USER 'ddb_user'@'localhost' IDENTIFIED WITH mysql_native_password BY 'sua_senha_forte';

-- 3. Dá permissão total nesse banco
GRANT ALL PRIVILEGES ON dist_db.* TO 'ddb_user'@'localhost';

-- 4. Cria a tabela necessária
USE dist_db;
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    nome VARCHAR(100), 
    email VARCHAR(100)
);

-- 5. Aplica as permissões
FLUSH PRIVILEGES;
EXIT;