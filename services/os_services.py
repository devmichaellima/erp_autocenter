from database.conn import execute, fetch_all


def abrir_os(cliente_id, veiculo_id):
    """
    Abre uma nova ordem de serviço com status 'aberta'.
    Valida que o veículo pertence ao cliente (via constraint do banco).
    """
    result = fetch_all(
        """INSERT INTO ordens_servico (cliente_id, veiculo_id, status)
           VALUES (%s, %s, 'aberta')
           RETURNING id""",
        (cliente_id, veiculo_id)
    )
    return result[0]['id'] if result else None


def listar_os(status=None):
    """
    Lista ordens de serviço com dados do cliente e veículo.
    Filtra por status se informado.
    """
    base_query = """
        SELECT os.id, os.status, os.data_abertura, os.data_fechamento,
               c.nome AS cliente, c.telefone,
               v.placa, v.modelo, v.marca,
               COALESCE(SUM(i.quantidade * i.valor_unitario), 0) AS total
        FROM ordens_servico os
        JOIN clientes c ON os.cliente_id = c.id
        JOIN veiculos v ON os.veiculo_id = v.id
        LEFT JOIN itens_ordem i ON i.ordem_id = os.id
    """
    if status:
        base_query += " WHERE os.status = %s"
        base_query += " GROUP BY os.id, c.nome, c.telefone, v.placa, v.modelo, v.marca ORDER BY os.id DESC"
        return fetch_all(base_query, (status,))
    else:
        base_query += " GROUP BY os.id, c.nome, c.telefone, v.placa, v.modelo, v.marca ORDER BY os.id DESC"
        return fetch_all(base_query)


def buscar_os(os_id):
    """
    Retorna dados completos de uma OS específica.
    """
    result = fetch_all(
        """SELECT os.id, os.status, os.data_abertura, os.data_fechamento,
                  os.cliente_id, os.veiculo_id,
                  c.nome AS cliente, c.telefone,
                  v.placa, v.modelo, v.marca, v.ano
           FROM ordens_servico os
           JOIN clientes c ON os.cliente_id = c.id
           JOIN veiculos v ON os.veiculo_id = v.id
           WHERE os.id = %s""",
        (os_id,)
    )
    return result[0] if result else None


def adicionar_item(ordem_id, descricao, quantidade, valor_unitario, tipo):
    """
    Adiciona um item (serviço ou peça) a uma OS.
    Valida que a OS existe e está aberta ou em andamento.
    """
    os_data = fetch_all(
        "SELECT status FROM ordens_servico WHERE id = %s", (ordem_id,)
    )
    if not os_data:
        raise ValueError(f"OS #{ordem_id} não encontrada.")
    if os_data[0]['status'] in ('finalizada', 'cancelada'):
        raise ValueError(f"Não é possível adicionar itens a uma OS {os_data[0]['status']}.")
    if valor_unitario < 0:
        raise ValueError("Valor unitário não pode ser negativo.")
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")

    execute(
        """INSERT INTO itens_ordem (ordem_id, descricao, quantidade, valor_unitario, tipo)
           VALUES (%s, %s, %s, %s, %s)""",
        (ordem_id, descricao, quantidade, valor_unitario, tipo)
    )


def listar_itens(ordem_id):
    """
    Retorna todos os itens de uma OS.
    """
    return fetch_all(
        """SELECT id, descricao, quantidade, valor_unitario, tipo,
                  (quantidade * valor_unitario) AS subtotal
           FROM itens_ordem
           WHERE ordem_id = %s
           ORDER BY id""",
        (ordem_id,)
    )


def remover_item(item_id):
    """
    Remove um item de uma OS.
    """
    execute("DELETE FROM itens_ordem WHERE id = %s", (item_id,))


def calcular_total(ordem_id):
    """
    Calcula o total da OS (soma de quantidade * valor_unitario).
    """
    result = fetch_all(
        """SELECT COALESCE(SUM(quantidade * valor_unitario), 0) AS total
           FROM itens_ordem
           WHERE ordem_id = %s""",
        (ordem_id,)
    )
    return float(result[0]['total']) if result else 0.0


