# Spec do dashboard

## CONTEXTO
Pipeline de dados sobre o case público de marketing do iFood (Kaggle, CC0).
Já existem os marts 01 a 04 em sql/marts/ e o executor pipeline/marts.py.
Spec-driven development: não acrescente requisito que não esteja aqui. Se
algo estiver ambíguo, pergunte antes.

Objetivo: visual moderno, com cara de produto, para publicação no LinkedIn.
Princípio: 3D no destaque, clareza na análise. Nenhum gráfico de análise
em 3D, porque a perspectiva distorce a comparação.
Esta versão substitui a anterior desta mesma spec. O que já estiver
implementado e for diferente daqui deve ser ajustado para ficar igual.

## ARTEFATOS A PRODUZIR
1. sql/marts/05_resumo.sql
2. Ajuste em sql/marts/01_desempenho_campanhas.sql (coluna nova, item 1.2).
3. Colunas novas nos marts para os títulos (item 5).
4. painel.py na raiz: funções de leitura, formatação e gráficos.
5. app.py na raiz, executável com: uv run streamlit run app.py
6. relatorio.py na raiz, executável com: uv run python relatorio.py
   Gera relatorio.html na raiz.
Adicione plotly às dependências com uv.

## 1. MARTS

1.1 Mart 05_resumo
   Grão: a base inteira, uma linha.
   Colunas: clientes, aceites, taxa_aceite_pct, clientes_aceitaram_alguma,
   pct_aceitou_alguma, gasto_medio_aceitou, gasto_medio_nunca_aceitou.
   Mesmas definições e mesma premissa dos outros marts.
   Aceite: 1 linha, clientes 2.002, aceites 603.

1.2 Mart 01_desempenho_campanhas ganha a coluna pior_campanha (BOOLEAN),
   verdadeira só na campanha de menor taxa de aceite. Em caso de empate,
   a de menor número. O painel usa essa coluna para pintar a barra, sem
   calcular nada.

## 2. REGRA CENTRAL DO PAINEL
   app.py e relatorio.py só fazem SELECT nos marts. Nenhum cálculo,
   agregação, ordenação ou filtro por valor em Python. Selecionar uma linha
   do mart pela chave é permitido. Todo número mostrado sai pronto de um
   mart. Se faltar um número, ele vira coluna ou mart novo, não um cálculo
   no painel.
   Motivo: regra de negócio escondida no painel é regra que ninguém acha.

## 3. BANCO AUSENTE
   Se o ifood.duckdb não existir, ou o schema marts não existir, app.py roda
   ingestão, transformação e marts, nessa ordem, antes de mostrar a tela, com
   uma mensagem de "preparando os dados". Depois disso o banco é aberto em
   modo somente leitura.
   Motivo: o banco não vai para o GitHub. No servidor do Streamlit Cloud, o
   app precisa recriá-lo a partir de raw/iFood.xlsx.

## 4. CONTEÚDO DA TELA, nesta ordem
   Título: "Quem responde às campanhas de marketing?"
   Subtítulo curto dizendo a base (clientes e campanhas, números do mart).
   a) Quatro cartões, do mart resumo: clientes, taxa de aceite geral,
      % de clientes que aceitaram alguma campanha, e gasto médio de quem
      aceitou contra quem nunca aceitou.
   b) Seção desempenho: barras da taxa de aceite por campanha (mart 01).
      A pior campanha em vermelho, as outras em cinza, pela coluna
      pior_campanha.
   c) Seção alcance: barras de clientes por quantidade de campanhas aceitas
      (mart 02).
   d) Seção gasto: comparação do gasto médio, compras com desconto e
      compras pelo site entre quem aceitou alguma e quem nunca aceitou
      (mart 03), com a frase de que é relação e não causa.
   e) Seção perfil: três gráficos de barras de taxa de aceite por grupo,
      um por dimensão, renda, filhos e escolaridade (mart 04).
   f) Rodapé: "Dados do case público de marketing do iFood (Kaggle, licença
      CC0). Projeto de estudo, sem relação oficial com o iFood." e a
      premissa de que todos os clientes receberam as 5 campanhas.

