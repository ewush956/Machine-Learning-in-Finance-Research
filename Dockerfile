
FROM python:3.14-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install -U pip && pip install -r /app/requirements.txt

COPY . /app

EXPOSE 8000
CMD ["shiny", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000", "--reload"]
