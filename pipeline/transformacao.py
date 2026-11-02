"""Transformação da camada raw para a camada refined.

Execução:
    uv run python -m pipeline.transformacao

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
"""

import sys

import duckdb

from pipeline.db import conectar, criar_schema

ORIGEM = "raw.clientes_campanhas"

# (coluna raw, coluna refined, tipo) na ordem em que aparecem na spec.
CLIENTES = [
    ("Index", "cliente_id", "INTEGER"),
    ("Income", "renda", "DECIMAL(12,2)"),
    ("Kidhome", "criancas_casa", "INTEGER"),
    ("Teenhome", "adolescentes_casa", "INTEGER"),
    ("Recency", "dias_ultima_compra", "INTEGER"),
    ("Age", "idade", "INTEGER"),
    ("Customer_Days", "dias_cliente", "INTEGER"),
    ("Complain", "reclamou", "BOOLEAN"),
    ("marital_status", "estado_civil", "MAPA"),
    ("education", "escolaridade", "MAPA"),
    ("MntWines", "gasto_vinhos", "DECIMAL(12,2)"),
    ("MntFruits", "gasto_frutas", "DECIMAL(12,2)"),
    ("MntMeatProducts", "gasto_carnes", "DECIMAL(12,2)"),
    ("MntFishProducts", "gasto_peixes", "DECIMAL(12,2)"),
    ("MntSweetProducts", "gasto_doces", "DECIMAL(12,2)"),
    ("MntGoldProds", "gasto_premium", "DECIMAL(12,2)"),
    ("MntRegularProds", "gasto_regular", "DECIMAL(12,2)"),
    ("MntTotal", "gasto_total", "DECIMAL(12,2)"),
    ("NumDealsPurchases", "compras_com_desconto", "INTEGER"),
    ("NumWebPurchases", "compras_site", "INTEGER"),
    ("NumCatalogPurchases", "compras_catalogo", "INTEGER"),
    ("NumStorePurchases", "compras_loja", "INTEGER"),
    ("NumWebVisitsMonth", "visitas_site_mes", "INTEGER"),
]
CAMPANHAS = [f"AcceptedCmp{i}" for i in range(1, 6)]
TOTAL_CAMPANHAS = "AcceptedCmpOverall"

MAPAS = {
    "estado_civil": {
        "Married": "casado",
        "Together": "uniao_estavel",
        "Single": "solteiro",
        "Divorced": "divorciado",
        "Widow": "viuvo",
    },
    "escolaridade": {
        "Basic": "basico",
        "Graduation": "graduacao",
        "Master": "mestrado",
        "2n Cycle": "mestrado",
        "PHD": "doutorado",
    },
}

# Marca as mensagens geradas por error() no SQL, para distingui-las dos
# erros de CAST do próprio DuckDB.
PREFIXO_ERRO = "FALHA DE CONVERSAO: "


class ErroTransformacao(Exception):
    pass


def _milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _q(nome: str) -> str:
    return '"' + nome.replace('"', '""') + '"'


def _lit(valor: str) -> str:
    return "'" + valor.replace("'", "''") + "'"


def _falha_sql(tabela: str, coluna: str, origem: str) -> str:
    """Expressão SQL que aborta a consulta citando tabela, coluna e o valor."""
    msg = f"{PREFIXO_ERRO}tabela {tabela}, coluna {coluna}, valor exemplo: "
    return f"error({_lit(msg)} || '\"' || {origem} || '\"')"


def _booleano(origem: str, tabela: str, coluna: str) -> str:
    # Não usa CAST(... AS BOOLEAN) porque o DuckDB aceitaria também
    # 'true', 't', 'yes' etc.; a spec só aceita "0" e "1". Nulo segue nulo.
    return (
        f"CASE WHEN {origem} IS NULL THEN NULL "
        f"WHEN {origem} = '1' THEN TRUE WHEN {origem} = '0' THEN FALSE "
        f"ELSE {_falha_sql(tabela, coluna, origem)} END"
    )


def _mapa(origem: str, tabela: str, coluna: str) -> str:
    casos = " ".join(
        f"WHEN {origem} = {_lit(de)} THEN {_lit(para)}"
        for de, para in MAPAS[coluna].items()
    )
    return (
        f"CASE WHEN {origem} IS NULL THEN NULL {casos} "
        f"ELSE {_falha_sql(tabela, coluna, origem)} END"
    )


def _expressao(raw: str, refined: str, tipo: str, tabela: str) -> str:
    origem = _q(raw)
    if tipo == "BOOLEAN":
        return _booleano(origem, tabela, refined)
    if tipo == "MAPA":
        return _mapa(origem, tabela, refined)
    return f"CAST({origem} AS {tipo})"


def _diagnosticar_cast(con: duckdb.DuckDBPyConnection, erro: duckdb.Error) -> str:
    """Descobre qual coluna fez o CAST falhar.

    A mensagem do DuckDB traz o valor, mas não a coluna. Repete o CAST de
    cada coluna numérica, isoladamente, sobre o raw inteiro.
    """
    alvos = [
        ("refined.clientes", raw, refined, tipo)
        for raw, refined, tipo in CLIENTES
        if tipo not in ("BOOLEAN", "MAPA")
    ] + [(ORIGEM, TOTAL_CAMPANHAS, TOTAL_CAMPANHAS, "INTEGER")]
    for tabela, raw, refined, tipo in alvos:
        try:
            con.execute(f"SELECT CAST({_q(raw)} AS {tipo}) FROM {ORIGEM}").fetchall()
        except duckdb.ConversionException as e:
            detalhe = str(e).splitlines()[0]
            return f"tabela {tabela}, coluna {refined} ({tipo}): {detalhe}"
    return str(erro)


