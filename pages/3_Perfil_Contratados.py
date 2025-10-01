import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re

st.set_page_config(layout="wide", page_title="Perfil dos Contratados")
st.title("📊 Perfil dos Candidatos Contratados")
st.markdown("Análise das **características e competências** dos candidatos que foram contratados.")

@st.cache_data
def carregar_dados(caminho_arquivo="dados_processados.parquet"):
    try:
        df = pd.read_parquet(caminho_arquivo)
        return df
    except FileNotFoundError:
        st.error(f"Arquivo '{caminho_arquivo}' não encontrado! Execute o 'preprocess.py' primeiro.")
        return None

def extrair_experiencia(texto_cv):
    """Extrai tempo de experiência do texto do CV"""
    if not isinstance(texto_cv, str) or texto_cv == 'Não informado':
        return "Não especificado"
    
    texto_cv = texto_cv.lower()
    
    # Padrões para encontrar experiência
    padroes = [
        r'(\d+)\s*anos?\s*(?:de\s*)?experiência',
        r'experiência\s*de\s*(\d+)\s*anos?',
        r'(\d+)\s*anos?\s*(?:de\s*)?exp',
        r'exp\s*de\s*(\d+)\s*anos?',
        r'(\d+)\s*anos?\s*na\s*área',
        r'(\d+)\s*anos?\s*em\s*[a-záéíóúâêîôûãõç\s]+',
    ]
    
    for padrao in padroes:
        matches = re.findall(padrao, texto_cv)
        if matches:
            anos = max([int(match) for match in matches if match.isdigit()])
            return f"{anos} anos"
    
    return "Não especificado"

def detectar_nivel_ingles(texto_cv):
    """Detecta nível de inglês no CV"""
    if not isinstance(texto_cv, str) or texto_cv == 'Não informado':
        return "Não especificado"
    
    texto_cv = texto_cv.lower()
    
    niveis = {
        'avançado': ['avançado', 'advanced', 'fluente', 'fluent', 'c2', 'c1'],
        'intermediário': ['intermediário', 'intermediate', 'b2', 'b1', 'intermediario'],
        'básico': ['básico', 'basic', 'iniciante', 'beginner', 'a2', 'a1', 'basico'],
        'nativo': ['nativo', 'native']
    }
    
    for nivel, palavras in niveis.items():
        for palavra in palavras:
            if palavra in texto_cv:
                return nivel.capitalize()
    
    return "Não especificado"

def extrair_competencias_tecnicas(texto_cv):
    """Extrai competências técnicas do CV"""
    if not isinstance(texto_cv, str) or texto_cv == 'Não informado':
        return []
    
    texto_cv = texto_cv.lower()
    
    competencias_comuns = [
        'python', 'java', 'javascript', 'sql', 'html', 'css', 'react', 'angular', 'vue',
        'node.js', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git', 'jenkins',
        'machine learning', 'ai', 'data science', 'big data', 'tableau', 'power bi',
        'excel', 'word', 'powerpoint', 'project management', 'scrum', 'agile',
        'linux', 'windows', 'macos', 'oracle', 'mysql', 'postgresql', 'mongodb',
        'php', 'c#', 'c++', 'ruby', 'go', 'rust', 'swift', 'kotlin'
    ]
    
    encontradas = []
    for competencia in competencias_comuns:
        if competencia in texto_cv:
            encontradas.append(competencia)
    
    return encontradas

def extrair_formacao(texto_cv):
    """Extrai informações de formação do CV"""
    if not isinstance(texto_cv, str) or texto_cv == 'Não informado':
        return "Não especificado"
    
    texto_cv = texto_cv.lower()
    
    formacoes = {
        'doutorado': ['doutorado', 'phd', 'doutor'],
        'mestrado': ['mestrado', 'mestre'],
        'pós-graduação': ['pós-graduação', 'pos-graduacao', 'especialização', 'especializacao'],
        'graduação': ['graduação', 'graduacao', 'bacharelado', 'licenciatura', 'tecnólogo', 'tecnologo'],
        'técnico': ['técnico', 'tecnico', 'curso técnico'],
        'ensino médio': ['ensino médio', 'ensino medio']
    }
    
    for formacao, palavras in formacoes.items():
        for palavra in palavras:
            if palavra in texto_cv:
                return formacao.capitalize()
    
    return "Não especificado"

