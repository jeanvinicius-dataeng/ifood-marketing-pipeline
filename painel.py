"""Leitura, formatação e gráficos do painel, usados por app.py e relatorio.py.

Regra central (specs/dashboard.md, item 2): aqui só se lê o que os marts
entregam. Nenhum cálculo, agregação, ordenação ou filtro por valor. Uma linha
é escolhida só pela chave do mart; os destaques vêm das colunas booleanas
dos marts (pior_campanha, maior_taxa). O JavaScript da cena 3D recebe os
números prontos e só calcula posições de layout.
"""

import json
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

import duckdb
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs_version
from plotly.subplots import make_subplots

MARTS = (
    "resumo",
    "desempenho_campanhas",
    "alcance",
    "gasto_por_resposta",
    "perfil_aceite",
)

# Tema (item 6)
FUNDO_1 = "#0B0D12"
FUNDO_2 = "#141824"
TEXTO = "#F2F2F2"
TEXTO_SECUNDARIO = "#9AA0AE"
DESTAQUE = "#FF3B4A"
BARRA = "#3A4152"
BARRA_2 = "#5B6375"
FONTE = "Inter, system-ui, -apple-system, 'Segoe UI', sans-serif"
FONTE_NUMEROS = "'Space Grotesk', Inter, system-ui, sans-serif"
GOOGLE_FONTS = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700"
    "&family=Space+Grotesk:wght@500;700&display=swap"
)
THREE_JS = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
# Pacote reduzido do Plotly, só com barras e afins, na versão do plotly.py.
PLOTLY_BASICO = f"https://cdn.plot.ly/plotly-basic-{get_plotlyjs_version()}.min.js"

TITULO = "Campanhas de marketing: quem responde e quem não responde"
CREDITO = (
    "Dados do case público de marketing do iFood (Kaggle, licença CC0). "
    "Projeto de estudo, sem relação oficial com o iFood."
)


# ---------------------------------------------------------------- leitura


def ler_marts(banco: Path) -> dict[str, pd.DataFrame]:
    """Lê os marts inteiros, em modo somente leitura, na ordem gravada."""
    con = duckdb.connect(str(banco), read_only=True)
    try:
        return {nome: con.execute(f"SELECT * FROM marts.{nome}").df() for nome in MARTS}
    finally:
        con.close()


def linhas(df: pd.DataFrame, **chave) -> pd.DataFrame:
    """Seleciona as linhas do mart com essa parte da chave, na ordem do mart."""
    mascara = pd.Series(True, index=df.index)
    for coluna, valor in chave.items():
        mascara &= df[coluna] == valor
    return df[mascara]


def linha(df: pd.DataFrame, **chave) -> pd.Series:
    """Seleciona a única linha do mart com essa chave."""
    encontradas = linhas(df, **chave)
    if len(encontradas) != 1:
        raise ValueError(f"esperava 1 linha com {chave}, achei {len(encontradas)}")
    return encontradas.iloc[0]


def tem_linha(df: pd.DataFrame, **chave) -> bool:
    """Diz se existe linha no mart com essa chave."""
    return not linhas(df, **chave).empty


def _conferir(condicao: bool, frase: str) -> None:
    # Os títulos citam um grupo pela chave. Se o dado mudar e o grupo deixar
    # de ser o destaque, o painel para em vez de publicar uma frase falsa.
    if not condicao:
        raise ValueError(f"Título não confere com o dado: {frase}")


# ------------------------------------------------------------- formatação


