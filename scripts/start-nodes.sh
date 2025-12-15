#!/bin/bash

# Script para iniciar os 3 nós DDB

echo "=== Iniciando Nós do DDB ==="
echo ""

# Compilar projeto
echo "Compilando projeto..."
mvn clean package -q

if [ $? -ne 0 ]; then
    echo "Erro ao compilar projeto!"
    exit 1
fi

JAR_FILE="target/distributed-database-1.0-SNAPSHOT-jar-with-dependencies.jar"

# Iniciar nós em background
echo "Iniciando Node 1..."
java -jar $JAR_FILE config/node1.json > logs/node1.log 2>&1 &
NODE1_PID=$!
echo "  PID: $NODE1_PID"

sleep 2

echo "Iniciando Node 2..."
java -jar $JAR_FILE config/node2.json > logs/node2.log 2>&1 &
NODE2_PID=$!
echo "  PID: $NODE2_PID"

sleep 2

echo "Iniciando Node 3..."
java -jar $JAR_FILE config/node3.json > logs/node3.log 2>&1 &
NODE3_PID=$!
echo "  PID: $NODE3_PID"

echo ""
echo "=== Nós DDB Iniciados ==="
echo "PIDs: $NODE1_PID $NODE2_PID $NODE3_PID"
echo ""
echo "Logs disponíveis em:"
echo "  - logs/node1.log"
echo "  - logs/node2.log"
echo "  - logs/node3.log"
echo ""
echo "Para parar os nós: kill $NODE1_PID $NODE2_PID $NODE3_PID"
echo ""

# Salvar PIDs
echo "$NODE1_PID $NODE2_PID $NODE3_PID" > .ddb_pids
