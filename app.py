import pandas as pd
import glob
import os
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font

# ==============================================================================
# 1. CONFIGURAÇÃO DE CORES (CÓDIGOS HEX REAIS)
# ==============================================================================
# IMPORTANTE: Não use '#' na frente para garantir compatibilidade total
REGRAS = {
    'nome_fantasia': 'ADD8E6',       # Azul Claro
    'website': 'E6E6FA',             # Lavanda
    'cnpj': 'FFFFE0',                # Amarelo Claro
    'cidade': 'F0FFF0',              # Verde bem claro
    'estado': 'F5F5DC',              # Bege
    'telefone_1': 'FFB6C1',          # Vermelho Claro (Alerta)
    'email_1': 'FFD700',             # Dourado (Alerta)
    'telefone_2': 'FFC0CB',          # Rosa
    'representante_nome': '98FB98',  # Verde Pálido
    'representante_email': 'FFA07A', # Salmão
    'categoria_nome': 'D3D3D3'       # Cinza
}

ARQUIVO_SAIDA = "Consolidado_Final_Cores_Reais.xlsx"

# ==============================================================================
# 2. CONSOLIDAÇÃO DOS DADOS
# ==============================================================================
print("🔄 Lendo arquivos...")
arquivos = glob.glob("Clientes_*.xlsx")
lista_dfs = []

if not arquivos:
    print("❌ Nenhum arquivo encontrado.")
else:
    # Ler todos os arquivos e juntar
    for arquivo in arquivos:
        try:
            df = pd.read_excel(arquivo)
            # Cria a coluna com nome do vendedor
            nome = os.path.basename(arquivo).replace('.xlsx', '').replace('Clientes_', '')
            df['Vendedor_Origem'] = nome
            lista_dfs.append(df)
        except Exception as e:
            print(f"Erro ao ler {arquivo}: {e}")

    if lista_dfs:
        df_final = pd.concat(lista_dfs, ignore_index=True)

        # Salva o arquivo "cru" primeiro, deixando espaço em cima para a legenda
        print("💾 Salvando dados...")
        linhas_pulo = len(REGRAS) + 2
        df_final.to_excel(ARQUIVO_SAIDA, index=False, startrow=linhas_pulo)

        # ==============================================================================
        # 3. PINTURA DIRETA (MÉTODO INFALÍVEL)
        # ==============================================================================
        print("🎨 Pintando células (Modo Compatibilidade Total)...")
        
        # Carrega o arquivo Excel para edição manual
        wb = load_workbook(ARQUIVO_SAIDA)
        ws = wb.active

        # Descobre qual número de coluna (1, 2, 3...) corresponde a qual nome ('email', 'cnpj'...)
        mapa_colunas = {}
        linha_cabecalho = linhas_pulo + 1
        
        # Lê o cabeçalho para mapear as colunas
        for celula in ws[linha_cabecalho]:
            if celula.value:
                mapa_colunas[celula.value] = celula.column

        # Itera sobre TODAS as linhas de dados
        for row in ws.iter_rows(min_row=linha_cabecalho + 1):
            for col_nome, cor_hex in REGRAS.items():
                
                # Se a coluna existe no arquivo
                if col_nome in mapa_colunas:
                    idx_coluna = mapa_colunas[col_nome]
                    celula = row[idx_coluna - 1] # Pega a célula exata
                    
                    # Verifica se está vazio (None ou texto vazio)
                    valor = celula.value
                    if valor is None or str(valor).strip() == "":
                        # APLICA A COR (Isso força o Excel/Sheets a mostrar a cor)
                        celula.fill = PatternFill(start_color=cor_hex, end_color=cor_hex, fill_type="solid")

        # ==============================================================================
        # 4. CRIAR LEGENDA
        # ==============================================================================
        ws['A1'] = "LEGENDA DE DADOS FALTANTES:"
        ws['A1'].font = Font(bold=True, size=12)

        linha_legenda = 2
        for col_nome, cor_hex in REGRAS.items():
            # Texto da legenda
            ws.cell(row=linha_legenda, column=1).value = f"Campo '{col_nome}' Vazio"
            
            # Pinta a célula ao lado para mostrar a cor
            celula_cor = ws.cell(row=linha_legenda, column=2)
            celula_cor.fill = PatternFill(start_color=cor_hex, end_color=cor_hex, fill_type="solid")
            
            linha_legenda += 1

        print("💾 Salvando arquivo final colorido...")
        wb.save(ARQUIVO_SAIDA)
        print(f"🚀 CONCLUÍDO! Baixe o arquivo: {ARQUIVO_SAIDA}")

    else:
        print("❌ Nenhum dado para gerar.")
