#!/usr/bin/env python3
"""
Test script to demonstrate MySQL compatibility improvements
This script tests all supported authentication methods
"""

import mysql.connector
from mysql.connector import Error
import sys

def test_connection(name, config):
    """Test a specific connection configuration"""
    print(f"\n[*] Testing: {name}")
    print(f"    Config: user='{config.get('user')}', password={'<set>' if config.get('password') else '<none>'}")
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"    ✓ SUCCESS! MySQL version: {version}")
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print(f"    ✗ FAILED: {e}")
        return False

def main():
    print("=" * 70)
    print("  MySQL Compatibility Test Suite")
    print("=" * 70)
    
    # Test configurations
    test_configs = [
        ("Root with no password", {
            'user': 'root',
            'host': '127.0.0.1'
        }),
        ("Root with empty password", {
            'user': 'root',
            'password': '',
            'host': '127.0.0.1'
        }),
        ("Root with password 'password'", {
            'user': 'root',
            'password': 'password',
            'host': '127.0.0.1'
        }),
        ("Root with socket", {
            'user': 'root',
            'password': 'password',
            'unix_socket': '/var/run/mysqld/mysqld.sock'
        }),
    ]
    
    # Try to import config_db.py if it exists
    try:
        from config_db import DB_CONFIG
        test_configs.append(("config_db.py (auto-generated)", DB_CONFIG))
        print("\n[*] Found config_db.py - will test it too!")
    except ImportError:
        print("\n[*] config_db.py not found - run db_setup.py to generate it")
    
    # Try to import from config.py
    try:
        from config import DB_CONFIG as config_main
        test_configs.append(("config.py (main config)", config_main))
    except ImportError:
        pass
    
    print(f"\n[*] Will test {len(test_configs)} configurations...")
    
    # Run tests
    results = []
    for name, config in test_configs:
        result = test_connection(name, config)
        results.append((name, result))
    
    # Summary
    print("\n" + "=" * 70)
    print("  Test Summary")
    print("=" * 70)
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Success Rate: {success_count}/{total_count} ({100*success_count//total_count}%)")
    
    if success_count > 0:
        print("\n  ✓ At least one configuration works!")
        print("  Your system can connect to MySQL.")
    else:
        print("\n  ✗ No configurations worked.")
        print("  Try running: python3 db_setup.py")
    
    print("\n" + "=" * 70)
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    sys.exit(main())
