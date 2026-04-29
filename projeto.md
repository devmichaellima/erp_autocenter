# 🚗 ERP AUTOCENTER TEKAR (VERSÃO PROFISSIONAL)

## 📌 Visão Geral

O **ERP Autocenter Tekar** é um sistema de gestão operacional e analítica para autocenters, baseado em uma modelagem relacional robusta e orientada a regras de negócio reais.

Diferente de sistemas simplificados, esta versão foi projetada para:

* Garantir **integridade dos dados**
* Refletir **fluxos reais de oficina**
* Permitir **escala e automação**
* Servir como base para **BI e integrações**

---

## 🎯 Objetivos do Sistema

* Cadastro estruturado de clientes e veículos
* Gestão completa de ordens de serviço (OS)
* Registro detalhado de serviços e peças
* Controle de status operacional
* Base para análise financeira e comercial
* Preparação para automações (n8n, WhatsApp)

---

## 🧠 Arquitetura

### 🔹 Backend

* Python (lógica + regras de negócio)

### 🔹 Banco de Dados

* PostgreSQL (modelagem relacional com constraints)

### 🔹 Camadas

1. Persistência (SQL)
2. Lógica de negócio (Python)
3. Interface (CLI → evoluindo para API)

---

## 🗄️ Modelagem do Banco

---

### 👤 TABELA: clientes

| Campo     | Tipo        | Regra            |
| --------- | ----------- | ---------------- |
| id        | SERIAL      | PK               |
| nome      | VARCHAR(50) | Obrigatório      |
| telefone  | VARCHAR(20) | Único            |
| cpf       | VARCHAR(20) | Único (opcional) |
| criado_em | TIMESTAMP   | Auto             |

### 🧠 Regras importantes:

* Não pode existir cliente com telefone duplicado
* CPF também é único (controle fiscal)

---

### 🚗 TABELA: veiculos

| Campo      | Tipo        | Regra    |
| ---------- | ----------- | -------- |
| id         | SERIAL      | PK       |
| cliente_id | INTEGER     | FK       |
| marca      | VARCHAR     | Opcional |
| modelo     | VARCHAR     | Opcional |
| ano        | INTEGER     | Opcional |
| placa      | VARCHAR(10) | Única    |
| criado_em  | TIMESTAMP   | Auto     |

### 🔗 Relacionamento:

* 1 cliente → N veículos

### ⚠️ Regra crítica:

```sql
FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
```

👉 Se cliente for deletado → veículos também são

---

### 📄 TABELA: ordens_servico

| Campo           | Tipo      | Descrição    |
| --------------- | --------- | ------------ |
| id              | SERIAL    | Número da OS |
| cliente_id      | INTEGER   | Cliente      |
| veiculo_id      | INTEGER   | Veículo      |
| status          | VARCHAR   | Estado da OS |
| data_abertura   | TIMESTAMP | Abertura     |
| data_fechamento | TIMESTAMP | Encerramento |

---

### 🔥 STATUS DA OS

* `aberta`
* `em_andamento`
* `finalizada`
* `cancelada`

👉 Controlado via `CHECK`

---

### 🔒 REGRA AVANÇADA (MUITO IMPORTANTE)

```sql
FOREIGN KEY (cliente_id, veiculo_id)
REFERENCES veiculos(cliente_id, id)
```

👉 Garante que:

> o veículo realmente pertence ao cliente

👉 Isso é nível sistema profissional

---

### 🧾 TABELA: itens_ordem

| Campo          | Tipo          | Descrição       |
| -------------- | ------------- | --------------- |
| id             | SERIAL        | PK              |
| ordem_id       | INTEGER       | FK              |
| descricao      | VARCHAR(150)  | Item            |
| quantidade     | INT           | Default 1       |
| valor_unitario | NUMERIC(10,2) | Valor           |
| tipo           | VARCHAR(20)   | servico ou peca |

---

### 🔗 Relacionamento:

* 1 OS → N itens

---

### 🧠 Regra de negócio:

* Um item pode ser:

  * serviço
  * peça

👉 Isso permite:

* cálculo detalhado
* relatórios mais precisos