def criar_analise_contratados(df):
    """Cria análise completa dos candidatos contratados"""
    
    # DEBUG: Mostrar todos os status únicos disponíveis
    st.sidebar.write("🔍 **Status disponíveis:**")
    status_unicos = df['situacao_candidado'].dropna().unique()
    for status in sorted(status_unicos):
        count = len(df[df['situacao_candidado'] == status])
        st.sidebar.write(f"- {status}: {count}")
    
    # STATUS QUE REALMENTE REPRESENTAM CONTRATAÇÃO
    status_contratacao_exatos = [
        'Contratado pela Decision',
        'Aprovado', 
        'Contratado como Hunting'
    ]
    
    # Filtrar apenas os status exatos de contratação
    df_contratados = df[df['situacao_candidado'].isin(status_contratacao_exatos)].copy()
    
    # DEBUG: Mostrar o que foi encontrado
    st.sidebar.write("🎯 **Status identificados como contratação:**")
    if len(df_contratados) > 0:
        status_contratados = df_contratados['situacao_candidado'].value_counts()
        for status, count in status_contratados.items():
            st.sidebar.write(f"- {status}: {count}")
        
        total_contratados = len(df_contratados)
        st.sidebar.success(f"**Total de contratados encontrados: {total_contratados}**")
    else:
        st.sidebar.warning("Nenhum candidato contratado encontrado!")
    
    if len(df_contratados) == 0:
        st.warning("⚠️ Nenhum candidato contratado encontrado na base de dados!")
        st.info("💡 **Dica:** Verifique se os status de contratação estão corretos na base de dados.")
        return None
    
    st.success(f"✅ Encontrados **{len(df_contratados)}** candidatos contratados!")
    
    # Aplicar análise aos CVs
    st.info(f"📈 Analisando o perfil de **{len(df_contratados)}** candidatos contratados...")
    
    with st.spinner("Processando currículos..."):
        # Extrair informações dos CVs
        df_contratados['experiencia'] = df_contratados['candidato_cv'].apply(extrair_experiencia)
        df_contratados['ingles'] = df_contratados['candidato_cv'].apply(detectar_nivel_ingles)
        df_contratados['formacao'] = df_contratados['candidato_cv'].apply(extrair_formacao)
        df_contratados['competencias'] = df_contratados['candidato_cv'].apply(extrair_competencias_tecnicas)
    
    return df_contratados

