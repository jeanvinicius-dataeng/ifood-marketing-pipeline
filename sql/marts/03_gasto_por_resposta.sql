-- Grão: um grupo de clientes, aceitou_alguma ou nunca_aceitou.
-- Atenção: o gasto é o total de 2 anos do cliente, não é atribuído a nenhuma
-- campanha. O mart mostra relação, não prova que a campanha causou o gasto.
WITH
-- Grão: um cliente.
aceites_por_cliente AS (
    SELECT
        c.cliente_id,
        count(r.cliente_id) FILTER (WHERE r.aceitou) AS aceites
    FROM refined.clientes AS c
    LEFT JOIN refined.respostas_campanhas AS r USING (cliente_id)
    GROUP BY c.cliente_id
),
-- Grão: um cliente, com o seu grupo.
clientes_com_grupo AS (
    SELECT
        CASE WHEN a.aceites > 0 THEN 'aceitou_alguma' ELSE 'nunca_aceitou' END
            AS grupo,
        c.gasto_total,
        c.compras_com_desconto,
        c.compras_site
    FROM refined.clientes AS c
    JOIN aceites_por_cliente AS a USING (cliente_id)
)
SELECT
    grupo,
    count(*) AS clientes,
    round(avg(gasto_total), 2) AS gasto_total_medio,
    round(avg(compras_com_desconto), 2) AS compras_com_desconto_media,
    round(avg(compras_site), 2) AS compras_site_media
FROM clientes_com_grupo
GROUP BY grupo
ORDER BY grupo
