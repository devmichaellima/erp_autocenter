from database.conn import execute, fetch_all


def cadastrar_cliente(nome, telefone, cpf=None):
    """
    Cadastra um novo cliente no banco de dados.
    Valida telefone e CPF únicos.
    """
    execute(
        "INSERT INTO clientes (nome, telefone, cpf) VALUES (%s, %s, %s)",
        (nome, telefone, cpf or None)
    )


def listar_clientes():
    """
    Lista todos os clientes cadastrados.
    """
    return fetch_all("SELECT * FROM clientes ORDER BY id DESC")


def buscar_cliente(termo):
    """
    Busca cliente por id, nome, telefone ou CPF.
    """
    query = """
        SELECT id, nome, telefone, cpf, criado_em
        FROM clientes
        WHERE
            CAST(id AS TEXT) = %s
            OR nome ILIKE %s
            OR telefone LIKE %s
            OR cpf LIKE %s
        ORDER BY nome
        LIMIT 10
    """
    params = (termo, f"%{termo}%", f"%{termo}%", f"%{termo}%")
    return fetch_all(query, params)


def buscar_cliente_por_id(cliente_id):
    """
    Retorna um cliente pelo ID.
    """
    result = fetch_all(
        "SELECT id, nome, telefone, cpf, criado_em FROM clientes WHERE id = %s",
        (cliente_id,)
    )
    return result[0] if result else None


def atualizar_cliente(cliente_id, nome, telefone, cpf=None):
    """
    Atualiza dados de um cliente.
    """
    execute(
        "UPDATE clientes SET nome=%s, telefone=%s, cpf=%s WHERE id=%s",
        (nome, telefone, cpf or None, cliente_id)
    )


def deletar_cliente(cliente_id):
    """
    Remove um cliente (cascata apaga veículos e OSs).
    """
    execute("DELETE FROM clientes WHERE id=%s", (cliente_id,))


def selecionar_cliente():
    """
    Helper CLI: busca e seleciona um cliente interativamente.
    """
    termo = input("Buscar cliente (id, nome, telefone ou cpf): ")
    clientes = buscar_cliente(termo)

    if not clientes:
        print("Nenhum cliente encontrado.\n")
        return None

    print("\nResultados:")
    for i, c in enumerate(clientes, start=1):
        print(f"{i} - {c['nome']} | {c['telefone']} | {c['cpf']}")

    try:
        escolha = int(input("Escolha o número: "))
        return clientes[escolha - 1]['id']
    except (ValueError, IndexError):
        print("Opção inválida.\n")
        return None