def _montar_base(con: duckdb.DuckDBPyConnection) -> None:
    """Deduplica o raw e converte os tipos numa tabela temporária."""
    # Duplicata = mesmo texto em todas as colunas exceto Index. PARTITION BY
    # trata nulos como iguais, então nulo na mesma coluna não separa o grupo.
    sem_index = ", ".join(
        [_q(raw) for raw, _, _ in CLIENTES if raw != "Index"]
        + [_q(c) for c in CAMPANHAS + [TOTAL_CAMPANHAS]]
    )

    colunas = [
        f"{_expressao(raw, refined, tipo, 'refined.clientes')} AS {_q(refined)}"
        for raw, refined, tipo in CLIENTES
    ]
    colunas += [
        f"{_booleano(_q(c), 'refined.respostas_campanhas', 'aceitou')} AS aceitou_{i}"
        for i, c in enumerate(CAMPANHAS, start=1)
    ]
    colunas.append(f"CAST({_q(TOTAL_CAMPANHAS)} AS INTEGER) AS total_campanhas")

    sql = f"""
        CREATE OR REPLACE TEMP TABLE base AS
        WITH ordenado AS (
            SELECT *, row_number() OVER (
                PARTITION BY {sem_index}
                ORDER BY CAST("Index" AS INTEGER)
            ) AS ordem
            FROM {ORIGEM}
        )
        SELECT {", ".join(colunas)}
        FROM ordenado
        WHERE ordem = 1
    """
    try:
        con.execute(sql)
    except duckdb.Error as e:
        texto = str(e)
        if PREFIXO_ERRO in texto:
            linha = texto.split(PREFIXO_ERRO, 1)[1].splitlines()[0]
            raise ErroTransformacao(f"Falha de conversão: {linha}") from None
        raise ErroTransformacao(
            f"Falha de conversão: {_diagnosticar_cast(con, e)}"
        ) from None


def _conferir_total(con: duckdb.DuckDBPyConnection) -> None:
    soma = " + ".join(f"CAST(aceitou_{i} AS INTEGER)" for i in range(1, 6))
    divergentes = [
        r[0]
        for r in con.execute(
            "SELECT cliente_id FROM base "
            f"WHERE total_campanhas IS DISTINCT FROM ({soma}) ORDER BY cliente_id"
        ).fetchall()
    ]
    if divergentes:
        ids = ", ".join(str(i) for i in divergentes)
        raise ErroTransformacao(
            f"{TOTAL_CAMPANHAS} diferente da soma das 5 campanhas em "
            f"{_milhar(len(divergentes))} cliente(s). cliente_id: {ids}"
        )


def _gravar_refined(con: duckdb.DuckDBPyConnection) -> None:
    colunas_clientes = ", ".join(_q(refined) for _, refined, _ in CLIENTES)
    respostas = " UNION ALL ".join(
        f"SELECT cliente_id, CAST({i} AS INTEGER) AS campanha, "
        f"aceitou_{i} AS aceitou FROM base"
        for i in range(1, 6)
    )
    con.execute("BEGIN TRANSACTION")
    try:
        criar_schema(con, "refined")
        con.execute(
            "CREATE OR REPLACE TABLE refined.clientes AS "
            f"SELECT {colunas_clientes} FROM base ORDER BY cliente_id"
        )
        con.execute(
            "CREATE OR REPLACE TABLE refined.respostas_campanhas AS "
            f"SELECT * FROM ({respostas}) ORDER BY cliente_id, campanha"
        )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise


def _contar(con: duckdb.DuckDBPyConnection, tabela: str) -> int:
    return con.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0]


def _nulos(con: duckdb.DuckDBPyConnection, tabela: str) -> list[tuple[str, int]]:
    colunas = [r[0] for r in con.execute(f"DESCRIBE {tabela}").fetchall()]
    contagens = con.execute(
        "SELECT "
        + ", ".join(f"count(*) - count({_q(c)})" for c in colunas)
        + f" FROM {tabela}"
    ).fetchone()
    return [(f"{tabela}.{c}", n) for c, n in zip(colunas, contagens) if n > 0]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    con = conectar()
    try:
        existe = con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema = 'raw' AND table_name = 'clientes_campanhas'"
        ).fetchone()[0]
        if not existe:
            print(
                f"Tabela {ORIGEM} não encontrada. "
                "Rode antes a ingestão: uv run python -m pipeline.ingestao",
                file=sys.stderr,
            )
            sys.exit(1)

        lidas = _contar(con, ORIGEM)
        try:
            _montar_base(con)
            _conferir_total(con)
            _gravar_refined(con)
        except ErroTransformacao as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        mantidas = _contar(con, "base")

        print(f"{ORIGEM}: {_milhar(lidas)} linhas lidas")
        print(f"duplicatas removidas: {_milhar(lidas - mantidas)}")
        for tabela in ("refined.clientes", "refined.respostas_campanhas"):
            print(f"{tabela}: {_milhar(_contar(con, tabela))} linhas")
        nulos = _nulos(con, "refined.clientes") + _nulos(
            con, "refined.respostas_campanhas"
        )
        if nulos:
            print("nulos por coluna:")
            for coluna, n in nulos:
                print(f"  {coluna}: {_milhar(n)}")
        else:
            print("nulos por coluna: nenhum")
    finally:
        con.close()


if __name__ == "__main__":
    main()
