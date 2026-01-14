import streamlit as st
import pandas as pd
import requests
import base64
import os
import random

# --- 1. CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira linha) ---
st.set_page_config(page_title="Cotação Frete", layout="wide", page_icon="🚚")

# Estilos CSS
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #E5E7EB; }
    div.stButton > button { background-color: #E31937; color: white; border: none; height: 50px; width: 100%; font-size: 18px; font-weight: bold; }
    .metric-card { background-color: #151515; border: 1px solid #333; padding: 15px; border-radius: 8px; border-left: 4px solid #E31937; }
    input { background-color: #252525 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. FUNÇÕES DE CÁLCULO ---

def simular_frete(nome, cep_origem, cep_destino, peso, valor):
    # Simulador matemático simples para quando não houver API
    try:
        dist = abs(int(cep_origem[:5]) - int(cep_destino[:5])) / 1000
    except:
        dist = 50
    
    base = 45.00
    frete = base + (peso * 0.9) + (valor * 0.005) + (dist * 0.1)
    return frete, random.randint(3, 7)

# --- 3. INTEGRAÇÃO CENTRAL DO FRETE ---
def cotar_central_frete(dados):
    # Pega token e limpa espaços vazios
    token = os.getenv("CENTRAL_TOKEN", "").strip()
    
    if not token:
        return [{"Transportadora": "⚠️ CONFIG", "Preço Final": "---", "Prazo": "-", "Tipo": "Sem Token no Dokploy"}]

    # URL OFICIAL (A quotation deu 404, então voltamos para a API padrão)
    url = "https://api.centraldofrete.com/v1/cotacao"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Payload formatado estritamente como numero
    payload = {
        "cep_origem": str(dados['cep_origem']).replace("-",""),
        "cep_destino": str(dados['cep_dest']).replace("-",""),
        "valornotafiscal": float(dados['valor']),
        "volumes": [{
            "peso": float(dados['peso_real']) / int(dados['qtd']),
            "altura": int(dados['alt']),
            "largura": int(dados['larg']),
            "comprimento": int(dados['comp']),
            "quantidade": int(dados['qtd'])
        }]
    }

    try:
        req = requests.post(url, headers=headers, json=payload, timeout=8)
        
        if req.status_code == 200:
            data = req.json()
            opcoes = data.get('cotacao', {}).get('opcoes', [])
            
            if not opcoes:
                return [{"Transportadora": "Central Frete", "Preço Final": "R$ 0.00", "Prazo": "-", "Tipo": "Nenhuma transp. atende o CEP"}]
                
            resultados = []
            for op in opcoes:
                resultados.append({
                    "Transportadora": op.get('transportadora', 'Central'),
                    "Preço Final": f"R$ {op.get('valor_frete', 0):.2f}",
                    "Prazo": f"{op.get('prazo_dias')} dias",
                    "Tipo": "Central do Frete (API)"
                })
            return resultados
        
        else:
            # Mostra o erro exato na tela
            return [{"Transportadora": "⚠️ ERRO API", "Preço Final": f"Status {req.status_code}", "Prazo": "-", "Tipo": req.text[:40]}]

    except Exception as e:
        return [{"Transportadora": "⚠️ ERRO CRÍTICO", "Preço Final": "---", "Prazo": "-", "Tipo": str(e)[:40]}]

# --- 4. INTEGRAÇÃO BRASPRESS ---
def cotar_braspress(dados):
    user = os.getenv("BRASPRESS_USER", "").strip()
    pwd = os.getenv("BRASPRESS_PASS", "").strip()
    
    if not user or not pwd:
        return {"simulado": True}

    url = "https://api.braspress.com/v1/cotacao/calcular/json"
    auth = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    
    try:
        req = requests.post(url, headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"}, json={
            "cnpjRemetente": 12345678000199,
            "cnpjDestinatario": int(dados['cnpj_dest']),
            "modal": "R", "tipoFrete": "1",
            "cepOrigem": int(dados['cep_origem'].replace("-","")),
            "cepDestino": int(dados['cep_dest'].replace("-","")),
            "vlrMercadoria": dados['valor'], "peso": dados['peso_real'], "volumes": dados['qtd'],
            "cubagem": [{"altura": dados['alt']/100, "largura": dados['larg']/100, "comprimento": dados['comp']/100, "volumes": dados['qtd']}]
        }, timeout=5)
        
        if req.status_code == 200:
            r = req.json()
            return {"simulado": False, "preco": r.get("totalFrete"), "prazo": r.get("prazo"), "transp": "BRASPRESS"}
    except: pass
    return {"simulado": True}

# --- 5. INTERFACE PRINCIPAL ---
st.title("🚚 Central do Frete")

try:
    with st.form("main_form"):
        st.write("📍 **Rota e Carga**")
        c1, c2, c3, c4 = st.columns(4)
        cep_origem = c1.text_input("CEP Origem", "01001-000")
        cep_dest = c2.text_input("CEP Destino")
        cnpj = c3.text_input("CNPJ Destino")
        valor = c4.number_input("Valor Nota (R$)", 100.0)
        
        d1, d2, d3, d4, d5 = st.columns(5)
        peso = d1.number_input("Peso (kg)", 1.0)
        alt = d2.number_input("Alt (cm)", 64.0)
        larg = d3.number_input("Larg (cm)", 40.0)
        comp = d4.number_input("Comp (cm)", 15.0)
        qtd = d5.number_input("Qtd", 5)
        
        btn_cotar = st.form_submit_button("CALCULAR FRETE")

    if btn_cotar:
        if not cep_dest:
            st.warning("⚠️ Preencha o CEP de Destino!")
        else:
            with st.spinner("Consultando transportadoras..."):
                dados = {
                    "cep_origem": cep_origem, "cep_dest": cep_dest, "cnpj_dest": cnpj or "00000000000000",
                    "valor": valor, "peso_real": peso * qtd, "qtd": qtd,
                    "alt": alt, "larg": larg, "comp": comp
                }
                
                lista_final = []
                
                # 1. Central do Frete
                lista_final.extend(cotar_central_frete(dados))
                
                # 2. Braspress Direta
                res_bp = cotar_braspress(dados)
                if not res_bp['simulado']:
                    lista_final.append({"Transportadora": "BRASPRESS", "Preço Final": f"R$ {res_bp['preco']:.2f}", "Prazo": f"{res_bp['prazo']} dias", "Tipo": "API Direta"})
                else:
                    # Só simula se a Central não trouxe Braspress
                    if not any("BRASPRESS" in x['Transportadora'].upper() for x in lista_final):
                        v, p = simular_frete("BRASPRESS", cep_origem, cep_dest, dados['peso_real'], valor)
                        lista_final.append({"Transportadora": "BRASPRESS", "Preço Final": f"R$ {v:.2f}", "Prazo": f"{p} dias", "Tipo": "Simulador"})
                
                # 3. Outras Simuladas
                for t in ["RODONAVES", "JAMEF", "TW", "GLOBAL"]:
                    if not any(t in x['Transportadora'].upper() for x in lista_final):
                        v, p = simular_frete(t, cep_origem, cep_dest, dados['peso_real'], valor)
                        lista_final.append({"Transportadora": t, "Preço Final": f"R$ {v:.2f}", "Prazo": f"{p} dias", "Tipo": "Simulador"})

                # Exibição
                vals = [float(x['Preço Final'].replace('R$ ','')) for x in lista_final if 'R$' in x['Preço Final']]
                melhor = min(vals) if vals else 0
                
                k1, k2 = st.columns(2)
                k1.markdown(f"<div class='metric-card'><h3>Opções</h3><h1>{len(lista_final)}</h1></div>", unsafe_allow_html=True)
                k2.markdown(f"<div class='metric-card'><h3>Melhor Preço</h3><h1 style='color:#E31937'>R$ {melhor:.2f}</h1></div>", unsafe_allow_html=True)
                
                st.write("")
                st.dataframe(pd.DataFrame(lista_final), use_container_width=True)

except Exception as e:
    st.error(f"Erro Crítico no App: {e}")
