#!/usr/bin/env python3
"""Figura del modelo 2D: campo de salinidad sin bombeo (A), con el pozo P90 a 5 años (B) y curvas por caudal (C).
Entrada: model/results/res_*.json. Salida: figures/fig_mf6_upconing.png"""
import json
from pathlib import Path
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]; R = ROOT / "model/results"; T_SPIN = 18250
zc = 1 - 2 * (np.arange(31) + .5); xc = np.arange(120) * 25 + 12.5
ref = json.load(open(R / "res_ref.json")); t = np.array(ref["times"]); ip = np.searchsorted(t, T_SPIN); tp = (t[ip:] - T_SPIN) / 365; cr = np.array(ref["c_well"])[ip:]
fig, ax = plt.subplots(1, 3, figsize=(12, 3.4), dpi=220, gridspec_kw={"width_ratios": [1.3, 1.3, 1]})
for a, (n, title) in zip(ax[:2], [("ref", "No pumping (reference)"), ("p90", "Pumping 1,876 m$^3$ d$^{-1}$ (P90 well), 5 yr")]):
    F = np.array(json.load(open(R / f"res_{n}.json"))["final"])
    im = a.pcolormesh(3000 - xc, zc, F, cmap="viridis", vmin=0, vmax=35, shading="nearest"); a.contour(3000 - xc, zc, F, levels=[1, 17.5], colors="w", linewidths=.7)
    a.plot(1000, -5, "v", color="#D7263D", ms=7); a.set_xlim(3000, 0); a.set_xlabel("Distance from coast (m)"); a.set_title(title, fontsize=8)
ax[0].set_ylabel("Elevation (m, sea level = 0)"); cb = plt.colorbar(im, ax=ax[1], pad=.02); cb.set_label("Salinity (g L$^{-1}$)", fontsize=7)
cols = {"p50": "#9ecae1", "p75": "#4292c6", "p90": "#08519c", "p95": "#D7263D"}
for n, lab in [("p50", "P50: 36 m$^3$ d$^{-1}$"), ("p75", "P75: 713"), ("p90", "P90: 1,876"), ("p95", "P95: 3,681")]:
    cp = np.array(json.load(open(R / f"res_{n}.json"))["c_well"])[ip:]; ax[2].plot(tp, cp - cr, color=cols[n], label=lab, lw=1.4)
ax[2].axhline(1, color="k", ls="--", lw=.7); ax[2].text(.1, 1.15, "brackish threshold (1 g L$^{-1}$)", fontsize=6.5)
ax[2].set_xlabel("Years of pumping"); ax[2].set_ylabel("Salinity at well above reference (g L$^{-1}$)"); ax[2].legend(fontsize=6.5, frameon=False, title="Pumping rate", title_fontsize=6.5)
for a, l in zip(ax, "ABC"): a.set_title(l, loc="left", fontweight="bold"); a.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(ROOT / "figures/fig_mf6_upconing.png")
