
import streamlit as st
import pandas as pd
import plotly.express as px
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import json

# Configuração inicial da página
st.set_page_config(layout="wide", page_title="TalentMatch AI", page_icon="✨")

# =============================================================================
# FUNÇÕES DE CARREGAMENTO DE DADOS (Compatíveis com Streamlit)
# =============================================================================

@st.cache_data(show_spinner=False, ttl=3600)
def baixar_json_direto(url):
    """Baixa JSON diretamente sem salvar arquivo"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"❌ ERRO ao baixar dados: {e}")
        return None

@st.cache_data(show_spinner=False)
def carregar_dados_completos():
    """Carrega e processa todos os dados do Google Drive"""
    # URLs do Google Drive
    PROSPECTS_URL = "https://drive.google.com/uc?id=1f_NPd0qA0iqqo9Im9FfQi78esPOlf1Bu"
    APPLICANTS_URL = "https://drive.google.com/uc?id=1jgiuRW402WUp-b5w1yE6nHrfR4KjFuzT"
    VAGAS_URL = "https://drive.google.com/uc?id=1hmUUdyuAd9hoM84drSXJrQ8EbvFsPEDb"
    
    with st.spinner("📥 Baixando dados do Google Drive..."):
        prospects_data = baixar_json_direto(PROSPECTS_URL)
        applicants_data = baixar_json_direto(APPLICANTS_URL)
        vagas_data = baixar_json_direto(VAGAS_URL)
    
    if not all([prospects_data, applicants_data, vagas_data]):
        st.error("❌ Falha no download de um ou mais arquivos.")
        return None

    with st.spinner("🔄 Processando candidaturas..."):
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
        TAMANHO_AMOSTRA = 5000
        if TAMANHO_AMOSTRA and len(df_final) > TAMANHO_AMOSTRA:
            df_final = df_final.sample(n=TAMANHO_AMOSTRA, random_state=42)
        
        # Limpeza final
        for col in df_final.columns:
            if df_final[col].dtype == 'object':
                df_final[col] = df_final[col].fillna('Não informado')
    
    return df_final

def carregar_dados():
    """Função principal para carregar dados"""
    if 'dados_processados' not in st.session_state:
        df = carregar_dados_completos()
        if df is not None:
            st.session_state.dados_processados = df
            return df
        else:
            return None
    return st.session_state.dados_processados

# =============================================================================
# FUNÇÕES DE IA E PROCESSAMENTO
# =============================================================================

@st.cache_resource
def carregar_encoder():
    return SentenceTransformer("all-MiniLM-L6-v2")

def calcular_compatibilidade(texto_vaga, texto_cv):
    """Calcula compatibilidade entre vaga e CV usando embeddings"""
    if not isinstance(texto_vaga, str) or not isinstance(texto_cv, str) or not texto_vaga or not texto_cv:
        return 0.0
    embeddings = text_encoder.encode([texto_vaga, texto_cv])
    return cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

# =============================================================================
# INTERFACE PRINCIPAL
# =============================================================================

# Cabeçalho
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    st.title("✨ TalentMatch AI")

st.markdown("Análise de IA para encontrar os **candidatos ideais** para cada vaga.")

# Sidebar com estatísticas
st.sidebar.header("📊 Estatísticas da Base")

# Carregar dados
df_completo = carregar_dados()
text_encoder = carregar_encoder()

# Inicializar estados da sessão
if 'pagina_atual_analise' not in st.session_state:
    st.session_state.pagina_atual_analise = 1

if 'resultados_analise' not in st.session_state:
    st.session_state.resultados_analise = None

ITENS_POR_PAGINA_ANALISE = 10

# =============================================================================
# SEÇÃO PRINCIPAL DE ANÁLISE
# =============================================================================

st.header("🔍 Análise de Vaga Específica")

if df_completo is not None:
    # Atualizar sidebar com estatísticas
    df_com_nome = df_completo[
        (df_completo['candidato_nome'].notna()) & 
        (df_completo['candidato_nome'] != 'Não informado') & 
        (df_completo['candidato_nome'] != '') &
        (df_completo['candidato_nome'] != 'nan')
    ].copy()
    
    st.sidebar.write(f"📊 Total de candidaturas: {len(df_completo)}")
    st.sidebar.write(f"👤 Candidatos com nome: {len(df_com_nome)}")
    st.sidebar.write(f"🏢 Vagas diferentes: {df_completo['vaga_id'].nunique()}")
    st.sidebar.write(f"📝 Títulos de vaga: {df_completo['vaga_titulo'].nunique()}")

    if len(df_com_nome) == 0:
        st.warning("⚠️ Nenhum candidato com nome informado encontrado na base de dados!")
    else:
        # Seção de busca de vagas
        st.write("### 🔍 Buscar Vaga")
        st.info("💡 **Use um ou ambos os campos abaixo para buscar vagas. Não é necessário preencher os dois.**")
        
        reset_key_suffix = st.session_state.get('reset_count', 0)
        
        col_busca1, col_busca2, col_busca3 = st.columns([2, 2, 1])
        
        with col_busca1:
            todas_vagas = sorted(df_com_nome['vaga_titulo'].dropna().unique())
            vaga_selecionada_titulo = st.selectbox(
                'Buscar por Título da Vaga',
                options=[''] + todas_vagas,
                help="Selecione uma vaga pelo título",
                key=f'vaga_titulo_{reset_key_suffix}'
            )
        
        with col_busca2:
            todas_vagas_ids = sorted(df_com_nome['vaga_id'].dropna().unique())
            vaga_selecionada_id = st.selectbox(
                'Buscar por ID da Vaga',
                options=[''] + todas_vagas_ids,
                help="Selecione uma vaga pelo ID",
                format_func=lambda x: f"ID: {x}" if x else "",
                key=f'vaga_id_{reset_key_suffix}'
            )
        
        with col_busca3:
            st.write("")  
            st.write("")  
            if st.button("🗑️ Limpar Buscas", use_container_width=True):
                st.session_state.reset_count = reset_key_suffix + 1
                st.session_state.resultados_analise = None
                st.session_state.pagina_atual_analise = 1
                st.rerun()
        
        # Determinar critério de busca
        vaga_para_analise = None
        if vaga_selecionada_titulo and vaga_selecionada_id:
            st.info(f"🔍 Buscando pela vaga com ID: **{vaga_selecionada_id}**")
            vaga_para_analise = vaga_selecionada_id
            tipo_busca = "ID"
        elif vaga_selecionada_id:
            st.info(f"🔍 Buscando pela vaga com ID: **{vaga_selecionada_id}**")
            vaga_para_analise = vaga_selecionada_id
            tipo_busca = "ID"
        elif vaga_selecionada_titulo:
            st.info(f"🔍 Buscando pela vaga: **{vaga_selecionada_titulo}**")
            vaga_para_analise = vaga_selecionada_titulo
            tipo_busca = "título"
        else:
            if st.session_state.resultados_analise is None:
                st.warning("⚠️ Selecione pelo menos um critério de busca (título ou ID da vaga)")
        
        # Botão de análise
        col_analise1, col_analise2 = st.columns([3, 1])
        with col_analise1:
            if vaga_para_analise and st.button("Analisar Candidatos", type="primary", use_container_width=True):
                if tipo_busca == "ID":
                    df_vaga = df_com_nome[df_com_nome['vaga_id'] == vaga_para_analise].copy()
                    titulo_vaga = df_vaga['vaga_titulo'].iloc[0] if len(df_vaga) > 0 else f"ID: {vaga_para_analise}"
                else:
                    df_vaga = df_com_nome[df_com_nome['vaga_titulo'] == vaga_para_analise].copy()
                    titulo_vaga = vaga_para_analise
                
                st.success(f"**Vaga encontrada:** {titulo_vaga} | **Candidatos com nome:** {len(df_vaga)}")
                
                if len(df_vaga) == 0:
                    st.warning("Nenhum candidato com nome informado para esta vaga.")
                    st.session_state.resultados_analise = None
                else:
                    with st.spinner("Analisando currículos com IA... Isso pode levar um momento."):
                        texto_vaga_base = df_vaga['vaga_competencias'].iloc[0] if 'vaga_competencias' in df_vaga.columns else ""
                        df_vaga['compatibilidade'] = df_vaga['candidato_cv'].apply(
                            lambda cv: calcular_compatibilidade(texto_vaga_base, cv)
                        )
                        df_vaga = df_vaga.sort_values('compatibilidade', ascending=False)
                    
                    st.session_state.resultados_analise = {
                        'df_vaga': df_vaga,
                        'titulo_vaga': titulo_vaga,
                        'tipo_busca': tipo_busca
                    }
                    st.session_state.pagina_atual_analise = 1
                    st.rerun()
        
        with col_analise2:
            if st.session_state.resultados_analise is not None:
                if st.button("🔄 Nova Análise", use_container_width=True):
                    st.session_state.resultados_analise = None
                    st.session_state.pagina_atual_analise = 1
                    st.rerun()
        
        # Exibir resultados
        if st.session_state.resultados_analise is not None:
            resultados = st.session_state.resultados_analise
            df_vaga = resultados['df_vaga']
            titulo_vaga = resultados['titulo_vaga']
            
            st.subheader(f"Resultados para: {titulo_vaga}")
            
            # Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Candidatos", len(df_vaga))
            with col2:
                st.metric("Compatibilidade Média", f"{df_vaga['compatibilidade'].mean()*100:.1f}%")
            with col3:
                top_score = df_vaga['compatibilidade'].max() * 100
                st.metric("Maior Compatibilidade", f"{top_score:.1f}%")

            # Paginação
            total_paginas = max(1, (len(df_vaga) + ITENS_POR_PAGINA_ANALISE - 1) // ITENS_POR_PAGINA_ANALISE)
            inicio = (st.session_state.pagina_atual_analise - 1) * ITENS_POR_PAGINA_ANALISE
            fim = inicio + ITENS_POR_PAGINA_ANALISE
            df_vaga_pagina = df_vaga.iloc[inicio:fim]

            if total_paginas > 1:
                col_pag_prev, col_pag_info, col_pag_next = st.columns([1, 2, 1])
                with col_pag_prev:
                    if st.button("⏪ Página Anterior", key="prev_analise", disabled=st.session_state.pagina_atual_analise == 1):
                        st.session_state.pagina_atual_analise -= 1
                        st.rerun()
                with col_pag_info:
                    st.write(f"Página {st.session_state.pagina_atual_analise} de {total_paginas} | Candidatos {inicio+1}-{min(fim, len(df_vaga))} de {len(df_vaga)}")
                with col_pag_next:
                    if st.button("Próxima Página ⏩", key="next_analise", disabled=st.session_state.pagina_atual_analise == total_paginas):
                        st.session_state.pagina_atual_analise += 1
                        st.rerun()

            # Lista de candidatos
            st.subheader("🎯 Candidatos Recomendados")
            
            for index, candidato in df_vaga_pagina.iterrows():
                score_percent = candidato['compatibilidade'] * 100
                
                if score_percent > 70:
                    border_color = "success"
                    emoji = "⭐"
                elif score_percent > 40:
                    border_color = "warning" 
                    emoji = "✅"
                else:
                    border_color = "secondary"
                    emoji = "👤"

                with st.container(border=True):
                    col_nome, col_score = st.columns([3, 1])
                    with col_nome:
                        st.markdown(f"{emoji} **{candidato['candidato_nome']}**")
                        
                        situacao = candidato.get('situacao_candidado', 'Não informado')
                        if pd.isna(situacao) or situacao in ['', 'nan']:
                            situacao = 'Não informado'
                        st.caption(f"📋 Situação: {situacao}")
                        st.caption(f"🆔 ID: {candidato.get('candidato_id', 'N/A')}")
                    
                    with col_score:
                        if score_percent > 70:
                            st.metric("Compatibilidade", f"{score_percent:.1f}%", "Excelente", delta_color="off")
                        elif score_percent > 50:
                            st.metric("Compatibilidade", f"{score_percent:.1f}%", "Boa", delta_color="off")
                        elif score_percent > 30:
                            st.metric("Compatibilidade", f"{score_percent:.1f}%", "Média", delta_color="off")
                        else:
                            st.metric("Compatibilidade", f"{score_percent:.1f}%", "Baixa", delta_color="off")
                    
                    with st.expander("📄 Ver detalhes completos"):
                        st.write(f"**ID do Candidato:** {candidato.get('candidato_id', 'N/A')}")
                        st.write(f"**ID da Vaga:** {candidato.get('vaga_id', 'N/A')}")
                        st.write(f"**Situação:** {situacao}")
                        
                        cv_preview = candidato.get('candidato_cv', '')
                        if cv_preview and cv_preview != 'Não informado':
                            st.write("**Currículo Completo:**")
                            st.text_area(
                                "Conteúdo do CV:",
                                cv_preview,
                                height=300,
                                key=f"cv_{candidato.get('candidato_id')}_{index}",
                                label_visibility="collapsed"
                            )
                            col_cv1, col_cv2 = st.columns(2)
                            with col_cv1:
                                st.caption(f"📏 Tamanho: {len(cv_preview)} caracteres")
                            with col_cv2:
                                st.caption(f"📄 Palavras: {len(cv_preview.split())}")
                        else:
                            st.write("**CV:** Não informado")

else:
    st.error("❌ Não foi possível carregar os dados. Verifique a conexão com a internet.")
