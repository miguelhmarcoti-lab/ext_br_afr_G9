"""
Exporta todos os gráficos do dashboard como PNG.
Instale kaleido antes de rodar:  pip install kaleido

Correções aplicadas:
  - Eixos agora exibem "B" (bilhões) em vez de "G" (giga/SI)
  - Margens aumentadas para evitar sobreposição de legenda e anotação
  - Legenda centralizada e ancorada corretamente
  - Alturas ajustadas para melhor legibilidade
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────
PASTA_SAIDA = "graficos_exportados"
os.makedirs(PASTA_SAIDA, exist_ok=True)

LARGURA  = 1400
ALTURA_P = 560    # gráficos de linha/barra vertical
ALTURA_H = 720    # gráficos horizontais (aumentado para legenda + anotação)
ESCALA   = 2      # resolução retina

FONTE   = "Fonte: SECEX/MDIC — ComexStat | Valor US$ FOB"
COR_EXP = "#1a6b3c"
COR_IMP = "#b22222"
COR_ORO = "#b87d2b"

# ── HELPERS ───────────────────────────────────────────────────────────────────

def to_b(values):
    """Escala valores USD → bilhões para uso no eixo do gráfico."""
    return [v / 1e9 for v in values]


def fmt(v):
    """Formata valor USD para label de hover (mantém precisão original)."""
    if abs(v) >= 1e9:
        return f"US$ {v / 1e9:.1f}B"
    if abs(v) >= 1e6:
        return f"US$ {v / 1e6:.0f}M"
    return f"US$ {v:,.0f}"


def salvar(fig, nome, altura=None):
    """Salva figura como PNG no diretório de saída."""
    caminho = os.path.join(PASTA_SAIDA, nome)
    kwargs = dict(width=LARGURA, scale=ESCALA)
    if altura:
        kwargs["height"] = altura
    fig.write_image(caminho, **kwargs)
    print(f"✅ {nome}")


# ── CONFIGURAÇÕES DE EIXO EM BILHÕES ─────────────────────────────────────────
# tickformat=","  → separador de milhar, sem notação SI (não usa G)
# tickprefix="$"  → símbolo de moeda explícito
# ticksuffix="B"  → sufixo "B" = bilhões

YAXIS_B = dict(
    tickformat=",",
    tickprefix="$",
    ticksuffix="B",
    gridcolor="#ece8e0",
)

XAXIS_B = dict(
    tickformat=",",
    tickprefix="$",
    ticksuffix="B",
    gridcolor="#ece8e0",
)


# ── LAYOUTS BASE ──────────────────────────────────────────────────────────────

def layout_v(titulo):
    """Layout para gráficos verticais (barras agrupadas, linhas)."""
    return dict(
        paper_bgcolor="white",
        plot_bgcolor="#fafaf7",
        font=dict(family="Arial, Helvetica, sans-serif", color="#1a1612", size=12),
        margin=dict(t=90, r=40, b=150, l=80),
        title=dict(text=titulo, font_size=15, pad=dict(b=8)),
        # Legenda horizontal centralizada, abaixo do gráfico
        legend=dict(
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.16, yanchor="top",
            bgcolor="rgba(255,255,255,0)",
        ),
        # Anotação de fonte abaixo da legenda (y mais negativo = mais para baixo)
        annotations=[dict(
            x=0.5, y=-0.30,
            xref="paper", yref="paper",
            text=FONTE, showarrow=False,
            xanchor="center",
            font=dict(size=10, color="#888888"),
        )],
    )


def layout_h(titulo, left_margin=165):
    """Layout para gráficos horizontais (barras de países/estados)."""
    return dict(
        paper_bgcolor="white",
        plot_bgcolor="#fafaf7",
        font=dict(family="Arial, Helvetica, sans-serif", color="#1a1612", size=12),
        margin=dict(t=90, r=40, b=160, l=left_margin),
        title=dict(text=titulo, font_size=15, pad=dict(b=8)),
        legend=dict(
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.13, yanchor="top",
            bgcolor="rgba(255,255,255,0)",
        ),
        annotations=[dict(
            x=0.5, y=-0.24,
            xref="paper", yref="paper",
            text=FONTE, showarrow=False,
            xanchor="center",
            font=dict(size=10, color="#888888"),
        )],
    )


# ── CARREGA DADOS ─────────────────────────────────────────────────────────────
print("Carregando dados...\n")
df     = pd.read_excel("dados.xlsx", sheet_name="Resultado")
africa = df[df["Bloco Econômico"].str.contains("frica", case=False, na=False)].copy()
china  = df[df["Países"] == "China"].copy()
eua    = df[df["Países"] == "Estados Unidos"].copy()

exp_cols = {int(c.split(" - ")[1]): c for c in df.columns if "Exportação" in c and "Valor US$" in c}
imp_cols = {int(c.split(" - ")[1]): c for c in df.columns if "Importação" in c and "Valor US$" in c}
ANOS = sorted(a for a in exp_cols if a <= 2025)

serie = pd.DataFrame({
    "ano": ANOS,
    "exp": [africa[exp_cols[a]].sum() for a in ANOS],
    "imp": [africa[imp_cols[a]].sum() for a in ANOS],
})
serie["saldo"]    = serie["exp"] - serie["imp"]
serie["corrente"] = serie["exp"] + serie["imp"]

exp_hist = [exp_cols[a] for a in ANOS]
imp_hist = [imp_cols[a] for a in ANOS]

af_grp = africa.groupby("Países")[exp_hist + imp_hist].sum()
af_grp["total_exp"] = af_grp[exp_hist].sum(axis=1)
af_grp["total_imp"] = af_grp[imp_hist].sum(axis=1)
af_grp["corrente"]  = af_grp["total_exp"] + af_grp["total_imp"]
top15 = af_grp.nlargest(15, "corrente").reset_index()

EXCLUIR_UF = {"Não Declarada", "Reexportação", "Mercadoria Nacionalizada",
              "Consumo de Bordo", "Exterior", "Zona Não Declarada"}
uf_grp = africa[~africa["UF do Produto"].isin(EXCLUIR_UF)].groupby("UF do Produto")[exp_hist + imp_hist].sum()
uf_grp["exp"]      = uf_grp[exp_hist].sum(axis=1)
uf_grp["imp"]      = uf_grp[imp_hist].sum(axis=1)
uf_grp["corrente"] = uf_grp["exp"] + uf_grp["imp"]
top_uf = uf_grp.nlargest(15, "corrente").reset_index()

china_serie = [china[exp_cols[a]].sum() + china[imp_cols[a]].sum() for a in ANOS]
eua_serie   = [eua[exp_cols[a]].sum()   + eua[imp_cols[a]].sum()   for a in ANOS]


# ── GRÁFICO 1: Exportações & Importações ─────────────────────────────────────
fig = go.Figure()
fig.add_bar(
    x=ANOS, y=to_b(serie["exp"]), name="Exportações",
    marker_color=COR_EXP, opacity=0.88,
    customdata=[fmt(v) for v in serie["exp"]],
    hovertemplate="<b>%{x}</b><br>Exportações: %{customdata}<extra></extra>",
)
fig.add_bar(
    x=ANOS, y=to_b(serie["imp"]), name="Importações",
    marker_color=COR_IMP, opacity=0.88,
    customdata=[fmt(v) for v in serie["imp"]],
    hovertemplate="<b>%{x}</b><br>Importações: %{customdata}<extra></extra>",
)
fig.update_layout(
    **layout_v("Exportações & Importações do Brasil com a África (1997–2025)"),
    barmode="group", bargap=0.35,
    xaxis=dict(showgrid=False, tickangle=-45),
    yaxis=dict(**YAXIS_B),
)
salvar(fig, "01_exportacoes_importacoes.png", ALTURA_P)


# ── GRÁFICO 2: Saldo comercial ───────────────────────────────────────────────
cores_saldo = [COR_EXP if v >= 0 else COR_IMP for v in serie["saldo"]]
fig = go.Figure()
fig.add_bar(
    x=ANOS, y=to_b(serie["saldo"]), name="Saldo",
    marker_color=cores_saldo, opacity=0.88,
    customdata=[fmt(v) for v in serie["saldo"]],
    hovertemplate="<b>%{x}</b><br>Saldo: %{customdata}<extra></extra>",
)
lv = layout_v("Saldo Comercial Brasil × África (1997–2025)")
lv["showlegend"] = False
fig.update_layout(
    **lv,
    bargap=0.35,
    xaxis=dict(showgrid=False, tickangle=-45),
    yaxis=dict(
        **YAXIS_B,
        zeroline=True,
        zerolinecolor="#1a1612",
        zerolinewidth=1.5,
    ),
)
salvar(fig, "02_saldo_comercial.png", ALTURA_P)


# ── GRÁFICO 3: Corrente — Brasil×África vs. China vs. EUA ────────────────────
fig = go.Figure()
fig.add_scatter(
    x=ANOS, y=to_b(serie["corrente"]), name="Brasil × África",
    mode="lines+markers",
    line=dict(color=COR_EXP, width=2.5),
    marker=dict(size=5),
    fill="tozeroy", fillcolor="rgba(26,107,60,0.08)",
    customdata=[fmt(v) for v in serie["corrente"]],
    hovertemplate="<b>%{x}</b> · Brasil×África<br>%{customdata}<extra></extra>",
)
fig.add_scatter(
    x=ANOS, y=to_b(china_serie), name="China",
    mode="lines",
    line=dict(color=COR_IMP, width=2, dash="dot"),
    customdata=[fmt(v) for v in china_serie],
    hovertemplate="<b>%{x}</b> · China<br>%{customdata}<extra></extra>",
)
fig.add_scatter(
    x=ANOS, y=to_b(eua_serie), name="EUA",
    mode="lines",
    line=dict(color="#1a4e6b", width=2, dash="dash"),
    customdata=[fmt(v) for v in eua_serie],
    hovertemplate="<b>%{x}</b> · EUA<br>%{customdata}<extra></extra>",
)
fig.update_layout(
    **layout_v("Corrente de Comércio — Brasil×África vs. China e EUA (1997–2025)"),
    xaxis=dict(showgrid=False, tickangle=-45),
    yaxis=dict(**YAXIS_B),
)
salvar(fig, "03_corrente_brasil_africa_china_eua.png", ALTURA_P)


# ── GRÁFICO 4: Maiores parceiros (acumulado histórico) ───────────────────────
p15 = top15.sort_values("corrente")
fig = go.Figure()
fig.add_bar(
    y=p15["Países"], x=to_b(p15["total_exp"]), name="Exportação",
    orientation="h", marker_color=COR_EXP, opacity=0.88,
    customdata=[fmt(v) for v in p15["total_exp"]],
    hovertemplate="<b>%{y}</b><br>Exportação: %{customdata}<extra></extra>",
)
fig.add_bar(
    y=p15["Países"], x=to_b(p15["total_imp"]), name="Importação",
    orientation="h", marker_color=COR_IMP, opacity=0.88,
    customdata=[fmt(v) for v in p15["total_imp"]],
    hovertemplate="<b>%{y}</b><br>Importação: %{customdata}<extra></extra>",
)
fig.update_layout(
    **layout_h("Maiores Parceiros Africanos do Brasil — Acumulado 1997–2025 (Top 15)"),
    barmode="group", bargap=0.25,
    xaxis=dict(**XAXIS_B),
    yaxis=dict(showgrid=False),
)
salvar(fig, "04_maiores_parceiros_africa.png", ALTURA_H)


# ── GRÁFICO 5: Estados brasileiros (UF) ──────────────────────────────────────
uf_ord = top_uf.sort_values("corrente")
fig = go.Figure()
fig.add_bar(
    y=uf_ord["UF do Produto"], x=to_b(uf_ord["exp"]), name="Exportação",
    orientation="h", marker_color=COR_EXP, opacity=0.88,
    customdata=[fmt(v) for v in uf_ord["exp"]],
    hovertemplate="<b>%{y}</b><br>Exportação: %{customdata}<extra></extra>",
)
fig.add_bar(
    y=uf_ord["UF do Produto"], x=to_b(uf_ord["imp"]), name="Importação",
    orientation="h", marker_color=COR_IMP, opacity=0.88,
    customdata=[fmt(v) for v in uf_ord["imp"]],
    hovertemplate="<b>%{y}</b><br>Importação: %{customdata}<extra></extra>",
)
fig.update_layout(
    **layout_h(
        "Estados Brasileiros com Maior Relação Comercial com a África — Acumulado 1997–2025",
        left_margin=175,  # margem extra para "Mato Grosso do Sul"
    ),
    barmode="group", bargap=0.3,
    xaxis=dict(**XAXIS_B),
    yaxis=dict(showgrid=False),
)
salvar(fig, "05_estados_brasileiros_africa.png", ALTURA_H)


print(f"\n✅ 5 gráficos salvos na pasta '{PASTA_SAIDA}/'")