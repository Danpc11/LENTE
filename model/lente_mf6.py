"""LENTE PoC: sección vertical 2D costa–interior, densidad variable (MF6 GWF+GWT+BUY).
Pozo de servicios a X_WELL m de la costa, rejilla a Z_SCREEN m bajo el nivel del mar.
Escenarios de caudal tomados de la distribución del REPDA 2026 (m3/d por pozo)."""
import numpy as np, flopy, os, sys, json
from flopy.mf6 import MFSimulation, ModflowTdis, ModflowIms, ModflowGwf, ModflowGwfdis, ModflowGwfnpf, ModflowGwfic, \
    ModflowGwfchd, ModflowGwfrcha, ModflowGwfwel, ModflowGwfsto, ModflowGwfbuy, ModflowGwfoc, ModflowGwt, ModflowGwtdis, \
    ModflowGwtic, ModflowGwtadv, ModflowGwtdsp, ModflowGwtmst, ModflowGwtssm, ModflowGwtcnc, ModflowGwtoc, ModflowGwfgwt

MF6 = os.environ.get('MF6', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin', 'mf6')))
# --- geometría
LX, DX = 3000.0, 25.0;  NCOL = int(LX/DX)
ZTOP, ZBOT, DZ = 1.0, -61.0, 2.0;  NLAY = int((ZTOP-ZBOT)/DZ)
ROWW = 200.0                      # ancho de franja (m): un frente hotelero
botm = [ZTOP - DZ*(k+1) for k in range(NLAY)]
zc = np.array([ZTOP - DZ*(k+0.5) for k in range(NLAY)])
# --- karst (Bauer-Gottwein et al. 2011: K regional 10^2–10^4 m/d)
KH, KV, POR = 1000.0, 100.0, 0.20
RCH = 0.00045                     # m/d  (~165 mm/a de recarga efectiva)
Q_IN = 4.0                        # m2/d flujo regional de agua dulce por metro de costa (Bauer-Gottwein 2011)
NLAY_IN = 10
RHOF, RHOS, CS = 1000.0, 1025.0, 35.0
DRHODC = (RHOS-RHOF)/CS
X_WELL, Z_SCREEN = 1000.0, -5.0
col_w = int((LX - X_WELL)/DX); lay_w = int((ZTOP - Z_SCREEN)/DZ)
T_SPIN, T_PUMP = 18250.0, 1825.0  # 50 a de equilibrio, 5 a de bombeo

def run(Q, name, xw=None):
    global col_w
    if xw: col_w = int((LX - xw)/DX)
    ws = f'mf6_{name}'; os.makedirs(ws, exist_ok=True)
    sim = MFSimulation(sim_name=name, sim_ws=ws, exe_name=MF6)
    ModflowTdis(sim, time_units='DAYS', nper=2, perioddata=[(T_SPIN, 150, 1.05), (T_PUMP, 120, 1.0)])
    ims_f = ModflowIms(sim, print_option='SUMMARY', complexity='COMPLEX', outer_maximum=200, inner_maximum=300,
               outer_dvclose=1e-4, inner_dvclose=1e-5, linear_acceleration='BICGSTAB', relaxation_factor=0.97,
               filename=f'{name}_gwf.ims')
    gwf = ModflowGwf(sim, modelname='gwf', save_flows=True, newtonoptions='NEWTON UNDER_RELAXATION')
    sim.register_ims_package(ims_f, [gwf.name])
    ModflowGwfdis(gwf, nlay=NLAY, nrow=1, ncol=NCOL, delr=DX, delc=ROWW, top=ZTOP, botm=botm)
    ModflowGwfnpf(gwf, icelltype=1, k=KH, k33=KV, save_specific_discharge=True)
    ModflowGwfsto(gwf, iconvert=1, ss=1e-5, sy=POR, transient={0: True})
    ModflowGwfic(gwf, strt=0.5)
    # frontera mar (columna final): carga equivalente de agua dulce de mar en reposo, conc = CS
    chd = [((k, 0, NCOL-1), -(RHOS/RHOF - 1.0)*zc[k] if zc[k] < 0 else 0.0, CS) for k in range(NLAY)]
    # frontera interior (columna 0): nivel freático dulce fijo en capas superiores
    ModflowGwfchd(gwf, stress_period_data={0: chd}, auxiliary=['CONCENTRATION'])
    ModflowGwfrcha(gwf, recharge=RCH, auxiliary=['CONCENTRATION'], aux={0: 0.0})
    inflow = [((k, 0, 0), Q_IN*ROWW/NLAY_IN, 0.0) for k in range(NLAY_IN)]
    ModflowGwfwel(gwf, stress_period_data={0: inflow + [((lay_w, 0, col_w), 0.0, 0.0)],
                                           1: inflow + [((lay_w, 0, col_w), -Q, 0.0)]},
                  auxiliary=['CONCENTRATION'])
    ModflowGwfbuy(gwf, denseref=RHOF, packagedata=[(0, DRHODC, 0.0, 'gwt', 'CONCENTRATION')])
    ModflowGwfoc(gwf, head_filerecord='gwf.hds', budget_filerecord='gwf.cbc',
                 saverecord=[('HEAD', 'LAST'), ('BUDGET', 'LAST')])
    gwt = ModflowGwt(sim, modelname='gwt')
    ims_t = ModflowIms(sim, complexity='COMPLEX', outer_maximum=200, inner_maximum=300, outer_dvclose=1e-5,
               inner_dvclose=1e-6, linear_acceleration='BICGSTAB', filename=f'{name}_gwt.ims')
    sim.register_ims_package(ims_t, [gwt.name])
    ModflowGwtdis(gwt, nlay=NLAY, nrow=1, ncol=NCOL, delr=DX, delc=ROWW, top=ZTOP, botm=botm)
    strt = np.zeros((NLAY, 1, NCOL)); strt[:, :, NCOL-1] = CS   # dominio dulce; el mar entra hasta su equilibrio
    ModflowGwtic(gwt, strt=strt)
    ModflowGwtadv(gwt, scheme='TVD')
    ModflowGwtdsp(gwt, alh=1.0, ath1=0.1, atv=0.01, diffc=1e-4)
    ModflowGwtmst(gwt, porosity=POR)
    ModflowGwtssm(gwt, sources=[('CHD_0', 'AUX', 'CONCENTRATION'), ('RCHA_0', 'AUX', 'CONCENTRATION'),
                                ('WEL_0', 'AUX', 'CONCENTRATION')])
    ModflowGwtoc(gwt, concentration_filerecord='gwt.ucn', saverecord=[('CONCENTRATION', 'ALL')])
    ModflowGwfgwt(sim, exgtype='GWF6-GWT6', exgmnamea='gwf', exgmnameb='gwt')
    sim.write_simulation(silent=True)
    ok, buff = sim.run_simulation(silent=True)
    if not ok:
        print('\n'.join(buff[-30:])); raise SystemExit(f'{name} failed')
    ucn = flopy.utils.HeadFile(os.path.join(ws, 'gwt.ucn'), text='concentration')
    times = ucn.get_times()
    cw = np.array([ucn.get_data(totim=t)[lay_w, 0, col_w] for t in times])
    # profundidad de la isolínea de 50% (17.5 g/L) bajo el pozo y perfil final
    def iface(arr, col):
        c = arr[:, 0, col]
        idx = np.where(c >= 0.5*CS)[0]
        return zc[idx[0]] if len(idx) else ZBOT
    hd = np.array([iface(ucn.get_data(totim=t), col_w) for t in times])
    out = dict(Q=Q, x_well=(LX-col_w*DX), times=times, c_well=cw.tolist(), iface_well=hd.tolist(),
               final=ucn.get_data(totim=times[-1])[:, 0, :].tolist(),
               spin=ucn.get_data(totim=T_SPIN)[:, 0, :].tolist())
    json.dump(out, open(f'res_{name}.json', 'w'))
    print(f'{name}: Q={Q} m3/d  conc en pozo tras 5 a = {cw[-1]:.2f} g/L ; haloclina bajo pozo {hd[0]:.0f} -> {hd[-1]:.0f} m')
    return out

if __name__ == '__main__':
    scen = {'p50': (36, 1000), 'p75': (713, 1000), 'p90': (1876, 1000), 'p95': (3681, 1000), 'p75_x500': (713, 500), 'ref': (0.0, 1000)}
    sel = sys.argv[1:] or list(scen)
    for n in sel: run(scen[n][0], n, scen[n][1])
