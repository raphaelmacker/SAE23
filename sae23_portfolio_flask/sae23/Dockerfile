FROM python:3.12-slim

# Dossier de travail
WORKDIR /app

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code source
COPY . .

# Exposition du port
EXPOSE 5000

# Lancement avec Gunicorn (production)
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
