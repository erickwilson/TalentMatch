import streamlit as st
import pandas as pd
import plotly.express as px
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Configuração inicial da página no Streamlit:
# Define o layout como "wide" (largura total), adiciona título e ícone da aplicação.
st.set_page_config(layout="wide", page_title="TalentMatch AI", page_icon="✨")

# Cabeçalho principal com logotipo e título estilizado.
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    st.title("✨ TalentMatch AI")

# Subtítulo descritivo para orientar o usuário sobre a funcionalidade da aplicação.
st.markdown("Análise de IA para encontrar os **candidatos ideais** para cada vaga.")

# Função para carregamento dos dados de candidatos e vagas.
# Utiliza cache para otimizar a performance, evitando a re-leitura do arquivo em cada execução.
@st.cache_data
def carregar_dados(caminho_arquivo="dados_processados.parquet"):
    try:
        df = pd.read_parquet(caminho_arquivo)

        # Mantém apenas registros de candidatos com nome informado e válido.
        df_com_nome = df[
            (df['candidato_nome'].notna()) & 
            (df['candidato_nome'] != 'Não informado') & 
            (df['candidato_nome'] != '') &
            (df['candidato_nome'] != 'nan')
        ].copy()
        
        # Exibe estatísticas de quantidade de registros na barra lateral.
        st.sidebar.write(f"📊 Total de candidaturas: {len(df)}")
        st.sidebar.write(f"👤 Candidatos com nome: {len(df_com_nome)}")
        st.sidebar.write(f"🚫 Sem nome: {len(df) - len(df_com_nome)}")
        
        return df_com_nome
    except FileNotFoundError:
        # Caso o arquivo não seja encontrado, orienta o usuário a executar o pré-processamento.
        st.error(f"Arquivo '{caminho_arquivo}' não encontrado! Execute o 'preprocess.py' primeiro.")
        return None

# Função para carregar o modelo de embeddings (SentenceTransformer).
# Utiliza cache para garantir que o modelo seja carregado apenas uma vez por sessão.
@st.cache_resource
def carregar_encoder():
    return SentenceTransformer("all-MiniLM-L6-v2")

df_completo = carregar_dados()
text_encoder = carregar_encoder()

# Função para calcular a compatibilidade entre a descrição da vaga e o currículo de um candidato.
# Utiliza embeddings de texto e similaridade de cosseno como métrica.
def calcular_compatibilidade(texto_vaga, texto_cv):
    if not isinstance(texto_vaga, str) or not isinstance(texto_cv, str) or not texto_vaga or not texto_cv:
        return 0.0
    embeddings = text_encoder.encode([texto_vaga, texto_cv])
    return cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

# Inicializa variáveis de estado (session_state) para controle de paginação dos resultados.
if 'pagina_atual_analise' not in st.session_state:
    st.session_state.pagina_atual_analise = 1

# Inicializa variáveis de estado (session_state) para armazenar resultados de análise.
if 'resultados_analise' not in st.session_state:
    st.session_state.resultados_analise = None

# Define a quantidade de itens (candidatos) a serem exibidos por página.
ITENS_POR_PAGINA_ANALISE = 10

# Seção principal da interface para análise de uma vaga específica.
st.header("🔍 Análise de Vaga Específica")

