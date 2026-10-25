# Metodología

## 1. Padrón de pozos
- **REPDA 2026** (consulta en línea, corte 30-sep-2026): resumen por título con número de anexos subterráneos y volumen concesionado. Sin coordenadas.
- **REPDA 2011** (servicio ArcGIS REST de CONAGUA, capa 4): un registro por aprovechamiento con coordenadas, uso, volumen y profundidad.
- Cruce por nombre normalizado del titular (tres primeras palabras tras quitar S.A., de C.V., etc.). Fiable para razones sociales únicas; produce falsos positivos con titulares institucionales.
- Caudal por pozo: volumen 2026 del título entre su número de pozos; si no hay cruce, volumen 2011.

## 2. Índice de riesgo (scripts/04_risk_index.py)
Para cada pozo de servicios:
1. Distancia a la costa 2024 (CONABIO).
2. Espesor de la lente por Ghyben-Herzberg con flujo regional q = 4 m²/d más recarga de 0.45 mm/d, K = 1,000 m/d, δ = ρf/(ρs−ρf) = 40:  d(x) = √(2 (q + R·x) x δ / K), tope 60 m.
3. Distancia entre rejilla y haloclina: lente − profundidad registrada (mínimo 0.5 m).
4. Caudal crítico de ascenso estable (Dagan & Bear 1968, criterio z < d/3): Q_c = 2π K d² / (3 δ).
5. R = Q / Q_c. Bajo < 0.3, medio 0.3-1, alto > 1.

## 3. Modelo físico (model/lente_mf6.py)
MODFLOW 6.6.1 con GWF + GWT + BUY. Sección vertical de 3,000 × 62 m (celdas de 25 × 2 m, frente de 200 m). Mar: carga equivalente de agua dulce en toda la columna, concentración 35 g/L. Interior: inyección de agua dulce de 4 m²/d en los 20 m superiores; fondo cerrado. Recarga 0.45 mm/d. Pozo a 1,000 m de la costa con rejilla a −5 m. Equilibrio de 50 años (150 pasos) y 5 años de bombeo (120 pasos). Escenarios: 0, 36, 713, 1,876 y 3,681 m³/d, percentiles de la distribución de caudal por pozo de servicios en Quintana Roo. Transporte TVD, dispersividad 1 / 0.1 / 0.01 m. Resultado: salinidad en la celda del pozo como exceso sobre el escenario sin bombeo.

## 4. App (scripts/05_build_app.py, app/template.html)
Un archivo HTML con D3 7.9. Las curvas por pozo se interpolan en log(Q) entre los escenarios del modelo; si la rejilla registrada queda por debajo de la lente estimada, se marca "ya salobre en la condición inicial" en lugar de proyectar.
