"""Isolamento e dados inventados compartilhados pelos testes.

Todo teste roda com o banco e a planilha apontando para tmp_path, nunca para
o ifood.duckdb nem para raw/iFood.xlsx do projeto.
"""

import duckdb
import pytest

from pipeline import db, ingestao

COLUNAS_RAW = [
    "Index", "Income", "Kidhome", "Teenhome", "Recency", "MntWines",
    "MntFruits", "MntMeatProducts", "MntFishProducts", "MntSweetProducts",
    "MntRegularProds", "MntGoldProds", "MntTotal", "NumDealsPurchases",
    "NumWebPurchases", "NumCatalogPurchases", "NumStorePurchases",
    "NumWebVisitsMonth", "AcceptedCmp1", "AcceptedCmp2", "AcceptedCmp3",
    "AcceptedCmp4", "AcceptedCmp5", "AcceptedCmpOverall", "Complain", "Age",
    "Customer_Days", "marital_status", "education",
]  # fmt: skip
CAMPANHAS = [f"AcceptedCmp{i}" for i in range(1, 6)]


@pytest.fixture(autouse=True)
def isolar(tmp_path, monkeypatch):
    """Aponta banco e planilha para tmp_path em todos os testes."""
    monkeypatch.setattr(db, "RAIZ", tmp_path)
    monkeypatch.setattr(ingestao, "ARQUIVO", tmp_path / "raw" / "iFood.xlsx")
    return tmp_path


def linha(index: int, **valores: str) -> dict[str, str]:
    """Uma linha do raw, toda em texto, com valores padrão válidos.

    Customer_Days recebe o próprio Index para que duas linhas só sejam
    idênticas quando o teste quiser. AcceptedCmpOverall é a soma das
    campanhas, a menos que o teste o informe.
    """
    base = {c: "0" for c in COLUNAS_RAW}
    base.update(
        Index=str(index),
        Income="50000",
        Recency="10",
        MntWines="100",
        MntRegularProds="90",
        MntGoldProds="10",
        MntTotal="100",
        NumWebPurchases="2",
        NumStorePurchases="3",
        NumWebVisitsMonth="5",
        Age="40",
        Customer_Days=str(index),
        marital_status="Married",
        education="Graduation",
    )
    base.update(valores)
    if "AcceptedCmpOverall" not in valores:
        base["AcceptedCmpOverall"] = str(sum(int(base[c]) for c in CAMPANHAS))
    return base


def criar_raw(linhas: list[dict[str, str]]) -> None:
    """Grava raw.clientes_campanhas, toda VARCHAR, no banco de teste."""
    con = db.conectar()
    colunas = ", ".join(f'"{c}" VARCHAR' for c in COLUNAS_RAW)
    con.execute("CREATE SCHEMA raw")
    con.execute(f"CREATE TABLE raw.clientes_campanhas ({colunas})")
    marcadores = ", ".join("?" for _ in COLUNAS_RAW)
    con.executemany(
        f"INSERT INTO raw.clientes_campanhas VALUES ({marcadores})",
        [[ln[c] for c in COLUNAS_RAW] for ln in linhas],
    )
    con.close()


def consultar(sql: str) -> list[tuple]:
    """Roda uma consulta no banco de teste e devolve as linhas."""
    con = duckdb.connect(str(db.RAIZ / "ifood.duckdb"), read_only=True)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def rodar(main) -> int:
    """Executa o main() de um módulo e devolve o código de saída."""
    try:
        main()
    except SystemExit as e:
        return e.code
    return 0
