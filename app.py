import streamlit as st
import pandas as pd
import requests
import os
import random

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Central do Frete - Debug", layout="wide", page_icon="🛠️")

st.markdown("""
<style>
    .stApp { background-color: #050505; color: #E5E7EB; }
    div.stButton > button { background-color: #E31937; color: white; border: none; height: 50px; width: 100%; font-size: 18px; font-weight: bold; }
    .metric-card { background-color: #151515; border: 1px solid #333; padding: 15px; border-radius: 8px; border-left: 4px solid #E31937; }
    input { background-color: #252525 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- MENU LATERAL DE CONFIGURAÇÃO (DEBUG) ---
with st.sidebar:
    st.header("🛠️ Configuração Avançada")
    st.write("Se a API der erro, tente trocar a URL abaixo:")
    
    # Tenta pegar do Dokploy, mas deixa editar na tela
    token_env = os.getenv("CENTRAL_TOKEN", "")
    token_input = st.text_input("Seu Token", value=token_env, type="password")
    
    # Lista de URLs prováveis para testar
    urls_possiveis = [
        "https://api.centraldofrete.com/v1/cotacao",      # Padrão API V1
        "https://quotation.centraldofrete.com/v1/cotacao", # Padrão Gateway
        "https://app.centraldofrete.com/api/v1/cotacao",   # Interna
        "https://quotation.centraldofrete.com/v1/api/cotacao"
    ]
    url_selecionada = st.selectbox("Selecione a URL para testar:", urls_possiveis, index=0)
    
    st.info("💡 Dica: Verifique no painel da Central do Frete > Integrações qual é a URL exata fornecida para o seu token.")

# --- FUNÇÃO CENTRAL DO FRETE (DINÂMICA) ---
def cotar_central_frete(dados, url_api, token):
    if not token:
        return [{"Transportadora": "⚠️ S/ TOKEN", "Preço Final": "-", "Prazo": "-", "Tipo": "Preencha o Token ao lado"}]

    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json"
    }
    
    # Payload formatado
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
        req = requests.post(url_api, headers=headers, json=payload, timeout=8)
        
        # SUCESSO
        if req.status_code == 200:
            data = req.json()
            opcoes = data.get('cotacao', {}).get('opcoes', [])
            
            if not opcoes:
                return [{"Transportadora": "Central Frete", "Preço Final": "R$ 0.00", "Prazo": "-", "Tipo": "Nenhuma opção encontrada"}]
                
            resultados = []
            for op in opcoes:
                resultados.append({
                    "Transportadora": op.get('transportadora', 'Central'),
                    "Preço Final": f"R$ {op.get('valor_frete', 0):.2f}",
                    "Prazo": f"{op.get('prazo_dias')} dias",
                    "Tipo": "API OK ✅"
                })
            return resultados
        
        # ERRO IDENTIFICADO
        else:
            msg_erro = req.text[:100]
            if "<html" in msg_erro: msg_erro = "Erro HTML (URL Errada)"
            return [{"Transportadora": "⚠️ ERRO API", "Preço Final": f"Status {req.status_code}", "Prazo": "-", "Tipo": msg_erro}]

    except Exception as e:
        return [{"Transportadora": "⚠️ FALHA", "Preço Final": "Exception", "Prazo": "-", "Tipo": str(e)[:30]}]

# --- INTERFACE PRINCIPAL ---
st.title("🚚 Testador de Frete Real")

with st.form("cotacao_form"):
    c1, c2, c3, c4 = st.columns(4)
    cep_origem = c1.text_input("CEP Origem", "01001-000")
    cep_dest = c2.text_input("CEP Destino")
    valor = c3.number_input("Valor Nota (R$)", 100.0)
    qtd = c4.number_input("Qtd Volumes", 1)
    
    d1, d2, d3, d4 = st.columns(4)
    peso = d1.number_input("Peso Total (kg)", 1.0)
    alt = d2.number_input("Altura (cm)", 20.0)
    larg = d3.number_input("Largura (cm)", 20.0)
    comp = d4.number_input("Comp (cm)", 20.0)
    
    btn = st.form_submit_button("COTAR AGORA")

if btn:
    if not cep_dest:
        st.warning("Preencha o CEP de Destino")
    else:
        dados = {
            "cep_origem": cep_origem, "cep_dest": cep_dest, 
            "valor": valor, "peso_real": peso, "qtd": qtd,
            "alt": alt, "larg": larg, "comp": comp
        }
        
        # Chama a função usando a URL selecionada no menu lateral
        resultado = cotar_central_frete(dados, url_selecionada, token_input)
        
        st.write("---")
        st.subheader(f"Testando URL: `{url_selecionada}`")
        
        df = pd.DataFrame(resultado)
        st.dataframe(df, use_container_width=True)
        
        if "API OK" in str(resultado):
            st.success(f"🎉 SUCESSO! A URL correta é: {url_selecionada}")
            st.caption("Agora você pode fixar essa URL no seu código final.")
