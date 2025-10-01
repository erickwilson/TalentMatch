# preprocess.py (Versão Compatível com Streamlit)
import pandas as pd
import requests
import json
import warnings
import io
import streamlit as st

warnings.filterwarnings('ignore', category=FutureWarning)

# =============================================================================
# CONFIGURAÇÕES DO GOOGLE DRIVE
# =============================================================================
PROSPECTS_URL = "https://drive.google.com/uc?id=1f_NPd0qA0iqqo9Im9FfQi78esPOlf1Bu"
APPLICANTS_URL = "https://drive.google.com/uc?id=1jgiuRW402WUp-b5w1yE6nHrfR4KjFuzT"
VAGAS_URL = "https://drive.google.com/uc?id=1hmUUdyuAd9hoM84drSXJrQ8EbvFsPEDb"

# --- CONTROLE DE AMOSTRAGEM PARA TESTES ---
TAMANHO_AMOSTRA = 5000 

@st.cache_data(show_spinner=False, ttl=3600)
def baixar_json_direto(url):
    """Baixa JSON diretamente sem salvar arquivo (compatível com Streamlit)"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"❌ ERRO ao baixar dados: {e}")
        return None

@st.cache_data(show_spinner=False)
def criar_base_de_dados_unificada():
    """Carrega, combina e limpa os 3 arquivos JSON do Google Drive"""
    
    with st.spinner("📥 Baixando dados do Google Drive..."):
        # Baixar todos os arquivos diretamente
        prospects_data = baixar_json_direto(PROSPECTS_URL)
        applicants_data = baixar_json_direto(APPLICANTS_URL)
        vagas_data = baixar_json_direto(VAGAS_URL)
    
    if not all([prospects_data, applicants_data, vagas_data]):
        st.error("❌ Falha no download de um ou mais arquivos.")
        return None

    with st.spinner("🔄 Processando e combinando candidaturas..."):
        candidaturas_list = []
        
        for vaga_id, data in prospects_data.items():
            for prospect in data.get('prospects', []):
                candidato_id = str(prospect.get('codigo'))
                applicant_details = applicants_data.get(candidato_id, {})
                vaga_details = vagas_data.get(vaga_id, {})
                
                infos_basicas = applicant_details.get('infos_basicas', {})
                nome_candidato = infos_basicas.get('nome')

                candidaturas_list.append({
                    'candidato_id': candidato_id,
                    'vaga_id': vaga_id,
                    'situacao_candidado': prospect.get('situacao_candidado'),
                    'candidato_nome': nome_candidato,
                    'candidato_cv': applicant_details.get('cv_pt'),
                    'vaga_titulo': vaga_details.get('informacoes_basicas', {}).get('titulo_vaga'),
                    'vaga_competencias': vaga_details.get('perfil_vaga', {}).get('competencia_tecnicas_e_comportamentais'),
                })
                
        df_final = pd.DataFrame(candidaturas_list)
        
        # Aplicar amostragem se necessário
        if TAMANHO_AMOSTRA and len(df_final) > TAMANHO_AMOSTRA:
            df_final = df_final.sample(n=TAMANHO_AMOSTRA, random_state=42)
        
        # Limpeza final
        for col in df_final.columns:
            if df_final[col].dtype == 'object':
                df_final[col] = df_final[col].fillna('Não informado')
    
    return df_final

def carregar_dados():
    """Função principal para carregar dados no Streamlit"""
    
    # Verificar se os dados já estão em cache
    if 'dados_processados' not in st.session_state:
        with st.spinner("🔄 Carregando base de dados..."):
            df = criar_base_de_dados_unificada()
            if df is not None:
                st.session_state.dados_processados = df
                st.success(f"✅ Base de dados carregada! {len(df)} registros disponíveis.")
            else:
                st.error("❌ Falha ao carregar dados.")
                return None
    
    return st.session_state.dados_processados

# Função para usar diretamente no Streamlit
def main():
    """Exemplo de uso no Streamlit"""
    st.title("Sistema de Análise de Candidatos")
    
    df = carregar_dados()
    
    if df is not None:
        st.write(f"📊 Total de candidaturas: {len(df)}")
        st.write("### Amostra dos dados:")
        st.dataframe(df[['candidato_nome', 'vaga_titulo', 'situacao_candidado']].head(10))
        
        # Estatísticas
        st.write("### Estatísticas:")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Candidaturas Únicas", len(df))
        
        with col2:
            st.metric("Vagas Diferentes", df['vaga_id'].nunique())
        
        with col3:
            st.metric("Candidatos Únicos", df['candidato_id'].nunique())
        
        # Distribuição por situação
        st.write("### Distribuição por Situação:")
        situacao_counts = df['situacao_candidado'].value_counts()
        st.bar_chart(situacao_counts.head(10))

if __name__ == "__main__":
    main()
