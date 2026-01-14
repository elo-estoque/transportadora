import streamlit as st
import pandas as pd
import requests
import base64
import time
import os
import json

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Cotação de Frete Real", layout="wide", page_icon="🚚")

st.markdown("""
<style>
    .stApp { background-color: #050505; color: #E5E7EB; font-family: 'Inter', sans-serif; }
    div.stButton > button { background-color: #E31937; color: white; border: none; border-radius: 6px; font-weight: bold; width: 100%; height: 50px; font-size: 18px; }
    div.stButton > button:hover { background-color: #C2132F; }
    .metric-card { background-color: #151515; border: 1px solid #333; padding: 15px; border-radius: 8px; border-left: 4px solid #E31937; }
    input { background-color: #252525 !important; color: white !important; border: 1px solid #444 !important; }
    label { color: #ccc !important; font-size: 14px; }
    .section-title { color: #E31937; font-size: 18px; margin-top: 10px; margin-bottom: 5px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---
def calcular_metricas(peso_unit, alt, larg, comp, qtd):
    vol_m3 = (alt/100 * larg/100 * comp/100) * qtd
    peso_cubado = vol_m3 * 300
    peso_real_total = peso_unit * qtd
    peso_taxavel = max(peso_real_total, peso_cubado)
    return peso_taxavel, vol_m3

# --- INTEGRAÇÕES REAIS ---

def cotar_braspress(dados):
    """Integração Oficial BRASPRESS"""
    # Tenta pegar do ENV (Dokploy) ou dos Secrets locais
    user = os.getenv("BRASPRESS_USER")
    pwd = os.getenv("BRASPRESS_PASS")
    
    if not user or not pwd:
        return {"simulado": True, "erro": "Credenciais não configuradas"}

    url = "https://api.braspress.com/v1/cotacao/calcular/json"
    credentials = f"{user}:{pwd}"
    auth_header = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "cnpjRemetente": 12345678000199, # SUBSTITUA PELO SEU CNPJ FIXO OU VARIAVEL
        "cnpjDestinatario": int(dados['cnpj_dest']),
        "modal": "R",
        "tipoFrete": "1",
        "cepOrigem": int(dados['cep_origem'].replace("-","")),
        "cepDestino": int(dados['cep_dest'].replace("-","")),
        "vlrMercadoria": dados['valor'],
        "peso": dados['peso_real'],
        "volumes": dados['qtd'],
        "cubagem": [{
            "altura": dados['alt'] / 100, 
            "largura": dados['larg'] / 100,
            "comprimento": dados['comp'] / 100,
            "volumes": dados['qtd']
        }]
    }

    try:
        req = requests.post(url, headers=headers, json=payload, timeout=5)
        if req.status_code == 200:
            resp = req.json()
            return {
                "simulado": False,
                "preco": resp.get("totalFrete"),
                "prazo": resp.get("prazo"),
                "transportadora": "BRASPRESS (API)"
            }
        return {"simulado": True, "erro": f"Erro API: {req.status_code}"}
    except:
        return {"simulado": True, "erro": "Falha Conexão"}

def cotar_central_frete(dados):
    """Integração CENTRAL DO FRETE (Hub)"""
    token = os.getenv("CENTRAL_TOKEN")
    
    if not token:
        return [] # Retorna lista vazia se não tiver token

    url = "https://api.centraldofrete.com/v1/cotacao"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "cep_origem": dados['cep_origem'].replace("-",""),
        "cep_destino": dados['cep_dest'].replace("-",""),
        "valornotafiscal": dados['valor'],
        "volumes": [{
            "peso": dados['peso_real'] / dados['qtd'], # Peso unitário
            "altura": dados['alt'],     # Em CM conforme doc deles
            "largura": dados['larg'],
            "comprimento": dados['comp'],
            "quantidade": dados['qtd']
        }]
    }

    try:
        req = requests.post(url, headers=headers, json=payload, timeout=8)
        resultados = []
        if req.status_code == 200:
            data = req.json()
            opcoes = data.get('cotacao', {}).get('opcoes', [])
            for op in opcoes:
                resultados.append({
                    "Transportadora": op.get('transportadora', 'Central Frete'),
                    "Preço Final": f"R$ {op.get('valor_frete', 0):.2f}",
                    "Prazo": f"{op.get('prazo_dias')} dias",
                    "Tipo": "Central do Frete"
                })
        return resultados
    except Exception as e:
        return []

# --- SIMULADOR DE FALLBACK ---
def simular_frete(nome, cep_origem, cep_destino, peso, valor):
    # Lógica simples para quando não tivermos a API ainda
    try:
        dist = abs(int(cep_origem[:5]) - int(cep_destino[:5])) / 1000
    except:
        dist = 50
    
    base = 45.00
    if nome == "RODONAVES": base = 48.00
    elif nome == "JAMEF": base = 55.00
    
    frete = base + (peso * 0.9) + (valor * 0.005) + (dist * 0.1)
    return frete, random.randint(3, 7)

# --- ROTAS PRINCIPAIS ---
import random # Importado aqui para garantir o simulador

def consultar_transportadora(nome, dados):
    # 1. Tenta API Braspress
    if nome == "BRASPRESS":
        res = cotar_braspress(dados)
        if not res['simulado']:
            return res['preco'], res['prazo'], "API Oficial"
            
    # 2. Outras (Rodonaves, etc) - Aqui entraria a chamada real futura
    # Por enquanto, cai direto no simulador
    
    # 3. Fallback (Simulador)
    val, prz = simular_frete(nome, dados['cep_origem'], dados['cep_dest'], dados['peso_real'], dados['valor'])
    return val, prz, "Simulador (Sem Key)"

# --- INTERFACE ---
st.title("🚚 Central do Frete Integrada")

with st.form("form_cotacao"):
    st.markdown("<div class='section-title'>📍 Rota e Fiscal</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: cep_origem = st.text_input("CEP Origem", value="01001-000")
    with c2: cep_dest = st.text_input("CEP Destino")
    with c3: cnpj = st.text_input("CNPJ Destinatário")
    with c4: valor_nota = st.number_input("Valor da Nota (R$)", min_value=0.0, step=100.0)

    st.markdown("<div class='section-title'>📦 Carga (Medidas em CM)</div>", unsafe_allow_html=True)
    d1, d2, d3, d4, d5 = st.columns(5)
    with d1: peso = st.number_input("Peso Unit. (kg)", min_value=0.0, value=1.0)
    with d2: alt = st.number_input("Altura (cm)", min_value=0.0, value=64.0)
    with d3: larg = st.number_input("Largura (cm)", min_value=0.0, value=40.0)
    with d4: comp = st.number_input("Comp. (cm)", min_value=0.0, value=15.0)
    with d5: qtd = st.number_input("Qtd. Vols", min_value=1, value=5, step=1)
    
    btn_cotar = st.form_submit_button("CALCULAR FRETE AGORA")

if btn_cotar:
    if not cep_dest:
        st.warning("⚠️ Digite o CEP de destino.")
    else:
        with st.spinner("Consultando APIs e Tabelas..."):
            
            # Dados consolidados
            dados_carga = {
                "cep_origem": cep_origem, "cep_dest": cep_dest, "cnpj_dest": cnpj if cnpj else "00000000000000",
                "valor": valor_nota, "peso_real": peso * qtd, "qtd": qtd,
                "alt": alt, "larg": larg, "comp": comp
            }
            
            resultados = []
            
            # A) Consulta Direta (Transportadoras Individuais)
            transps_diretas = ["BRASPRESS", "RODONAVES", "JAMEF", "TW", "GLOBAL"]
            for t in transps_diretas:
                val, prz, tipo = consultar_transportadora(t, dados_carga)
                resultados.append({
                    "Transportadora": t,
                    "Preço Final": f"R$ {val:.2f}",
                    "Prazo": f"{prz} dias",
                    "Tipo": tipo
                })
                
            # B) Consulta Central do Frete (Hub)
            res_central = cotar_central_frete(dados_carga)
            if res_central:
                resultados.extend(res_central)
            else:
                # Se falhar ou não tiver token, avisa no log (opcional)
                pass

            # Exibe Resultados
            st.divider()
            
            # KPIs
            peso_tax, _ = calcular_metricas(peso, alt, larg, comp, qtd)
            vals = [float(x['Preço Final'].replace('R$ ','').replace(',','.')) for x in resultados]
            melhor = min(vals) if vals else 0
            
            k1, k2, k3 = st.columns(3)
            k1.markdown(f"<div class='metric-card'><h3>Peso Taxável</h3><h1>{peso_tax:.2f} kg</h1></div>", unsafe_allow_html=True)
            k2.markdown(f"<div class='metric-card'><h3>Cotações Obtidas</h3><h1>{len(resultados)}</h1></div>", unsafe_allow_html=True)
            k3.markdown(f"<div class='metric-card'><h3>Melhor Preço</h3><h1 style='color:#E31937'>R$ {melhor:.2f}</h1></div>", unsafe_allow_html=True)
            
            st.write("")
            df = pd.DataFrame(resultados)
            st.dataframe(df, use_container_width=True, hide_index=True)
