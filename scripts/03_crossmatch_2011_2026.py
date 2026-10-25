#!/usr/bin/env python3
"""Cruza los pozos georreferenciados del REPDA 2011 (servicio REST) con los títulos vigentes 2026
por nombre normalizado de titular (tres primeras palabras significativas).
Entrada : data/raw/repda2011_{qroo,yucatan,campeche}.csv ; data/processed/repda2026_titulos.csv
Salida  : data/processed/repda2011_peninsula_con_vol2026.csv
          data/processed/titulares_servicios_costa_qroo_2011_2026.csv (prospectos, franja Cancún–Tulum)
Nota    : el emparejamiento por nombre es fiable para razones sociales únicas (hoteles) y produce
          falsos positivos con titulares genéricos (SEP, municipios); fíltralos antes de usar Yucatán.
"""
import re, unicodedata
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data/raw", ROOT / "data/processed"
EDO = {23: "Quintana Roo", 31: "Yucatán", 4: "Campeche"}
CODE = {23: "QNR", 31: "YUC", 4: "CAM"}
BBOX = dict(lat=(17.5, 21.7), lon=(-92.5, -86.5))

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    s = re.sub(r"\b(S\.?\s?A\.?|S\.?\s?DE\s?R\.?\s?L\.?|C\.?\s?V\.?|S\.?A\.?P\.?I\.?|A\.?\s?C\.?|DE|S\.?C\.?)\b", "", s)
    return re.sub(r"[^A-Z0-9 ]", "", s).strip()

def key(s):
    return " ".join(norm(s).split()[:3])

w = pd.concat([pd.read_csv(RAW / f"repda2011_{n}.csv") for n in ["qroo", "yucatan", "campeche"]], ignore_index=True)
w = w[w.LATDEC.between(*BBOX["lat"]) & w.LONDEC.between(*BBOX["lon"])].copy()
w["estado"] = w.ESTADO.map(EDO)
w["k"] = w.TITULAR.map(key)

t = pd.read_csv(OUT / "repda2026_titulos.csv", dtype={"titulo": str})
t = t[t.n_sub > 0].copy()
t["k"] = t.titular.map(key)
t["ESTADO"] = t.edo.map({v: k for k, v in CODE.items()})
agg = (t.groupby(["ESTADO", "k"])
       .agg(titular_2026=("titular", "first"), pozos_2026=("n_sub", "sum"),
            vol_sub_2026=("vol_sub", "sum"), uso_2026=("uso", "first")).reset_index())
m = w.merge(agg, on=["ESTADO", "k"], how="left")
m.to_csv(OUT / "repda2011_peninsula_con_vol2026.csv", index=False)

serv = m[m.USO_SUB.str.contains("SERV", na=False)]
costa = serv[(serv.ESTADO == 23) & (serv.LONDEC > -87.6) & (serv.LATDEC > 20.0)]
pros = (costa[costa.vol_sub_2026.notna()].groupby("k")
        .agg(titular=("TITULAR", "first"), pozos_2011=("FID", "size"), pozos_2026=("pozos_2026", "first"),
             vol_sub_2026=("vol_sub_2026", "first"), lat=("LATDEC", "median"), lon=("LONDEC", "median"))
        .sort_values("vol_sub_2026", ascending=False))
pros.to_csv(OUT / "titulares_servicios_costa_qroo_2011_2026.csv")

print(f"{len(w)} pozos 2011 con coordenadas; servicios: {len(serv)}; costa QRoo: {len(costa)}, "
      f"con volumen 2026: {costa.vol_sub_2026.notna().sum()} ({len(pros)} titulares, "
      f"{pros.vol_sub_2026.sum()/1e6:.1f} hm3/a)")