---

## ⚙️ FUNCIONALIDADES DO SISTEMA

---

### ✅ 1. Cadastro de Cliente

* valida telefone único
* opcional CPF

---

### ✅ 2. Cadastro de Veículo

* vinculado ao cliente
* valida placa única

---

### ✅ 3. Abertura de Ordem de Serviço

Fluxo:

1. selecionar cliente
2. selecionar veículo
3. criar OS com status `aberta`

---

### ✅ 4. Adição de Itens na OS

* adicionar serviços
* adicionar peças
* múltiplos itens por OS

---

### ✅ 5. Cálculo de Total

```text
Total OS = SUM(quantidade * valor_unitario)
```

👉 calculado via SQL ou Python

---

### ✅ 6. Finalização da OS

* muda status → `finalizada`
* registra `data_fechamento`

---

### ✅ 7. Consulta de Histórico

* por cliente
* por veículo
* por período

---

## 🧠 CONSULTAS IMPORTANTES (SQL)

---

### 💰 Faturamento total

```sql
SELECT SUM(quantidade * valor_unitario)
FROM itens_ordem;
```

---

### 🧑‍🔧 Cliente que mais gastou

```sql
SELECT c.nome, SUM(i.quantidade * i.valor_unitario) AS total
FROM itens_ordem i
JOIN ordens_servico os ON i.ordem_id = os.id
JOIN clientes c ON os.cliente_id = c.id
GROUP BY c.nome
ORDER BY total DESC;
```

---

### 🔧 Serviços mais realizados

```sql
SELECT descricao, COUNT(*) 
FROM itens_ordem
WHERE tipo = 'servico'
GROUP BY descricao
ORDER BY COUNT(*) DESC;
```

---

## 🧠 REGRAS DE NEGÓCIO CRÍTICAS

* cliente deve existir antes da OS
* veículo deve pertencer ao cliente
* OS não pode ser finalizada sem itens
* valores não podem ser negativos
* status deve seguir fluxo lógico

---

## 🚀 ROADMAP DE EVOLUÇÃO

---

### 🔹 Fase 1 (Atual)

* CLI funcional
* CRUD completo
* geração de OS

---

### 🔹 Fase 2

* validação forte de dados
* evitar duplicidades inteligentes
* logs de operação

---

### 🔹 Fase 3

* exportação Excel
* integração Power BI
* métricas financeiras

---

### 🔹 Fase 4 (DIFERENCIAL)

* integração com n8n
* envio automático via WhatsApp
* alertas de retorno de cliente
* automação de follow-up

---

## 🧠 HABILIDADES DESENVOLVIDAS

Este projeto desenvolve:

* Modelagem de banco avançada
* SQL profissional (JOIN, agregações)
* Python aplicado (backend)
* Regras de negócio reais
* Pensamento sistêmico
* Base para engenharia de dados

---

## 🎯 CONCLUSÃO

Esse ERP não é mais um projeto simples.

👉 Ele já representa:

* sistema real de oficina
* base escalável
* arquitetura correta
* alto valor de mercado

Se evoluído corretamente, pode virar:

* produto SaaS
* ferramenta interna
* portfólio forte

---

👉 Próximo passo recomendado:
Transformar isso em **API (FastAPI)** ou **dashboard integrado**.

# 🎨 FRONTEND — ERP AUTOCENTER TEKAR (DASHBOARD LOCAL)

## 📌 Objetivo

Criar um **frontend moderno, clean e funcional**, rodando localmente, para:

* Visualizar dados do sistema
* Interagir com o backend Python
* Exibir dashboards simples e intuitivos
* Simular um ERP real com boa UX

---

## 🧠 Estratégia (simples e profissional)

👉 Stack:

* HTML → estrutura
* CSS → design (minimalista)
* JavaScript → lógica + integração

👉 Backend:

* Python (vamos evoluir para API local com Flask/FastAPI)

---

## 🎯 Estrutura do Frontend

```bash
frontend/
│
├── index.html
├── styles.css
├── app.js
```

---

# 🧱 1. HTML (estrutura do dashboard)

