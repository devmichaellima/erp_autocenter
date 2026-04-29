
-- TABELA DE CLIENTES

CREATE TABLE clientes (
	id SERIAL PRIMARY KEY,
	nome VARCHAR(50) NOT NULL,
	telefone VARCHAR(20) NOT NULL UNIQUE,
	cpf VARCHAR(20) UNIQUE,
	criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- TABELO DE VEICULOS

CREATE TABLE veiculos (
	id SERIAL PRIMARY KEY,
	cliente_id INTEGER NOT NULL,
	marca VARCHAR(20),
	modelo VARCHAR(20),
	ano INTEGER,
	placa VARCHAR(10) NOT NULL UNIQUE,
	criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

	CONSTRAINT fk_veiculo_cliente
		FOREIGN KEY (cliente_id)
		REFERENCES clientes(id)
		ON DELETE CASCADE,
	
	CONSTRAINT uq_cliente_veiculo
		UNIQUE (cliente_id, id)

);


-- TABELA ORDENS DE SERVIÇO

CREATE TABLE ordens_servico (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    veiculo_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'aberta' CHECK (status IN ('aberta', 'em_andamento', 'finalizada', 'cancelada')),
    data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_fechamento TIMESTAMP,

    CONSTRAINT fk_cliente_os
        FOREIGN KEY(cliente_id)
        REFERENCES clientes(id),

    CONSTRAINT fk_veiculo_os
        FOREIGN KEY(veiculo_id)
        REFERENCES veiculos(id)
        ON DELETE CASCADE,

	-- Garante que o veículo pertence ao cliente
	CONSTRAINT fk_cliente_veiculo
		FOREIGN KEY (cliente_id, veiculo_id)
		REFERENCES veiculos(cliente_id, id)
);


-- ITENS DA ORDEM (SERVIÇOS/PEÇAS)

CREATE TABLE itens_ordem (
    id SERIAL PRIMARY KEY,
    ordem_id INTEGER NOT NULL,
    descricao VARCHAR(150) NOT NULL,
    quantidade INT DEFAULT 1,
    valor_unitario NUMERIC(10,2) NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('servico', 'peca')),

    CONSTRAINT fk_ordem
        FOREIGN KEY(ordem_id)
        REFERENCES ordens_servico(id)
        ON DELETE CASCADE
);