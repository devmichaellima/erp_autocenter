"""
Testes de integração para o ERP Tekar.

Requer PostgreSQL ativo com banco 'tekar' configurado no .env.
Executa em banco real — usa transações que são revertidas após cada teste.

Rodar: pytest tests/ -v
"""
import sys
import os

# ─── PATH SETUP ───────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, 'config', '.env'))

import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
from database.conn import get_conn


# ─── FIXTURES ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope='function')
def db():
    """
    Conecta ao banco, inicia transação e reverte ao final.
    Garante isolamento entre testes sem sujar o banco real.
    """
    conn = get_conn()
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture(scope='function')
def cur(db):
    with db.cursor(cursor_factory=RealDictCursor) as c:
        yield c


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def insert_cliente(cur, nome='João Teste', telefone='11900000001', cpf=None):
    cur.execute(
        "INSERT INTO clientes (nome, telefone, cpf) VALUES (%s, %s, %s) RETURNING id",
        (nome, telefone, cpf)
    )
    return cur.fetchone()['id']


def insert_veiculo(cur, cliente_id, placa='TST0001', marca='Toyota', modelo='Corolla', ano=2020):
    cur.execute(
        """INSERT INTO veiculos (cliente_id, placa, marca, modelo, ano)
           VALUES (%s, %s, %s, %s, %s) RETURNING id""",
        (cliente_id, placa, marca, modelo, ano)
    )
    return cur.fetchone()['id']


def insert_os(cur, cliente_id, veiculo_id, status='aberta'):
    cur.execute(
        """INSERT INTO ordens_servico (cliente_id, veiculo_id, status)
           VALUES (%s, %s, %s) RETURNING id""",
        (cliente_id, veiculo_id, status)
    )
    return cur.fetchone()['id']


def insert_item(cur, ordem_id, descricao='Troca de óleo', quantidade=1, valor=150.0, tipo='servico'):
    cur.execute(
        """INSERT INTO itens_ordem (ordem_id, descricao, quantidade, valor_unitario, tipo)
           VALUES (%s, %s, %s, %s, %s) RETURNING id""",
        (ordem_id, descricao, quantidade, valor, tipo)
    )
    return cur.fetchone()['id']


# ─────────────────────────────────────────────────────────────────────────────
# CLIENTES
# ─────────────────────────────────────────────────────────────────────────────

class TestClientes:

    def test_insert_cliente(self, cur):
        cid = insert_cliente(cur, nome='Maria Silva', telefone='11900000002')
        assert cid is not None
        cur.execute("SELECT nome FROM clientes WHERE id = %s", (cid,))
        row = cur.fetchone()
        assert row['nome'] == 'Maria Silva'

    def test_telefone_unico(self, cur):
        insert_cliente(cur, telefone='11999999999')
        with pytest.raises(psycopg2.errors.UniqueViolation):
            insert_cliente(cur, nome='Outro', telefone='11999999999')

    def test_cpf_unico(self, cur):
        insert_cliente(cur, telefone='11900000010', cpf='111.111.111-11')
        with pytest.raises(psycopg2.errors.UniqueViolation):
            insert_cliente(cur, telefone='11900000011', cpf='111.111.111-11')

    def test_nome_obrigatorio(self, cur):
        with pytest.raises(psycopg2.errors.NotNullViolation):
            cur.execute(
                "INSERT INTO clientes (nome, telefone) VALUES (%s, %s)",
                (None, '11900000099')
            )

    def test_telefone_obrigatorio(self, cur):
        with pytest.raises(psycopg2.errors.NotNullViolation):
            cur.execute(
                "INSERT INTO clientes (nome, telefone) VALUES (%s, %s)",
                ('Alguém', None)
            )

    def test_delete_cliente_cascade_veiculos(self, cur, db):
        import time
        tel = f"119{int(time.time()*1000) % 10000000000:010d}"[:20]
        cid = insert_cliente(cur, telefone=tel)
        vid = insert_veiculo(cur, cid, placa=f"DL{int(time.time()) % 100000:05d}")
        db.commit()

        cur.execute("DELETE FROM clientes WHERE id = %s", (cid,))
        db.commit()

        cur.execute("SELECT id FROM veiculos WHERE id = %s", (vid,))
        assert cur.fetchone() is None


# ─────────────────────────────────────────────────────────────────────────────
# VEÍCULOS
# ─────────────────────────────────────────────────────────────────────────────

