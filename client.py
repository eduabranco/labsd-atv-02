from socket import socket, AF_INET, SOCK_STREAM
from json import loads, dumps
from random import choice
from hashlib import md5
from config import NODES
from typing import Any
import time

def calculate_checksum(data: dict[str, Any]) -> str:
    return md5(dumps(data, sort_keys = True).encode()).hexdigest()

def send_query(query: str) -> dict[str, Any]:
    # Escolhe um nó aleatório para Load Balancing inicial
    node_id = choice(list(NODES.keys()))
    ip, port = NODES[node_id]

    msg = {
        'type': 'EXECUTE_QUERY',
        'payload': {'query': query}
    }

    msg['checksum'] = calculate_checksum(msg['payload'])
    msg['source_id'] = 0 # 0 representa cliente externo

    print(f"--- Conectando ao Nó {node_id} ({ip}: {port}) ---")

    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip, port))
        s.sendall(dumps(msg).encode())

        resp = s.recv(4096).decode()
        if not resp:
            s.close()
            return {'status': 'error', 'msg': 'No response from server'}

        data = loads(resp)
        s.close()
        return data
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}

def format_table(data: list[dict]) -> str:
    """Format results as a MySQL-style table"""
    if not data:
        return ""
    
    # Get column names
    columns = list(data[0].keys())
    
    # Calculate column widths
    widths = {col: len(str(col)) for col in columns}
    for row in data:
        for col in columns:
            widths[col] = max(widths[col], len(str(row.get(col, ''))))
    
    # Build separator line
    separator = '+' + '+'.join(['-' * (widths[col] + 2) for col in columns]) + '+'
    
    # Build header
    header = '|' + '|'.join([f" {col:{widths[col]}} " for col in columns]) + '|'
    
    # Build rows
    rows = []
    for row in data:
        rows.append('|' + '|'.join([f" {str(row.get(col, '')):{widths[col]}} " for col in columns]) + '|')
    
    # Combine all parts
    result = [separator, header, separator]
    result.extend(rows)
    result.append(separator)
    
    return '\n'.join(result)

def print_help():
    """Print MySQL-style help"""
    print("""
List of all MySQL-like commands:
Note: All commands end with ; (semicolon)

General:
  \\q, quit, exit     Exit the client
  \\h, help           Display this help
  \\c                 Clear the current input statement
  
SQL Commands:
  SELECT ...         Query data
  INSERT ...         Insert data
  UPDATE ...         Update data
  DELETE ...         Delete data
  CREATE ...         Create table/database
  DROP ...           Drop table/database
  SHOW TABLES;       List tables
  DESCRIBE <table>;  Show table structure
""")

def get_multiline_query() -> str:
    """Read a multi-line SQL query until semicolon is found"""
    lines = []
    prompt = "mysql> "
    
    while True:
        try:
            line = input(prompt)
            
            # Handle special commands
            if line.strip() in ['\\q', 'quit', 'exit', 'EXIT', 'QUIT']:
                return 'EXIT'
            if line.strip() in ['\\h', 'help', 'HELP']:
                print_help()
                return ''
            if line.strip() == '\\c':
                return ''
            
            lines.append(line)
            
            # Check if query is complete (ends with semicolon)
            if line.strip().endswith(';'):
                break
            
            # Change prompt for continuation
            prompt = "    -> "
            
        except EOFError:
            return 'EXIT'
        except KeyboardInterrupt:
            print("\n^C")
            return ''
    
    return ' '.join(lines)

def main():
    print("Welcome to the Distributed MySQL monitor.  Commands end with ; or \\g.")
    print(f"Server version: DDB 1.0 (Distributed Database)")
    print()
    print()
    print("Type 'help;' or '\\h' for help. Type '\\c' to clear the current input statement.")
    print()

    while True:
        query = get_multiline_query()
        
        # Handle exit command
        if query == 'EXIT':
            print("Bye")
            break
        
        # Skip empty queries
        if not query.strip():
            continue
        
        # Remove trailing semicolon for processing
        query = query.strip().rstrip(';')
        
        if not query:
            continue
        
        # Execute query and measure time
        start_time = time.time()
        result = send_query(query)
        elapsed_time = time.time() - start_time

        if not result:
            print("ERROR: No response received from server")
            continue

        if result.get('status') == 'success':
            # Display results
            if 'data' in result and result['data']:
                data = result['data']
                
                if isinstance(data, list) and len(data) > 0:
                    # Check if it's a list of dictionaries (SELECT result)
                    if isinstance(data[0], dict):
                        print(format_table(data))
                        row_count = len(data)
                        print(f"{row_count} row{'s' if row_count != 1 else ''} in set ({elapsed_time:.2f} sec)")
                    else:
                        # Simple list output
                        for row in data:
                            print(row)
                        print(f"{len(data)} row{'s' if len(data) != 1 else ''} in set ({elapsed_time:.2f} sec)")
                elif isinstance(data, str):
                    print(data)
                else:
                    print(f"Query OK ({elapsed_time:.2f} sec)")
            else:
                # For INSERT/UPDATE/DELETE operations
                msg = result.get('msg', 'Query OK')
                print(f"{msg} ({elapsed_time:.2f} sec)")
            
            # REQUISITO #16: Mostrar nó que executou a query
            executed_node = result.get('node')
            if executed_node is not None:
                print(f"[Executed on Node: {executed_node}]")
            
            # Se foi replicado em múltiplos nós (2PC), mostrar todos
            replicated_nodes = result.get('nodes')
            if replicated_nodes:
                print(f"[Replicated to Nodes: {', '.join(map(str, replicated_nodes))}]")
        else:
            error_msg = result.get('msg', 'Unknown error')
            print(f"ERROR: {error_msg}")
        
        print()

if __name__ == "__main__": main()