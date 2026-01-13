import streamlit as st
import pandas as pd
import time

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Cotação de Frete", layout="wide", page_icon="🚚")

st.markdown("""
<style>
    .stApp { background-color: #050505; color: #E5E7EB; font-family: 'Inter', sans-serif; }
    div.stButton > button { background-color: #E31937; color: white; border: none; border-radius: 6px; font-weight: bold; width: 100%; }
    div.stButton > button:hover { background-color: #C2132F; }
    .metric-card { background-color: #151515; border: 1px solid #333; padding: 15px; border-radius: 8px; border-left: 4px solid #E31937; }
    input { background-color: #252525 !important; color: white !important; }
    label { color: #ccc !important; }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA CORRIGIDA (CUBAGEM PADRÃO) ---
def calcular_frete_real(peso_unitario, alt_cm, larg_cm, comp_cm, quantidade):
    # 1. Converter CM para Metros (o cálculo de transporte é sempre em metros cúbicos)
    alt_m = alt_cm / 100
    larg_m = larg_cm / 100
    comp_m = comp_cm / 100
    
    # 2. Calcular Volume Total (m3)
    volume_total = (alt_m * larg_m * comp_m) * quantidade
    
    # 3. Calcular Peso Cubado (Padrão Rodoviário usa fator 300)
    # Fórmula: Volume x 300
    peso_cubado_total = volume_total * 300
    
    # 4. Peso Real Total
    peso_real_total = peso_unitario * quantidade
    
    # 5. O Frete é cobrado pelo MAIOR valor entre (Peso Real) e (Peso Cubado)
    peso_taxavel = max(peso_real_total, peso_cubado_total)
    
    return peso_taxavel, volume_total

st.title("🚚 Central do Frete")

# --- FORMULÁRIO ---
st.caption("Preencha as dimensões em CENTÍMETROS (cm)")

c1, c2, c3, c4, c5 = st.columns(5)

# Agora os inputs deixam claro que é CM
with c1: peso = st.number_input("Peso Unit. (kg)", min_value=0.0, value=1.0)
with c2: alt = st.number_input("Altura (cm)", min_value=0.0, value=64.0)
with c3: larg = st.number_input("Largura (cm)", min_value=0.0, value=40.0)
with c4: comp = st.number_input("Comp. (cm)", min_value=0.0, value=15.0)
with c5: qtd = st.number_input("Qtd. Vols", min_value=1, value=5, step=1)

if st.button("COTAR FRETE"):
    # Faz o cálculo corrigido
    peso_cobrado, volume_m3 = calcular_frete_real(peso, alt, larg, comp, qtd)
    
    # Simulação de Preço Baseado no Peso Taxável (Ex: R$ 1,50 por kg + Taxa Fixa)
    base_price = 45.00 # Taxa fixa de coleta/emissão
    km_factor = 0.85   # Exemplo: Frete para região próxima
    
    # Cálculo estimado do valor do frete
    valor_base = base_price + (peso_cobrado * km_factor * 10) 
    
    # Simulação baseada nas empresas
    dados = [
        {"Transp.": "BRASPRESS", "Tipo": "Site", "Valor": f"R$ {valor_base * 1.05:.2f}", "Prazo": "3 dias"},
        {"Transp.": "RODONAVES", "Tipo": "Site", "Valor": f"R$ {valor_base * 0.95:.2f}", "Prazo": "4 dias"},
        {"Transp.": "JAMEF", "Tipo": "Site", "Valor": f"R$ {valor_base * 1.15:.2f}", "Prazo": "2 dias"},
        {"Transp.": "TW", "Tipo": "Site", "Valor": f"R$ {valor_base * 0.90:.2f}", "Prazo": "5 dias"},
        {"Transp.": "GLOBAL", "Tipo": "Site", "Valor": f"R$ {valor_base * 1.02:.2f}", "Prazo": "3 dias"},
        {"Transp.": "TCE", "Tipo": "E-mail", "Valor": "Aguardando", "Prazo": "-"},
        {"Transp.": "MANDALA", "Tipo": "Planilha", "Valor": "Verificar Manual", "Prazo": "-"},
    ]
    
    st.divider()
    
    # Exibição dos Totais Corrigidos
    k1, k2, k3 = st.columns(3)
    k1.markdown(f"<div class='metric-card'><h3>Peso Considerado (kg)</h3><h1>{peso_cobrado:.2f} kg</h1></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='metric-card'><h3>Volume Total (m³)</h3><h1>{volume_m3:.4f}</h1></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='metric-card'><h3>Melhor Estimativa</h3><h1 style='color:#E31937'>R$ {valor_base * 0.90:.2f}</h1></div>", unsafe_allow_html=True)
    
    st.write(f"ℹ️ *Cálculo baseado no fator de cubagem 300. Peso Real: {peso*qtd}kg | Peso Cubado: {volume_m3*300:.2f}kg*")
    
    st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)
