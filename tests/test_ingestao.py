"""Testes de pipeline/ingestao.py."""

import openpyxl
from conftest import consultar, rodar

from pipeline import ingestao


def _planilha(caminho, linhas):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    aba = wb.active
    aba.title = "iFood"
    aba.append(["Index", "Income", "education"])
    for ln in linhas:
        aba.append(ln)
    wb.save(caminho)


def test_todas_as_colunas_chegam_como_varchar():
    """Regra: toda coluna entra como texto, mesmo a que tem número na planilha."""
    _planilha(ingestao.ARQUIVO, [[1001, 58138, "Graduation"], [1002, 46344, "PhD"]])

    assert rodar(ingestao.main) == 0

    tipos = {r[1] for r in consultar("DESCRIBE raw.clientes_campanhas")}
    assert tipos == {"VARCHAR"}


def test_celula_vazia_vira_nulo_e_texto_na_continua_na():
    """Regra: só célula vazia vira nulo; o texto "NA" fica como "NA"."""
    _planilha(ingestao.ARQUIVO, [[1001, None, "NA"]])

    assert rodar(ingestao.main) == 0

    assert consultar('SELECT "Income", education FROM raw.clientes_campanhas') == [
        (None, "NA")
    ]


def test_rodar_duas_vezes_nao_duplica_linhas():
    """Regra: a tabela é recriada a cada execução, nunca acrescentada."""
    _planilha(ingestao.ARQUIVO, [[1001, 1, "a"], [1002, 2, "b"], [1003, 3, "c"]])

    assert rodar(ingestao.main) == 0
    assert rodar(ingestao.main) == 0

    assert consultar("SELECT count(*) FROM raw.clientes_campanhas") == [(3,)]


def test_planilha_ausente_encerra_com_erro_sem_criar_banco(isolar):
    """Regra: sem a planilha, sai com código 1 antes de criar o banco."""
    assert rodar(ingestao.main) == 1

    assert not (isolar / "ifood.duckdb").exists()