## 5. TÍTULOS QUE DIZEM A CONCLUSÃO
   Cada gráfico tem como título uma frase com a descoberta, montada com os
   números do mart. Exemplos de forma (os números vêm do banco):
   - "A campanha 2 converteu X vezes menos que a média das outras"
   - "Ninguém aceitou as 5 campanhas, e N% nunca aceitaram nenhuma"
   - "Quem aceita campanha gasta X vezes mais"
   - "Cliente sem filhos aceita X vezes mais que cliente com filhos"
   - "Renda acima de 75 mil tem a maior taxa de aceite: X%"
   Abaixo do título, uma linha menor e cinza explicando o que o gráfico mede.
   Os números dessas frases que exigem conta (como "X vezes", ou qual grupo
   é o maior) viram colunas novas nos marts, nunca conta no painel.
   Se uma frase não se confirmar no dado, ela muda para o que o dado diz.

## 6. TEMA
- Fundo escuro com degradê suave: de #0B0D12 para #141824.
- Texto principal #F2F2F2, texto secundário #9AA0AE.
- Uma cor de destaque: vermelho #FF3B4A, usada só no dado que conta a
  história (a pior campanha, o grupo de maior taxa, quem aceitou, quem
  nunca aceitou no alcance). Pode ter brilho suave (glow) nesse vermelho.
- Todo o resto em cinza azulado #3A4152 (barras) e #5B6375 (destaques
  secundários).
- Fontes do Google Fonts: Inter para textos, Space Grotesk para os
  números grandes.
- .streamlit/config.toml com tema escuro nessas cores.

## 7. TOPO EM 3D
- Título e subtítulo do item 4, acima da cena.
- Cena 3D com Three.js r128 (cdnjs, three.min.js), embutida no app com
  streamlit.components.v1.html e igual no relatorio.html.
- Conceito: cada esfera é um aceite (cena 1) ou um cliente (cenas 2 e 3).
  As esferas se reorganizam entre três cenas, com transição animada de
  cerca de 1,4 segundo, baseada em tempo e não em quadros.
- A página abre na cena 1, e a ordem das cenas e dos botões é esta:
- Cena 1, "Por campanha": uma coluna por campanha, cada esfera é um aceite
  (coluna aceites do mart 01), empilhadas em base 4x4. Só a coluna com
  pior_campanha verdadeira em vermelho, as outras em prata. Os clientes
  viram uma poeira cinza pequena no chão. Rótulos "Camp. N" na base e a
  taxa no topo, no formato brasileiro.
- Cena 2, "Quem respondeu": dois blocos empilhados lado a lado, à esquerda
  quem nunca respondeu a nenhuma campanha (cinza), à direita quem
  respondeu a alguma (vermelho). Em cima de cada bloco, o número grande
  do mart 05, com "nunca responderam" e "responderam a alguma" (este em
  vermelho).
- Cena 3, "Todos os clientes": todos os clientes do mart 05 numa grade
  plana, em posições embaralhadas com semente fixa. Quem respondeu a
  alguma em vermelho, o resto em cinza. Em cima da grade, o total de
  clientes e quantos responderam a alguma (este em vermelho).
  Os dois números ficam afastados e nunca se sobrepõem, em nenhuma largura
  de tela, e não saem da cena.
- Três botões abaixo da cena, nesta ordem: Por campanha, Quem respondeu,
  Todos os clientes. A cena troca sozinha a cada 4 segundos, nessa
  ordem, até o usuário clicar num botão, e depois para no que ele
  escolheu.
- Legenda no canto superior da cena explicando o que está na tela, como
  na prévia.
- Câmera fixa, com leve deslocamento seguindo o mouse (parallax). Não gira.
- Os números vêm dos marts 01 e 05 passados como dados para o JavaScript.
  O JavaScript só calcula posições de layout, nunca números de negócio.
- Se o navegador não suportar WebGL, aparece o gráfico 2D de barras do
  mart 01 no lugar, sem erro.
- Altura da cena: 420 px no computador, 300 px no celular.
- Referência visual: specs/referencia_visual.html, a prévia aprovada pelo
  Jean. Ela usa números aproximados escritos no código, só para mostrar o
  visual. Use o design e o JavaScript da cena como base, mas os números
  têm que vir dos marts, nunca copiados da prévia.

## 8. CARTÕES
- Os 4 cartões do item 4a, em grade de 4 colunas no computador e
  2 no celular.
- Efeito de vidro: fundo rgba(255,255,255,0.04), borda 1px
  rgba(255,255,255,0.08), cantos arredondados 16px, blur no fundo.
- Número grande em Space Grotesk, peso 700, animado contando do zero até
  o valor em cerca de 1,2 segundo quando a página abre. O valor final é
  o do mart, já formatado no padrão brasileiro.
