CONTEXTO
Pipeline de dados sobre o case público de marketing do iFood (Kaggle, CC0).
Spec-driven development: esta spec é a fonte da verdade. Não acrescente
requisito que não esteja aqui. Se algo estiver ambíguo, pergunte antes.

O QUE JÁ EXISTE
pipeline/db.py: conectar(), criar_schema(con, nome)
refined.clientes: 2.002 linhas, chave cliente_id.
refined.respostas_campanhas: 10.010 linhas, chave (cliente_id, campanha),
  colunas cliente_id, campanha (1 a 5), aceitou (BOOLEAN). Soma de aceitou: 603.

ARTEFATOS A PRODUZIR
1. pipeline/marts.py, executável com: uv run python -m pipeline.marts
2. Quatro arquivos em sql/marts/, descritos abaixo.

SPEC DO EXECUTOR
1. Lê todos os arquivos sql/marts/NN_nome.sql em ordem de nome. Cada
   arquivo tem um único SELECT, e vira a tabela marts.nome (sem o NN_).
   Arquivo sem o prefixo NN_ ou com mais de um comando: para tudo.
2. Só lê de refined. Nunca escreve em raw nem em refined.
3. Todos os marts são gravados numa única transação, com CREATE OR REPLACE.
   Um erro em qualquer arquivo desfaz tudo e mostra o nome do arquivo e a
   mensagem do DuckDB.
4. Mart com zero linhas é erro. Motivo: quase sempre é um JOIN que não casou.
5. Saída: uma linha por mart com o nome e a contagem vinda do banco, e uma
   linha final com o total. Milhar com ponto. stdout em utf-8.
6. Faltando refined.clientes ou refined.respostas_campanhas: manda rodar a
   transformação e sys.exit(1).

DEFINIÇÕES QUE VALEM PARA TODOS OS MARTS
- Cliente: cliente_id de refined.clientes, já sem duplicatas.
- Aceite: uma linha de respostas_campanhas com aceitou = true.
- Taxa de aceite: aceites dividido por (clientes x campanhas), em %.
  Premissa: o dado não diz quem recebeu cada campanha, só quem aceitou.
  Assume-se que todos os clientes receberam as 5 campanhas.
- Tem filhos: criancas_casa + adolescentes_casa > 0.
- Faixa de renda: ate_35k, 35k_a_55k, 55k_a_75k, acima_75k
  (limite inferior incluído na faixa de cima).

REGRA DOS ARQUIVOS SQL
A primeira linha de cada arquivo é um comentário com o grão do resultado
(o que uma linha representa). Cada CTE tem um comentário com o seu grão.
Percentuais com uma casa decimal, valores médios com duas.

OS QUATRO MARTS

01_desempenho_campanhas.sql
  Pergunta: como foi o desempenho de cada campanha?
  Grão: uma campanha.
  Colunas: campanha, clientes, aceites, taxa_aceite_pct.
  Ordem: por campanha.

02_alcance.sql
  Pergunta: quantos clientes as campanhas alcançam?
  Grão: uma quantidade de campanhas aceitas por cliente (0 a 5).
  Colunas: campanhas_aceitas, clientes, pct_clientes.
  Só aparecem as quantidades que existem no dado.

03_gasto_por_resposta.sql
  Pergunta: quem aceita campanha gasta mais?
  Grão: um grupo, aceitou_alguma ou nunca_aceitou.
  Colunas: grupo, clientes, gasto_total_medio, compras_com_desconto_media,
  compras_site_media.
  Comentário obrigatório no arquivo: o gasto é o total de 2 anos do
  cliente, não é atribuído a nenhuma campanha. O mart mostra relação, não
  prova que a campanha causou o gasto.

04_perfil_aceite.sql
  Pergunta: que perfil de cliente mais aceita campanha?
  Grão: um grupo dentro de uma dimensão.
  Colunas: dimensao (renda, filhos ou escolaridade), grupo, clientes,
  aceites, taxa_aceite_pct, pct_aceitou_alguma.
  Grupos: as 4 faixas de renda, com_filhos e sem_filhos, e os 4 valores
  de escolaridade.

CRITÉRIOS DE ACEITE
- 01 tem 5 linhas e a soma de aceites dá 603.
- 02: a soma de clientes dá 2.002, e a soma de campanhas_aceitas x clientes dá 603.
- 03 tem 2 linhas e a soma de clientes dá 2.002.
- 04 tem 10 linhas, e em cada dimensão a soma de clientes dá 2.002 e a de aceites dá 603.
- Rodar duas vezes imprime exatamente a mesma coisa.

ENTREGA
1. A spec do executor como docstring no topo de pipeline/marts.py.
2. Os quatro SQL com os comentários de grão.
3. Uma lista final do que você assumiu e que não estava nesta spec.
