-- Grão: uma quantidade de campanhas aceitas por cliente (0 a 5); só as que existem no dado.
WITH
-- Grão: um cliente.
aceites_por_cliente AS (
    SELECT
        c.cliente_id,
        count(r.cliente_id) FILTER (WHERE r.aceitou) AS campanhas_aceitas
    FROM refined.clientes AS c
    LEFT JOIN refined.respostas_campanhas AS r USING (cliente_id)
    GROUP BY c.cliente_id
)
SELECT
    campanhas_aceitas,
    count(*) AS clientes,
    round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct_clientes
FROM aceites_por_cliente
GROUP BY campanhas_aceitas
ORDER BY campanhas_aceitas