- Rótulo pequeno em cima e linha de contexto embaixo.

## 9. GRÁFICOS DE ANÁLISE (2D)
- Os 6 gráficos do item 4, em Plotly com
  fundo transparente, para aparecer o degradê da página.
- Barras com cantos arredondados (marker.cornerradius).
- Sem linhas de grade, sem borda, valor na ponta de cada barra.
- Tooltip escuro no mesmo estilo dos cartões.
- Cada seção dentro de um painel de vidro igual aos cartões.

## 10. RÓTULOS EM PORTUGUÊS
Mapa só de exibição em painel.py, troca de texto, não cálculo:
  ate_35k -> Até 35 mil, 35k_a_55k -> 35 a 55 mil, 55k_a_75k -> 55 a 75 mil,
  acima_75k -> Acima de 75 mil, com_filhos -> Com filhos,
  sem_filhos -> Sem filhos, basico -> Básico, graduacao -> Graduação,
  mestrado -> Mestrado, doutorado -> Doutorado,
  aceitou_alguma -> Aceitou alguma, nunca_aceitou -> Nunca aceitou.
Valor fora do mapa aparece como veio.

## 11. FORMATO
   Percentuais com vírgula e uma casa (12,3%). Dinheiro como R$ 1.023,31.
   Nenhuma logo ou marca do iFood.

## 12. MOVIMENTO
- As seções aparecem com um deslize suave de baixo para cima ao entrar
  na tela.
- Se o usuário tiver "reduzir movimento" ligado no sistema
  (prefers-reduced-motion), nada anima: a cena 3D troca de cena sem
  transição e só quando o usuário clica, e os números aparecem direto no
  valor final.

## 13. RELATÓRIO HTML
   relatorio.html com o mesmo conteúdo, a mesma ordem, o mesmo design, a
   mesma cena 3D, os mesmos cartões e gráficos do app, em um arquivo só,
   usando as mesmas funções de painel.py. Largura máxima de 1080 px.
   Three.js e Plotly pelo CDN, uma vez cada. Cada gráfico com div_id fixo
   ("g01", "g02"...). Rodapé com a data e hora de geração.
   Imprime o caminho do arquivo e o tamanho em KB. stdout em utf-8.

## 14. DESEMPENHO
   Otimizações sem mudar nada do visual nem dos números.
- Cena 3D desenha só quando algo muda: durante a transição entre cenas, a
  contagem inicial e o movimento do mouse. Parada, não redesenha.
- Cena 3D pausa tudo (quadros e troca automática) quando sai da tela
  (IntersectionObserver) ou quando a aba fica em segundo plano.
- Esferas com menos detalhe: SphereGeometry com 8 e 6 segmentos. Pixel ratio
  máximo de 1,5.
- As matrizes das esferas só são atualizadas durante a transição.
- relatorio.html usa o pacote reduzido plotly-basic (só barras e afins), em
  vez do Plotly completo.
- app.py lê os marts com st.cache_data e faz a verificação do banco com
  st.cache_resource, para não refazer a cada interação.
   Motivo: o painel e o relatório ficavam pesados, demoravam para abrir e
   travavam.

## CRITÉRIOS DE ACEITE
- uv run python -m pipeline.marts grava 5 marts, o resumo com 1 linha
  (clientes 2.002, aceites 603), e o 01 com uma única pior_campanha.
- uv run streamlit run app.py abre a tela com a cena 3D, os 4 cartões e
  os 6 gráficos.
- Nenhum título de gráfico é genérico. Todos contêm um número e uma conclusão.
- Na cena 1, cada coluna tem tantas esferas quanto aceites no mart 01, e
  só a pior campanha está em vermelho.
- A cena 3 tem tantas esferas quanto clientes no mart 05, com a
  quantidade de vermelhas igual a clientes_aceitaram_alguma.
- Nenhum rótulo sem acento na tela.
- No celular (390 px de largura), nada sai da tela e os cartões ficam
  em 2 colunas.
- Com prefers-reduced-motion, nada anima.
- Apagando o ifood.duckdb, o app recria o banco sozinho e abre normal.
- relatorio.html tem menos de 200 KB, e rodar duas vezes muda só a data.
- uv run pytest verde e uv run ruff check . sem avisos.
- Mande prints do app e do relatório, em 1080 px e em 390 px.

## ENTREGA
1. A spec do painel como docstring em app.py.
2. A lista do que você assumiu e que não estava nesta spec.
