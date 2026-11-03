# Spec do README

## CONTEXTO
Última etapa obrigatória do desafio final do Acelera Dados. O README é o
que o avaliador e quem vem do LinkedIn leem primeiro. Escreva em português,
direto, sem exagero. Não invente números: todo número do README tem que
vir do banco, dos testes ou desta spec. Se algo estiver ambíguo, pergunte.

## ARTEFATOS A PRODUZIR
1. README.md na raiz.
2. specs/ingestao.md, recriado a partir da docstring de
   pipeline/ingestao.py, sem mudar o conteúdo. Motivo: a spec da ingestão
   foi colada no chat e nunca foi salva como arquivo.

## SEÇÕES DO README, nesta ordem

1. Título e uma frase dizendo o que é o projeto.

2. A pergunta de negócio
   Quem responde às campanhas de marketing e quem não responde.

3. Resultados
   Os principais achados, com os números lidos dos marts no momento em
   que você escrever (pior campanha e quantas vezes menor, % que nunca
   aceitou nenhuma, gasto de quem aceita contra quem nunca aceitou,
   filhos, renda, escolaridade). Um print do dashboard, salvo em
   docs/img/ e referenciado no README.

4. Arquitetura
   Diagrama em Mermaid do fluxo raw/iFood.xlsx -> raw -> refined -> marts
   -> app.py e relatorio.html, com o nome de cada script nas setas.
   Uma linha por camada explicando o que ela guarda.

5. Decisões tomadas sobre o dado, cada uma com o número que a justifica
   - 203 linhas idênticas exceto o Index tratadas como o mesmo cliente
     cadastrado duas vezes. 2.205 linhas viram 2.002 clientes.
   - "2n Cycle" e "Master" juntados como mestrado.
   - As 5 colunas de campanha viram a tabela respostas_campanhas, com
     10.010 linhas, para permitir o JOIN com o perfil do cliente.
   - AcceptedCmpOverall descartada depois de conferir que é a soma das 5.

6. Limitações
   - O dado não diz quem recebeu cada campanha, só quem aceitou. Os
     indicadores assumem que todos receberam as 5.
   - O gasto é o total de 2 anos do cliente, não atribuído a campanha.
     A comparação de gasto mostra relação, não causa.
   - Não dá para medir venda gerada por campanha, porque o dado não liga
     compra a campanha.

7. Como rodar
   Pré-requisito uv. Comandos na ordem: uv sync, ingestão,
   transformação, marts, pytest, ruff, streamlit, relatório.

8. Estrutura de pastas
   Árvore curta das pastas e arquivos principais.

9. Testes
   Quantos são, o que cobrem, e que rodam com dados inventados sem tocar
   no banco. Citar que uma regra foi quebrada de propósito (o mapa do
   2n Cycle) e o teste certo ficou vermelho.

10. Fonte dos dados e licença
    Dataset "iFood Marketing Campaigns Analysis" no Kaggle, licença CC0.
    Projeto de estudo, sem relação oficial com o iFood.

11. Onde a IA errou ou assumiu algo que eu não pedi
    Seção obrigatória do desafio. Escreva em primeira pessoa, como o Jean,
    usando exatamente os casos abaixo. Para cada um, uma linha dizendo o
    que aconteceu e outra dizendo como foi descoberto.
    - Versão do Python. As specs pediam Python 3.12, mas o projeto roda
      em 3.13. O uv init com --python 3.12 virou "3.12 ou mais novo" e o
      uv escolheu o mais novo, sem aviso. Descobri lendo a saída do
      pytest, que mostrava Python 3.13.
    - Arredondamento silencioso. O CAST do DuckDB transforma "1.5" em 2
      sem erro, o que contraria a regra da spec de parar quando a
      conversão falha. Hoje os dados não têm casas decimais, então nada
      mudou, mas a regra não está garantida. Quem apontou foi a própria
      IA, na lista do que assumiu.
    - Regra "só lê de refined" não verificada. A spec dos marts dizia
      que eles só leem de refined, mas o executor não confere isso. Um
      SQL que lesse de raw passaria. Também apareceu na lista do que a
      IA assumiu.
    - Rótulos sem acento. A spec pedia nomes do mart com a primeira letra
      maiúscula, e a IA seguiu ao pé da letra, gerando "Ate 35k" e
      "Basico". Descobri lendo a lista do que ela assumiu, e virou um
      mapa de rótulos na spec.
    - Spec cortada. Na etapa do dashboard o texto colado no chat chegou
      cortado no meio. A IA parou e pediu o resto em vez de inventar.
      Passei a entregar as specs como arquivo.
    - O arquivo do Kaggle. A página dizia ifood_df.csv, mas o download
      trouxe iFood.xlsx. Descobri ao tentar contar as linhas do CSV e o
      arquivo não existir.
    Fechar a seção com uma frase sobre o hábito de contar antes e depois
    de cada etapa, que foi o que mais pegou erro.

12. Autor
    Jean Vinicius. GitHub github.com/jeanvinicius-dataeng e LinkedIn
    linkedin.com/in/jeanvinicius.
    Links do painel publicado e do relatório como [link], para eu
    preencher depois do deploy.

## CRITÉRIOS DE ACEITE
- Todos os números do README conferem com os marts e com a saída dos
  scripts no momento da escrita.
- O diagrama Mermaid renderiza no GitHub.
- A seção 11 tem os seis casos, em primeira pessoa.
- specs/ingestao.md existe e é igual à docstring da ingestão.
- uv run pytest verde e uv run ruff check . sem avisos.

## ENTREGA
1. README.md e specs/ingestao.md.
2. A lista do que você assumiu e que não estava nesta spec.
