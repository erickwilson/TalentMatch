# preprocess.py (Versão Corrigida - Download do Google Drive)
import pandas as pd
import requests
import json
import warnings
import os

warnings.filterwarnings('ignore', category=FutureWarning)

# =============================================================================
# CONFIGURAÇÕES DO GOOGLE DRIVE
# =============================================================================
# URLs dos arquivos no Google Drive (convertidas para download direto)
PROSPECTS_URL = "https://drive.google.com/uc?id=1f_nPd0qA0iqqo9Im9FfQi78esPOlf1Bu"
APPLICANTS_URL = "https://drive.google.com/uc?id=1jgiuRW402WUp-b5w1yE6nHrfR4KjFuzT"
VAGAS_URL = "https://drive.google.com/uc?id=1hmUUdyuAd9hoM84drSXJrQ8EbvFsPEDb"
OUTPUT_FILE = "dados_processados.parquet"

# --- CONTROLE DE AMOSTRAGEM PARA TESTES ---
TAMANHO_AMOSTRA = 5000 
# -------------------------------------------

def baixar_json_do_drive(url, nome_arquivo):
    """Baixa e salva um arquivo JSON do Google Drive"""
    try:
        print(f"📥 Baixando {nome_arquivo}...")
        response = requests.get(url)
        response.raise_for_status()
        
        # Salvar o arquivo localmente
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"✅ {nome_arquivo} baixado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO ao baixar {nome_arquivo}: {e}")
        return False

def carregar_json_local(nome_arquivo):
    """Carrega um arquivo JSON local"""
    try:
        with open(nome_arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        print(f"✅ {nome_arquivo} carregado! ({len(dados) if isinstance(dados, dict) else 'N/A'} registros)")
        return dados
    except Exception as e:
        print(f"❌ ERRO ao carregar {nome_arquivo}: {e}")
        return None

def criar_base_de_dados_unificada():
    """Carrega, combina e limpa os 3 arquivos JSON do Google Drive"""
    print("--- INICIANDO PRÉ-PROCESSAMENTO DO GOOGLE DRIVE ---")
    
    # Nomes dos arquivos temporários
    prospects_file = "prospects_temp.json"
    applicants_file = "applicants_temp.json"
    vagas_file = "vagas_temp.json"
    
    try:
        print("1/3: Baixando todos os arquivos JSON do Google Drive...")
        
        # Baixar todos os arquivos
        success_prospects = baixar_json_do_drive(PROSPECTS_URL, prospects_file)
        success_applicants = baixar_json_do_drive(APPLICANTS_URL, applicants_file)
        success_vagas = baixar_json_do_drive(VAGAS_URL, vagas_file)
        
        # Verificar se todos os downloads foram bem sucedidos
        if not all([success_prospects, success_applicants, success_vagas]):
            print("❌ Falha no download de um ou mais arquivos. Processamento interrompido.")
            return

        # Carregar os arquivos baixados
        prospects_data = carregar_json_local(prospects_file)
        applicants_data = carregar_json_local(applicants_file)
        vagas_data = carregar_json_local(vagas_file)
        
        if not all([prospects_data, applicants_data, vagas_data]):
            print("❌ Falha ao carregar um ou mais arquivos. Processamento interrompido.")
            return

    except Exception as e:
        print(f"❌ ERRO CRÍTICO no processamento: {e}")
        return

    print("2/3: Processando e combinando as candidaturas...")
    candidaturas_list = []
    
    # Debug: contar candidatos com e sem nome
    total_candidatos = 0
    candidatos_com_nome = 0
    
    for vaga_id, data in prospects_data.items():
        for prospect in data.get('prospects', []):
            candidato_id = str(prospect.get('codigo'))
            applicant_details = applicants_data.get(candidato_id, {})
            vaga_details = vagas_data.get(vaga_id, {})
            
            # Usar 'infos_basicas' em vez de 'infosbasicas'
            infos_basicas = applicant_details.get('infos_basicas', {})
            nome_candidato = infos_basicas.get('nome')
            
            total_candidatos += 1
            if nome_candidato:
                candidatos_com_nome += 1

            candidaturas_list.append({
                'candidato_id': candidato_id,
                'vaga_id': vaga_id,
                'situacao_candidado': prospect.get('situacao_candidado'),
                'candidato_nome': nome_candidato,
                'candidato_cv': applicant_details.get('cv_pt'),  # cv_pt em vez de cvpt
                'vaga_titulo': vaga_details.get('informacoes_basicas', {}).get('titulo_vaga'),
                'vaga_competencias': vaga_details.get('perfil_vaga', {}).get('competencia_tecnicas_e_comportamentais'),
            })
            
    df_final = pd.DataFrame(candidaturas_list)
    print(f"Foram encontradas {len(df_final)} candidaturas no total.")
    print(f"Candidatos com nome: {candidatos_com_nome}")
    print(f"Candidatos sem nome: {total_candidatos - candidatos_com_nome}")

    # --- APLICAÇÃO DA AMOSTRAGEM ---
    if TAMANHO_AMOSTRA and len(df_final) > TAMANHO_AMOSTRA:
        print(f"Aplicando amostragem aleatória para {TAMANHO_AMOSTRA} candidaturas...")
        df_final = df_final.sample(n=TAMANHO_AMOSTRA, random_state=42)
    # -----------------------------

    print("3/3: Limpando e salvando o arquivo de dados final...")
    for col in df_final.columns:
        if df_final[col].dtype == 'object':
            df_final[col] = df_final[col].fillna('Não informado')
    
    df_final.to_parquet(OUTPUT_FILE, index=False)
    print(f"\n✅ Base de dados unificada com {len(df_final)} registros salva com sucesso em '{OUTPUT_FILE}'!")
    
    # Limpar arquivos temporários
    try:
        os.remove(prospects_file)
        os.remove(applicants_file)
        os.remove(vagas_file)
        print("🧹 Arquivos temporários removidos.")
    except:
        print("⚠️ Não foi possível remover alguns arquivos temporários.")
    
    # Estatísticas finais
    print("\n📊 ESTATÍSTICAS FINAIS:")
    print(f"Total de candidaturas processadas: {len(df_final)}")
    print(f"Colunas disponíveis: {list(df_final.columns)}")
    
    if 'situacao_candidado' in df_final.columns:
        print(f"\nDistribuição por situação:")
        print(df_final['situacao_candidado'].value_counts().head(10))

def verificar_dados_existentes():
    """Verifica se já existe o arquivo processado"""
    if os.path.exists(OUTPUT_FILE):
        try:
            df = pd.read_parquet(OUTPUT_FILE)
            print(f"✅ Arquivo '{OUTPUT_FILE}' já existe! {len(df)} registros disponíveis.")
            return True
        except:
            print("⚠️ Arquivo existente corrompido. Recriando...")
            return False
    return False

if __name__ == "__main__":
    # Verificar se já temos os dados processados
    if verificar_dados_existentes():
        print("💡 Os dados já estão processados. Execute o Streamlit diretamente.")
        df = pd.read_parquet(OUTPUT_FILE)
        print(f"📊 Amostra dos dados:")
        print(df[['candidato_nome', 'vaga_titulo', 'situacao_candidado']].head())
    else:
        # Criar nova base de dados
        criar_base_de_dados_unificada()