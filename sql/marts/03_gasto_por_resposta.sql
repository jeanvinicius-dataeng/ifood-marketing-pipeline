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
),
-- Grão: um grupo, com as médias sem arredondar.
por_grupo AS (
    SELECT
        grupo,
        count(*) AS clientes,
        avg(gasto_total) AS gasto_total_medio,
        avg(compras_com_desconto) AS compras_com_desconto_media,
        avg(compras_site) AS compras_site_media
    FROM clientes_com_grupo
    GROUP BY grupo
)
SELECT
    grupo,
    clientes,
    round(gasto_total_medio, 2) AS gasto_total_medio,
    round(compras_com_desconto_media, 2) AS compras_com_desconto_media,
    round(compras_site_media, 2) AS compras_site_media,
    -- Quantas vezes o gasto médio deste grupo é o do outro grupo. Com dois
    -- grupos, a soma da coluna menos o próprio valor é o valor do outro.
    round(
        gasto_total_medio
            / nullif(sum(gasto_total_medio) OVER () - gasto_total_medio, 0),
        1
    ) AS gasto_vezes_outro_grupo
FROM por_grupo
ORDER BY grupo
