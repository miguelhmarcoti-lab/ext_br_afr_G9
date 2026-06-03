import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# ── HELPERS ───────────────────────────────────────────────────────────────────

def fmt(v):
    """Formata valor USD em string legível (ex: 'US$ 15.5B')."""
    if abs(v) >= 1e9:
        return f"US$ {v / 1e9:.1f}B"
    if abs(v) >= 1e6:
        return f"US$ {v / 1e6:.0f}M"
    return f"US$ {v:,.0f}"


def to_b(values):
    """Escala lista de valores USD → bilhões (float)."""
    return [round(v / 1e9, 3) for v in values]


# ── CARREGA E PRÉ-PROCESSA UMA VEZ ──────────────────────────────────────────
df = pd.read_excel("dados.xlsx", sheet_name="Resultado")

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

china_serie = [china[exp_cols[a]].sum()  + china[imp_cols[a]].sum()  for a in ANOS]
eua_serie   = [eua[exp_cols[a]].sum()    + eua[imp_cols[a]].sum()    for a in ANOS]

exp_hist = [exp_cols[a] for a in ANOS]
imp_hist = [imp_cols[a] for a in ANOS]

af_grp = africa.groupby("Países")[exp_hist + imp_hist].sum()
af_grp["total_exp"] = af_grp[exp_hist].sum(axis=1)
af_grp["total_imp"] = af_grp[imp_hist].sum(axis=1)
af_grp["corrente"]  = af_grp["total_exp"] + af_grp["total_imp"]
top15 = af_grp.nlargest(15, "corrente").reset_index()

anos_rec = [a for a in ANOS if a >= 2020]
af_rec = africa.groupby("Países")[
    [exp_cols[a] for a in anos_rec] + [imp_cols[a] for a in anos_rec]
].sum()
af_rec["exp"]      = af_rec[[exp_cols[a] for a in anos_rec]].sum(axis=1)
af_rec["imp"]      = af_rec[[imp_cols[a] for a in anos_rec]].sum(axis=1)
af_rec["corrente"] = af_rec["exp"] + af_rec["imp"]
top12 = af_rec.nlargest(12, "corrente").reset_index()

EXCLUIR_UF = {"Não Declarada", "Reexportação", "Mercadoria Nacionalizada",
              "Consumo de Bordo", "Exterior", "Zona Não Declarada"}
uf_grp = africa[~africa["UF do Produto"].isin(EXCLUIR_UF)].groupby("UF do Produto")[exp_hist + imp_hist].sum()
uf_grp["exp"]      = uf_grp[exp_hist].sum(axis=1)
uf_grp["imp"]      = uf_grp[imp_hist].sum(axis=1)
uf_grp["corrente"] = uf_grp["exp"] + uf_grp["imp"]
top_uf = uf_grp.nlargest(15, "corrente").reset_index()

# ── KPIs ─────────────────────────────────────────────────────────────────────
kpi_exp_2025      = int(serie[serie.ano == 2025]["exp"].values[0])
kpi_imp_2025      = int(serie[serie.ano == 2025]["imp"].values[0])
kpi_saldo_2025    = kpi_exp_2025 - kpi_imp_2025
kpi_corrente_2025 = kpi_exp_2025 + kpi_imp_2025

exp_2024 = int(serie[serie.ano == 2024]["exp"].values[0])
var_exp  = round((kpi_exp_2025 - exp_2024) / exp_2024 * 100, 1)

# ── ROTAS ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    kpis = {
        "exp_2025":       kpi_exp_2025,
        "imp_2025":       kpi_imp_2025,
        "saldo_2025":     kpi_saldo_2025,
        "corrente_2025":  kpi_corrente_2025,
        "var_exp":        var_exp,
        # Valores pré-formatados para uso direto no template
        "exp_2025_fmt":      fmt(kpi_exp_2025),
        "imp_2025_fmt":      fmt(kpi_imp_2025),
        "saldo_2025_fmt":    fmt(kpi_saldo_2025),
        "corrente_2025_fmt": fmt(kpi_corrente_2025),
    }
    return render_template("index.html", kpis=kpis)


