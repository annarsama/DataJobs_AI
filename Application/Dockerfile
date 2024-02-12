FROM python:3.10-slim

COPY requirements.txt /app/requirements.txt
WORKDIR /app 

RUN pip install -r requirements.txt

COPY . /app

CMD ["streamlit", "run", "app_main.py", "8501:8501"]