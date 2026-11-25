PY = uv run python

pipeline:            # s'arrête à la première étape en erreur
	$(PY) pipelines/extract.py
	$(PY) pipelines/transform.py
	$(PY) pipelines/quality.py
	$(PY) pipelines/load.py