# NOTA PARA O TEMPLATE (index.html):
# Os endpoints abaixo retornam os valores em BILHÕES (campo *_b) além dos
# valores brutos em USD. Para corrigir o eixo nos gráficos Plotly.js do
# dashboard (que atualmente exibe "G" em vez de "B"), use os campos *_b e
# configure o eixo assim:
#
#   yaxis: {
#     tickformat: "$,",   // separador de milhar, sem notação SI
#     ticksuffix: "B",    // sufixo explícito
#   }
#
# Usando os campos *_b (já divididos por 1e9) o Plotly não ativa o prefixo
# "G" e o eixo exibe "$15B", "$10B" etc. corretamente.

@app.route("/api/fluxo-anual")
def api_fluxo_anual():
    return jsonify({
        "anos":        ANOS,
        # Valores brutos (USD) — mantidos para compatibilidade
        "exportacoes": [int(v) for v in serie["exp"]],
        "importacoes": [int(v) for v in serie["imp"]],
        "saldo":       [int(v) for v in serie["saldo"]],
        "corrente":    [int(v) for v in serie["corrente"]],
        # Valores em bilhões — use estes nos eixos dos gráficos
        "exportacoes_b": to_b(serie["exp"]),
        "importacoes_b": to_b(serie["imp"]),
        "saldo_b":       to_b(serie["saldo"]),
        "corrente_b":    to_b(serie["corrente"]),
        # Labels formatados para hover/tooltip
        "exportacoes_fmt": [fmt(v) for v in serie["exp"]],
        "importacoes_fmt": [fmt(v) for v in serie["imp"]],
        "saldo_fmt":       [fmt(v) for v in serie["saldo"]],
        "corrente_fmt":    [fmt(v) for v in serie["corrente"]],
    })


@app.route("/api/parceiros")
def api_parceiros():
    return jsonify({
        "paises":       top15["Países"].tolist(),
        "exportacao":   [int(v) for v in top15["total_exp"]],
        "importacao":   [int(v) for v in top15["total_imp"]],
        # Em bilhões — use nos eixos
        "exportacao_b": to_b(top15["total_exp"]),
        "importacao_b": to_b(top15["total_imp"]),
        "exportacao_fmt": [fmt(v) for v in top15["total_exp"]],
        "importacao_fmt": [fmt(v) for v in top15["total_imp"]],
    })


@app.route("/api/potencias")
def api_potencias():
    return jsonify({
        "anos":    ANOS,
        "africa":  [int(v) for v in serie["corrente"]],
        "china":   [int(v) for v in china_serie],
        "eua":     [int(v) for v in eua_serie],
        # Em bilhões
        "africa_b": to_b(serie["corrente"]),
        "china_b":  to_b(china_serie),
        "eua_b":    to_b(eua_serie),
        "africa_fmt": [fmt(v) for v in serie["corrente"]],
        "china_fmt":  [fmt(v) for v in china_serie],
        "eua_fmt":    [fmt(v) for v in eua_serie],
    })


@app.route("/api/fluxo-recente")
def api_fluxo_recente():
    return jsonify({
        "paises":     top12["Países"].tolist(),
        "exportacao": [int(v) for v in top12["exp"]],
        "importacao": [int(v) for v in top12["imp"]],
        "corrente":   [int(v) for v in top12["corrente"]],
        # Em bilhões
        "exportacao_b": to_b(top12["exp"]),
        "importacao_b": to_b(top12["imp"]),
        "corrente_b":   to_b(top12["corrente"]),
        "exportacao_fmt": [fmt(v) for v in top12["exp"]],
        "importacao_fmt": [fmt(v) for v in top12["imp"]],
        "corrente_fmt":   [fmt(v) for v in top12["corrente"]],
    })


@app.route("/api/uf")
def api_uf():
    return jsonify({
        "ufs":        top_uf["UF do Produto"].tolist(),
        "exportacao": [int(v) for v in top_uf["exp"]],
        "importacao": [int(v) for v in top_uf["imp"]],
        "corrente":   [int(v) for v in top_uf["corrente"]],
        # Em bilhões
        "exportacao_b": to_b(top_uf["exp"]),
        "importacao_b": to_b(top_uf["imp"]),
        "corrente_b":   to_b(top_uf["corrente"]),
        "exportacao_fmt": [fmt(v) for v in top_uf["exp"]],
        "importacao_fmt": [fmt(v) for v in top_uf["imp"]],
        "corrente_fmt":   [fmt(v) for v in top_uf["corrente"]],
    })


if __name__ == "__main__":
    app.run(debug=True)