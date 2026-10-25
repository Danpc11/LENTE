# LENTE

Repositorio: https://github.com/Danpc11/LENTE

Riesgo de intrusión salina en pozos de servicios de la península de Yucatán: datos abiertos, modelo físico y web app.

Bajo la costa caribeña de Quintana Roo el agua dulce flota sobre el mar en una lente de pocos metros. Los hoteles, parques y aeropuertos la bombean desde pozos someros (profundidad mediana: 5 m) y nadie les dice cuándo su pozo se volverá salobre. LENTE junta el padrón de concesiones (REPDA), un modelo de flujo de densidad variable (MODFLOW 6) y un índice analítico de ascenso de la haloclina para clasificar cada pozo y proyectar su salinidad.

App publicada: https://claude.ai/artifact/SS6CTEkVu9wiX6riBCckBd

## Resultados principales

- En Quintana Roo, el uso **servicios** tiene 794 pozos y **333.7 hm³/año** concesionados, 2.7 veces el abasto público urbano (122.4 hm³/año). REPDA, corte 30-sep-2026.
- 1,802 pozos de servicios de la península tienen coordenadas (REPDA 2011). De ellos, **179 bombean por encima del caudal crítico** de su lente; **173 están en Quintana Roo** y casi todos entre Cancún y Tulum.
- En el modelo 2D, un pozo hotelero típico (P75, 713 m³/d) a 1 km de la costa cruza 1 g/L en 12 meses; uno grande (P90, 1,876 m³/d) en 7; el P95 en 2.
- 142 titulares de servicios de la costa aparecen tanto en 2011 (con ubicación) como en 2026 (con volumen vigente) y concentran 215.5 hm³/año: son el mercado nombrado.

## Estructura

```
data/raw/        exportaciones del REPDA 2026 (ReporteRepda*.csv), pozos REPDA 2011 por estado, costa 2024 (GeoJSON)
data/processed/  títulos limpios, cruce 2011-2026, índice de riesgo por pozo, piezómetros y sitios RENAMECA de QRoo, capas geo recortadas
scripts/         01 descarga REST, 02 limpieza REPDA 2026, 03 cruce, 04 índice de riesgo, 05 app, 06 figura del modelo
model/           lente_mf6.py (MODFLOW 6 GWF+GWT+BUY) y results/*.json
app/             template.html y lente_app.html (autocontenida)
figures/         figuras en formato de publicación
docs/            metodología y fuentes
```

## Reproducir

```bash
pip install -r requirements.txt
make download   # REPDA 2011 por REST (necesita red; a veces bloquea redes institucionales)
make data       # limpieza, cruce e índice de riesgo
make mf6        # binario MODFLOW 6.6.1 (Linux); en macOS baja mf6.6.1_mac.zip del mismo release
make model      # cinco escenarios + referencia, ~4 min
make figures app
```

Las exportaciones del REPDA 2026 se hacen a mano en https://app.conagua.gob.mx/ConsultaRepda.aspx (búsqueda avanzada por tipo de aprovechamiento, estado y uso) y se dejan en `data/raw/`. El script 02 descarta los archivos vacíos y los títulos repetidos.

## Fuentes

- CONAGUA, REPDA: consulta en línea (2026) y servicio REST `sigagis.conagua.gob.mx/ArcGIS/rest/services/Aprovechamientos/MapServer/4` (2011).
- CONAGUA, SINA: red piezométrica 2025, disponibilidad por acuífero (DOF 2023), diagnóstico de calidad del agua del acuífero Península de Yucatán 2012-2023.
- CONABIO: línea de costa de México 2024, manglares 2025 y cambios 2020-2025, cuerpos de agua 1:50 000.
- Natural Earth 1:10 m: batimetría y ríos.
- Bauer-Gottwein et al. (2011) *Hydrogeology Journal*; Beddows et al. (2007) *Journal of Hydrology*: rango de K y profundidad de la haloclina usados para fijar los parámetros.

## Limitaciones

Las coordenadas y profundidades de pozo son del REPDA 2011 y tienen errores conocidos de georreferenciación; la profundidad registrada puede ser total y no de rejilla. El modelo 2D usa K = 1,000 m/d y 4 m²/d de flujo regional, fijados para reproducir una lente de 20-25 m a 1 km de la costa, no calibrados con pozos, y su equilibrio de 50 años no es estacionario, por lo que los resultados se reportan como exceso sobre la referencia sin bombeo. El índice analítico es un ranking relativo; se convierte en pronóstico por pozo con sensores de conductividad, nivel y caudal en campo.

## Licencia

MIT para el código. Los datos de CONAGUA y CONABIO conservan sus términos de uso.
