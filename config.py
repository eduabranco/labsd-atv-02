# config.py
# Configuração dos Nós (ID: (IP, PORTA))
# O ID deve ser um inteiro único. O maior ID será o Líder inicial/preferencial.

NODES = {
    1: ('127.0.0.1', 5001), # Máquina 1
    2: ('127.0.0.1', 5002), # Máquina 2 (Simulando localhost com portas diferentes)
    3: ('127.0.0.1', 5003)  # Máquina 3
}

DB_CONFIG = {
    'user': 'root',
    'password': 'password',  
    'unix_socket': '/var/run/mysqld/mysqld.sock', # <--- ADICIONE ISTO
    'host': '127.0.0.1',           # Usando IP ao invés de 'localhost' para forçar TCP
    'database': 'dist_db'
}