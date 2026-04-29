from services.clientes_services import cadastrar_cliente, listar_clientes

def menu_clientes():
    """
    Menu de clientes.
    """
    while True:
        print("1 - Cadastrar cliente")
        print("2 - Listar clientes")
        print("0 - Voltar")

        op = input("Escolha: ")

        if op == "1":
            nome = input("Nome: ")
            telefone = input("Telefone: ")
            cpf = input("CPF: ")

            cadastrar_cliente(nome, telefone, cpf)

        elif op == "2":
            clientes = listar_clientes()
            for c in clientes:
                print(c)

        elif op == "0":
            break

