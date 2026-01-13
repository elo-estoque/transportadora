# Usa uma imagem leve do Python
FROM python:3.9-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Variáveis de ambiente para evitar arquivos .pyc e logs em buffer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copia os requisitos e instala (melhora o cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código para dentro do container
COPY . .

# Expõe a porta que o FastAPI vai usar
EXPOSE 8000

# Comando para rodar a aplicação quando o container iniciar
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
