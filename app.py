import streamlit as st
import pandas as pd
import requests
import base64
import os
import random

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Cotação de Frete Real", layout="wide", page_icon="🚚")
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #E5E7EB; font-family: 'Inter', sans-serif; }
    div.stButton > button { background-color: #E31937; color: white; border: none; border-radius: 6px; font-weight: bold; width: 100%; height: 50px; font-size: 18px; }
    .metric-card { background-color: #151515; border: 1px solid #333; padding: 15px; border-radius: 8px; border-left: 4px solid #E31937; }
    input { background-color: #252525 !important; color: white !important; border: 1px solid #444 !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE INTEGRAÇÃO ---

def testar_central_frete_todas_urls(dados):
    """
    Testa as 3 URLs possíveis da Central do Frete para descobrir a certa.
    """
    token = os.getenv("CENTRAL_TOKEN", "").strip()
    
    if not token:
        return [{"Transportadora": "⚠️ CONFIG", "Preço Final": "Sem Token", "Prazo": "-", "Tipo": "Adicione o Token no Dokploy"}]

    # Lista de tentativas baseada na documentação oficial e padrões
    urls_tentativa = [
        # 1. Padrão API REST (Mais provável)
        {"url": "https://api.centraldofrete.com/v1/cotacao", "method": "POST", "auth": "Header"},
        # 2. Padrão com Token na URL (Comum em integrações antigas deles)
        {"url": f"https://api.centraldofrete.com/v1/cotacao?token={token}", "method": "POST", "auth": "Query"},
        # 3. Subdomínio Quotation (Visto em plugins)
        {"url": f"https://quotation.centraldofrete.com/v1/cotacao?token={token}", "method": "POST", "auth": "Query"}
    ]
    
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

    headers_padrao = {"Content-Type": "application/json"}
    headers_auth = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    resultados_debug = []

    for tentativa in urls_tentativa:
        try:
            # Decide qual header usar
            h = headers_auth if tentativa['auth'] == "Header" else headers_padrao
            
            req = requests.post(tentativa['url'], headers=h, json=payload, timeout=5)
            
            # Se deu certo (200), processa e retorna IMEDIATAMENTE
            if req.status_code == 200:
                data = req.json()
                opcoes = data.get('cotacao', {}).get('opcoes', [])
                
                lista_sucesso = []
                for op in opcoes:
                    lista_sucesso.append({
                        "Transportadora": op.get('transportadora', 'Central'),
                        "Preço Final": f"R$ {op.get('valor_frete', 0):.2f}",
                        "Prazo": f"{op.get('prazo_dias')} dias",
                        "Tipo": "Central do Frete (API OK)"
                    })
                if lista_sucesso:
                    return lista_sucesso # SUCESSO! Encontramos a URL certa.

            # Se falhou, guarda o erro para mostrar na tabela se todas falharem
            resultados_debug.append({
                "Transportadora": f"Tentativa {tentativa['auth']}",
                "Preço Final": f"Status {req.status_code}",
                "Prazo": "Falhou",
                "Tipo": f"URL: {tentativa['url'][:25]}..."
            })
            
        except Exception as e:
            resultados_debug.append({
                "Transportadora": "Erro Conexão",
                "Preço Final": "Exception",
                "Prazo": "-",
                "Tipo": str(e)[:20]
            })

    # Se chegou aqui, nenhuma URL funcionou. Mostra o relatório de erros.
    return resultados_debug

def cotar_braspress(dados):
    user = os.getenv("BRASPRESS_USER", "").strip()
    pwd = os.getenv("BRASPRESS_PASS", "").strip()
    
    if not user or not pwd:
        return {"simulado": True}

    url = "https://api.braspress.com/v1/cotacao/calcular/json"
    auth_header = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    
    try:
        req = requests.post(url, headers={"Authorization": f"Basic {auth_header}", "Content-Type": "application/json"}, json={
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

def simular_frete(nome, cep_origem, cep_destino, peso, valor):
    try: dist = abs(int(cep_origem[:5]) - int(cep_destino[:5])) / 1000
    except: dist = 50
    return 45.00 + (peso * 0.9) + (valor * 0.005) + (dist * 0.1), random.randint(3, 7)

# --- INTERFACE ---
st.title("🚚 Central do Frete (Diagnostic Mode)")

with st.form("form"):
    c1, c2, c3, c4 = st.columns(4)
    cep_origem = c1.text_input("CEP Origem", "01001-000")
    cep_dest = c2.text_input("CEP Destino")
    cnpj = c3.text_input("CNPJ Destino")
    valor = c4.number_input("Valor", 100.0)
    
    d1, d2, d3, d4, d5 = st.columns(5)
    peso = d1.number_input("Peso kg", 1.0)
    alt = d2.number_input("Alt cm", 64.0)
    larg = d3.number_input("Larg cm", 40.0)
    comp = d4.number_input("Comp cm", 15.0)
    qtd = d5.number_input("Qtd", 5)
    
    if st.form_submit_button("COTAR AGORA"):
        if not cep_dest:
            st.warning("Preencha o CEP Destino")
        else:
            dados = {"cep_origem": cep_origem, "cep_dest": cep_dest, "cnpj_dest": cnpj or "00000000000000", "valor": valor, "peso_real": peso*qtd, "qtd": qtd, "alt": alt, "larg": larg, "comp": comp}
            
            lista = []
            
            # 1. Teste Central do Frete (Vai tentar 3 URLs)
            lista.extend(testar_central_frete_todas_urls(dados))
            
            # 2. Braspress
            res_bp = cotar_braspress(dados)
            if not res_bp['simulado']:
                lista.append({"Transportadora": "BRASPRESS", "Preço Final": f"R$ {res_bp['preco']:.2f}", "Prazo": f"{res_bp['prazo']} dias", "Tipo": "API Oficial"})
            elif not any("Central" in x['Tipo'] for x in lista): # Só adiciona simulada se a Central não trouxe ela
                 v, p = simular_frete("BRASPRESS", cep_origem, cep_dest, dados['peso_real'], valor)
                 lista.append({"Transportadora": "BRASPRESS", "Preço Final": f"R$ {v:.2f}", "Prazo": f"{p} dias", "Tipo": "Simulador"})

            # 3. Outras Simuladas
            for t in ["RODONAVES", "JAMEF", "TW", "GLOBAL"]:
                 v, p = simular_frete(t, cep_origem, cep_dest, dados['peso_real'], valor)
                 lista.append({"Transportadora": t, "Preço Final": f"R$ {v:.2f}", "Prazo": f"{p} dias", "Tipo": "Simulador"})
            
            st.dataframe(pd.DataFrame(lista), use_container_width=True)
