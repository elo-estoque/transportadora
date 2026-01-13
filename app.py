import streamlit as st
import pandas as pd
import time
import random

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

# --- LÓGICA DE CÁLCULO (PESO CUBADO) ---
def calcular_metricas(peso_unit, alt, larg, comp, qtd):
    # Converte cm para m
    vol_m3 = (alt/100 * larg/100 * comp/100) * qtd
    peso_cubado = vol_m3 * 300
    peso_real_total = peso_unit * qtd
    peso_taxavel = max(peso_real_total, peso_cubado)
    return peso_taxavel, vol_m3

# --- SIMULAÇÃO DE API (Onde entraria a conexão real) ---
def consultar_api_transportadora(nome, cep_origem, cep_destino, peso, valor_nota, cnpj):
    """
    IMPORTANTE: Aqui é onde entraria o código real tipo:
    response = requests.post("https://api.braspress.com.br/cotar", json={...})
    Como não temos as chaves, estou simulando uma lógica de precificação baseada na distância (CEP) e Valor.
    """
    
    # Lógica Fictícia de Preço para Simulação
    try:
        distancia_fator = abs(int(cep_origem[:5]) - int(cep_destino[:5])) / 1000
    except:
        distancia_fator = 50 # Valor padrão se CEP for inválido
        
    frete_base = 40.00
    frete_peso = peso * 0.80
    ad_valorem = valor_nota * 0.005 # 0.5% de seguro
    pedagio = 5.00
    gris = valor_nota * 0.002
    
    # Variação por transportadora (simulação)
    if nome == "BRASPRESS":
        total = frete_base + frete_peso + ad_valorem + pedagio + 15
        prazo = 3
    elif nome == "RODONAVES":
        total = frete_base + frete_peso + ad_valorem + pedagio + 5
        prazo = 4
    elif nome == "JAMEF":
        total = frete_base + (peso * 1.1) + ad_valorem + pedagio + 20
        prazo = 2
    elif nome == "TW":
        total = frete_base + (peso * 0.7) + ad_valorem + pedagio
        prazo = 5
    elif nome == "GLOBAL":
        total = frete_base + frete_peso + ad_valorem + pedagio + 10
        prazo = 3
    else:
        total = 0
        prazo = 0
        
    return total, prazo

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
    
    st.write("")
    btn_cotar = st.form_submit_button("CALCULAR FRETE REAL")

if btn_cotar:
    if not cep_dest or not cnpj:
        st.warning("⚠️ Preencha CEP de Destino e CNPJ para cálculo de impostos.")
    else:
        with st.spinner("Conectando aos servidores das transportadoras..."):
            time.sleep(1.5) # Simula delay de rede
            
            # 1. Cálculos Físicos
            peso_taxavel, vol_m3 = calcular_metricas(peso, alt, larg, comp, qtd)
            
            # 2. Loop de Cotação (Simulado)
            transportadoras = ["BRASPRESS", "RODONAVES", "JAMEF", "TW", "GLOBAL"]
            resultados = []
            
            for transp in transportadoras:
                val, prz = consultar_api_transportadora(transp, cep_origem, cep_dest, peso_taxavel, valor_nota, cnpj)
                resultados.append({
                    "Transportadora": transp,
                    "Preço Final": f"R$ {val:.2f}",
                    "Prazo": f"{prz} dias úteis",
                    "Tipo": "API Online"
                })
            
            # Adiciona os manuais
            resultados.append({"Transportadora": "TCE", "Preço Final": "Cotação via Email", "Prazo": "-", "Tipo": "Manual"})
            resultados.append({"Transportadora": "MANDALA", "Preço Final": "Ver Tabela Fixa", "Prazo": "-", "Tipo": "Manual"})
            
            st.divider()
            
            # Exibe Métricas
            k1, k2, k3 = st.columns(3)
            k1.markdown(f"<div class='metric-card'><h3>Peso Taxável (Cubado)</h3><h1>{peso_taxavel:.2f} kg</h1></div>", unsafe_allow_html=True)
            k2.markdown(f"<div class='metric-card'><h3>Valor da Mercadoria</h3><h1>R$ {valor_nota:.2f}</h1></div>", unsafe_allow_html=True)
            # Pega o menor valor da lista (simulado)
            melhor_preco = min([float(x['Preço Final'].replace('R$ ','')) for x in resultados if 'R$' in x['Preço Final']])
            k3.markdown(f"<div class='metric-card'><h3>Melhor Oferta</h3><h1 style='color:#E31937'>R$ {melhor_preco:.2f}</h1></div>", unsafe_allow_html=True)
            
            st.success(f"Cotação realizada para CEP: {cep_dest} | CNPJ: {cnpj}")
            
            # Tabela Final
            df = pd.DataFrame(resultados)
            st.dataframe(df, use_container_width=True, hide_index=True)
