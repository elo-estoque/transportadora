from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List

# --- CONFIGURAÇÃO DA SUBPASTA ---
# root_path é o segredo para funcionar em intranet.elobrindes.com.br/transportadora
app = FastAPI(title="Central do Frete", root_path="/transportadora")

# Configura onde fica o arquivo HTML
templates = Jinja2Templates(directory="templates")

# --- MODELO DE DADOS ---
class DimensoesCarga(BaseModel):
    peso: float
    altura: float
    largura: float
    comprimento: float
    quantidade: int = 1

# --- LÓGICA DE CÁLCULO (Igual imagem 1) ---
def calcular_cubagem_logica(c: DimensoesCarga) -> float:
    # Fórmula: PESO X ALTURA X LARGURA X COMPRIMENTO
    return (c.peso * c.altura * c.largura * c.comprimento) * c.quantidade

# --- ROTAS ---

@app.get("/")
def home(request: Request):
    # Renderiza o index.html
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/cotar")
def cotar_frete(carga: DimensoesCarga):
    cubagem = calcular_cubagem_logica(carga)
    
    # Simulação de resposta (Baseado na imagem)
    return {
        "cubagem": cubagem,
        "cotacoes": [
            {"nome": "BRASPRESS", "valor": f"R$ {120 + (cubagem*10):.2f}", "tipo": "API"},
            {"nome": "RODONAVES", "valor": f"R$ {115 + (cubagem*12):.2f}", "tipo": "API"},
            {"nome": "JAMEF", "valor": f"R$ {140 + (cubagem*8):.2f}", "tipo": "API"},
            {"nome": "TW", "valor": f"R$ {110 + (cubagem*11):.2f}", "tipo": "API"},
            {"nome": "GLOBAL", "valor": f"R$ {130 + (cubagem*9):.2f}", "tipo": "API"},
            {"nome": "TCE", "valor": "Enviado por E-mail", "tipo": "Email"},
            {"nome": "MANDALA", "valor": "Verificar Planilha", "tipo": "Manual"},
        ]
    }
