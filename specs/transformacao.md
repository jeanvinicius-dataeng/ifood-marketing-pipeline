CONTEXTO
Pipeline de dados em Python sobre o case público de marketing do iFood
(Kaggle, CC0). Spec-driven development: esta spec é a fonte da verdade e o
código é consequência dela. Não acrescente requisito que não esteja aqui. Se
algo estiver ambíguo, pergunte antes de escrever código.

STACK
- Python 3.12, uv, DuckDB (ifood.duckdb na raiz)

O QUE JÁ EXISTE (use, não reimplemente)
pipeline/db.py: conectar(), criar_schema(con, nome)
raw.clientes_campanhas: 2.205 linhas, 29 colunas, todas VARCHAR.

ARTEFATO A PRODUZIR
pipeline/transformacao.py, executável com:
  uv run python -m pipeline.transformacao

SPEC

1. ESCOPO
   Lê de raw, escreve no schema refined. Nunca escreve em raw.
   A tabela raw vira duas tabelas em refined:
     refined.clientes             uma linha por cliente, perfil e gastos
     refined.respostas_campanhas  uma linha por cliente em cada campanha
   Motivo: as 5 campanhas estão em 5 colunas. Em linhas, dá para
   agrupar por campanha e cruzar com o perfil do cliente por JOIN.

2. NOMES (mapa completo e literal)
   refined.clientes
     Index -> cliente_id                  Income -> renda
     Kidhome -> criancas_casa             Teenhome -> adolescentes_casa
     Recency -> dias_ultima_compra        Age -> idade
     Customer_Days -> dias_cliente        Complain -> reclamou
     marital_status -> estado_civil       education -> escolaridade
     MntWines -> gasto_vinhos             MntFruits -> gasto_frutas
     MntMeatProducts -> gasto_carnes      MntFishProducts -> gasto_peixes
     MntSweetProducts -> gasto_doces      MntGoldProds -> gasto_premium
     MntRegularProds -> gasto_regular     MntTotal -> gasto_total
     NumDealsPurchases -> compras_com_desconto
     NumWebPurchases -> compras_site      NumCatalogPurchases -> compras_catalogo
     NumStorePurchases -> compras_loja    NumWebVisitsMonth -> visitas_site_mes
   refined.respostas_campanhas
     cliente_id (de Index), campanha (1 a 5, de AcceptedCmp1 a AcceptedCmp5),
     aceitou (o valor da coluna)
   AcceptedCmpOverall não vai para refined.
   Motivo: é a soma das 5 campanhas, pode ser recalculada a qualquer hora.
   Antes de descartar, conferir que ela é igual à soma em todas as linhas.
   Se não for, para tudo e lista os cliente_id que não batem.

3. TIPOS
   cliente_id, idade, criancas_casa, adolescentes_casa, dias_ultima_compra,
   dias_cliente, campanha e todas as compras_* e visitas_*: INTEGER.
   renda e todos os gasto_*: DECIMAL(12,2). Motivo: são valores em dinheiro.
   reclamou e aceitou: BOOLEAN. Só "0" e "1" são aceitos.
   estado_civil e escolaridade: VARCHAR, traduzidos pelo mapa abaixo.
     estado_civil: Married -> casado, Together -> uniao_estavel,
       Single -> solteiro, Divorced -> divorciado, Widow -> viuvo
     escolaridade: Basic -> basico, Graduation -> graduacao,
       Master -> mestrado, 2n Cycle -> mestrado, PHD -> doutorado
     Motivo do 2n Cycle: é o nome europeu do mestrado. Master e 2n Cycle
     são a mesma escolaridade escrita de dois jeitos (198 clientes no raw).
   A conversão é feita em SQL pelo DuckDB.

4. CONVERSÃO QUE FALHA
   Para tudo. Use CAST, nunca TRY_CAST. Valor fora dos mapas de estado_civil
   e escolaridade, ou fora de "0" e "1" nos campos booleanos, também para
   tudo. Ao falhar, diga tabela, coluna e um exemplo do valor.
   Motivo: virar nulo em silêncio esconderia dado novo e estranho.

5. DUPLICATAS
   Chave de refined.clientes: cliente_id.
   Chave de refined.respostas_campanhas: (cliente_id, campanha).
   203 linhas do raw são idênticas a outra em todas as 28 colunas, exceto o
   Index. São o mesmo cliente cadastrado duas vezes. Em cada grupo de linhas
   idênticas, fica a de menor Index e as outras saem.
   Motivo: dois clientes diferentes com as mesmas 28 informações é
   praticamente impossível. Sem isso, todo indicador conta 203 clientes a mais.
   A deduplicação acontece antes de montar as duas tabelas, então
   respostas_campanhas só tem clientes que estão em clientes.

6. NULOS
   Manter. Nenhum valor é preenchido. A saída na tela mostra quantos nulos
   ficaram por coluna, só das colunas que têm algum.

7. SAÍDA NA TELA
   Linhas lidas do raw, duplicatas removidas, linhas de cada tabela de
   refined (contagem vinda do banco), nulos por coluna. Milhar com ponto.
   stdout reconfigurado para utf-8.

REEXECUÇÃO E ERRO
   CREATE OR REPLACE, nunca acrescenta. As duas tabelas são gravadas numa
   única transação: ou as duas mudam, ou nenhuma.
   Faltando raw.clientes_campanhas: manda rodar a ingestão e sys.exit(1).

CRITÉRIOS DE ACEITE
- Lê 2.205 linhas, remove 203 duplicatas.
- refined.clientes com 2.002 linhas, sem cliente_id repetido.
- refined.respostas_campanhas com 10.010 linhas, 5 por cliente.
- Todo cliente_id de respostas_campanhas existe em clientes.
- A soma de aceitou em respostas_campanhas é igual à soma de
  AcceptedCmpOverall das 2.002 linhas mantidas.
- Escolaridade só tem 4 valores: basico, graduacao, mestrado, doutorado.
- Rodar duas vezes imprime exatamente a mesma coisa.

ENTREGA
1. A spec como docstring no topo do arquivo, com o motivo de cada regra.
2. O código, comentado só onde a decisão não é óbvia.
3. Uma lista final do que você assumiu e que não estava nesta spec.
