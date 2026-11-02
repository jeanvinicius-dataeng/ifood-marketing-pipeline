"""Acesso ao banco DuckDB do pipeline.

SPEC (parte que este módulo implementa; a spec completa está em
pipeline/ingestao.py)

STACK
    DuckDB como banco, arquivo ifood.duckdb na raiz do projeto.

CONTRATO
    RAIZ           Path da raiz do projeto
    PASTA_RAW      RAIZ / "raw"
    conectar()     abre o ifood.duckdb, criando se faltar
    criar_schema(con, nome)            CREATE SCHEMA IF NOT EXISTS
    gravar(con, df, schema, tabela)    CREATE OR REPLACE TABLE a partir do
                                       DataFrame e devolve a contagem lida
                                       do banco

3. REEXECUÇÃO
   A tabela é recriada a cada execução (CREATE OR REPLACE), nunca acrescentada.
   Motivo: rodar dez vezes tem que dar o mesmo resultado que rodar uma.

6. SAÍDA NA TELA (parte da contagem)
   A contagem de linhas vem do banco, não do DataFrame.
   Motivo: é o instrumento de conferência desta etapa.
"""

from pathlib import Path

import duckdb
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PASTA_RAW = RAIZ / "raw"


def conectar() -> duckdb.DuckDBPyConnection:
    """Abre o ifood.duckdb na raiz do projeto, criando o arquivo se faltar."""
    return duckdb.connect(str(RAIZ / "ifood.duckdb"))


def criar_schema(con: duckdb.DuckDBPyConnection, nome: str) -> None:
    """Cria o schema se ainda não existir."""
    con.execute(f'CREATE SCHEMA IF NOT EXISTS "{nome}"')


def gravar(
    con: duckdb.DuckDBPyConnection, df: pd.DataFrame, schema: str, tabela: str
) -> int:
    """Recria schema.tabela a partir do DataFrame e devolve a contagem do banco."""
    # Registro explícito em vez de depender da varredura de variáveis locais
    # do DuckDB: deixa claro qual objeto vira tabela.
    con.register("_df_gravar", df)
    try:
        con.execute(
            f'CREATE OR REPLACE TABLE "{schema}"."{tabela}" AS SELECT * FROM _df_gravar'
        )
    finally:
        con.unregister("_df_gravar")
    return con.execute(f'SELECT count(*) FROM "{schema}"."{tabela}"').fetchone()[0]
