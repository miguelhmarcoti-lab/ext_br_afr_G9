import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify

app = Flask(__name__)

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

china_serie  = [china[exp_cols[a]].sum()  + china[imp_cols[a]].sum()  for a in ANOS]
eua_serie    = [eua[exp_cols[a]].sum()    + eua[imp_cols[a]].sum()    for a in ANOS]

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

# UF do Produto — acumulado histórico
EXCLUIR_UF = {"Não Declarada", "Reexportação", "Mercadoria Nacionalizada",
              "Consumo de Bordo", "Exterior", "Zona Não Declarada"}
uf_grp = africa[~africa["UF do Produto"].isin(EXCLUIR_UF)].groupby("UF do Produto")[exp_hist + imp_hist].sum()
uf_grp["exp"]      = uf_grp[exp_hist].sum(axis=1)
uf_grp["imp"]      = uf_grp[imp_hist].sum(axis=1)
uf_grp["corrente"] = uf_grp["exp"] + uf_grp["imp"]
top_uf = uf_grp.nlargest(15, "corrente").reset_index()

# ── KPIs ─────────────────────────────────────────────────────────────────────
kpi_exp_2025   = int(serie[serie.ano == 2025]["exp"].values[0])
kpi_imp_2025   = int(serie[serie.ano == 2025]["imp"].values[0])
kpi_saldo_2025 = kpi_exp_2025 - kpi_imp_2025
kpi_corrente_2025 = kpi_exp_2025 + kpi_imp_2025

exp_2024 = int(serie[serie.ano == 2024]["exp"].values[0])
var_exp = round((kpi_exp_2025 - exp_2024) / exp_2024 * 100, 1)

# ── ROTAS ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    kpis = {
        "exp_2025":   kpi_exp_2025,
        "imp_2025":   kpi_imp_2025,
        "saldo_2025": kpi_saldo_2025,
        "corrente_2025": kpi_corrente_2025,
        "var_exp": var_exp,
    }
    return render_template("index.html", kpis=kpis)


@app.route("/api/fluxo-anual")
def api_fluxo_anual():
    return jsonify({
        "anos": ANOS,
        "exportacoes": [int(v) for v in serie["exp"]],
        "importacoes": [int(v) for v in serie["imp"]],
        "saldo":       [int(v) for v in serie["saldo"]],
        "corrente":    [int(v) for v in serie["corrente"]],
    })


@app.route("/api/parceiros")
def api_parceiros():
    return jsonify({
        "paises":    top15["Países"].tolist(),
        "exportacao": [int(v) for v in top15["total_exp"]],
        "importacao": [int(v) for v in top15["total_imp"]],
    })


@app.route("/api/potencias")
def api_potencias():
    return jsonify({
        "anos":   ANOS,
        "africa": [int(v) for v in serie["corrente"]],
        "china":  [int(v) for v in china_serie],
        "eua":    [int(v) for v in eua_serie],
    })


@app.route("/api/fluxo-recente")
def api_fluxo_recente():
    return jsonify({
        "paises":     top12["Países"].tolist(),
        "exportacao": [int(v) for v in top12["exp"]],
        "importacao": [int(v) for v in top12["imp"]],
        "corrente":   [int(v) for v in top12["corrente"]],
    })


@app.route("/api/uf")
def api_uf():
    return jsonify({
        "ufs":        top_uf["UF do Produto"].tolist(),
        "exportacao": [int(v) for v in top_uf["exp"]],
        "importacao": [int(v) for v in top_uf["imp"]],
        "corrente":   [int(v) for v in top_uf["corrente"]],
    })

if __name__ == "__main__":
    app.run(debug=True)
