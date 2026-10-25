#!/usr/bin/env python3
"""Índice de riesgo de ascenso de la haloclina (upconing) para cada pozo de servicios.

Para cada pozo:  distancia a la costa -> espesor de lente (Ghyben-Herzberg con flujo regional + recarga)
                 -> distancia entre rejilla y haloclina -> caudal crítico de ascenso estable (Dagan & Bear)
                 -> R = Q / Q_critico  (bajo < 0.3, medio 0.3-1, alto > 1)
Parámetros físicos idénticos a model/lente_mf6.py.
Entrada : data/processed/repda2011_peninsula_con_vol2026.csv ; costa opcional en data/raw/costa.geojson
Salida  : data/processed/indice_riesgo_pozos_servicios.csv ; figures/fig_riesgo_upconing_peninsula.png
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
K, Q_IN, DELTA, RCH = 1000.0, 4.0, 40.0, 0.00045   # m/d, m2/d, rho_f/(rho_s-rho_f), m/d
LAT0 = np.radians(20.5); KX, KY = 111.32 * np.cos(LAT0), 110.57

m = pd.read_csv(ROOT / "data/processed/repda2011_peninsula_con_vol2026.csv")
s = m[m.USO_SUB.str.contains("SERV", na=False)].copy()

# --- costa: GeoJSON real si existe, si no la aproximación por la nube de pozos
coast_file = ROOT / "data/raw/costa.geojson"
if coast_file.exists():
    gj = json.load(open(coast_file)); pts = []
    def walk(c):
        if isinstance(c[0], (int, float)): pts.append(c)
        else: [walk(x) for x in c]
    [walk(f["geometry"]["coordinates"]) for f in gj["features"]]
    coast = np.array(pts)
else:
    lat_b = np.round(m.LATDEC / 0.02) * 0.02; lon_b = np.round(m.LONDEC / 0.02) * 0.02
    east = m.groupby(lat_b).LONDEC.quantile(.995); north = m.groupby(lon_b).LATDEC.quantile(.995); west = m.groupby(lat_b).LONDEC.quantile(.005)
    coast = np.vstack([np.c_[east.values, east.index], np.c_[north.index, north.values], np.c_[west.values, west.index]])
cx, cy = coast[:, 0] * KX, coast[:, 1] * KY
s["d_costa_km"] = [np.sqrt((lo * KX - cx) ** 2 + (la * KY - cy) ** 2).min() for lo, la in zip(s.LONDEC, s.LATDEC)]

# --- caudal por pozo: 2026 si hay cruce, 2011 si no
s["Q_m3d"] = np.where(s.vol_sub_2026.notna(), s.vol_sub_2026 / s.pozos_2026 / 365, s.VOL_CONS.clip(lower=0) / 365)
s["screen_m"] = s.PROFUND.where(s.PROFUND.between(0.5, 80), 8.0)
x = np.clip(s.d_costa_km * 1000, 50, None)
s["lente_m"] = np.sqrt(2 * (Q_IN + RCH * x) * x * DELTA / K).clip(upper=60)
s["d_bajo_rejilla"] = (s.lente_m - s.screen_m).clip(lower=0.5)
s["Q_crit_m3d"] = (2 * np.pi * K * s.d_bajo_rejilla ** 2 / DELTA) / 3
s["R"] = s.Q_m3d / s.Q_crit_m3d
s["riesgo"] = pd.cut(s.R, [-1, 0.3, 1, np.inf], labels=["bajo", "medio", "alto"])
s.to_csv(ROOT / "data/processed/indice_riesgo_pozos_servicios.csv", index=False)
print(s.groupby(["estado", "riesgo"], observed=True).size().unstack(fill_value=0))

# --- figura
col = {"bajo": "#5C6B73", "medio": "#F4A259", "alto": "#D7263D"}
fig, ax = plt.subplots(1, 2, figsize=(10, 4.6), dpi=220, gridspec_kw={"width_ratios": [1.5, 1]})
o = m[~m.USO_SUB.str.contains("SERV", na=False)]; ax[0].scatter(o.LONDEC, o.LATDEC, s=.8, c="#D9DDD9")
for lv in ["bajo", "medio", "alto"]:
    g = s[s.riesgo == lv]; ax[0].scatter(g.LONDEC, g.LATDEC, s=4, c=col[lv], label=f"{lv} (n={len(g)})", alpha=.9)
ax[0].set_aspect(1 / np.cos(LAT0)); ax[0].legend(fontsize=7, frameon=False, title="Upconing risk, services wells", title_fontsize=7, loc="lower left")
ax[0].set_xlabel("Longitude"); ax[0].set_ylabel("Latitude")
r = np.log10(s.R.clip(1e-4, 1e3)); qr = s.estado == "Quintana Roo"
ax[1].hist(r[qr], bins=40, color="#0E7C86", alpha=.85, label="Quintana Roo"); ax[1].hist(r[~qr], bins=40, color="#B5BDC2", alpha=.85, label="Yucatán + Campeche")
ax[1].axvline(np.log10(0.3), color="k", ls=":", lw=.8); ax[1].axvline(0, color="k", ls="--", lw=.8)
ax[1].set_xlabel("log$_{10}$ (Q / Q$_{critical}$)"); ax[1].set_ylabel("Wells"); ax[1].legend(fontsize=7, frameon=False)
for a, l in zip(ax, "AB"): a.set_title(l, loc="left", fontweight="bold"); a.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); (ROOT / "figures").mkdir(exist_ok=True); plt.savefig(ROOT / "figures/fig_riesgo_upconing_peninsula.png")
