-- Grão: a base inteira, uma linha.
-- Taxa de aceite = aceites / (clientes x campanhas), assumindo que todos os
-- clientes receberam todas as campanhas (o dado só registra quem aceitou).
-- O gasto é o total de 2 anos do cliente, não é atribuído a nenhuma campanha.
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
        c.gasto_total,
        count(r.cliente_id) FILTER (WHERE r.aceitou) AS aceites
    FROM refined.clientes AS c
    LEFT JOIN refined.respostas_campanhas AS r USING (cliente_id)
    GROUP BY c.cliente_id, c.gasto_total
)
SELECT
    count(*) AS clientes,
    sum(a.aceites) AS aceites,
    round(100.0 * sum(a.aceites) / (count(*) * any_value(k.quantidade)), 1)
        AS taxa_aceite_pct,
    count(*) FILTER (WHERE a.aceites > 0) AS clientes_aceitaram_alguma,
    -- Coluna extra para a cena 3D (regra 2: o JavaScript não calcula número).
    count(*) FILTER (WHERE a.aceites = 0) AS clientes_nunca_aceitaram,
    round(100.0 * count(*) FILTER (WHERE a.aceites > 0) / count(*), 1)
        AS pct_aceitou_alguma,
    round(avg(a.gasto_total) FILTER (WHERE a.aceites > 0), 2)
        AS gasto_medio_aceitou,
    round(avg(a.gasto_total) FILTER (WHERE a.aceites = 0), 2)
        AS gasto_medio_nunca_aceitou,
    -- Coluna extra para o subtítulo do painel (regra 2: número vem do mart).
    any_value(k.quantidade) AS campanhas
FROM aceites_por_cliente AS a
CROSS JOIN campanhas AS k
