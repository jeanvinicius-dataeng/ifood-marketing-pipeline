Ingestão da planilha do case de marketing do iFood na camada raw.

Execução:
    uv run python -m pipeline.ingestao

SPEC

1. ESCOPO E NOMES
   Origem: raw/iFood.xlsx, aba "iFood".
   Destino: schema raw, tabela raw.clientes_campanhas.
   Motivo: a planilha tem uma linha por cliente com o perfil e as respostas
   às campanhas. O nome diz as duas coisas.

2. PROIBIÇÕES
   Nenhuma conversão de tipo. Nenhuma linha descartada ou deduplicada.
   Nenhum nome de coluna alterado. Nenhum valor corrigido, preenchido ou
   normalizado.
   Motivo: a camada raw é o espelho fiel do que chegou. Toda decisão sobre
   o dado acontece na transformação, onde fica registrada.

3. REEXECUÇÃO
   A tabela é recriada a cada execução (CREATE OR REPLACE), nunca acrescentada.
   Motivo: rodar dez vezes tem que dar o mesmo resultado que rodar uma.

4. LEITURA
   pd.read_excel com sheet_name="iFood" declarado, nunca a primeira aba por
   padrão. dtype=str. Só célula vazia vira nulo (keep_default_na=False,
   na_values=[""]).
   Motivo: se a planilha ganhar outra aba, o script continua lendo a certa.
   Textos como "NA" não podem virar nulo sem eu decidir.

5. TIPAGEM
   Toda coluna entra como texto.
   Motivo: a conversão é uma decisão da transformação, não da ingestão.

6. SAÍDA NA TELA
   Uma linha com o nome qualificado da tabela, a contagem de linhas vinda do
   banco (não do DataFrame) e a quantidade de colunas. Milhar com ponto.
   stdout reconfigurado para utf-8.
   Motivo: é o instrumento de conferência desta etapa.

7. ERRO
   Se raw/iFood.xlsx não existir, ou a aba "iFood" não existir, diga o que
   faltou e onde procurou, e encerre com sys.exit(1) antes de abrir o banco.
   Motivo: falhar cedo e com mensagem clara, sem criar banco vazio.

CRITÉRIOS DE ACEITE
- A execução imprime raw.clientes_campanhas com 2.205 linhas e 29 colunas.
- Rodar duas vezes seguidas imprime exatamente a mesma coisa.
- DESCRIBE raw.clientes_campanhas mostra todas as colunas como VARCHAR.
- Renomear o arquivo faz o script parar com a mensagem, sem criar o banco.
