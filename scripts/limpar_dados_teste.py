from dotenv import load_dotenv
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))
import psycopg2

conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT')
)
cur = conn.cursor()

nomes_teste = ('Joao Teste', 'Teste Service', 'FluxoTeste', 'SemItem', 'API Test')
for nome in nomes_teste:
    cur.execute("DELETE FROM clientes WHERE nome = %s", (nome,))

# Remove clientes criados automaticamente pelos testes (telefones gerados por timestamp)
cur.execute("DELETE FROM clientes WHERE nome ILIKE '%teste%' OR nome ILIKE '%fluxo%'")

deleted = cur.rowcount
conn.commit()
print(f"Limpeza: {deleted} registros de teste removidos.")
conn.close()
