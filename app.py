import streamlit as st
import pandas as pd
import time

# --- CONFIGURAÇÃO VISUAL IGUAL AO SEU SISTEMA ---
st.set_page_config(page_title="Cotação de Frete", layout="wide", page_icon="🚚")

st.markdown("""
<style>
    .stApp { background-color: #050505; color: #E5E7EB; font-family: 'Inter', sans-serif; }
    div.stButton > button { background-color: #E31937; color: white; border: none; border-radius: 6px; font-weight: bold; width: 100%; }
    div.stButton > button:hover { background-color: #C2132F; }
    .metric-card { background-color: #151515; border: 1px solid #333; padding: 15px; border-radius: 8px; border-left: 4px solid #E31937; }
    input { background-color: #252525 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE NEGÓCIO (BASEADA NA IMAGEM 1) ---
def calcular(peso, alt, larg, comp, qtd):
    # Fórmula da imagem: PESO X ALTURA X LARGURA X COMPRIMENTO
    cubagem = (peso * alt * larg * comp) * qtd
    return cubagem

st.title("🚚 Central do Frete")

# --- FORMULÁRIO ---
c1, c2, c3, c4, c5 = st.columns(5)
with c1: peso = st.number_input("Peso (kg)", min_value=0.0)
with c2: alt = st.number_input("Altura (m)", min_value=0.0)
with c3: larg = st.number_input("Largura (m)", min_value=0.0)
with c4: comp = st.number_input("Comp. (m)", min_value=0.0)
with c5: qtd = st.number_input("Qtd.", min_value=1, value=1)

if st.button("COTAR FRETE"):
    cubagem = calcular(peso, alt, larg, comp, qtd)
    
    # Simulação baseada nas empresas da imagem
    dados = [
        {"Transp.": "BRASPRESS", "Tipo": "Site", "Valor": f"R$ {120 + (cubagem*10):.2f}"},
        {"Transp.": "RODONAVES", "Tipo": "Site", "Valor": f"R$ {115 + (cubagem*12):.2f}"},
        {"Transp.": "JAMEF", "Tipo": "Site", "Valor": f"R$ {140 + (cubagem*8):.2f}"},
        {"Transp.": "TW", "Tipo": "Site", "Valor": f"R$ {110 + (cubagem*11):.2f}"},
        {"Transp.": "GLOBAL", "Tipo": "Site", "Valor": f"R$ {130 + (cubagem*9):.2f}"},
        {"Transp.": "TCE", "Tipo": "E-mail", "Valor": "Aguardando"},
        {"Transp.": "MANDALA", "Tipo": "Planilha", "Valor": "Verificar Manual"},
    ]
    
    st.divider()
    k1, k2 = st.columns(2)
    k1.markdown(f"<div class='metric-card'><h3>Cubagem Total</h3><h1>{cubagem:.4f}</h1></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='metric-card'><h3>Melhor Estimativa</h3><h1>R$ {110 + (cubagem*11):.2f}</h1></div>", unsafe_allow_html=True)
    
    st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)