def numero(valor: float, casas: int = 0) -> str:
    """Formato brasileiro: 1.023,31."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def pct(valor: float) -> str:
    return f"{numero(valor, 1)}%"


def dinheiro(valor: float) -> str:
    return f"R$ {numero(valor, 2)}"


def numero2(valor: float) -> str:
    return numero(valor, 2)


def vezes(valor: float) -> str:
    return numero(valor, 1)


# Só exibição: troca o nome do mart pelo rótulo em português. Não é cálculo.
ROTULOS = {
    "ate_35k": "Até 35 mil",
    "35k_a_55k": "35 a 55 mil",
    "55k_a_75k": "55 a 75 mil",
    "acima_75k": "Acima de 75 mil",
    "com_filhos": "Com filhos",
    "sem_filhos": "Sem filhos",
    "basico": "Básico",
    "graduacao": "Graduação",
    "mestrado": "Mestrado",
    "doutorado": "Doutorado",
    "aceitou_alguma": "Aceitou alguma",
    "nunca_aceitou": "Nunca aceitou",
}


def rotulo(nome: str) -> str:
    """Rótulo de exibição do valor do mart; fora do mapa, aparece como veio."""
    return ROTULOS.get(nome, str(nome))


def rotulo_campanha(n: int) -> str:
    return f"Campanha {n}"


def rotulo_quantidade(n: int) -> str:
    return f"{n} campanha" if n == 1 else f"{n} campanhas"


# --------------------------------------------------------------- gráficos

CONFIG_PLOTLY = {"displayModeBar": False, "responsive": True}


def _estilo(fig: go.Figure, altura: int) -> go.Figure:
    """Barras horizontais, fundo transparente, sem grade, valor na ponta."""
    fig.update_layout(
        template="none",  # sem os contornos e grades do tema padrão
        height=altura,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": FONTE, "color": TEXTO_SECUNDARIO, "size": 13},
        showlegend=False,
        margin={"l": 8, "r": 96, "t": 8, "b": 8},
        bargap=0.32,
        hoverlabel={
            "bgcolor": FUNDO_2,
            "bordercolor": "rgba(255,255,255,0.08)",
            "font": {"family": FONTE, "color": TEXTO, "size": 13},
        },
    )
    eixo = {"showgrid": False, "zeroline": False, "showline": False, "ticks": ""}
    fig.update_xaxes(**eixo, visible=False)  # o valor já está na barra
    # Primeira linha do mart no topo; ticksuffix afasta o rótulo da barra.
    fig.update_yaxes(**eixo, autorange="reversed", ticksuffix="  ", automargin=True)
    fig.update_traces(
        orientation="h",
        cliponaxis=False,
        textposition="outside",
        textfont={"family": FONTE_NUMEROS, "color": TEXTO, "size": 14},
        marker_cornerradius=7,
        marker_line_width=0,
        hovertemplate="%{y}: <b>%{text}</b><extra></extra>",
    )
    return fig


def _cores(destaques) -> list[str]:
    return [DESTAQUE if d else BARRA for d in destaques]


def _barras(rotulos, valores, textos, destaques) -> go.Figure:
    fig = go.Figure(
        go.Bar(
            y=list(rotulos),
            x=list(valores),
            text=list(textos),
            marker_color=_cores(destaques),
        )
    )
    return _estilo(fig, 40 + 46 * len(fig.data[0].y))


@dataclass
class Grafico:
    div_id: str
    titulo: str
    destaque: str  # trecho do título pintado de vermelho
    explicacao: str
    figura: go.Figure
    nota: str | None = None


@dataclass
class Secao:
    chave: str
    nome: str
    graficos: list[Grafico] = field(default_factory=list)


@dataclass
class Cartao:
    rotulo: str
    texto: str  # valor final, já formatado
    valor: float  # o mesmo valor, cru, para a contagem animada
    formato: str  # int, pct ou brl
    contexto: str
    destaque: bool = False


@dataclass
class Painel:
    titulo: str
    subtitulo: str
    cartoes: list[Cartao]
    cena: dict
    secoes: list[Secao]
    rodape: list[str]


def _desempenho(m: dict[str, pd.DataFrame]) -> Secao:
    df = m["desempenho_campanhas"]
    pior = linha(df, campanha=2)
    _conferir(bool(pior["pior_campanha"]), "a campanha 2 não é a pior")
    destaque = f"{vezes(pior['vezes_menor_que_outras'])} vezes menos"
    return Secao(
        "desempenho",
        "Desempenho",
        [
            Grafico(
                "g01",
                f"A campanha {pior['campanha']} converteu {destaque} que a média "
                "das outras",
                destaque,
                "Taxa de aceite de cada campanha: clientes que aceitaram, em % do "
                "total de clientes.",
                _barras(
                    [rotulo_campanha(c) for c in df["campanha"]],
                    df["taxa_aceite_pct"],
                    [pct(v) for v in df["taxa_aceite_pct"]],
                    df["pior_campanha"],
                ),
            )
        ],
    )


def _alcance(m: dict[str, pd.DataFrame]) -> Secao:
    df = m["alcance"]
    campanhas = int(m["resumo"].iloc[0]["campanhas"])
    nenhuma = linha(df, campanhas_aceitas=0)
    _conferir(
        not tem_linha(df, campanhas_aceitas=campanhas),
        f"existe cliente que aceitou as {campanhas} campanhas",
    )
    destaque = pct(nenhuma["pct_clientes"])
    return Secao(
        "alcance",
        "Alcance",
        [
            Grafico(
                "g02",
                f"Ninguém aceitou as {campanhas} campanhas, e {destaque} nunca "
                "aceitaram nenhuma",
                destaque,
                "Clientes por quantidade de campanhas aceitas, em % do total de "
                "clientes.",
                _barras(
                    [rotulo_quantidade(n) for n in df["campanhas_aceitas"]],
                    df["pct_clientes"],
                    [pct(v) for v in df["pct_clientes"]],
                    df["campanhas_aceitas"] == 0,  # comparação de chave
                ),
            )
        ],
    )


def _gasto(m: dict[str, pd.DataFrame]) -> Secao:
    df = m["gasto_por_resposta"]
    aceitou = linha(df, grupo="aceitou_alguma")
    _conferir(
        aceitou["gasto_vezes_outro_grupo"] > 1,
        "quem aceitou não gasta mais que quem nunca aceitou",
    )
    medidas = [
        ("gasto_total_medio", "Gasto médio em 2 anos", dinheiro),
        ("compras_com_desconto_media", "Compras com desconto, média", numero2),
        ("compras_site_media", "Compras pelo site, média", numero2),
    ]
    fig = make_subplots(
        rows=len(medidas),
        cols=1,
        subplot_titles=[titulo for _, titulo, _ in medidas],
        vertical_spacing=0.17,
    )
    cores = _cores(df["grupo"] == "aceitou_alguma")  # comparação de chave
    for i, (coluna, _, formato) in enumerate(medidas, start=1):
        fig.add_trace(
            go.Bar(
                y=[rotulo(g) for g in df["grupo"]],
                x=list(df[coluna]),
                text=[formato(v) for v in df[coluna]],
                marker_color=cores,
            ),
            row=i,
            col=1,
        )
    _estilo(fig, 430)
    fig.update_layout(margin={"t": 28})
    fig.update_annotations(
        font={"size": 12, "color": TEXTO_SECUNDARIO, "family": FONTE},
        x=0,
        xanchor="left",
    )
    destaque = f"{vezes(aceitou['gasto_vezes_outro_grupo'])} vezes mais"
    return Secao(
        "gasto",
        "Gasto",
        [
            Grafico(
                "g03",
                f"Quem aceita campanha gasta {destaque}",
                destaque,
                "Média por cliente de quem aceitou alguma campanha e de quem nunca "
                "aceitou.",
                fig,
                nota=(
                    "O gasto é o total de 2 anos do cliente, não é atribuído a "
                    "nenhuma campanha. O gráfico mostra relação, não prova que a "
                    "campanha causou o gasto."
                ),
            )
        ],
    )


def _perfil(m: dict[str, pd.DataFrame]) -> Secao:
    df = m["perfil_aceite"]
    campanhas = int(m["resumo"].iloc[0]["campanhas"])
    explicacao = (
        f"Taxa de aceite por {{}}: aceites em % de clientes × {campanhas} campanhas."
    )

    renda = linha(df, dimensao="renda", grupo="acima_75k")
    _conferir(bool(renda["maior_taxa"]), "acima_75k não é a maior taxa de renda")

    sem = linha(df, dimensao="filhos", grupo="sem_filhos")
    com = linha(df, dimensao="filhos", grupo="com_filhos")
    _conferir(
        bool(sem["maior_taxa"]) and bool(com["menor_taxa"]),
        "sem_filhos não aceita mais que com_filhos",
    )

    doutorado = linha(df, dimensao="escolaridade", grupo="doutorado")
    basico = linha(df, dimensao="escolaridade", grupo="basico")
    _conferir(
        bool(doutorado["maior_taxa"]) and bool(basico["menor_taxa"]),
        "doutorado não é a maior taxa ou basico não é a menor",
    )

    def grafico(dimensao: str) -> go.Figure:
        grupos = linhas(df, dimensao=dimensao)
        return _barras(
            [rotulo(g) for g in grupos["grupo"]],
            grupos["taxa_aceite_pct"],
            [pct(v) for v in grupos["taxa_aceite_pct"]],
            grupos["maior_taxa"],
        )

    d_renda = pct(renda["taxa_aceite_pct"])
    d_filhos = f"{vezes(sem['vezes_menor_taxa'])} vezes mais"
    d_esc = f"{vezes(doutorado['vezes_menor_taxa'])} vezes"
    return Secao(
        "perfil",
        "Perfil",
        [
            Grafico(
                "g04",
                f"Renda acima de 75 mil tem a maior taxa de aceite: {d_renda}",
                d_renda,
                explicacao.format("faixa de renda anual"),
                grafico("renda"),
            ),
            Grafico(
                "g05",
                f"Cliente sem filhos aceita {d_filhos} que cliente com filhos",
                d_filhos,
                explicacao.format("presença de crianças ou adolescentes em casa"),
                grafico("filhos"),
            ),
            Grafico(
                "g06",
                "Doutorado tem a maior taxa de aceite "
                f"({pct(doutorado['taxa_aceite_pct'])}), {d_esc} a do básico",
                d_esc,
                explicacao.format("escolaridade"),
                grafico("escolaridade"),
            ),
        ],
    )


def _cena(m: dict[str, pd.DataFrame]) -> dict:
    """Dados da cena 3D. Números prontos dos marts 01 e 05, já formatados."""
    r = m["resumo"].iloc[0]  # o mart resumo tem uma linha só, a base inteira
    df = m["desempenho_campanhas"]
    pior = linha(df, campanha=2)
    _conferir(bool(pior["pior_campanha"]), "a campanha 2 não é a pior")
    campanhas = [
        {
            "rotulo": f"Camp. {c}",
            "aceites": int(a),
            "taxa": float(t),
            "taxa_txt": pct(t),
            "pior": bool(p),
        }
        for c, a, t, p in zip(
            df["campanha"],
            df["aceites"],
            df["taxa_aceite_pct"],
            df["pior_campanha"],
            strict=True,
        )
    ]
    clientes = numero(r["clientes"])
    alguma = numero(r["clientes_aceitaram_alguma"])
    nunca = numero(r["clientes_nunca_aceitaram"])
    return {
        "campanhas": campanhas,
        "clientes": int(r["clientes"]),
        "alguma": int(r["clientes_aceitaram_alguma"]),
        "nunca": int(r["clientes_nunca_aceitaram"]),
        "aceites": int(r["aceites"]),
        "rotulos": {
            "clientes": [clientes, "clientes no total"],
            "alguma_total": [alguma, "responderam a alguma campanha"],
            "nunca": [nunca, "nunca responderam"],
            "alguma": [alguma, "responderam a alguma"],
        },
        "legenda_reserva": [
            "Taxa de aceite por campanha.",
            (
                f"A campanha {pior['campanha']} teve a menor: "
                f"{pct(pior['taxa_aceite_pct'])}."
            ),
        ],
        "legendas": [
            [
                "Cada ponto é um aceite.",
                (
                    f"Uma coluna por campanha. A campanha {pior['campanha']} juntou só "
                    f"{numero(pior['aceites'])} aceites."
                ),
            ],
            [
                "Cada ponto é um cliente.",
                (
                    f"À esquerda, os {nunca} que nunca responderam. À direita, os "
                    f"{alguma} que responderam a alguma campanha."
                ),
            ],
            [
                "Cada ponto é um cliente.",
                (
                    f"Todos os {clientes} clientes. Em vermelho, quem respondeu a pelo "
                    "menos uma campanha."
                ),
            ],
        ],
    }


def montar(m: dict[str, pd.DataFrame]) -> Painel:
    """Todo o conteúdo do painel, na ordem da tela."""
    r = m["resumo"].iloc[0]  # o mart resumo tem uma linha só, a base inteira
    campanhas = int(r["campanhas"])
    cartoes = [
        Cartao(
            "Clientes",
            numero(r["clientes"]),
            float(r["clientes"]),
            "int",
            f"receberam as {campanhas} campanhas",
        ),
        Cartao(
            "Taxa de aceite geral",
            pct(r["taxa_aceite_pct"]),
            float(r["taxa_aceite_pct"]),
            "pct",
            f"{numero(r['aceites'])} aceites em {campanhas} campanhas",
        ),
        Cartao(
            "Aceitaram alguma campanha",
            pct(r["pct_aceitou_alguma"]),
            float(r["pct_aceitou_alguma"]),
            "pct",
            f"{numero(r['clientes_aceitaram_alguma'])} de "
            f"{numero(r['clientes'])} clientes",
        ),
        Cartao(
            "Gasto médio de quem aceitou",
            dinheiro(r["gasto_medio_aceitou"]),
            float(r["gasto_medio_aceitou"]),
            "brl",
            f"contra {dinheiro(r['gasto_medio_nunca_aceitou'])} de quem nunca aceitou",
            destaque=True,
        ),
    ]
    return Painel(
        titulo=TITULO,
        subtitulo=(
            f"{numero(r['clientes'])} clientes e {campanhas} campanhas do case "
            "público de marketing do iFood."
        ),
        cartoes=cartoes,
        cena=_cena(m),
        secoes=[_desempenho(m), _alcance(m), _gasto(m), _perfil(m)],
        rodape=[
            CREDITO,
            (
                "Premissa: o dado não diz quem recebeu cada campanha, só quem "
                "aceitou. Assume-se que todos os clientes receberam as "
                f"{campanhas} campanhas."
            ),
        ],
    )


# ------------------------------------------------------------------- HTML


def css() -> str:
    """Estilo da página inteira: app (fora e dentro do iframe) e relatório."""
    return (
        _CSS.replace("$FUNDO_1", FUNDO_1)
        .replace("$FUNDO_2", FUNDO_2)
        .replace("$TEXTO_SECUNDARIO", TEXTO_SECUNDARIO)
        .replace("$TEXTO", TEXTO)
        .replace("$DESTAQUE", DESTAQUE)
        .replace("$BARRA_2", BARRA_2)
        .replace("$BARRA", BARRA)
        .replace("$FONTE_NUMEROS", FONTE_NUMEROS)
        .replace("$FONTE", FONTE)
        .replace("$GOOGLE_FONTS", GOOGLE_FONTS)
    )


_CSS = """
@import url('$GOOGLE_FONTS');
:root { color-scheme: dark; }
.painel { font-family: $FONTE; color: $TEXTO; font-size: 15px; line-height: 1.5; }
.painel .titulo { font-family: $FONTE_NUMEROS; font-weight: 700; line-height: 1.1;
  font-size: clamp(26px, 4.6vw, 44px); margin: 0; text-wrap: balance; }