```html
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <title>ERP Tekar</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>

  <div class="container">
    
    <aside class="sidebar">
      <h2>TEKAR</h2>
      <ul>
        <li onclick="loadDashboard()">Dashboard</li>
        <li onclick="loadClientes()">Clientes</li>
        <li onclick="loadOS()">Ordens de Serviço</li>
      </ul>
    </aside>

    <main class="content" id="content">
      <h1>Dashboard</h1>
      <div class="cards">
        <div class="card">
          <h3>Faturamento</h3>
          <p id="faturamento">R$ 0</p>
        </div>

        <div class="card">
          <h3>Ordens</h3>
          <p id="ordens">0</p>
        </div>
      </div>

      <canvas id="grafico"></canvas>
    </main>

  </div>

  <script src="app.js"></script>
</body>
</html>
```

---

# 🎨 2. CSS (design moderno e minimalista)

```css
body {
  margin: 0;
  font-family: Arial, sans-serif;
  background: #f5f6fa;
}

.container {
  display: flex;
}

.sidebar {
  width: 220px;
  background: #1e272e;
  color: white;
  height: 100vh;
  padding: 20px;
}

.sidebar h2 {
  text-align: center;
}

.sidebar ul {
  list-style: none;
  padding: 0;
}

.sidebar li {
  padding: 10px;
  cursor: pointer;
  transition: 0.2s;
}

.sidebar li:hover {
  background: #485460;
}

.content {
  flex: 1;
  padding: 20px;
}

.cards {
  display: flex;
  gap: 20px;
}

.card {
  background: white;
  padding: 20px;
  border-radius: 10px;
  width: 200px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}

.card h3 {
  margin: 0;
  font-size: 16px;
}

.card p {
  font-size: 24px;
  margin-top: 10px;
}
```

---

# ⚙️ 3. JavaScript (lógica + integração)

```javascript
// simulação inicial (depois vem API real)
function loadDashboard() {
  document.getElementById("faturamento").innerText = "R$ 5.200";
  document.getElementById("ordens").innerText = "12";
}

// exemplo de navegação
function loadClientes() {
  document.getElementById("content").innerHTML = `
    <h1>Clientes</h1>
    <p>Lista de clientes aqui...</p>
  `;
}

function loadOS() {
  document.getElementById("content").innerHTML = `
    <h1>Ordens de Serviço</h1>
    <p>Lista de OS aqui...</p>
  `;
}
```

---

# 🚀 4. INTEGRAÇÃO COM PYTHON (PRÓXIMO PASSO)

👉 Para conectar com seu backend:

Vamos criar uma API com **FastAPI** ou **Flask**

Exemplo (FastAPI):

```python
from fastapi import FastAPI
import psycopg2

app = FastAPI()

@app.get("/faturamento")
def faturamento():
    # query no banco
    return {"total": 5200}
```

---

## 🔗 Front chama API:

```javascript
async function carregarFaturamento() {
  const res = await fetch("http://localhost:8000/faturamento");
  const data = await res.json();

  document.getElementById("faturamento").innerText = "R$ " + data.total;
}
```

---

# 📊 Evolução do Dashboard

Você pode adicionar:

* gráfico de faturamento (Chart.js)
* serviços mais realizados
* clientes que mais gastam

---

# 🎨 PRINCÍPIOS DE DESIGN APLICADOS

* minimalismo (menos é mais)
* foco em dados importantes
* navegação lateral simples
* cores neutras
* feedback visual rápido

---

# 🚀 ROADMAP FRONTEND

### 🔹 Fase 1 (agora)

* layout básico
* navegação
* dados mockados

---

### 🔹 Fase 2

* integração com API Python
* dados reais do banco

---

### 🔹 Fase 3

* gráficos (Chart.js)
* filtros (data, cliente)

---

### 🔹 Fase 4 (nível profissional)

* autenticação
* responsividade
* deploy local ou cloud

---

# 🎯 CONCLUSÃO

Você agora tem:

* backend estruturado
* banco robusto
* frontend funcional
* base de sistema real

👉 Isso já é um ERP inicial completo.

---


