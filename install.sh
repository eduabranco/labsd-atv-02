#!/bin/bash
# Installation script for Distributed Database System

echo "============================================================"
echo "  Distributed Database System - Installation"
echo "============================================================"
echo

# Check Python version
echo "[*] Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "[!] Python 3 is not installed. Please install Python 3.6 or higher."
    exit 1
fi
echo

# Install Python dependencies
echo "[*] Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[!] Failed to install dependencies"
    exit 1
fi
echo "[✓] Dependencies installed successfully"
echo

# Check MySQL
echo "[*] Checking MySQL installation..."
if command -v mysql &> /dev/null; then
    echo "[✓] MySQL is installed"
    mysql --version
else
    echo "[!] MySQL is not installed"
    echo "    Install with: sudo apt install mysql-server (Ubuntu/Debian)"
    echo "               or: sudo yum install mysql-server (RHEL/CentOS)"
    echo "               or: brew install mysql (macOS)"
    exit 1
fi
echo

# Ask if user wants to run setup
echo "============================================================"
read -p "Run database setup now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 db_setup.py
fi

echo
echo "============================================================"
echo "  Installation Complete!"
echo "============================================================"
echo
echo "Next steps:"
echo "  1. Configure node IPs in config.py"
echo "  2. Run on each node: python middleware.py <NODE_ID>"
echo "  3. Connect with: python client.py"
echo
echo "For more information, see README.md or QUICKSTART.md"
echo
