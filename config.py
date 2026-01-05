# config.py
# Configuração dos Nós (ID: (IP, PORTA))
# O ID deve ser um inteiro único. O maior ID será o Líder inicial/preferencial.

NODES = {
    1: ('127.0.0.1', 5001), # Máquina 1
    2: ('127.0.0.1', 5002), # Máquina 2 (Simulando localhost com portas diferentes)
    3: ('127.0.0.1', 5003)  # Máquina 3
}

DB_CONFIG = {
    'user': 'root',          # O usuário que criamos
    'password': 'password', # A senha definida no SQL acima
    'host': '127.0.0.1',         # Use IP explícito em vez de 'localhost' para forçar TCP
    'database': 'dist_db',
    'port': 3306                 # Garante a porta padrão
}