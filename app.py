def cotar_central_frete(dados):
    token = os.getenv("CENTRAL_TOKEN", "").strip()
    if not token:
        return [{"Transportadora": "⚠️ CONFIG", "Preço Final": "---", "Prazo": "-", "Tipo": "Sem Token"}]

    # TENTATIVA 1: URL de Cotação Direta (A mais comum para integrações recentes)
    # Se esta falhar com 404, a documentação oficial da sua conta deve ser consultada
    url = "https://quotation.centraldofrete.com/v1/cotacao" 
    
    # Alguns endpoints exigem o token direto no header sem 'Bearer'
    headers = {
        "Authorization": token,  # Tente sem 'Bearer' se der erro 401
        "Content-Type": "application/json"
    }
    
    # Payload corrigido (chaves padronizadas)
    payload = {
        "cep_origem": str(dados['cep_origem']).replace("-",""),
        "cep_destino": str(dados['cep_dest']).replace("-",""),
        "valor_nf": float(dados['valor']), # Corrigido de valornotafiscal para valor_nf
        "tipo_veiculo": 1, # Frequentemente exigido (1 = caminhão, etc.)
        "volumes": [{
            "peso": float(dados['peso_real']) / int(dados['qtd']),
            "altura": int(dados['alt']),
            "largura": int(dados['larg']),
            "comprimento": int(dados['comp']),
            "quantidade": int(dados['qtd'])
        }]
    }

    try:
        req = requests.post(url, headers=headers, json=payload, timeout=10)
        
        # DEBUG: Mostra o erro real no terminal do Streamlit
        if req.status_code != 200:
            print(f"ERRO API: {req.text}") 
        
        if req.status_code == 200:
            data = req.json()
            # A estrutura de resposta pode variar, ajuste conforme o print(data)
            opcoes = data.get('cotacao', {}).get('opcoes', []) or data.get('opcoes', [])
            
            resultados = []
            for op in opcoes:
                resultados.append({
                    "Transportadora": op.get('transportadora', 'Central'),
                    "Preço Final": f"R$ {op.get('valor_frete', op.get('valor', 0)):.2f}",
                    "Prazo": f"{op.get('prazo_dias', op.get('prazo', '?'))} dias",
                    "Tipo": "API Central"
                })
            return resultados if resultados else [{"Transportadora": "Central", "Preço Final": "-", "Prazo": "-", "Tipo": "Sem opções"}]
            
        else:
            return [{"Transportadora": "⚠️ ERRO API", "Preço Final": f"{req.status_code}", "Prazo": "-", "Tipo": "Verificar Logs"}]

    except Exception as e:
        return [{"Transportadora": "⚠️ ERRO CRÍTICO", "Preço Final": "---", "Prazo": "-", "Tipo": str(e)[:20]}]
