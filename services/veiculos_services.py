from database.conn import execute, fetch_all


def cadastrar_veiculo(cliente_id, marca, modelo, ano, placa):
    """
    Cadastra um novo veículo vinculado ao cliente.
    """
    execute(
        """INSERT INTO veiculos (cliente_id, marca, modelo, ano, placa)
           VALUES (%s, %s, %s, %s, %s)""",
        (cliente_id, marca, modelo, ano, placa)
    )


def listar_veiculos():
    """
    Lista todos os veículos com dados do cliente.
    """
    return fetch_all(
        """SELECT v.id, v.placa, v.marca, v.modelo, v.ano,
                  c.nome AS cliente, c.id AS cliente_id
           FROM veiculos v
           JOIN clientes c ON v.cliente_id = c.id
           ORDER BY v.id DESC"""
    )


def listar_veiculos_por_cliente(cliente_id):
    """
    Lista veículos de um cliente específico.
    """
    return fetch_all(
        """SELECT id, placa, marca, modelo, ano
           FROM veiculos
           WHERE cliente_id = %s
           ORDER BY id""",
        (cliente_id,)
    )


def buscar_veiculo(termo):
    """
    Busca veículo por placa, modelo ou marca.
    """
    return fetch_all(
        """SELECT v.id, v.placa, v.marca, v.modelo, v.ano,
                  c.nome AS cliente, c.id AS cliente_id
           FROM veiculos v
           JOIN clientes c ON v.cliente_id = c.id
           WHERE v.placa ILIKE %s OR v.modelo ILIKE %s OR v.marca ILIKE %s
           ORDER BY v.placa
           LIMIT 10""",
        (f"%{termo}%", f"%{termo}%", f"%{termo}%")
    )


def atualizar_veiculo(veiculo_id, marca, modelo, ano, placa):
    """
    Atualiza dados de um veículo.
    """
    execute(
        """UPDATE veiculos
           SET marca=%s, modelo=%s, ano=%s, placa=%s
           WHERE id=%s""",
        (marca, modelo, ano, placa, veiculo_id)
    )


def deletar_veiculo(veiculo_id):
    """
    Remove um veículo (cascata apaga OSs vinculadas).
    """
    execute("DELETE FROM veiculos WHERE id=%s", (veiculo_id,))
