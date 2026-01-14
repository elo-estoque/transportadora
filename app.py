import streamlit as st
import pandas as pd
import requests
import base64
import time
import os
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

# --- FUNÇÕES AUXILIARES ---
def calcular_metricas(peso_unit, alt, larg, comp, qtd):
    vol_m3 = (alt/100 * larg/100 * comp/100) * qtd
    peso_cubado = vol_m3 * 300
    peso_real_total = peso_unit * qtd
    peso_taxavel = max(peso_real_total, peso_cubado)
    return peso_taxavel, vol_m3

# --- INTEGRAÇÃO 1: BRASPRESS (DIRETA) ---
def cotar_braspress(dados):
    user = os.getenv("BRASPRESS_USER")
    pwd = os.getenv("BRASPRESS_PASS")
    
    if not user or not pwd:
        return {"simulado": True, "erro": "Credenciais ENV ausentes"}

    url = "https://api.braspress.com/v1/cotacao/calcular/json"
    credentials = f"{user}:{pwd}"
    auth_header = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "cnpjRemetente": 12345678000199, # SEU CNPJ AQUI
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
                "transportadora": "BRASPRESS"
            }
        return {"simulado": True, "erro": f"Status {req.status_code}"}
    except:
        return {"simulado": True, "erro": "Conexão"}

# --- INTEGRAÇÃO 2: CENTRAL DO FRETE (HUB) - COM DEBUG ---
def cotar_central_frete(dados):
    """
    Tenta conectar na Central do Frete.
    Se falhar, retorna o erro visível para a tabela.
    """
    token = os.getenv("CENTRAL_TOKEN")
    
    # 1. Teste de Token (Verifica se o Dokploy leu a variável)
    if not token:
        return [{
            "Transportadora": "⚠️ ERRO CONFIG",
            "Preço Final": "---",
            "Prazo": "---",
            "Tipo": "TOKEN NÃO ENCONTRADO"
        }]

    url = "https://api.centraldofrete.com/v1/cotacao"
    headers = {
        "Authorization": f"Bearer {token}", # Bearer é o padrão deles
        "Content-Type": "application/json"
    }
    
    # Payload rigoroso para evitar erro 400
    payload = {
        "cep_origem": str(dados['cep_origem']).replace("-",""),
        "cep_destino": str(dados['cep_dest']).replace("-",""),
        "valornotafiscal": float(dados['valor']),
        "volumes": [{
            "peso": float(dados['peso_real']) / int(dados['qtd']), # Peso unitário
            "altura": int(dados['alt']),     
            "largura": int(dados['larg']),
            "comprimento": int(dados['comp']),
            "quantidade": int(dados['qtd'])
        }]
    }

    try:
        req = requests.post(url, headers=headers, json=payload, timeout=8)
        
        # 2. Sucesso
        if req.status_code == 200:
            data = req.json()
            opcoes = data.get('cotacao', {}).get('opcoes', [])
            
            if not opcoes:
                return [{
                    "Transportadora": "Central Frete",
                    "Preço Final": "R$ 0.00",
                    "Prazo": "-",
                    "Tipo": "Sem opções de frete disponíveis"
                }]
                
            resultados = []
            for op in opcoes:
                resultados.append({
                    "Transportadora": op.get('transportadora', 'Central'),
                    "Preço Final": f"R$ {op.get('valor_frete', 0):.2f}",
                    "Prazo": f"{op.get('prazo_dias')} dias",
                    "Tipo": "Central do Frete (API)"
                })
            return resultados
        
        # 3. Erro de Resposta da API
        else:
            return [{
                "Transportadora": "⚠️ ERRO API",
                "Preço Final": f"Status {req.status_code}",
                "Prazo": "-",
                "Tipo": f"Msg: {req.text[:30]}" # Mostra o começo do erro
            }]
            
    except Exception as e:
        # 4. Erro de Conexão/Código
        return [{
            "Transportadora": "⚠️ ERRO CRÍTICO",
            "Preço Final": "---",
            "Prazo": "-",
            "Tipo": str(e)[:40]
        }]