def atualizar_status(ordem_id, novo_status):
    """
    Atualiza o status de uma OS seguindo fluxo lógico:
    aberta → em_andamento → finalizada
    qualquer → cancelada
    """
    status_validos = ('aberta', 'em_andamento', 'finalizada', 'cancelada')
    if novo_status not in status_validos:
        raise ValueError(f"Status inválido: {novo_status}")

    os_data = buscar_os(ordem_id)
    if not os_data:
        raise ValueError(f"OS #{ordem_id} não encontrada.")

    status_atual = os_data['status']

    # Valida fluxo de status
    fluxo = {
        'aberta': ['em_andamento', 'cancelada'],
        'em_andamento': ['finalizada', 'cancelada'],
        'finalizada': [],
        'cancelada': []
    }

    if novo_status not in fluxo.get(status_atual, []):
        raise ValueError(
            f"Transição inválida: {status_atual} → {novo_status}"
        )

    # OS não pode ser finalizada sem itens
    if novo_status == 'finalizada':
        itens = listar_itens(ordem_id)
        if not itens:
            raise ValueError("Não é possível finalizar uma OS sem itens.")

        execute(
            """UPDATE ordens_servico
               SET status = %s, data_fechamento = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (novo_status, ordem_id)
        )
    else:
        execute(
            "UPDATE ordens_servico SET status = %s WHERE id = %s",
            (novo_status, ordem_id)
        )


def cancelar_os(ordem_id):
    """
    Cancela uma OS (atalho para atualizar_status).
    """
    atualizar_status(ordem_id, 'cancelada')


def historico_cliente(cliente_id):
    """
    Retorna histórico de OS de um cliente.
    """
    return fetch_all(
        """SELECT os.id, os.status, os.data_abertura, os.data_fechamento,
                  v.placa, v.modelo,
                  COALESCE(SUM(i.quantidade * i.valor_unitario), 0) AS total
           FROM ordens_servico os
           JOIN veiculos v ON os.veiculo_id = v.id
           LEFT JOIN itens_ordem i ON i.ordem_id = os.id
           WHERE os.cliente_id = %s
           GROUP BY os.id, v.placa, v.modelo
           ORDER BY os.data_abertura DESC""",
        (cliente_id,)
    )


# ─── ANALYTICS / DASHBOARD ────────────────────────────────────────────────────

def faturamento_total():
    """Faturamento total das OSs finalizadas."""
    result = fetch_all(
        """SELECT COALESCE(SUM(i.quantidade * i.valor_unitario), 0) AS total
           FROM itens_ordem i
           JOIN ordens_servico os ON i.ordem_id = os.id
           WHERE os.status = 'finalizada'"""
    )
    return float(result[0]['total']) if result else 0.0


def faturamento_mensal():
    """Faturamento agrupado por mês (últimos 12 meses)."""
    return fetch_all(
        """SELECT TO_CHAR(os.data_fechamento, 'YYYY-MM') AS mes,
                  COALESCE(SUM(i.quantidade * i.valor_unitario), 0) AS total
           FROM ordens_servico os
           JOIN itens_ordem i ON i.ordem_id = os.id
           WHERE os.status = 'finalizada'
             AND os.data_fechamento >= NOW() - INTERVAL '12 months'
           GROUP BY mes
           ORDER BY mes"""
    )


def top_clientes(limit=5):
    """Clientes que mais gastaram."""
    return fetch_all(
        """SELECT c.id, c.nome, c.telefone,
                  SUM(i.quantidade * i.valor_unitario) AS total
           FROM itens_ordem i
           JOIN ordens_servico os ON i.ordem_id = os.id
           JOIN clientes c ON os.cliente_id = c.id
           WHERE os.status = 'finalizada'
           GROUP BY c.id, c.nome, c.telefone
           ORDER BY total DESC
           LIMIT %s""",
        (limit,)
    )


def servicos_mais_realizados(limit=5):
    """Serviços mais frequentes."""
    return fetch_all(
        """SELECT descricao, COUNT(*) AS quantidade,
                  SUM(quantidade * valor_unitario) AS receita
           FROM itens_ordem
           WHERE tipo = 'servico'
           GROUP BY descricao
           ORDER BY quantidade DESC
           LIMIT %s""",
        (limit,)
    )


def resumo_dashboard():
    """Retorna KPIs gerais para o dashboard."""
    stats = fetch_all(
        """SELECT
               COUNT(*) FILTER (WHERE status = 'aberta') AS os_abertas,
               COUNT(*) FILTER (WHERE status = 'em_andamento') AS os_andamento,
               COUNT(*) FILTER (WHERE status = 'finalizada') AS os_finalizadas,
               COUNT(*) FILTER (WHERE status = 'cancelada') AS os_canceladas,
               COUNT(*) AS os_total
           FROM ordens_servico"""
    )[0]

    clientes_total = fetch_all("SELECT COUNT(*) AS total FROM clientes")[0]['total']
    veiculos_total = fetch_all("SELECT COUNT(*) AS total FROM veiculos")[0]['total']
    faturamento = faturamento_total()

    return {
        'os_abertas': int(stats['os_abertas']),
        'os_andamento': int(stats['os_andamento']),
        'os_finalizadas': int(stats['os_finalizadas']),
        'os_canceladas': int(stats['os_canceladas']),
        'os_total': int(stats['os_total']),
        'clientes_total': int(clientes_total),
        'veiculos_total': int(veiculos_total),
        'faturamento_total': faturamento
    }
