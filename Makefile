.PHONY: load ratios test report dashboard api clean help

help:
	@echo "Nifty 100 Financial Intelligence Platform Makefile Commands:"
	@echo "  make load      - Run ETL pipeline to build nifty100.db"
	@echo "  make ratios    - Populate financial_ratios table (Sprint 2)"
	@echo "  make test      - Run full pytest test suite"
	@echo "  make report    - Generate PDF reports"
	@echo "  make dashboard - Start Streamlit dashboard"
	@echo "  make api       - Start REST API server"
	@echo "  make clean     - Clean python bytecode and test cache"

load:
	python -m src.etl.loader

ratios:
	python -m src.analytics.engine

test:
	pytest tests/ -v --tb=short

report:
	python -m src.reports.portfolio_report

dashboard:
	streamlit run src/dashboard/app.py

api:
	uvicorn src.api.main:app --port 8000 --reload

clean:
	python -c "import os, glob; [os.remove(f) for f in glob.glob('**/*.pyc', recursive=True)]; [os.rmdir(d) for d in glob.glob('**/__pycache__', recursive=True) if os.path.exists(d)]"
