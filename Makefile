.PHONY: all data model app figures mf6
PY=python3
all: data model figures app
data:
	$(PY) scripts/02_clean_repda2026.py
	$(PY) scripts/03_crossmatch_2011_2026.py
	$(PY) scripts/04_risk_index.py
download:
	cd data/raw && $(PY) ../../scripts/01_download_repda2011.py
mf6:
	mkdir -p bin && curl -sL -o /tmp/mf6.zip https://github.com/MODFLOW-ORG/modflow6/releases/download/6.6.1/mf6.6.1_linux.zip \
	&& unzip -oq /tmp/mf6.zip -d /tmp/mf6 && cp /tmp/mf6/mf6.6.1_linux/bin/mf6 bin/ && chmod +x bin/mf6
model:
	cd model && $(PY) lente_mf6.py
figures:
	$(PY) scripts/06_fig_mf6.py
app:
	$(PY) scripts/05_build_app.py
