"""Executor dos marts: transforma cada sql/marts/NN_nome.sql em marts.nome.

Execução:
    uv run python -m pipeline.marts

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
"""

import re
import sys

import duckdb

from pipeline.db import RAIZ, conectar, criar_schema

PASTA_SQL = RAIZ / "sql" / "marts"
SCHEMA = "marts"
DEPENDENCIAS = ("clientes", "respostas_campanhas")
NOME_ARQUIVO = re.compile(r"^\d{2}_(?P<nome>[a-z0-9_]+)\.sql$")


class ErroMarts(Exception):
    pass


def _milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _ler_marts(con: duckdb.DuckDBPyConnection) -> list[tuple[str, str, str]]:
    """Valida todos os arquivos antes de gravar qualquer coisa.

    Devolve (arquivo, nome do mart, SELECT) em ordem de nome de arquivo.
    """
    marts = []
    for arquivo in sorted(PASTA_SQL.glob("*.sql")):
        casamento = NOME_ARQUIVO.match(arquivo.name)
        if not casamento:
            raise ErroMarts(
                f"{arquivo.name}: nome fora do padrão NN_nome.sql em {PASTA_SQL}"
            )
        texto = arquivo.read_text(encoding="utf-8")
        try:
            comandos = con.extract_statements(texto)
        except duckdb.Error as e:
            raise ErroMarts(f"{arquivo.name}: {e}") from None
        if len(comandos) != 1:
            raise ErroMarts(
                f"{arquivo.name}: tem {len(comandos)} comandos, deve ter um único SELECT"
            )
        # Exigir SELECT também impede que um arquivo escreva em raw ou refined.
        if comandos[0].type != duckdb.StatementType.SELECT:
            raise ErroMarts(
                f"{arquivo.name}: o comando é {comandos[0].type.name}, deve ser SELECT"
            )
        select = comandos[0].query.strip().rstrip(";")
        marts.append((arquivo.name, casamento["nome"], select))
    return marts


def _gravar(
    con: duckdb.DuckDBPyConnection, marts: list[tuple[str, str, str]]
) -> list[tuple[str, int]]:
    contagens = []
    con.execute("BEGIN TRANSACTION")
    try:
        criar_schema(con, SCHEMA)
        for arquivo, nome, select in marts:
            tabela = f"{SCHEMA}.{nome}"
            try:
                # Quebra de linha antes do fim: o SELECT pode terminar num
                # comentário de linha.
                con.execute(f"CREATE OR REPLACE TABLE {tabela} AS\n{select}\n")
                linhas = con.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0]
            except duckdb.Error as e:
                raise ErroMarts(f"{arquivo}: {e}") from None
            if linhas == 0:
                raise ErroMarts(f"{arquivo}: {tabela} ficou com zero linhas")
            contagens.append((tabela, linhas))
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return contagens


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    con = conectar()
    try:
        faltando = [
            f"refined.{t}"
            for t in DEPENDENCIAS
            if not con.execute(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema = 'refined' AND table_name = ?",
                [t],
            ).fetchone()[0]
        ]
        if faltando:
            print(
                f"Tabela(s) não encontrada(s): {', '.join(faltando)}. "
                "Rode antes a transformação: uv run python -m pipeline.transformacao",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            contagens = _gravar(con, _ler_marts(con))
        except ErroMarts as e:
            print(f"Erro em {e}", file=sys.stderr)
            sys.exit(1)

        for tabela, linhas in contagens:
            print(f"{tabela}: {_milhar(linhas)} linhas")
        total = sum(linhas for _, linhas in contagens)
        print(f"total: {_milhar(total)} linhas em {len(contagens)} marts")
    finally:
        con.close()


if __name__ == "__main__":
    main()
