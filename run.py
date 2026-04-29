#!/usr/bin/env python
"""
Ponto de entrada da API Flask — ERP Tekar Autocenter.

Uso:
    python run.py

A API sobe em http://localhost:5000
O frontend fica em frontend/index.html (abrir no browser)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))

from src.main import app

if __name__ == '__main__':
    print("=" * 50)
    print("  ERP TEKAR -- Autocenter")
    print("=" * 50)
    print("  API:      http://localhost:5000/api")
    print("  Frontend: abrir frontend/index.html no browser")
    print("=" * 50)
    app.run(debug=True, port=5000, host='0.0.0.0')
