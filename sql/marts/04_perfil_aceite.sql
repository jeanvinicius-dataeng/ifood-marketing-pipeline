-- Grão: um grupo dentro de uma dimensão (renda, filhos ou escolaridade).
-- Taxa de aceite = aceites / (clientes x campanhas), assumindo que todos os
-- clientes receberam todas as campanhas (o dado só registra quem aceitou).
WITH
-- Grão: um único registro com a quantidade de campanhas.
campanhas AS (
    SELECT count(DISTINCT campanha) AS quantidade
    FROM refined.respostas_campanhas
),
-- Grão: um cliente.
aceites_por_cliente AS (
    SELECT
        c.cliente_id,
        count(r.cliente_id) FILTER (WHERE r.aceitou) AS aceites
    FROM refined.clientes AS c
    LEFT JOIN refined.respostas_campanhas AS r USING (cliente_id)
    GROUP BY c.cliente_id
),
-- Grão: um cliente, com o grupo dele em cada dimensão.
-- Faixas de renda: o limite inferior entra na faixa de cima. Sem ELSE, para
-- que uma renda nula apareça como grupo nulo em vez de cair numa faixa.
clientes_perfil AS (
    SELECT
        c.cliente_id,
        a.aceites,
        CASE
            WHEN c.renda < 35000 THEN 'ate_35k'
            WHEN c.renda < 55000 THEN '35k_a_55k'
            WHEN c.renda < 75000 THEN '55k_a_75k'
            WHEN c.renda >= 75000 THEN 'acima_75k'
        END AS faixa_renda,
        CASE
            WHEN c.criancas_casa + c.adolescentes_casa > 0 THEN 'com_filhos'
            ELSE 'sem_filhos'
        END AS filhos,
        c.escolaridade
    FROM refined.clientes AS c
    JOIN aceites_por_cliente AS a USING (cliente_id)
),
-- Grão: um cliente em uma dimensão (3 linhas por cliente).
-- As colunas ordem_* só servem para ordenar o resultado.
clientes_dimensao AS (
    SELECT
        1 AS ordem_dimensao, 'renda' AS dimensao, faixa_renda AS grupo,
        CASE faixa_renda
            WHEN 'ate_35k' THEN 1 WHEN '35k_a_55k' THEN 2
            WHEN '55k_a_75k' THEN 3 WHEN 'acima_75k' THEN 4
        END AS ordem_grupo,
        aceites
    FROM clientes_perfil
    UNION ALL
    SELECT
        2, 'filhos', filhos,
        CASE filhos WHEN 'com_filhos' THEN 1 WHEN 'sem_filhos' THEN 2 END,
        aceites
    FROM clientes_perfil
    UNION ALL
    SELECT
        3, 'escolaridade', escolaridade,
        CASE escolaridade
            WHEN 'basico' THEN 1 WHEN 'graduacao' THEN 2
            WHEN 'mestrado' THEN 3 WHEN 'doutorado' THEN 4
        END,
        aceites
    FROM clientes_perfil
)
SELECT
    d.dimensao,
    d.grupo,
    count(*) AS clientes,
    sum(d.aceites) AS aceites,
    round(100.0 * sum(d.aceites) / (count(*) * any_value(k.quantidade)), 1)
        AS taxa_aceite_pct,
    round(100.0 * count(*) FILTER (WHERE d.aceites > 0) / count(*), 1)
        AS pct_aceitou_alguma
FROM clientes_dimensao AS d
CROSS JOIN campanhas AS k
GROUP BY d.ordem_dimensao, d.dimensao, d.ordem_grupo, d.grupo
ORDER BY d.ordem_dimensao, d.ordem_grupo
