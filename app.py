from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates # Import novo
from pydantic import BaseModel
from typing import List
import os

app = FastAPI(title="Central do Frete API")

# Configura a pasta de templates (onde está o index.html)
templates = Jinja2Templates(directory="templates")

# --- MODELOS ---
class DimensoesCarga(BaseModel):
    peso: float
    altura: float
    largura: float
    comprimento: float
    quantidade: int = 1

# --- LÓGICA (Mantive igual) ---
def calcular_cubagem_customizada(c: DimensoesCarga) -> float:
    return (c.peso * c.altura * c.largura * c.comprimento) * c.quantidade

class CotadorService:
    def __init__(self):
        self.api_carriers = ['BRASPRESS', 'RODONAVES', 'JAMEF', 'TW', 'GLOBAL']
        self.email_carriers = ['TCE']
        self.sheet_carriers = ['MANDALA']

    def simular_api_externa(self, carrier, cubagem):
        return {
            "transportadora": carrier,
            "tipo": "API",
            "valor_estimado": round(cubagem * 15.5 + 50, 2),
            "status": "SUCESSO"
        }

    def processar_manual(self, carrier, cubagem):
        msg = ""
        if carrier in self.email_carriers:
            msg = "Email enviado."
        elif carrier in self.sheet_carriers:
            msg = "Verificar planilha."
        
        return {
            "transportadora": carrier,
            "tipo": "MANUAL",
            "mensagem": msg,
            "status": "PENDENTE"
        }

    def realizar_cotacao(self, dados: DimensoesCarga):
        cubagem = calcular_cubagem_customizada(dados)
        resultados = []
        for carrier in self.api_carriers:
            resultados.append(self.simular_api_externa(carrier, cubagem))
        for carrier in self.email_carriers:
            resultados.append(self.processar_manual(carrier, cubagem))
        for carrier in self.sheet_carriers:
            resultados.append(self.processar_manual(carrier, cubagem))

        return {
            "dados_entrada": dados,
            "cubagem_calculada": cubagem,
            "cotacoes": resultados
        }

# --- ROTAS ---

# Rota nova: Serve a interface gráfica
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Rota API: Recebe o JSON (enviado pelo Javascript do HTML)
@app.post("/cotar")
def cotar_frete(carga: DimensoesCarga):
    cotador = CotadorService()
    return cotador.realizar_cotacao(carga)
