# Dockerfile para Railway - GaMi-AI
FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema (necessárias para psycopg2 e outras libs)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro (para cache do Docker)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da aplicação
COPY . .

# Expõe a porta (Railway define a variável PORT)
EXPOSE $PORT

# Comando para iniciar a aplicação
# Railway fornece a variável de ambiente $PORT automaticamente
CMD chainlit run app.py --host 0.0.0.0 --port ${PORT:-8000}

