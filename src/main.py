import sys
import os

# Garante que o root do projeto está no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from services.clientes_services import (
    cadastrar_cliente, listar_clientes, buscar_cliente,
    buscar_cliente_por_id, atualizar_cliente, deletar_cliente
)
from services.veiculos_services import (
    cadastrar_veiculo, listar_veiculos, listar_veiculos_por_cliente,
    buscar_veiculo, atualizar_veiculo, deletar_veiculo
)
from services.os_services import (
    abrir_os, listar_os, buscar_os, adicionar_item, listar_itens,
    remover_item, calcular_total, atualizar_status, cancelar_os,
    historico_cliente, faturamento_total, faturamento_mensal,
    top_clientes, servicos_mais_realizados, resumo_dashboard
)

# Serve o frontend a partir da pasta frontend/
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)


@app.route('/')
def index():
    """Serve o frontend no endereço raiz."""
    return send_from_directory(FRONTEND_DIR, 'index.html')


def serialize(obj):
    """Converte tipos especiais do Python para JSON-safe."""
    import decimal, datetime
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def ok(data=None, message="ok", status=200):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    import json
    return app.response_class(
        response=json.dumps(payload, default=serialize),
        status=status,
        mimetype='application/json'
    )


def err(message, status=400):
    return jsonify({"success": False, "message": message}), status


# ─── HEALTH ───────────────────────────────────────────────────────────────────

@app.route('/api/health')
def health():
    return ok(message="ERP Tekar API online")


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@app.route('/api/dashboard')
def dashboard():
    try:
        data = resumo_dashboard()
        return ok(data)
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/dashboard/faturamento-mensal')
def dashboard_faturamento_mensal():
    try:
        data = faturamento_mensal()
        return ok([dict(r) for r in data])
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/dashboard/top-clientes')
def dashboard_top_clientes():
    try:
        data = top_clientes(5)
        return ok([dict(r) for r in data])
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/dashboard/servicos')
def dashboard_servicos():
    try:
        data = servicos_mais_realizados(5)
        return ok([dict(r) for r in data])
    except Exception as e:
        return err(str(e), 500)


# ─── CLIENTES ─────────────────────────────────────────────────────────────────

@app.route('/api/clientes', methods=['GET'])
def get_clientes():
    try:
        termo = request.args.get('q')
        if termo:
            data = buscar_cliente(termo)
        else:
            data = listar_clientes()
        return ok([dict(r) for r in data])
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/clientes/<int:cliente_id>', methods=['GET'])
def get_cliente(cliente_id):
    try:
        data = buscar_cliente_por_id(cliente_id)
        if not data:
            return err("Cliente não encontrado", 404)
        return ok(dict(data))
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/clientes', methods=['POST'])
def post_cliente():
    body = request.get_json()
    nome = (body.get('nome') or '').strip()
    telefone = (body.get('telefone') or '').strip()
    cpf = (body.get('cpf') or '').strip() or None

    if not nome:
        return err("Nome é obrigatório")
    if not telefone:
        return err("Telefone é obrigatório")

    try:
        cadastrar_cliente(nome, telefone, cpf)
        return ok(message="Cliente cadastrado com sucesso", status=201)
    except Exception as e:
        msg = str(e)
        if 'unique' in msg.lower() or 'duplicate' in msg.lower():
            return err("Telefone ou CPF já cadastrado")
        return err(msg, 500)


@app.route('/api/clientes/<int:cliente_id>', methods=['PUT'])
def put_cliente(cliente_id):
    body = request.get_json()
    nome = (body.get('nome') or '').strip()
    telefone = (body.get('telefone') or '').strip()
    cpf = (body.get('cpf') or '').strip() or None

    if not nome:
        return err("Nome é obrigatório")
    if not telefone:
        return err("Telefone é obrigatório")

    try:
        atualizar_cliente(cliente_id, nome, telefone, cpf)
        return ok(message="Cliente atualizado com sucesso")
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/clientes/<int:cliente_id>', methods=['DELETE'])
def delete_cliente(cliente_id):
    try:
        deletar_cliente(cliente_id)
        return ok(message="Cliente removido com sucesso")
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/clientes/<int:cliente_id>/historico')
def get_historico_cliente(cliente_id):
    try:
        data = historico_cliente(cliente_id)
        return ok([dict(r) for r in data])
    except Exception as e:
        return err(str(e), 500)


# ─── VEÍCULOS ─────────────────────────────────────────────────────────────────