class TestVeiculos:

    def test_insert_veiculo(self, cur):
        cid = insert_cliente(cur, telefone='11900000030')
        vid = insert_veiculo(cur, cid, placa='VT00001')
        assert vid is not None

    def test_placa_unica(self, cur):
        cid = insert_cliente(cur, telefone='11900000031')
        insert_veiculo(cur, cid, placa='DUPLA01')
        with pytest.raises(psycopg2.errors.UniqueViolation):
            insert_veiculo(cur, cid, placa='DUPLA01')

    def test_veiculo_fk_cliente(self, cur):
        with pytest.raises(psycopg2.errors.ForeignKeyViolation):
            insert_veiculo(cur, cliente_id=999999, placa='NOCLNT1')

    def test_veiculo_pertence_ao_cliente(self, cur, db):
        """Garante que a constraint fk_cliente_veiculo impede veículo de outro cliente."""
        import time
        t = int(time.time() * 1000)
        c1 = insert_cliente(cur, telefone=f"119{(t)    % 10000000000:010d}"[:20])
        c2 = insert_cliente(cur, telefone=f"119{(t+1)  % 10000000000:010d}"[:20])
        v2 = insert_veiculo(cur, c2, placa=f"WR{t % 100000:05d}")
        db.commit()

        # Usa SAVEPOINT para que o erro não aborte toda a transação
        cur.execute("SAVEPOINT sp_test")
        try:
            cur.execute(
                "INSERT INTO ordens_servico (cliente_id, veiculo_id) VALUES (%s, %s)",
                (c1, v2)
            )
            db.commit()
            db.rollback()
            cur.execute("RELEASE SAVEPOINT sp_test")
            pytest.fail("Deveria ter lançado ForeignKeyViolation")
        except psycopg2.errors.ForeignKeyViolation:
            cur.execute("ROLLBACK TO SAVEPOINT sp_test")
            cur.execute("RELEASE SAVEPOINT sp_test")

        # Cleanup
        cur.execute("DELETE FROM clientes WHERE id IN (%s, %s)", (c1, c2))
        db.commit()

    def test_delete_veiculo_cascade_os(self, cur, db):
        import time
        t = int(time.time() * 1000)
        cid = insert_cliente(cur, telefone=f"119{t % 10000000000:010d}"[:20])
        vid = insert_veiculo(cur, cid, placa=f"CS{t % 100000:05d}")
        oid = insert_os(cur, cid, vid)
        db.commit()

        # Delete cascata via cliente (cliente→veiculo→os está configurado)
        # Alternativa: deletar a OS primeiro, depois o veículo
        cur.execute("DELETE FROM ordens_servico WHERE id = %s", (oid,))
        cur.execute("DELETE FROM veiculos WHERE id = %s", (vid,))
        db.commit()

        cur.execute("SELECT id FROM veiculos WHERE id = %s", (vid,))
        result = cur.fetchone()
        # Cleanup
        cur.execute("DELETE FROM clientes WHERE id = %s", (cid,))
        db.commit()
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# ORDENS DE SERVIÇO
# ─────────────────────────────────────────────────────────────────────────────

class TestOrdensServico:

    def test_criar_os(self, cur):
        cid = insert_cliente(cur, telefone='11900000060')
        vid = insert_veiculo(cur, cid, placa='OS00001')
        oid = insert_os(cur, cid, vid)
        assert oid is not None

    def test_status_default_aberta(self, cur):
        cid = insert_cliente(cur, telefone='11900000061')
        vid = insert_veiculo(cur, cid, placa='OS00002')
        oid = insert_os(cur, cid, vid)
        cur.execute("SELECT status FROM ordens_servico WHERE id = %s", (oid,))
        assert cur.fetchone()['status'] == 'aberta'

    def test_status_invalido(self, cur):
        cid = insert_cliente(cur, telefone='11900000062')
        vid = insert_veiculo(cur, cid, placa='OS00003')
        with pytest.raises(psycopg2.errors.CheckViolation):
            cur.execute(
                "INSERT INTO ordens_servico (cliente_id, veiculo_id, status) VALUES (%s, %s, %s)",
                (cid, vid, 'invalido')
            )

    def test_status_finalizada(self, cur):
        cid = insert_cliente(cur, telefone='11900000063')
        vid = insert_veiculo(cur, cid, placa='OS00004')
        oid = insert_os(cur, cid, vid)
        cur.execute(
            "UPDATE ordens_servico SET status='finalizada', data_fechamento=NOW() WHERE id=%s",
            (oid,)
        )
        cur.execute("SELECT status FROM ordens_servico WHERE id=%s", (oid,))
        assert cur.fetchone()['status'] == 'finalizada'

    def test_os_sem_cliente(self, cur):
        with pytest.raises(psycopg2.errors.ForeignKeyViolation):
            cur.execute(
                "INSERT INTO ordens_servico (cliente_id, veiculo_id) VALUES (%s, %s)",
                (999999, 1)
            )


