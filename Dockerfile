FROM python:3.9-slim

WORKDIR /app

# Instala as bibliotecas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o app
COPY . .

# Expõe a porta
EXPOSE 8501

# --- CONFIGURAÇÃO CRÍTICA PARA SUBPASTA ---
# Isso diz ao Streamlit: "Você não está na raiz, você está em /transportadora"
ENV STREAMLIT_SERVER_BASE_URL_PATH=transportadora
# Desabilita verificação de CORS para evitar erro de conexão websocket
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Roda o app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
