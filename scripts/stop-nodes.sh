#!/bin/bash

# Script para parar todos os nós DDB

echo "Parando nós DDB..."

if [ -f .ddb_pids ]; then
    PIDS=$(cat .ddb_pids)
    kill $PIDS 2>/dev/null
    echo "Nós parados: $PIDS"
    rm .ddb_pids
else
    echo "Arquivo .ddb_pids não encontrado"
    echo "Tentando parar processos manualmente..."
    pkill -f "distributed-database"
fi

echo "Concluído!"