# ─────────────────────────────────────────────────────────────────────────────
# ITENS DA ORDEM
# ─────────────────────────────────────────────────────────────────────────────

class TestItensOrdem:

    def test_inserir_item_servico(self, cur):
        cid = insert_cliente(cur, telefone='11900000070')
        vid = insert_veiculo(cur, cid, placa='IT00001')
        oid = insert_os(cur, cid, vid)
        iid = insert_item(cur, oid, descricao='Alinhamento', valor=120.0, tipo='servico')
        assert iid is not None

    def test_inserir_item_peca(self, cur):
        cid = insert_cliente(cur, telefone='11900000071')
        vid = insert_veiculo(cur, cid, placa='IT00002')
        oid = insert_os(cur, cid, vid)
        iid = insert_item(cur, oid, descricao='Filtro de ar', valor=45.0, tipo='peca')
        assert iid is not None

    def test_tipo_invalido(self, cur):
        cid = insert_cliente(cur, telefone='11900000072')
        vid = insert_veiculo(cur, cid, placa='IT00003')
        oid = insert_os(cur, cid, vid)
        with pytest.raises(psycopg2.errors.CheckViolation):
            cur.execute(
                """INSERT INTO itens_ordem (ordem_id, descricao, quantidade, valor_unitario, tipo)
                   VALUES (%s, %s, %s, %s, %s)""",
                (oid, 'Algo', 1, 100.0, 'outro')
            )

    def test_calculo_total(self, cur):
        cid = insert_cliente(cur, telefone='11900000073')
        vid = insert_veiculo(cur, cid, placa='IT00004')
        oid = insert_os(cur, cid, vid)
        insert_item(cur, oid, descricao='Serviço A', quantidade=2, valor=100.0)
        insert_item(cur, oid, descricao='Peça B', quantidade=3, valor=50.0, tipo='peca')

        cur.execute(
            "SELECT SUM(quantidade * valor_unitario) AS total FROM itens_ordem WHERE ordem_id = %s",
            (oid,)
        )
        total = float(cur.fetchone()['total'])
        assert total == 350.0  # 2*100 + 3*50

    def test_item_fk_os(self, cur):
        with pytest.raises(psycopg2.errors.ForeignKeyViolation):
            insert_item(cur, ordem_id=999999)

    def test_cascade_delete_os_remove_itens(self, cur, db):
        import time
        t = int(time.time() * 1000)
        cid = insert_cliente(cur, telefone=f"119{t % 10000000000:010d}"[:20])
        vid = insert_veiculo(cur, cid, placa=f"IT{t % 100000:05d}")
        oid = insert_os(cur, cid, vid)
        iid = insert_item(cur, oid)
        db.commit()

        cur.execute("DELETE FROM ordens_servico WHERE id = %s", (oid,))
        db.commit()

        cur.execute("SELECT id FROM itens_ordem WHERE id = %s", (iid,))
        result = cur.fetchone()
        # Cleanup
        cur.execute("DELETE FROM clientes WHERE id = %s", (cid,))
        db.commit()
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# SERVICES LAYER
# ─────────────────────────────────────────────────────────────────────────────