if df_completo is not None:
    # Caso não existam candidatos após o filtro, emite um alerta.
    if len(df_completo) == 0:
        st.warning("⚠️ Nenhum candidato com nome informado encontrado na base de dados!")
    else:
        # Seção de busca de vagas, permitindo seleção por título ou por ID.
        st.write("### 🔍 Buscar Vaga")
        st.info("💡 **Use um ou ambos os campos abaixo para buscar vagas. Não é necessário preencher os dois.**")
        
        # Gerencia chaves únicas para os widgets, permitindo limpeza da seleção.
        reset_key_suffix = st.session_state.get('reset_count', 0)
        
        col_busca1, col_busca2, col_busca3 = st.columns([2, 2, 1])
        
        with col_busca1:
            # Campo de busca por título da vaga.
            todas_vagas = sorted(df_completo['vaga_titulo'].dropna().unique())
            vaga_selecionada_titulo = st.selectbox(
                'Buscar por Título da Vaga',
                options=[''] + todas_vagas,
                help="Selecione uma vaga pelo título",
                key=f'vaga_titulo_{reset_key_suffix}'
            )
        
        with col_busca2:
            # Campo de busca por ID da vaga.
            todas_vagas_ids = sorted(df_completo['vaga_id'].dropna().unique())
            vaga_selecionada_id = st.selectbox(
                'Buscar por ID da Vaga',
                options=[''] + todas_vagas_ids,
                help="Selecione uma vaga pelo ID",
                format_func=lambda x: f"ID: {x}" if x else "",
                key=f'vaga_id_{reset_key_suffix}'
            )
        
        with col_busca3:
            # Botão para limpar filtros de busca e redefinir o estado.
            st.write("")  
            st.write("")  
            if st.button("🗑️ Limpar Buscas", use_container_width=True):
                st.session_state.reset_count = reset_key_suffix + 1
                st.session_state.resultados_analise = None
                st.session_state.pagina_atual_analise = 1
                st.rerun()
        
        # Determina o critério de busca prioritário (ID tem precedência sobre título).
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
        
        # Se uma vaga foi selecionada, inicia a análise de compatibilidade.
        col_analise1, col_analise2 = st.columns([3, 1])
        with col_analise1:
            if vaga_para_analise and st.button("Analisar Candidatos", type="primary", use_container_width=True):
                # Filtra os registros conforme o critério de busca definido.
                if tipo_busca == "ID":
                    df_vaga = df_completo[df_completo['vaga_id'] == vaga_para_analise].copy()
                    titulo_vaga = df_vaga['vaga_titulo'].iloc[0] if len(df_vaga) > 0 else f"ID: {vaga_para_analise}"
                else:
                    df_vaga = df_completo[df_completo['vaga_titulo'] == vaga_para_analise].copy()
                    titulo_vaga = vaga_para_analise
                
                # Exibe estatísticas básicas da vaga.
                st.success(f"**Vaga encontrada:** {titulo_vaga} | **Candidatos com nome:** {len(df_vaga)}")
                
                if len(df_vaga) == 0:
                    st.warning("Nenhum candidato com nome informado para esta vaga.")
                    st.session_state.resultados_analise = None
                else:
                    with st.spinner("Analisando currículos com IA... Isso pode levar um momento."):
                        # Obtém a descrição da vaga como base de comparação.
                        texto_vaga_base = df_vaga['vaga_competencias'].iloc[0] if 'vaga_competencias' in df_vaga.columns else ""
                        # Calcula a compatibilidade entre a vaga e cada currículo.
                        df_vaga['compatibilidade'] = df_vaga['candidato_cv'].apply(
                            lambda cv: calcular_compatibilidade(texto_vaga_base, cv)
                        )
                        df_vaga = df_vaga.sort_values('compatibilidade', ascending=False)
                    
                    # Armazena os resultados no session_state para permitir paginação e exibição.
                    st.session_state.resultados_analise = {
                        'df_vaga': df_vaga,
                        'titulo_vaga': titulo_vaga,
                        'tipo_busca': tipo_busca
                    }
                    st.session_state.pagina_atual_analise = 1
                    st.rerun()
        
        with col_analise2:
            # Botão para reiniciar a análise, mantendo os filtros selecionados.
            if st.session_state.resultados_analise is not None:
                if st.button("🔄 Nova Análise", use_container_width=True):
                    st.session_state.resultados_analise = None
                    st.session_state.pagina_atual_analise = 1
                    st.rerun()
        
        # Caso já existam resultados processados, apresenta-os ao usuário.
        if st.session_state.resultados_analise is not None:
            resultados = st.session_state.resultados_analise
            df_vaga = resultados['df_vaga']
            titulo_vaga = resultados['titulo_vaga']
            
            st.subheader(f"Resultados para: {titulo_vaga}")
            
            # Exibição de métricas gerais da análise.
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Candidatos", len(df_vaga))
            with col2:
                st.metric("Compatibilidade Média", f"{df_vaga['compatibilidade'].mean()*100:.1f}%")
            with col3:
                top_score = df_vaga['compatibilidade'].max() * 100
                st.metric("Maior Compatibilidade", f"{top_score:.1f}%")

            # Configuração da paginação dos resultados.
            total_paginas = max(1, (len(df_vaga) + ITENS_POR_PAGINA_ANALISE - 1) // ITENS_POR_PAGINA_ANALISE)
            inicio = (st.session_state.pagina_atual_analise - 1) * ITENS_POR_PAGINA_ANALISE
            fim = inicio + ITENS_POR_PAGINA_ANALISE
            df_vaga_pagina = df_vaga.iloc[inicio:fim]

            # Controles de navegação entre páginas.
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

            # Exibição dos candidatos em formato de cartões com indicadores de compatibilidade.
            st.subheader("🎯 Candidatos Recomendados")
            
            for index, candidato in df_vaga_pagina.iterrows():
                score_percent = candidato['compatibilidade'] * 100
                
                # Definição visual com base no nível de compatibilidade.
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
                        # Exibição do nome e situação do candidato.
                        st.markdown(f"{emoji} **{candidato['candidato_nome']}**")
                        
                        situacao = candidato.get('situacao_candidado', 'Não informado')
                        if pd.isna(situacao) or situacao in ['', 'nan']:
                            situacao = 'Não informado'
                        st.caption(f"📋 Situação: {situacao}")
                        
                        # Identificação do candidato.
                        st.caption(f"🆔 ID: {candidato.get('candidato_id', 'N/A')}")
                    
                    with col_score:
                        # Exibição da compatibilidade com feedback textual.
                        if score_percent > 70:
                            st.metric("Compatibilidade", f"{score_percent:.1f}%", "Excelente", delta_color="off")
                        elif score_percent > 50:
                            st.metric("Compatibilidade", f"{score_percent:.1f}%", "Boa", delta_color="off")
                        elif score_percent > 30:
                            st.metric("Compatibilidade", f"{score_percent:.1f}%", "Média", delta_color="off")
                        else:
                            st.metric("Compatibilidade", f"{score_percent:.1f}%", "Baixa", delta_color="off")
                    
                    # Seção expansível com detalhes completos do candidato.
                    with st.expander("📄 Ver detalhes completos"):
                        st.write(f"**ID do Candidato:** {candidato.get('candidato_id', 'N/A')}")
                        st.write(f"**ID da Vaga:** {candidato.get('vaga_id', 'N/A')}")
                        st.write(f"**Situação:** {situacao}")
                        
                        # Exibição do currículo completo, se disponível.
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
                            # Estatísticas textuais do currículo.
                            col_cv1, col_cv2 = st.columns(2)
                            with col_cv1:
                                st.caption(f"📏 Tamanho: {len(cv_preview)} caracteres")
                            with col_cv2:
                                st.caption(f"📄 Palavras: {len(cv_preview.split())}")
                        else:
                            st.write("**CV:** Não informado")