.painel .subtitulo { color: $TEXTO_SECUNDARIO; margin: 8px 0 0; max-width: 62ch; }

/* Topo: cena 3D e cartões */
.topo { display: flex; flex-direction: column; gap: 28px; }
.hero { position: relative; height: 420px; border-radius: 20px; overflow: hidden;
  background: radial-gradient(ellipse at 50% 85%, rgba(255,59,74,.10), transparent 60%),
    rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08); }
.hero canvas { display: block; width: 100%; height: 100%; }
.hero-cap { position: absolute; left: 20px; top: 16px; right: 20px; font-size: 13px;
  color: $TEXTO_SECUNDARIO; pointer-events: none; }
.hero-cap b { color: $TEXTO; font-weight: 600; }
.lbl { position: absolute; transform: translate(-50%, -100%); font-family: $FONTE_NUMEROS;
  font-weight: 700; font-size: 15px; white-space: nowrap; pointer-events: none;
  text-shadow: 0 2px 10px rgba(0,0,0,.6); transition: opacity .4s; }
.lbl.base { transform: translate(-50%, 8px); font-family: $FONTE; font-weight: 500;
  font-size: 12px; color: $TEXTO_SECUNDARIO; }
.lbl.hot { color: $DESTAQUE; }
.lbl.big { font-size: 26px; text-align: center; line-height: 1.1; }
.lbl.big small { display: block; font: 500 12px $FONTE; color: $TEXTO_SECUNDARIO; }
.lbl.big.hot small { color: #FFB4BA; }
.steps { position: absolute; left: 50%; bottom: 14px; transform: translateX(-50%);
  display: flex; gap: 6px; background: rgba(11,13,18,.7);
  border: 1px solid rgba(255,255,255,0.08); border-radius: 999px; padding: 4px;
  backdrop-filter: blur(8px); }
.steps button { font: 500 12.5px $FONTE; color: $TEXTO_SECUNDARIO; background: transparent;
  border: 0; border-radius: 999px; padding: 7px 12px; cursor: pointer; white-space: nowrap; }
.steps button.on { background: $DESTAQUE; color: #fff; }
.steps button:focus-visible { outline: 2px solid $TEXTO; outline-offset: 2px; }
.reserva { position: absolute; inset: 56px 20px 20px; display: flex;
  flex-direction: column; gap: 9px; }
.reserva .row { display: grid; grid-template-columns: 96px 1fr; align-items: center;
  gap: 10px; font-size: 13px; color: $TEXTO_SECUNDARIO; }
.reserva .fill { height: 26px; border-radius: 7px; background: $BARRA; display: flex;
  align-items: center; justify-content: flex-end; padding-right: 8px; min-width: 46px;
  font: 700 13px $FONTE_NUMEROS; color: $TEXTO; }
.reserva .fill.hot { background: linear-gradient(90deg, #c92a37, $DESTAQUE);
  box-shadow: 0 0 18px rgba(255,59,74,.35); }
.cards { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
.card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px; padding: 18px; backdrop-filter: blur(8px); min-width: 0; }
.card .k { font-size: 12px; letter-spacing: .05em; text-transform: uppercase;
  color: $TEXTO_SECUNDARIO; }
.card .v { font-family: $FONTE_NUMEROS; font-weight: 700; line-height: 1.15;
  font-size: clamp(24px, 3.4vw, 36px); margin-top: 6px; font-variant-numeric: tabular-nums;
  white-space: nowrap; }
.card .v.hot { color: $DESTAQUE; text-shadow: 0 0 24px rgba(255,59,74,.35); }
.card .c { font-size: 13px; color: $TEXTO_SECUNDARIO; margin-top: 4px; }

/* Seções de análise em painéis de vidro */
.sec, [class*="st-key-secao_"] { background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 22px;
  backdrop-filter: blur(8px); animation: subir .7s ease both; }
@supports (animation-timeline: view()) {
  .sec, [class*="st-key-secao_"] { animation-timeline: view();
    animation-range: entry 0% entry 35%; }
}
.painel .tag { font-size: 12px; letter-spacing: .08em; text-transform: uppercase;
  color: $TEXTO_SECUNDARIO; }
.painel .grafico + .grafico, .grafico-bloco + .grafico-bloco { margin-top: 26px; }
.painel .titulo-grafico { font-family: $FONTE_NUMEROS; font-weight: 700; line-height: 1.25;
  font-size: clamp(19px, 2.6vw, 24px); margin: 10px 0 0; text-wrap: balance; }
.painel .titulo-grafico em { font-style: normal; color: $DESTAQUE; }
.painel .explicacao { color: $TEXTO_SECUNDARIO; font-size: 13.5px; margin: 6px 0 4px; }
.painel .nota { font-size: 12.5px; color: $TEXTO_SECUNDARIO; margin: 6px 0 0;
  border-left: 2px solid $BARRA_2; padding-left: 12px; }
.painel .rodape { color: $TEXTO_SECUNDARIO; font-size: 12.5px;
  border-top: 1px solid rgba(255,255,255,0.08); padding-top: 16px; }
.painel .rodape p { margin: 0 0 4px; }
/* Brilho suave só nas barras vermelhas do Plotly */
.js-plotly-plot .point path[style*="rgb(255, 59, 74)"] {
  filter: drop-shadow(0 0 6px rgba(255,59,74,.55)); }

@keyframes subir { from { opacity: .0001; transform: translateY(14px); }
  to { opacity: 1; transform: none; } }
@media (max-width: 760px) {
  .cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hero { height: 300px; }
  .lbl.big { font-size: 20px; }
  .steps button { padding: 7px 9px; font-size: 11.5px; }
  .sec, [class*="st-key-secao_"] { padding: 16px; }
}
@media (prefers-reduced-motion: reduce) {
  .sec, [class*="st-key-secao_"] { animation: none; }
  .lbl { transition: none; }
}
"""


def html_cabecalho(p: Painel) -> str:
    return (
        f'<div class="painel"><div class="titulo">{escape(p.titulo)}</div>'
        f'<p class="subtitulo">{escape(p.subtitulo)}</p></div>'
    )


def html_topo(p: Painel) -> str:
    """Cena 3D, cartões e o script que anima os dois. Precisa de Three.js."""
    cartoes = "".join(
        f'<div class="card"><div class="k">{escape(c.rotulo)}</div>'
        f'<div class="v{" hot" if c.destaque else ""}" data-n="{c.valor}" '
        f'data-f="{c.formato}">{escape(c.texto)}</div>'
        f'<div class="c">{escape(c.contexto)}</div></div>'
        for c in p.cartoes
    )
    botoes = "".join(
        f'<button type="button" data-s="{i}" aria-pressed="false">{nome}</button>'
        for i, nome in enumerate(
            ("Por campanha", "Quem respondeu", "Todos os clientes")
        )
    )
    dados = json.dumps(p.cena, ensure_ascii=False).replace("</", "<\\/")
    return (
        '<div class="painel topo">'
        '<div class="hero" id="hero">'
        '<div class="hero-cap"><b id="cap-t"></b> <span id="cap-s"></span></div>'
        f'<div class="steps" role="group" aria-label="Cenas">{botoes}</div>'
        "</div>"
        f'<div class="cards">{cartoes}</div>'
        "</div>"
        f"<script>{_JS.replace('__DADOS__', dados)}</script>"
    )


def html_secao_inicio(s: Secao) -> str:
    return f'<div class="painel"><span class="tag">{escape(s.nome)}</span></div>'


def html_cabecalho_grafico(g: Grafico) -> str:
    titulo = escape(g.titulo).replace(
        escape(g.destaque), f"<em>{escape(g.destaque)}</em>", 1
    )
    return (
        f'<div class="painel"><p class="titulo-grafico">{titulo}</p>'
        f'<p class="explicacao">{escape(g.explicacao)}</p></div>'
    )


def html_nota(g: Grafico) -> str:
    return (
        f'<div class="painel"><p class="nota">{escape(g.nota)}</p></div>'
        if g.nota
        else ""
    )


def html_rodape(linhas_rodape: list[str]) -> str:
    texto = "".join(f"<p>{escape(t)}</p>" for t in linhas_rodape)
    return f'<div class="painel"><div class="rodape">{texto}</div></div>'


# Cena 3D (item 7), adaptada de specs/referencia_visual.html. Recebe os números
# prontos em D; só calcula posições, cores e animação.
_JS = r"""
(function(){
const D = __DADOS__;
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const br = (x, d) => x.toLocaleString("pt-BR", {minimumFractionDigits: d, maximumFractionDigits: d});

// Cartões: contam do zero até o valor; o texto final é o do mart, já formatado.
if (!reduce) document.querySelectorAll(".card .v[data-n]").forEach(el => {
  const n = +el.dataset.n, f = el.dataset.f, fim = el.textContent, t0 = performance.now(), dur = 1200;
  const fmt = x => f === "int" ? br(Math.round(x), 0) : f === "pct" ? br(x, 1) + "%" : "R$ " + br(x, 2);
  el.textContent = fmt(0);
  (function passo(t){
    const p = Math.min(1, Math.max(0, (t - t0) / dur)), e = 1 - Math.pow(1 - p, 3);
    el.textContent = p < 1 ? fmt(n * e) : fim;
    if (p < 1) requestAnimationFrame(passo);
  })(t0);
});

const host = document.getElementById("hero");
const capT = document.getElementById("cap-t"), capS = document.getElementById("cap-s");
const botoes = [...host.querySelectorAll(".steps button")];

function reserva(){
  // Sem WebGL: barras 2D da taxa de aceite por campanha (mart 01).
  host.querySelector(".steps").hidden = true;
  capT.textContent = D.legenda_reserva[0]; capS.textContent = D.legenda_reserva[1];
  const caixa = document.createElement("div"); caixa.className = "reserva";
  const maior = Math.max(...D.campanhas.map(c => c.taxa));  // escala da largura
  D.campanhas.forEach(c => {
    const r = document.createElement("div"); r.className = "row";
    r.innerHTML = `<span>${c.rotulo}</span><div class="fill${c.pior ? " hot" : ""}" style="width:${Math.max(4, c.taxa / maior * 100)}%">${c.taxa_txt}</div>`;
    caixa.appendChild(r);
  });
  host.appendChild(caixa);
}

let ok = false;
try {
  const c = document.createElement("canvas");
  ok = !!(window.THREE && window.WebGLRenderingContext && (c.getContext("webgl") || c.getContext("experimental-webgl")));
} catch (e) { ok = false; }
if (!ok) { reserva(); return; }

const NC = D.campanhas.length, ACC = D.campanhas.map(c => c.aceites);
const NUNCA = D.nunca, ALGUMA = D.alguma, NRED = Math.max(D.aceites, ALGUMA);
const W = () => host.clientWidth, H = () => host.clientHeight;
const r = new THREE.WebGLRenderer({antialias: true, alpha: true});
r.setPixelRatio(Math.min(1.5, devicePixelRatio)); r.setSize(W(), H());
host.insertBefore(r.domElement, host.firstChild);
const s = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(34, W() / H(), .1, 100);
s.add(new THREE.AmbientLight(0xffffff, .55));
const luz = new THREE.DirectionalLight(0xffffff, .8); luz.position.set(4, 10, 6); s.add(luz);
const glow = new THREE.PointLight(0xff3b4a, 1.6, 10); glow.position.set(0, 3, 2); s.add(glow);
const geo = new THREE.SphereGeometry(.055, 8, 6);
const gray = new THREE.InstancedMesh(geo, new THREE.MeshStandardMaterial({color: 0x6b7488, metalness: .2, roughness: .6}), NUNCA);
const red = new THREE.InstancedMesh(geo, new THREE.MeshStandardMaterial({color: 0xffffff, emissive: 0x330609, roughness: .4}), NRED);
s.add(gray, red);
const C_HOT = new THREE.Color(0xff3b4a), C_SIL = new THREE.Color(0x9aa3b5);
const campDe = []; ACC.forEach((n, c) => { for (let i = 0; i < n; i++) campDe.push(c); });
function pintar(n){
  for (let i = 0; i < NRED; i++) red.setColorAt(i, n === 0 && !(D.campanhas[campDe[i]] || {}).pior ? C_SIL : C_HOT);
  red.instanceColor.needsUpdate = true;
}

// Gerador com semente fixa: a mesma cena toda vez.
let semente = 7; const rnd = () => (semente = (semente * 16807) % 2147483647) / 2147483647;
const SP = .17, FORA = [0, -3, 0];
const cols = 50, rows = Math.ceil(D.clientes / cols), vagas = [];
for (let i = 0; i < D.clientes; i++) vagas.push(i);
for (let i = vagas.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [vagas[i], vagas[j]] = [vagas[j], vagas[i]]; }
const naGrade = k => [(k % cols - (cols - 1) / 2) * SP, 0, (Math.floor(k / cols) - (rows - 1) / 2) * SP];
const bloco = (n, cx, w) => { const a = []; for (let i = 0; i < n; i++) { const l = Math.floor(i / (w * w)), k = i % (w * w); a.push([cx + (k % w - (w - 1) / 2) * SP, l * SP + .06, (Math.floor(k / w) - (w - 1) / 2) * SP]); } return a; };
const GAPX = 1.45, colX = c => (c - (NC - 1) / 2) * GAPX;

// Cena 0, por campanha: cada esfera vermelha/prata é um aceite; clientes viram poeira.
const st = [{g: [], r: []}, {g: [], r: []}, {g: [], r: []}];
for (let i = 0; i < NUNCA; i++) { const p = naGrade(vagas[i]); st[0].g.push([p[0] * 1.6, -.05, p[2] * 1.3 - 1]); }
ACC.forEach((n, c) => { for (let i = 0; i < n; i++) { const l = Math.floor(i / 16), k = i % 16; st[0].r.push([colX(c) + (k % 4 - 1.5) * SP, l * SP + .06, (Math.floor(k / 4) - 1.5) * SP]); } });
while (st[0].r.length < NRED) st[0].r.push(FORA);
// Cena 1, quem respondeu: dois blocos, nunca (cinza) e alguma (vermelho).
st[1].g = bloco(NUNCA, -1.9, 16);
st[1].r = bloco(ALGUMA, 1.9, 16); while (st[1].r.length < NRED) st[1].r.push(FORA);
// Cena 2, todos os clientes: grade plana embaralhada.
for (let i = 0; i < NUNCA; i++) st[2].g.push(naGrade(vagas[i]));
for (let i = 0; i < NRED; i++) st[2].r.push(i < ALGUMA ? naGrade(vagas[NUNCA + i]) : FORA);

const cur = {g: st[0].g.map(p => [p[0], p[1] + (reduce ? 0 : 4 + rnd() * 3), p[2]]), r: st[0].r.map(p => [p[0], p[1] + (reduce ? 0 : 4 + rnd() * 3), p[2]])};
let de = {g: cur.g.map(p => p.slice()), r: cur.r.map(p => p.slice())}, t0 = performance.now(), cena = 0;
// Recuo da câmera por cena: quanto a cena precisa de largura para caber na tela.
const DUR = 1400, ESCALA = [.35, 1, 1], LARGURA = [1.12, 1.12, 1.5];
let escDe = 1, esc = 1, recDe = 1, rec = 1;
const recuoAlvo = n => Math.max(1, LARGURA[n] / cam.aspect);

const novo = (cls, html) => { const d = document.createElement("div"); d.className = "lbl " + cls; d.innerHTML = html; host.appendChild(d); return d; };
const grande = (par, hot) => novo("big" + (hot ? " hot" : ""), `${par[0]}<small>${par[1]}</small>`);
const colunas = D.campanhas.map((c, i) => ({
  t: novo(c.pior ? "hot" : "", c.taxa_txt), b: novo("base", c.rotulo),
  x: colX(i), h: Math.ceil(c.aceites / 16) * SP + .2
}));
const fundo = -(rows - 1) / 2 * SP;
const rotulosCena = [[], [
  {el: grande(D.rotulos.nunca, false), p: [-1.9, Math.ceil(NUNCA / 256) * SP + .35, 0]},
  {el: grande(D.rotulos.alguma, true), p: [1.9, Math.ceil(ALGUMA / 256) * SP + .75, 0]}
], [
  {el: grande(D.rotulos.clientes, false), p: [-1.4, .35, fundo]},
  {el: grande(D.rotulos.alguma_total, true), p: [1.4, .35, fundo]}
]];

// Desenho sob demanda: só há quadro durante a transição entre cenas (inclui a
// entrada inicial), no movimento do mouse e no redimensionamento. Parada, a
// cena não redesenha. Fora da tela ou com a aba oculta, tudo pausa.
let auto = !reduce, temporizador = null, pedido = 0, emTransicao = true, visivel = true;
const glowX = n => n === 0 ? colX(D.campanhas.findIndex(c => c.pior)) : n === 1 ? 1.9 : 0;
let glowDe = 0;
const ativo = () => visivel && !document.hidden;
function pedirQuadro(){ if (!pedido && ativo()) pedido = requestAnimationFrame(quadro); }
function agendar(){
  clearTimeout(temporizador); temporizador = null;
  if (auto && ativo()) temporizador = setTimeout(() => ir((cena + 1) % 3, false), 4000);
}
function ir(n, usuario){
  de = {g: cur.g.map(p => p.slice()), r: cur.r.map(p => p.slice())}; escDe = esc;
  recDe = rec; glowDe = glow.position.x; t0 = performance.now(); cena = n; emTransicao = true;
  if (usuario) auto = false;
  botoes.forEach(b => { const on = +b.dataset.s === n; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on); });
  capT.textContent = D.legendas[n][0]; capS.textContent = D.legendas[n][1];
  pintar(n);
  colunas.forEach(c => { c.t.style.opacity = c.b.style.opacity = n === 0 ? 1 : 0; });
  rotulosCena.forEach((lista, i) => lista.forEach(o => { o.el.style.opacity = i === n ? 1 : 0; }));
  agendar(); pedirQuadro();
}
botoes.forEach(b => b.addEventListener("click", () => ir(+b.dataset.s, true)));

// Parallax: a câmera desloca um pouco com o mouse; não gira.
let mx = 0, my = 0;
host.addEventListener("pointermove", e => { const rc = host.getBoundingClientRect(); mx = (e.clientX - rc.left) / rc.width - .5; my = (e.clientY - rc.top) / rc.height - .5; pedirQuadro(); });
const v = new THREE.Vector3(), M = new THREE.Matrix4(), Q = new THREE.Quaternion(), S = new THREE.Vector3(), P = new THREE.Vector3();
function por(x, y, z, el){ v.set(x, y, z).project(cam); el.style.left = ((v.x + 1) / 2 * W()) + "px"; el.style.top = ((1 - v.y) / 2 * H()) + "px"; }
function mover(mesh, arr, src, alvo, escala, k){
  for (let i = 0; i < arr.length; i++) {
    const a = arr[i], f = src[i], b = alvo[i], d = Math.min(1, Math.max(0, k * 1.25 - (i % 97) / 97 * .25));
    a[0] = f[0] + (b[0] - f[0]) * d; a[1] = f[1] + (b[1] - f[1]) * d; a[2] = f[2] + (b[2] - f[2]) * d;
    const sc = a[1] < -1 ? 0 : escala; P.set(a[0], a[1], a[2]); S.set(sc, sc, sc); M.compose(P, Q, S); mesh.setMatrixAt(i, M);
  }
  mesh.instanceMatrix.needsUpdate = true;
}
function quadro(t){
  pedido = 0;
  if (emTransicao) {
    const lin = reduce ? 1 : Math.min(1, Math.max(0, (t - t0) / DUR));  // por tempo, não por quadros
    const k = lin < .5 ? 4 * lin * lin * lin : 1 - Math.pow(-2 * lin + 2, 3) / 2;
    esc = escDe + (ESCALA[cena] - escDe) * k;
    // Matrizes das esferas só mudam durante a transição.
    mover(gray, cur.g, de.g, st[cena].g, esc, k); mover(red, cur.r, de.r, st[cena].r, 1, k);
    // Em telas estreitas a câmera recua para a cena caber na largura.
    rec = recDe + (recuoAlvo(cena) - recDe) * k;
    glow.position.x = glowDe + (glowX(cena) - glowDe) * k;
    emTransicao = lin < 1;
  }
  cam.position.set(mx * 1.2, (4.6 - my * .6) * rec, 9.2 * rec); cam.lookAt(0, .25, 0);
  colunas.forEach(c => { por(c.x, c.h, 0, c.t); por(c.x, 0, 0, c.b); });
  rotulosCena.forEach(lista => lista.forEach(o => por(o.p[0], o.p[1], o.p[2], o.el)));
  r.render(s, cam);
  if (emTransicao) pedirQuadro();
}
function retomar(){ if (ativo()) { pedirQuadro(); if (!temporizador) agendar(); } else { cancelAnimationFrame(pedido); pedido = 0; clearTimeout(temporizador); temporizador = null; } }
new IntersectionObserver(es => { visivel = es[es.length - 1].isIntersecting; retomar(); }).observe(host);
document.addEventListener("visibilitychange", retomar);
rec = recDe = recuoAlvo(0); glow.position.x = glowX(0); ir(0, false);
addEventListener("resize", () => {
  r.setSize(W(), H()); cam.aspect = W() / H(); cam.updateProjectionMatrix();
  rec = recuoAlvo(cena); if (!emTransicao) recDe = rec; pedirQuadro();
});
})();
"""
