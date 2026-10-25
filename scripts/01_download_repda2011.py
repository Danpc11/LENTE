#!/usr/bin/env python3
"""Descarga los pozos del REPDA (capa 2011) de Quintana Roo, Yucatán y Campeche
desde el servicio REST de CONAGUA.
Uso:  python3 repda2011_peninsula.py
Salida: repda2011_qroo.csv, repda2011_yucatan.csv, repda2011_campeche.csv
        y repda2011_peninsula.csv (los tres juntos).
"""
import sys, time
import requests
import pandas as pd

URL = "https://sigagis.conagua.gob.mx/ArcGIS/rest/services/Aprovechamientos/MapServer/4/query"
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36",
     "Referer": "https://sigagis.conagua.gob.mx/ArcGIS/rest/services/Aprovechamientos/MapServer/4"}
FIELDS = "FID,FOLIOREG,TITULAR,LATDEC,LONDEC,USO_SUB,USO_SUB2,VOL_CONS,VOLEXTANUA,PROFUND,ESTADO,MUPIO,NOM_LOCAL,ACU_SUB,TIP_OBRA"
ESTADOS = {23: "qroo", 31: "yucatan", 4: "campeche"}
PAGE = 500

requests.packages.urllib3.disable_warnings()

def query(where):
    p = {"where": where, "outFields": FIELDS, "returnGeometry": "false", "f": "json"}
    for intento in range(3):
        try:
            r = requests.get(URL, params=p, headers=H, timeout=90, verify=False)
            r.raise_for_status()
            j = r.json()
            if "error" in j:
                raise RuntimeError(j["error"])
            return j.get("features", []), j.get("exceededTransferLimit", False)
        except Exception as e:
            print(f"  intento {intento+1} falló: {e}", file=sys.stderr)
            time.sleep(3)
    raise SystemExit("El servidor no respondió. Prueba más tarde o con otra red.")

todo = []
for estado, nombre in ESTADOS.items():
    print(f"\n== Estado {estado} ({nombre})")
    rows, last_fid = [], -1
    while True:
        feats, more = query(f"ESTADO={estado} AND FID>{last_fid}")
        if not feats:
            break
        rows += [f["attributes"] for f in feats]
        last_fid = max(f["attributes"]["FID"] for f in feats)
        print(f"  {len(rows)} registros… (último FID {last_fid})")
        if not more and len(feats) < PAGE:
            break
    if not rows:
        print(f"  Sin registros para {nombre}.")
        continue
    df = pd.DataFrame(rows)
    df["LATDEC"] = pd.to_numeric(df["LATDEC"], errors="coerce")
    df["LONDEC"] = pd.to_numeric(df["LONDEC"], errors="coerce")
    df.to_csv(f"repda2011_{nombre}.csv", index=False)
    print(f"  {len(df)} pozos guardados en repda2011_{nombre}.csv")
    print(df.USO_SUB.value_counts().head(6).to_string())
    todo.append(df)

if todo:
    pd.concat(todo).to_csv("repda2011_peninsula.csv", index=False)
    print(f"\nTotal península: {sum(len(d) for d in todo)} pozos → repda2011_peninsula.csv")
