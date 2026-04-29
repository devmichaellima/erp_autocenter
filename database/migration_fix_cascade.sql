-- Migration: adiciona ON DELETE CASCADE na FK fk_veiculo_os de ordens_servico
-- Execute este script uma única vez no banco 'tekar' se o schema já foi criado.

ALTER TABLE ordens_servico
    DROP CONSTRAINT IF EXISTS fk_veiculo_os;

ALTER TABLE ordens_servico
    ADD CONSTRAINT fk_veiculo_os
        FOREIGN KEY (veiculo_id)
        REFERENCES veiculos(id)
        ON DELETE CASCADE;