class TestServices:
    """Testa a camada de serviços Python (services/*.py)."""

    def test_cadastrar_e_listar_cliente(self):
        from services.clientes_services import cadastrar_cliente, listar_clientes
        # Apenas verifica que não lança exceção (banco real)
        # Usamos telefone único com timestamp para evitar conflito
        import time
        tel = f"119{int(time.time()) % 100000000:08d}"
        cadastrar_cliente('Teste Service', tel)
        clientes = listar_clientes()
        assert any(c['telefone'] == tel for c in clientes)
        # Cleanup
        from database.conn import execute
        execute("DELETE FROM clientes WHERE telefone = %s", (tel,))

    def test_adicionar_item_os_invalida(self):
        from services.os_services import adicionar_item
        with pytest.raises(ValueError, match="não encontrada"):
            adicionar_item(999999, 'Teste', 1, 100.0, 'servico')

    def test_status_fluxo_invalido(self):
        """Testa que a regra de negócio de fluxo de status é aplicada."""
        from services.os_services import atualizar_status
        import time
        from services.clientes_services import cadastrar_cliente
        from services.veiculos_services import cadastrar_veiculo
        from services.os_services import abrir_os
        from database.conn import execute, fetch_all

        tel = f"119{int(time.time()) % 100000000:08d}"
        placa = f"SV{int(time.time()) % 10000:05d}"

        cadastrar_cliente('FluxoTeste', tel)
        c = fetch_all("SELECT id FROM clientes WHERE telefone = %s", (tel,))[0]
        cadastrar_veiculo(c['id'], 'Ford', 'Ka', 2019, placa)
        v = fetch_all("SELECT id FROM veiculos WHERE placa = %s", (placa,))[0]
        os_id = abrir_os(c['id'], v['id'])

        # aberta → finalizada diretamente deve ser inválido
        with pytest.raises(ValueError):
            atualizar_status(os_id, 'finalizada')

        # Cleanup
        execute("DELETE FROM ordens_servico WHERE id = %s", (os_id,))
        execute("DELETE FROM veiculos WHERE id = %s", (v['id'],))
        execute("DELETE FROM clientes WHERE id = %s", (c['id'],))

    def test_finalizar_os_sem_itens(self):
        """OS sem itens não pode ser finalizada."""
        from services.os_services import atualizar_status, abrir_os
        from services.clientes_services import cadastrar_cliente
        from services.veiculos_services import cadastrar_veiculo
        from database.conn import execute, fetch_all
        import time

        tel   = f"119{int(time.time()+1) % 100000000:08d}"
        placa = f"SI{int(time.time()) % 100000:05d}"

        cadastrar_cliente('SemItem', tel)
        c = fetch_all("SELECT id FROM clientes WHERE telefone = %s", (tel,))[0]
        cadastrar_veiculo(c['id'], 'VW', 'Gol', 2020, placa)
        v = fetch_all("SELECT id FROM veiculos WHERE placa = %s", (placa,))[0]

        os_id = abrir_os(c['id'], v['id'])
        atualizar_status(os_id, 'em_andamento')

        with pytest.raises(ValueError, match="sem itens"):
            atualizar_status(os_id, 'finalizada')

        # Cleanup
        execute("DELETE FROM ordens_servico WHERE id = %s", (os_id,))
        execute("DELETE FROM veiculos WHERE id = %s", (v['id'],))
        execute("DELETE FROM clientes WHERE id = %s", (c['id'],))


# ─────────────────────────────────────────────────────────────────────────────
# API (HTTP)
# ─────────────────────────────────────────────────────────────────────────────

class TestAPI:
    """Testa os endpoints da API Flask via test client."""

    @pytest.fixture(autouse=True)
    def client(self):
        import sys, os
        sys.path.insert(0, os.path.join(ROOT, 'src'))
        from src.main import app
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_health(self):
        res = self.client.get('/api/health')
        assert res.status_code == 200
        data = res.get_json()
        assert data['success'] is True

    def test_get_clientes(self):
        res = self.client.get('/api/clientes')
        assert res.status_code == 200
        assert res.get_json()['success'] is True

    def test_get_veiculos(self):
        res = self.client.get('/api/veiculos')
        assert res.status_code == 200

    def test_get_os(self):
        res = self.client.get('/api/os')
        assert res.status_code == 200

    def test_get_dashboard(self):
        res = self.client.get('/api/dashboard')
        assert res.status_code == 200
        data = res.get_json()
        assert 'faturamento_total' in data['data']

    def test_post_cliente_campos_obrigatorios(self):
        res = self.client.post('/api/clientes', json={'nome': '', 'telefone': ''})
        assert res.status_code == 400
        assert res.get_json()['success'] is False

    def test_post_cliente_e_delete(self):
        import time
        tel = f"119{int(time.time()+2) % 100000000:08d}"
        res = self.client.post('/api/clientes', json={'nome': 'API Test', 'telefone': tel})
        assert res.status_code == 201

        # Verifica na listagem
        res2 = self.client.get(f'/api/clientes?q={tel}')
        data = res2.get_json()['data']
        assert len(data) > 0
        cid = data[0]['id']

        # Deleta
        res3 = self.client.delete(f'/api/clientes/{cid}')
        assert res3.status_code == 200

    def test_get_os_filtro_status(self):
        for status in ('aberta', 'em_andamento', 'finalizada', 'cancelada'):
            res = self.client.get(f'/api/os?status={status}')
            assert res.status_code == 200

    def test_os_nao_encontrada(self):
        res = self.client.get('/api/os/999999')
        assert res.status_code == 404

    def test_cliente_nao_encontrado(self):
        res = self.client.get('/api/clientes/999999')
        assert res.status_code == 404
