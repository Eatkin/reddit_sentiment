run_api:
	uvicorn API.fastapi:app --reload

run_frontend:
	streamlit run frontend/index.py

update_packages:
	pip install --upgrade pip
	pip install -r requirements.txt
