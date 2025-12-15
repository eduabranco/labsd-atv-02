#!/bin/bash

# Script para iniciar 3 instâncias MySQL via Docker

echo "=== Configurando Banco de Dados Distribuído ==="
echo ""

# Para containers existentes
echo "Parando e removendo containers antigos..."
docker stop mysql-node1 mysql-node2 mysql-node3 2>/dev/null
docker rm mysql-node1 mysql-node2 mysql-node3 2>/dev/null

# Inicia nó 1
echo "Iniciando MySQL Node 1 (porta 3307)..."
docker run -d --name mysql-node1 -p 3307:3306 \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=ddb \
  -e MYSQL_USER=ddb_user \
  -e MYSQL_PASSWORD=ddb_pass \
  mysql:8.0

# Inicia nó 2
echo "Iniciando MySQL Node 2 (porta 3308)..."
docker run -d --name mysql-node2 -p 3308:3306 \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=ddb \
  -e MYSQL_USER=ddb_user \
  -e MYSQL_PASSWORD=ddb_pass \
  mysql:8.0

# Inicia nó 3
echo "Iniciando MySQL Node 3 (porta 3309)..."
docker run -d --name mysql-node3 -p 3309:3306 \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=ddb \
  -e MYSQL_USER=ddb_user \
  -e MYSQL_PASSWORD=ddb_pass \
  mysql:8.0

echo ""
echo "Aguardando MySQL iniciar (30 segundos)..."
sleep 30

# Criar tabelas em cada nó
echo ""
echo "Criando tabelas de exemplo..."
docker exec -i mysql-node1 mysql -uddb_user -pddb_pass ddb < config/setup-mysql.sql
docker exec -i mysql-node2 mysql -uddb_user -pddb_pass ddb < config/setup-mysql.sql
docker exec -i mysql-node3 mysql -uddb_user -pddb_pass ddb < config/setup-mysql.sql

echo ""
echo "=== Setup Completo ==="
echo "Nós MySQL disponíveis:"
echo "  - Node 1: localhost:3307"
echo "  - Node 2: localhost:3308"
echo "  - Node 3: localhost:3309"
echo ""
echo "Credenciais:"
echo "  - Usuário: ddb_user"
echo "  - Senha: ddb_pass"
echo "  - Database: ddb"
echo ""
