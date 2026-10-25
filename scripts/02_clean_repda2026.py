#!/usr/bin/env python3
"""Limpia y consolida las exportaciones del REPDA (consulta en línea, corte sep-2026).
Entrada : data/raw/ReporteRepda*.csv   (uno o varios; se descartan los vacíos y duplicados)
Salida  : data/processed/repda2026_titulos.csv        (todos los títulos, todos los estados)
          data/processed/repda2026_qroo_titulos.csv   (Quintana Roo, con bandera de titular hotelero)
          data/processed/repda2026_resumen_uso.csv    (pozos y volumen por estado y uso)
"""
import glob, re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data/raw", ROOT / "data/processed"
COLS = ["titular", "titulo", "uso", "autoridad", "fecha", "vol_total", "n_sup", "vol_sup",
        "n_sub", "vol_sub", "n_desc", "vol_desc", "n_zf", "sup_m2"]
HOTEL_PAT = (r"HOTEL|RESORT|TURIS|INMOBILIAR|DESARROLLO|PLAYA|CLUB|VILLAS|HOSPITALITY|SUITES|MARINA|GOLF|"
             r"CONDOMIN|VACATION|BEACH|PALACE|RIU|IBEROSTAR|BAHIA|XCARET|XPLOR|SANDOS|BARCELO|HARD ROCK|"
             r"PARADISUS|MELIA|HILTON|MARRIOTT|HYATT|SECRETS|DREAMS|EXCELLENCE|OCCIDENTAL|CATALONIA|ROYAL|"
             r"VIDANTA|MAYAKOBA|FAIRMONT|ROSEWOOD|HOTELERA|HOTELES|OPERADORA|PROMOTORA")

def load(path):
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    if len(df) == 0 or df.shape[1] != len(COLS):
        return None
    df.columns = COLS
    for c in COLS:
        df[c] = df[c].astype(str).str.strip()
    for c in ["vol_total", "vol_sup", "vol_sub", "vol_desc", "sup_m2"]:
        df[c] = pd.to_numeric(df[c].str.replace(" ", "").str.replace(",", ""), errors="coerce")
    for c in ["n_sup", "n_sub", "n_desc", "n_zf"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    df["edo"] = df.titulo.str.extract(r"^\d{2}([A-Z]{3})")
    df["archivo"] = Path(path).name
    return df

frames = [f for f in (load(p) for p in sorted(glob.glob(str(RAW / "ReporteRepda*.csv")))) if f is not None]
df = pd.concat(frames, ignore_index=True).drop_duplicates("titulo")
OUT.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT / "repda2026_titulos.csv", index=False)

q = df[df.edo == "QNR"].copy()
q["hotelero"] = q.titular.str.upper().str.contains(HOTEL_PAT, regex=True)
q.to_csv(OUT / "repda2026_qroo_titulos.csv", index=False)

res = (df[df.n_sub > 0].groupby(["edo", "uso"])
       .agg(titulos=("titulo", "size"), pozos=("n_sub", "sum"), vol_sub_hm3=("vol_sub", lambda s: s.sum() / 1e6))
       .reset_index().sort_values(["edo", "vol_sub_hm3"], ascending=[True, False]))
res.to_csv(OUT / "repda2026_resumen_uso.csv", index=False)

print(f"{len(df)} títulos ({df.edo.value_counts().to_dict()})")
print(res[res.edo == "QNR"].head(8).round(1).to_string(index=False))
