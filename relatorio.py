"""Gera relatorio.html: o mesmo painel do app em um arquivo só.

Execução:
    uv run python relatorio.py

Spec: specs/dashboard.md, item 13. Mesmo conteúdo, ordem e design do app,
com a mesma cena 3D, cartões e gráficos, montados pelas mesmas funções de
painel.py. Largura máxima de 1080 px. Three.js e Plotly (pacote reduzido
plotly-basic) pelo CDN, uma vez cada. Cada gráfico com div_id fixo. Rodapé
com a data e hora de geração. Imprime o caminho e o tamanho em KB.
"""

import sys
from datetime import datetime
from html import escape

import painel
from pipeline.db import RAIZ

BANCO = RAIZ / "ifood.duckdb"
SAIDA = RAIZ / "relatorio.html"


def gerar() -> str:
    p = painel.montar(painel.ler_marts(BANCO))
    gerado = datetime.now().strftime("%d/%m/%Y %H:%M")

    partes = [
        painel.html_cabecalho(p),
        f'<script src="{painel.THREE_JS}"></script>',
        painel.html_topo(p),
    ]
    # Plotly reduzido (plotly-basic) uma vez só, antes do primeiro gráfico.
    partes.append(f'<script charset="utf-8" src="{painel.PLOTLY_BASICO}"></script>')
    for secao in p.secoes:
        blocos = [painel.html_secao_inicio(secao)]
        for g in secao.graficos:
            grafico = g.figura.to_html(
                full_html=False,
                include_plotlyjs=False,
                div_id=g.div_id,
                config=painel.CONFIG_PLOTLY,
            )
            blocos.append(
                '<div class="grafico-bloco">'
                f"{painel.html_cabecalho_grafico(g)}{grafico}{painel.html_nota(g)}"
                "</div>"
            )
        partes.append(f'<section class="sec">{"".join(blocos)}</section>')
    partes.append(painel.html_rodape([*p.rodape, f"Dados gerados em {gerado}"]))

    corpo = "\n".join(partes)
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(p.titulo)}</title>
<style>
{painel.css()}
html, body {{ margin: 0; }}
body {{ background: linear-gradient(180deg, {painel.FUNDO_1}, {painel.FUNDO_2}) fixed;
  background-color: {painel.FUNDO_1}; color: {painel.TEXTO}; }}
.wrap {{ max-width: 1080px; margin: 0 auto; padding: 28px 16px 48px;
  box-sizing: border-box; display: flex; flex-direction: column; gap: 28px; }}
</style>
</head>
<body>
<div class="wrap">
{corpo}
</div>
</body>
</html>
"""


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if not BANCO.exists():
        print(
            f"Banco não encontrado: {BANCO}. Rode antes ingestão, transformação "
            "e marts (ou abra o app, que prepara os dados).",
            file=sys.stderr,
        )
        sys.exit(1)
    SAIDA.write_text(gerar(), encoding="utf-8")
    tamanho = painel.numero(SAIDA.stat().st_size / 1024, 1)
    print(f"{SAIDA} ({tamanho} KB)")


if __name__ == "__main__":
    main()
