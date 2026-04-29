# ERP Autocenter Tekar

Sistema de gestão (ERP) para autocenter desenvolvido com foco em aplicação prática, análise de dados e automação.

---

## Visão Geral

O ERP Autocenter Tekar é um sistema que permite:

* Gerenciar clientes e veículos
* Criar e controlar ordens de serviço (OS)
* Registrar serviços e peças
* Analisar faturamento e desempenho
* Servir como base para automações futuras

---

## Objetivos

* Centralizar dados do negócio
* Melhorar o controle operacional
* Permitir análise de dados financeiros e comerciais
* Criar base para automações e integração com outras ferramentas

---

## Arquitetura do Sistema

### Backend

* Python
* PostgreSQL

### Frontend

* HTML
* CSS
* JavaScript (dashboard local)

### Integrações planejadas

* Power BI
* n8n
* API com FastAPI

---

## Estrutura do Projeto

```bash
project/
│
├── backend/
│   ├── database.py
│   ├── services.py
│   ├── models.sql
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│
├── README.md
```

---

## Modelagem do Banco de Dados

### Tabela clientes

* id (SERIAL, PK)
* nome (VARCHAR, obrigatório)
* telefone (VARCHAR, único)
* cpf (VARCHAR, único, opcional)
* criado_em (TIMESTAMP)

---

### Tabela veiculos

* id (SERIAL, PK)
* cliente_id (FK)
* marca
* modelo
* ano
* placa (única)
* criado_em

Relacionamento:

* Um cliente pode ter vários veículos

---

### Tabela ordens_servico

* id (SERIAL, PK)
* cliente_id (FK)
* veiculo_id (FK)
* status (aberta, em_andamento, finalizada, cancelada)
* data_abertura
* data_fechamento

Regras:

* O veículo deve pertencer ao cliente (constraint composta)

---

### Tabela itens_ordem

* id (SERIAL, PK)
* ordem_id (FK)
* descricao
* quantidade
* valor_unitario
* tipo (servico ou peca)

Relacionamento:

* Uma ordem de serviço pode ter vários itens

---

## Funcionalidades

### Cadastro de clientes

* Validação de telefone único
* Registro opcional de CPF

---

### Cadastro de veículos

* Associação com cliente
* Validação de placa única

---

### Ordem de serviço

* Criação de OS vinculada ao cliente e veículo
* Controle de status
* Registro de data de abertura e fechamento

---

### Itens da ordem

* Inclusão de serviços e peças
* Controle de quantidade e valor
* Cálculo do total da ordem

---

### Consulta e análise

* Histórico por cliente
* Histórico por veículo
* Faturamento total
* Serviços mais realizados

---

## Consultas SQL relevantes

Faturamento total:

```sql
SELECT SUM(quantidade * valor_unitario)
FROM itens_ordem;
```

Cliente com maior faturamento:

```sql
SELECT c.nome, SUM(i.quantidade * i.valor_unitario) AS total
FROM itens_ordem i
JOIN ordens_servico os ON i.ordem_id = os.id
JOIN clientes c ON os.cliente_id = c.id
GROUP BY c.nome
ORDER BY total DESC;
```

Serviços mais realizados:

```sql
SELECT descricao, COUNT(*)
FROM itens_ordem
WHERE tipo = 'servico'
GROUP BY descricao
ORDER BY COUNT(*) DESC;
```

---

## Frontend

O frontend consiste em um dashboard simples e funcional com:

* Navegação lateral
* Cards de indicadores
* Visualização de dados básicos
* Integração futura com API

---

## Regras de Negócio

* Não permitir duplicidade de telefone ou placa
* Garantir vínculo correto entre cliente e veículo
* Não permitir valores negativos
* Ordem de serviço deve ter pelo menos um item para ser finalizada
* Status deve seguir fluxo lógico

---

## Roadmap

### Fase 1

* CRUD completo
* CLI funcional
* Banco estruturado

---

### Fase 2

* Integração frontend com API
* Validações mais robustas
* Melhoria da experiência do usuário

---

### Fase 3

* Dashboard com Power BI
* Exportação de dados
* Relatórios financeiros

---

### Fase 4

* Integração com n8n
* Automação de mensagens
* Envio de ordem de serviço
* Follow-up de clientes

---

## Tecnologias Utilizadas

* Python
* PostgreSQL
* HTML
* CSS
* JavaScript

---

## Conclusão

Este projeto representa um sistema real de gestão para autocenter, com base sólida em modelagem de dados, backend e análise.

Pode evoluir para:

* ferramenta interna de gestão
* produto comercial
* portfólio profissional

O foco principal é aprendizado aplicado com uso real.
