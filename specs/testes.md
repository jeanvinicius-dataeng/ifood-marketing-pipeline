CONTEXTO
Pipeline de dados sobre o case de marketing do iFood. Já existem
pipeline/ingestao.py, pipeline/transformacao.py, pipeline/marts.py e os SQL
em sql/marts/. Spec-driven development: não acrescente requisito que não
esteja aqui. Se algo estiver ambíguo, pergunte antes.

ARTEFATOS A PRODUZIR
Pasta tests/ na raiz, com um arquivo por módulo: test_ingestao.py,
test_transformacao.py e test_marts.py. Executável com: uv run pytest

REGRAS
1. Nenhum teste abre o ifood.duckdb do projeto nem lê raw/iFood.xlsx.
   Todo teste cria o seu banco e os seus arquivos dentro de tmp_path do
   pytest, com dados inventados de poucas linhas.
   Motivo: o teste tem que dar o mesmo resultado em qualquer computador, e
   não pode estragar o banco de verdade.
2. Se o código atual não permitir trocar o caminho do banco ou da planilha,
   faça a menor mudança possível para isso (por exemplo, monkeypatch de uma
   constante em pipeline/db.py) e liste a mudança na entrega.
3. Cada teste confere uma regra só, e o nome dele diz qual.
4. Os testes conferem resultado, não como o código faz por dentro.

O QUE TESTAR

Ingestão
- Todas as colunas chegam como VARCHAR.
- Célula vazia vira nulo, e o texto "NA" continua sendo o texto "NA".
- Rodar duas vezes não duplica linhas.
- Planilha ausente encerra com erro e não cria o banco.

Transformação
- Duas linhas idênticas exceto o Index viram um cliente só, e fica o
  menor Index.
- Cada cliente gera exatamente 5 linhas em respostas_campanhas.
- "2n Cycle" e "Master" viram "mestrado".
- Escolaridade fora do mapa faz o script parar e refined não é criada.
- Valor diferente de "0" e "1" em AcceptedCmp faz o script parar.
- AcceptedCmpOverall diferente da soma das 5 campanhas faz o script parar.

Marts
- No desempenho_campanhas, a soma de aceites é igual ao total de aceites
  do dado inventado.
- No alcance, a soma de clientes é igual ao total de clientes.
- No perfil_aceite, em cada dimensão a soma de clientes é igual ao total.
- Um SQL que devolve zero linhas é erro.

CRITÉRIOS DE ACEITE
- uv run pytest passa tudo, em verde.
- uv run ruff check . passa sem aviso.
- Depois de rodar os testes, o ifood.duckdb do projeto continua igual
  (mesma data de modificação).
- Quebrando de propósito uma regra no código (por exemplo, tirando o
  2n Cycle do mapa), pelo menos um teste fica vermelho. Faça esse teste,
  me mostre o vermelho, e desfaça a quebra.

ENTREGA
1. Os testes, com uma docstring curta em cada um dizendo a regra.
2. A lista das mudanças feitas no código do pipeline para permitir os
   testes, se houver.
3. Uma lista final do que você assumiu e que não estava nesta spec.
