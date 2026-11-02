-- Grão: uma campanha (1 a 5).
-- Taxa de aceite = aceites / (clientes x 1 campanha), assumindo que todos os
-- clientes receberam todas as campanhas (o dado só registra quem aceitou).
WITH
-- Grão: um único registro com o total de clientes.
total_clientes AS (
    SELECT count(*) AS clientes
    FROM refined.clientes
),
-- Grão: uma campanha.
aceites_por_campanha AS (
    SELECT
        r.campanha,
        count(*) FILTER (WHERE r.aceitou) AS aceites
    FROM refined.respostas_campanhas AS r
    JOIN refined.clientes AS c USING (cliente_id)
    GROUP BY r.campanha
)
SELECT
    a.campanha,
    t.clientes,
    a.aceites,
    round(100.0 * a.aceites / t.clientes, 1) AS taxa_aceite_pct
FROM aceites_por_campanha AS a
CROSS JOIN total_clientes AS t
ORDER BY a.campanha
