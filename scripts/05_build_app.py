#!/usr/bin/env python3
"""Arma la web app autocontenida: inyecta pozos, curvas del modelo y capas geográficas en app/template.html.
Entrada : data/processed/indice_riesgo_pozos_servicios.csv ; model/results/res_*.json ; data/processed/geo/*.geojson
Salida  : app/lente_app.html  (un solo archivo, sin dependencias externas salvo D3 y una fuente)
"""
import json, glob
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T_SPIN = 18250.0

s = pd.read_csv(ROOT / "data/processed/indice_riesgo_pozos_servicios.csv")
wells = [dict(id=int(r.FID), t=str(r.TITULAR).title()[:60], lat=round(r.LATDEC, 4), lon=round(r.LONDEC, 4), e=r.estado,
              d=round(r.d_costa_km, 2), z=round(float(r.screen_m), 1), L=round(r.lente_m, 1), Q=round(float(r.Q_m3d), 1),
              R=round(float(r.R), 3), k=str(r.riesgo), y26=bool(pd.notna(r.vol_sub_2026))) for r in s.itertuples()]

ref = json.load(open(ROOT / "model/results/res_ref.json"))
t = np.array(ref["times"]); ip = np.searchsorted(t, T_SPIN); tp = (t[ip:] - T_SPIN) / 365; cr = np.array(ref["c_well"])[ip:]
curves = {}
for f in sorted(glob.glob(str(ROOT / "model/results/res_p*.json"))):
    r = json.load(open(f))
    if r.get("x_well", 1000) != 1000: continue
    ex = np.clip(np.array(r["c_well"])[ip:] - cr, 0, None)
    ex = np.convolve(ex, np.ones(7) / 7, mode="same"); ex[:3] = ex[3]; ex[-3:] = ex[-4]   # suaviza la oscilación numérica del paso de tiempo
    idx = np.linspace(0, len(tp) - 1, 40).astype(int)
    curves[str(int(r["Q"]))] = [[round(float(tp[i]), 2), round(float(ex[i]), 2)] for i in idx]

geo = {Path(f).stem: json.load(open(f)) for f in glob.glob(str(ROOT / "data/processed/geo/*.geojson"))}
data = json.dumps(dict(wells=wells, curves=curves, geo=geo), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
d3js = (ROOT / "app/d3.v7.9.0.min.js").read_text()
html = (ROOT / "app/template.html").read_text().replace("__D3__", d3js).replace("__DATA__", data).replace("__NWELLS__", f"{len(wells):,}")
(ROOT / "app/lente_app.html").write_text(html)
(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs/index.html").write_text(html)   # GitHub Pages (Settings > Pages > main /docs)
print(f"{len(wells)} pozos, {len(curves)} curvas, capas {list(geo)} -> app/lente_app.html ({len(html)//1024} KB)")