# --- SIMULADOR (FALLBACK) ---
def simular_frete(nome, cep_origem, cep_destino, peso, valor):
    try:
        dist = abs(int(cep_origem[:5]) - int(cep_destino[:5])) / 1000
    except:
        dist = 50
    
    base = 45.00
    frete = base + (peso * 0.9) + (valor * 0.005) + (dist * 0.1)
    return frete, random.randint(3, 7)

# --- INTERFACE PRINCIPAL ---
st.title("🚚 Central do Frete Integrada (Debug Mode)")

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
        with st.spinner("Processando APIs..."):
            
            dados_carga = {
                "cep_origem": cep_origem, 
                "cep_dest": cep_dest, 
                "cnpj_dest": cnpj if cnpj else "00000000000000",
                "valor": valor_nota, 
                "peso_real": peso * qtd, 
                "qtd": qtd,
                "alt": alt, "larg": larg, "comp": comp
            }
            
            lista_final = []
            
            # 1. Tenta Central do Frete (Prioridade)
            # Retorna lista de transportadoras OU erro visível
            res_central = cotar_central_frete(dados_carga)
            lista_final.extend(res_central)
            
            # 2. Tenta Braspress Direta (Se configurado)
            res_bp = cotar_braspress(dados_carga)
            if not res_bp['simulado']:
                lista_final.append({
                    "Transportadora": res_bp['transportadora'],
                    "Preço Final": f"R$ {res_bp['preco']:.2f}",
                    "Prazo": f"{res_bp['prazo']} dias",
                    "Tipo": "API Direta"
                })
            else:
                # Se falhar a Braspress direta, adiciona simulada
                v, p = simular_frete("BRASPRESS", cep_origem, cep_dest, dados_carga['peso_real'], valor_nota)
                lista_final.append({"Transportadora": "BRASPRESS", "Preço Final": f"R$ {v:.2f}", "Prazo": f"{p} dias", "Tipo": "Simulador (Sem Key)"})

            # 3. Adiciona Simuladores para as outras que ainda não temos API
            for t in ["RODONAVES", "JAMEF", "TW", "GLOBAL"]:
                # Verifica se essa transp já veio pela Central do Frete para não duplicar
                ja_tem = any(t.upper() in item['Transportadora'].upper() for item in lista_final)
                
                if not ja_tem:
                    v, p = simular_frete(t, cep_origem, cep_dest, dados_carga['peso_real'], valor_nota)
                    lista_final.append({
                        "Transportadora": t,
                        "Preço Final": f"R$ {v:.2f}",
                        "Prazo": f"{p} dias",
                        "Tipo": "Simulador (Sem Key)"
                    })

            # Exibe
            st.divider()
            
            # Filtra valores válidos para o KPI de "Melhor Preço"
            vals = []
            for x in lista_final:
                try:
                    v = float(x['Preço Final'].replace('R$ ','').replace(',','.'))
                    if v > 0: vals.append(v)
                except: pass
            
            melhor = min(vals) if vals else 0
            peso_tax, _ = calcular_metricas(peso, alt, larg, comp, qtd)

            k1, k2, k3 = st.columns(3)
            k1.markdown(f"<div class='metric-card'><h3>Peso Taxável</h3><h1>{peso_tax:.2f} kg</h1></div>", unsafe_allow_html=True)
            k2.markdown(f"<div class='metric-card'><h3>Opções Encontradas</h3><h1>{len(lista_final)}</h1></div>", unsafe_allow_html=True)
            k3.markdown(f"<div class='metric-card'><h3>Melhor Preço</h3><h1 style='color:#E31937'>R$ {melhor:.2f}</h1></div>", unsafe_allow_html=True)
            
            st.write("")
            df = pd.DataFrame(lista_final)
            
            # Formatação condicional simples para destacar erros
            st.dataframe(df, use_container_width=True, hide_index=True)
