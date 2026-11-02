"""Testes de pipeline/transformacao.py."""

from conftest import consultar, criar_raw, linha, rodar

from pipeline import transformacao


def _tabelas_refined() -> list[tuple]:
    return consultar(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'refined'"
    )


def test_linhas_identicas_exceto_index_viram_um_cliente_com_menor_index():
    """Regra: duplicata (tudo igual menos o Index) fica só com o menor Index."""
    criar_raw(
        [
            linha(1005, Customer_Days="700"),
            linha(1002, Customer_Days="700"),
            linha(1003),
        ]
    )

    assert rodar(transformacao.main) == 0

    ids = consultar("SELECT cliente_id FROM refined.clientes ORDER BY 1")
    assert ids == [(1002,), (1003,)]


def test_cada_cliente_gera_cinco_linhas_em_respostas_campanhas():
    """Regra: uma linha por cliente em cada uma das 5 campanhas."""
    criar_raw([linha(1001), linha(1002, AcceptedCmp2="1"), linha(1003)])

    assert rodar(transformacao.main) == 0

    contagens = consultar(
        "SELECT cliente_id, count(*), count(DISTINCT campanha) "
        "FROM refined.respostas_campanhas GROUP BY 1 ORDER BY 1"
    )
    assert contagens == [(1001, 5, 5), (1002, 5, 5), (1003, 5, 5)]


def test_2n_cycle_e_master_viram_mestrado():
    """Regra: "2n Cycle" e "Master" são a mesma escolaridade, mestrado."""
    criar_raw([linha(1001, education="2n Cycle"), linha(1002, education="Master")])

    assert rodar(transformacao.main) == 0

    valores = consultar("SELECT DISTINCT escolaridade FROM refined.clientes")
    assert valores == [("mestrado",)]


def test_escolaridade_fora_do_mapa_para_e_nao_cria_refined():
    """Regra: escolaridade desconhecida para tudo, sem gravar em refined."""
    criar_raw([linha(1001), linha(1002, education="Doctor")])

    assert rodar(transformacao.main) == 1

    assert _tabelas_refined() == []


def test_accepted_cmp_diferente_de_0_e_1_para():
    """Regra: só "0" e "1" são aceitos nas campanhas."""
    criar_raw([linha(1001, AcceptedCmp3="2", AcceptedCmpOverall="0")])

    assert rodar(transformacao.main) == 1


def test_accepted_cmp_overall_diferente_da_soma_para():
    """Regra: AcceptedCmpOverall tem que ser a soma das 5 campanhas."""
    criar_raw([linha(1001, AcceptedCmp1="1", AcceptedCmpOverall="2")])

    assert rodar(transformacao.main) == 1
