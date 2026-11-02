"""Testes de pipeline/marts.py e dos SQL em sql/marts/.

O refined de cada teste é produzido pela transformação a partir de um raw
inventado com 4 clientes e 7 aceites.
"""

import pytest
from conftest import consultar, criar_raw, linha, rodar

from pipeline import marts, transformacao

CLIENTES = 4
ACEITES = 7


@pytest.fixture
def refined():
    criar_raw(
        [
            linha(1001, Income="30000", Kidhome="1", education="Basic",
                  AcceptedCmp1="1"),
            linha(1002, Income="40000", Teenhome="1", AcceptedCmp1="1",
                  AcceptedCmp3="1"),
            linha(1003, Income="60000", education="Master"),
            linha(1004, Income="80000", education="PHD", AcceptedCmp2="1",
                  AcceptedCmp3="1", AcceptedCmp4="1", AcceptedCmp5="1"),
        ]
    )  # fmt: skip
    assert rodar(transformacao.main) == 0


def test_desempenho_campanhas_soma_de_aceites_igual_ao_total(refined):
    """Regra: os aceites por campanha somam o total de aceites do dado."""
    assert rodar(marts.main) == 0

    assert consultar("SELECT sum(aceites) FROM marts.desempenho_campanhas") == [
        (ACEITES,)
    ]


def test_alcance_soma_de_clientes_igual_ao_total(refined):
    """Regra: cada cliente aparece em exatamente uma quantidade de aceites."""
    assert rodar(marts.main) == 0

    assert consultar("SELECT sum(clientes) FROM marts.alcance") == [(CLIENTES,)]


def test_perfil_aceite_soma_de_clientes_por_dimensao_igual_ao_total(refined):
    """Regra: em cada dimensão, todo cliente cai em exatamente um grupo."""
    assert rodar(marts.main) == 0

    somas = consultar(
        "SELECT dimensao, sum(clientes) FROM marts.perfil_aceite GROUP BY 1 ORDER BY 1"
    )
    assert somas == [
        ("escolaridade", CLIENTES),
        ("filhos", CLIENTES),
        ("renda", CLIENTES),
    ]


def test_sql_que_devolve_zero_linhas_e_erro(refined, isolar, monkeypatch):
    """Regra: mart com zero linhas para tudo com erro."""
    pasta = isolar / "sql" / "marts"
    pasta.mkdir(parents=True)
    (pasta / "01_vazio.sql").write_text(
        "-- Grão: nenhum\nSELECT * FROM refined.clientes WHERE false\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(marts, "PASTA_SQL", pasta)

    assert rodar(marts.main) == 1