def exibir_metricas_gerais(df_contratados):
    """Exibe métricas gerais dos contratados"""
    st.subheader("📊 Métricas Gerais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_contratados = len(df_contratados)
        st.metric("Total de Contratados", total_contratados)
    
    with col2:
        # Experiência média (apenas dos que especificaram)
        df_com_experiencia = df_contratados[df_contratados['experiencia'] != 'Não especificado']
        if len(df_com_experiencia) > 0:
            anos_lista = []
            for exp in df_com_experiencia['experiencia']:
                numeros = re.findall(r'\d+', exp)
                if numeros:
                    anos_lista.append(int(numeros[0]))
            
            if anos_lista:
                media_experiencia = sum(anos_lista) / len(anos_lista)
                st.metric("Experiência Média", f"{media_experiencia:.1f} anos")
            else:
                st.metric("Experiência Média", "N/A")
        else:
            st.metric("Experiência Média", "N/A")
    
    with col3:
        # Percentual com inglês avançado (apenas dos que especificaram)
        df_com_ingles = df_contratados[df_contratados['ingles'] != 'Não especificado']
        if len(df_com_ingles) > 0:
            ingles_avancado = len(df_com_ingles[df_com_ingles['ingles'].str.contains('Avançado|Nativo', case=False, na=False)])
            percent_ingles = (ingles_avancado / len(df_com_ingles)) * 100
            st.metric("Inglês Avançado/Nativo", f"{percent_ingles:.1f}%")
        else:
            st.metric("Inglês Avançado/Nativo", "N/A")
    
    with col4:
        # Percentual com ensino superior (apenas dos que especificaram)
        df_com_formacao = df_contratados[df_contratados['formacao'] != 'Não especificado']
        if len(df_com_formacao) > 0:
            formacao_superior = len(df_com_formacao[df_com_formacao['formacao'].str.contains('Graduação|Mestrado|Doutorado|Pós-graduação', case=False, na=False)])
            percent_formacao = (formacao_superior / len(df_com_formacao)) * 100
            st.metric("Ensino Superior", f"{percent_formacao:.1f}%")
        else:
            st.metric("Ensino Superior", "N/A")

def exibir_distribuicao_experiencia(df_contratados):
    """Exibe gráfico de distribuição de experiência"""
    st.subheader("⏳ Distribuição de Experiência Profissional")
    
    # Filtrar apenas experiências especificadas
    df_com_experiencia = df_contratados[df_contratados['experiencia'] != 'Não especificado']
    
    if len(df_com_experiencia) == 0:
        st.info("ℹ️ Nenhuma experiência profissional especificada nos currículos.")
        return
    
    # Agrupar experiências
    experiencia_counts = df_com_experiencia['experiencia'].value_counts()
    
    # Ordenar por anos de experiência
    def ordenar_experiencia(exp):
        numeros = re.findall(r'\d+', exp)
        return int(numeros[0]) if numeros else 0
    
    experiencia_ordenada = sorted(experiencia_counts.index, key=ordenar_experiencia)
    experiencia_counts = experiencia_counts.reindex(experiencia_ordenada)
    
    fig = px.bar(
        x=experiencia_counts.index,
        y=experiencia_counts.values,
        title="Distribuição de Anos de Experiência",
        labels={'x': 'Anos de Experiência', 'y': 'Número de Contratados'}
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

def exibir_nivel_ingles(df_contratados):
    """Exibe gráfico de nível de inglês"""
    st.subheader("🌐 Nível de Inglês dos Contratados")
    
    # Filtrar apenas níveis de inglês especificados
    df_com_ingles = df_contratados[df_contratados['ingles'] != 'Não especificado']
    
    if len(df_com_ingles) == 0:
        st.info("ℹ️ Nenhum nível de inglês especificado nos currículos.")
        return
    
    ingles_counts = df_com_ingles['ingles'].value_counts()
    
    fig = px.pie(
        values=ingles_counts.values,
        names=ingles_counts.index,
        title="Distribuição do Nível de Inglês"
    )
    st.plotly_chart(fig, use_container_width=True)

def exibir_formacao(df_contratados):
    """Exibe gráfico de formação acadêmica"""
    st.subheader("🎓 Nível de Formação Acadêmica")
    
    # Filtrar apenas formações especificadas
    df_com_formacao = df_contratados[df_contratados['formacao'] != 'Não especificado']
    
    if len(df_com_formacao) == 0:
        st.info("ℹ️ Nenhuma formação acadêmica especificada nos currículos.")
        return
    
    formacao_counts = df_com_formacao['formacao'].value_counts()
    
    fig = px.bar(
        x=formacao_counts.index,
        y=formacao_counts.values,
        title="Distribuição por Nível de Formação",
        labels={'x': 'Nível de Formação', 'y': 'Número de Contratados'}
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

def exibir_competencias_populares(df_contratados):
    """Exibe competências técnicas mais populares"""
    st.subheader("💻 Competências Técnicas Mais Frequentes")
    
    # Contar todas as competências
    todas_competencias = []
    for competencias in df_contratados['competencias']:
        todas_competencias.extend(competencias)
    
    competencias_counts = Counter(todas_competencias)
    top_competencias = competencias_counts.most_common(15)
    
    if top_competencias:
        competencias_nomes = [comp[0] for comp in top_competencias]
        competencias_quantidades = [comp[1] for comp in top_competencias]
        
        fig = px.bar(
            x=competencias_nomes,
            y=competencias_quantidades,
            title="Top 15 Competências Técnicas",
            labels={'x': 'Competência', 'y': 'Frequência'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ Nenhuma competência técnica identificada nos currículos.")
        
def exibir_perfil_completo(candidato):
    """Exibe perfil completo de um candidato"""
    st.subheader(f"👤 Perfil Completo - {candidato['candidato_nome']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 📋 Informações Básicas")
        st.write(f"**ID do Candidato:** {candidato.get('candidato_id', 'N/A')}")
        st.write(f"**Vaga:** {candidato.get('vaga_titulo', 'N/A')}")
        st.write(f"**Situação:** {candidato.get('situacao_candidado', 'Não informado')}")
        
        st.write("### 🎯 Perfil Extraído")
        st.write(f"**Experiência:** {candidato.get('experiencia', 'Não informado')}")
        st.write(f"**Inglês:** {candidato.get('ingles', 'Não informado')}")
        st.write(f"**Formação:** {candidato.get('formacao', 'Não informado')}")
        
        # Competências técnicas
        competencias = candidato.get('competencias', [])
        if competencias:
            st.write("**Competências Técnicas:**")
            for competencia in competencias:
                st.write(f"- {competencia.title()}")
        else:
            st.write("**Competências Técnicas:** Nenhuma identificada")
    
    with col2:
        st.write("### 📝 Currículo Completo")
        cv_texto = candidato.get('candidato_cv', '')
        if cv_texto and cv_texto != 'Não informado':
            st.text_area(
                "Conteúdo do CV:",
                cv_texto,
                height=400,
                key=f"cv_perfil_{candidato.get('candidato_id')}",
                label_visibility="collapsed"
            )
        else:
            st.warning("CV não disponível")
    
    # Botão para voltar
    st.divider()
    if st.button("⬅️ Voltar para a Lista"):
        st.session_state.mostrar_perfil = False
        st.session_state.candidato_selecionado = None
        st.rerun()

def exibir_lista_contratados(df_contratados):
    """Exibe lista simplificada dos contratados com botão para ver perfil completo"""
    st.subheader("👥 Lista de Candidatos Contratados")
    
    # Criar dataframe resumido para exibição
    df_detalhes = df_contratados[[
        'candidato_nome', 'candidato_id', 'vaga_titulo', 'situacao_candidado'
    ]].copy()
    
    df_detalhes.columns = ['Nome', 'ID', 'Vaga', 'Status']
    
    # Paginação
    itens_por_pagina = 10
    total_paginas = max(1, (len(df_detalhes) + itens_por_pagina - 1) // itens_por_pagina)
    
    pagina = st.session_state.pagina_contratados
    inicio = (pagina - 1) * itens_por_pagina
    fim = inicio + itens_por_pagina
    
    # Exibir métrica correta
    st.write(f"**Mostrando {min(fim, len(df_detalhes))} de {len(df_detalhes)} contratados**")
    
    # Controles de paginação
    if total_paginas > 1:
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("⏪ Anterior", key="prev_contratados", disabled=pagina == 1):
                st.session_state.pagina_contratados -= 1
                st.rerun()
        with col_info:
            st.write(f"Página {pagina} de {total_paginas}")
        with col_next:
            if st.button("Próxima ⏩", key="next_contratados", disabled=pagina == total_paginas):
                st.session_state.pagina_contratados += 1
                st.rerun()
    
    # Exibir lista com botões
    for idx in range(inicio, min(fim, len(df_detalhes))):
        candidato_detalhes = df_detalhes.iloc[idx]
        candidato_completo = df_contratados.iloc[idx]
        
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.write(f"**{candidato_detalhes['Nome']}**")
                st.caption(f"ID: {candidato_detalhes['ID']}")
            
            with col2:
                st.write(f"**Vaga:** {candidato_detalhes['Vaga']}")
            
            with col3:
                st.write(f"**Status:** {candidato_detalhes['Status']}")
            
            with col4:
                if st.button("👁️ Ver Perfil", key=f"perfil_{idx}"):
                    st.session_state.mostrar_perfil = True
                    st.session_state.candidato_selecionado = candidato_completo
                    st.rerun()

# Inicializar session states
if 'mostrar_perfil' not in st.session_state:
    st.session_state.mostrar_perfil = False
if 'candidato_selecionado' not in st.session_state:
    st.session_state.candidato_selecionado = None
if 'df_contratados' not in st.session_state:
    st.session_state.df_contratados = None
if 'pagina_contratados' not in st.session_state:
    st.session_state.pagina_contratados = 1

# MAIN EXECUTION
df_completo = carregar_dados()

if df_completo is not None:
    # Se estiver mostrando perfil individual, exibir e sair
    if st.session_state.mostrar_perfil and st.session_state.candidato_selecionado is not None:
        exibir_perfil_completo(st.session_state.candidato_selecionado)
    
    else:
        # Modo normal - análise geral
        st.sidebar.header("🔍 Filtros")
        
        todas_vagas = sorted(df_completo['vaga_titulo'].dropna().unique())
        vaga_filtro = st.sidebar.selectbox(
            "Filtrar por Vaga (Opcional)",
            options=['Todas as Vagas'] + todas_vagas
        )
        
        if vaga_filtro != 'Todas as Vagas':
            df_filtrado = df_completo[df_completo['vaga_titulo'] == vaga_filtro].copy()
            st.sidebar.info(f"Filtrando por: **{vaga_filtro}**")
        else:
            df_filtrado = df_completo.copy()
            st.sidebar.info("Mostrando **todas as vagas**")
        
        # Botão para gerar análise
        if st.button("🚀 Gerar Análise dos Contratados", type="primary"):
            df_contratados = criar_analise_contratados(df_filtrado)
            
            if df_contratados is not None:
                # Guardar no session state
                st.session_state.df_contratados = df_contratados
                st.session_state.pagina_contratados = 1
                
                # Exibir todas as seções de análise
                exibir_metricas_gerais(df_contratados)
                st.divider()
                
                col_graf1, col_graf2 = st.columns(2)
                
                with col_graf1:
                    exibir_distribuicao_experiencia(df_contratados)
                
                with col_graf2:
                    exibir_nivel_ingles(df_contratados)
                
                st.divider()
                
                col_graf3, col_graf4 = st.columns(2)
                
                with col_graf3:
                    exibir_formacao(df_contratados)
                
                with col_graf4:
                    exibir_competencias_populares(df_contratados)
                
                st.divider()
                exibir_lista_contratados(df_contratados)
        
        # Se já existem resultados, exibir mesmo sem clicar no botão
        elif st.session_state.df_contratados is not None:
            df_contratados = st.session_state.df_contratados
            
            # Verificar se o filtro mudou
            if vaga_filtro != 'Todas as Vagas':
                current_vaga = df_contratados['vaga_titulo'].iloc[0] if len(df_contratados) > 0 else None
                if current_vaga != vaga_filtro:
                    # Filtro mudou, limpar resultados
                    st.session_state.df_contratados = None
                    st.session_state.pagina_contratados = 1
                    st.rerun()
            
            exibir_metricas_gerais(df_contratados)
            st.divider()
            
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                exibir_distribuicao_experiencia(df_contratados)
            
            with col_graf2:
                exibir_nivel_ingles(df_contratados)
            
            st.divider()
            
            col_graf3, col_graf4 = st.columns(2)
            
            with col_graf3:
                exibir_formacao(df_contratados)
            
            with col_graf4:
                exibir_competencias_populares(df_contratados)
            
            st.divider()
            exibir_lista_contratados(df_contratados)
        
        else:
            st.info("💡 Clique no botão acima para gerar a análise do perfil dos candidatos contratados.")
            
            # Mostrar estatísticas rápidas
            st.sidebar.header("📈 Estatísticas Rápidas")
            total_candidatos = len(df_filtrado)
            status_counts = df_filtrado['situacao_candidado'].value_counts()
            
            st.sidebar.write(f"**Total de candidatos:** {total_candidatos}")
            for status, count in status_counts.head(10).items():
                st.sidebar.write(f"**{status}:** {count}")

else:
    st.error("Não foi possível carregar os dados. Verifique se o arquivo 'dados_processados.parquet' existe.")