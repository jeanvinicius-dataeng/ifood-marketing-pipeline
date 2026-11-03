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
),
-- Grão: uma campanha, com a taxa sem arredondar.
taxas AS (
    SELECT
        a.campanha,
        t.clientes,
        a.aceites,
        a.aceites / t.clientes AS taxa
    FROM aceites_por_campanha AS a
    CROSS JOIN total_clientes AS t
),
-- Grão: uma campanha, comparada com as demais.
-- taxa_outras: aceites das outras campanhas / (clientes x outras campanhas).
-- pior_campanha: menor taxa; no empate, a de menor número.
comparacao AS (
    SELECT
        *,
        (sum(aceites) OVER () - aceites)
            / (clientes * (count(*) OVER () - 1)) AS taxa_outras,
        row_number() OVER (ORDER BY taxa, campanha) = 1 AS pior_campanha
    FROM taxas
)
SELECT
    campanha,
    clientes,
    aceites,
    round(100.0 * taxa, 1) AS taxa_aceite_pct,
    pior_campanha,
    -- Quantas vezes a taxa média das outras campanhas é maior que a desta.
    round(taxa_outras / nullif(taxa, 0), 1) AS vezes_menor_que_outras
FROM comparacao
ORDER BY campanha