@app.route('/api/veiculos', methods=['GET'])
def get_veiculos():
    try:
        termo = request.args.get('q')
        cliente_id = request.args.get('cliente_id')
        if cliente_id:
            data = listar_veiculos_por_cliente(int(cliente_id))
        elif termo:
            data = buscar_veiculo(termo)
        else:
            data = listar_veiculos()
        return ok([dict(r) for r in data])
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/veiculos', methods=['POST'])
def post_veiculo():
    body = request.get_json()
    cliente_id = body.get('cliente_id')
    marca = (body.get('marca') or '').strip()
    modelo = (body.get('modelo') or '').strip()
    ano = body.get('ano')
    placa = (body.get('placa') or '').strip().upper()

    if not cliente_id:
        return err("cliente_id é obrigatório")
    if not placa:
        return err("Placa é obrigatória")

    try:
        cadastrar_veiculo(cliente_id, marca, modelo, ano, placa)
        return ok(message="Veículo cadastrado com sucesso", status=201)
    except Exception as e:
        msg = str(e)
        if 'unique' in msg.lower() or 'duplicate' in msg.lower():
            return err("Placa já cadastrada")
        return err(msg, 500)


@app.route('/api/veiculos/<int:veiculo_id>', methods=['PUT'])
def put_veiculo(veiculo_id):
    body = request.get_json()
    marca = (body.get('marca') or '').strip()
    modelo = (body.get('modelo') or '').strip()
    ano = body.get('ano')
    placa = (body.get('placa') or '').strip().upper()

    if not placa:
        return err("Placa é obrigatória")

    try:
        atualizar_veiculo(veiculo_id, marca, modelo, ano, placa)
        return ok(message="Veículo atualizado com sucesso")
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/veiculos/<int:veiculo_id>', methods=['DELETE'])
def delete_veiculo(veiculo_id):
    try:
        deletar_veiculo(veiculo_id)
        return ok(message="Veículo removido com sucesso")
    except Exception as e:
        return err(str(e), 500)


# ─── ORDENS DE SERVIÇO ────────────────────────────────────────────────────────

@app.route('/api/os', methods=['GET'])
def get_os():
    try:
        status = request.args.get('status')
        data = listar_os(status)
        return ok([dict(r) for r in data])
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/os/<int:os_id>', methods=['GET'])
def get_os_detail(os_id):
    try:
        os_data = buscar_os(os_id)
        if not os_data:
            return err("OS não encontrada", 404)
        itens = listar_itens(os_id)
        total = calcular_total(os_id)
        result = dict(os_data)
        result['itens'] = [dict(i) for i in itens]
        result['total'] = total
        return ok(result)
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/os', methods=['POST'])
def post_os():
    body = request.get_json()
    cliente_id = body.get('cliente_id')
    veiculo_id = body.get('veiculo_id')

    if not cliente_id or not veiculo_id:
        return err("cliente_id e veiculo_id são obrigatórios")

    try:
        os_id = abrir_os(cliente_id, veiculo_id)
        return ok({"id": os_id}, "Ordem de serviço aberta com sucesso", status=201)
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/os/<int:os_id>/status', methods=['PATCH'])
def patch_os_status(os_id):
    body = request.get_json()
    novo_status = body.get('status')
    if not novo_status:
        return err("status é obrigatório")
    try:
        atualizar_status(os_id, novo_status)
        return ok(message=f"Status atualizado para '{novo_status}'")
    except ValueError as e:
        return err(str(e))
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/os/<int:os_id>/itens', methods=['GET'])
def get_itens(os_id):
    try:
        data = listar_itens(os_id)
        return ok([dict(r) for r in data])
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/os/<int:os_id>/itens', methods=['POST'])
def post_item(os_id):
    body = request.get_json()
    descricao = (body.get('descricao') or '').strip()
    quantidade = body.get('quantidade', 1)
    valor_unitario = body.get('valor_unitario')
    tipo = body.get('tipo', 'servico')

    if not descricao:
        return err("Descrição é obrigatória")
    if valor_unitario is None:
        return err("Valor unitário é obrigatório")
    if tipo not in ('servico', 'peca'):
        return err("Tipo deve ser 'servico' ou 'peca'")

    try:
        adicionar_item(os_id, descricao, quantidade, valor_unitario, tipo)
        return ok(message="Item adicionado com sucesso", status=201)
    except ValueError as e:
        return err(str(e))
    except Exception as e:
        return err(str(e), 500)


@app.route('/api/itens/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    try:
        remover_item(item_id)
        return ok(message="Item removido com sucesso")
    except Exception as e:
        return err(str(e), 500)


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('ERP TEKAR -- rodando em http://localhost:5000')
    #app.run(host='0.0.0.0', port=5000)  >> para rodar com ip
    app.run(debug=True, port=5000)
