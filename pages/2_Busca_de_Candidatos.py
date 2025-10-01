import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide", page_title="Busca de Candidatos")
st.title("👩‍💻 Busca de Candidatos")
st.markdown("Use um ou mais campos abaixo para buscar candidatos. **Não é necessário preencher todos os campos.**")

@st.cache_data
def carregar_dados(caminho_arquivo="dados_processados.parquet"):
    try:
        df = pd.read_parquet(caminho_arquivo)
        # Debug: mostrar informações sobre os dados
        st.sidebar.write("📊 Informações dos dados:")
        st.sidebar.write(f"- Total de candidatos: {len(df)}")
        st.sidebar.write(f"- CVs não vazios: {df['candidato_cv'].notna().sum()}")
        st.sidebar.write(f"- CVs com conteúdo: {(df['candidato_cv'] != 'Não informado').sum()}")
        return df
    except FileNotFoundError:
        st.error(f"Ficheiro '{caminho_arquivo}' não encontrado! Execute o 'preprocess.py' primeiro.")
        return None

def buscar_por_habilidades(df, keywords):
    """Busca candidatos que contenham as keywords APENAS nas informações do candidato"""
    resultados = []
    
    for idx, candidato in df.iterrows():
        # Dicionário para rastrear onde cada keyword foi encontrada
        encontrado_em = {keyword: [] for keyword in keywords}
        
        # VERIFICAR APENAS INFORMAÇÕES DO CANDIDATO (remover informações da vaga)
        
        # Campo: CV (informação do candidato)
        cv_texto = candidato.get('candidato_cv', '')
        if pd.notna(cv_texto) and cv_texto != 'Não informado':
            cv_lower = str(cv_texto).lower()
            for keyword in keywords:
                if keyword.lower() in cv_lower:
                    encontrado_em[keyword].append('CV do Candidato')
        
        # Campo: Nome do Candidato (informação do candidato)
        nome_candidato = candidato.get('candidato_nome', '')
        if pd.notna(nome_candidato) and nome_candidato != 'Não informado':
            nome_lower = str(nome_candidato).lower()
            for keyword in keywords:
                if keyword.lower() in nome_lower:
                    encontrado_em[keyword].append('Nome do Candidato')
        
        # Campo: Situação (informação do candidato)
        situacao = candidato.get('situacao_candidado', '')
        if pd.notna(situacao) and situacao != 'Não informado':
            situacao_lower = str(situacao).lower()
            for keyword in keywords:
                if keyword.lower() in situacao_lower:
                    encontrado_em[keyword].append('Situação da Candidatura')
        
        # Verificar se TODAS as keywords foram encontradas em pelo menos um campo DO CANDIDATO
        todas_encontradas = all(len(encontrado_em[keyword]) > 0 for keyword in keywords)
        
        if todas_encontradas:
            # Contar número de palavras encontradas (não ocorrências)
            palavras_encontradas = sum(1 for keyword in keywords if len(encontrado_em[keyword]) > 0)
            resultados.append({
                'candidato': candidato,
                'matches': palavras_encontradas,
                'encontrado_em': encontrado_em,
                'tipo_busca': 'habilidades'
            })
    
    return resultados

def buscar_por_nome(df, nome_busca):
    """Busca candidatos por nome (busca parcial)"""
    resultados = []
    
    for idx, candidato in df.iterrows():
        nome_candidato = candidato.get('candidato_nome', '')
        if pd.notna(nome_candidato) and nome_candidato != 'Não informado':
            if nome_busca.lower() in nome_candidato.lower():
                resultados.append({
                    'candidato': candidato,
                    'matches': 1,
                    'encontrado_em': {'nome': ['Nome do Candidato']},
                    'tipo_busca': 'nome'
                })
    
    return resultados

def buscar_por_id(df, id_busca):
    """Busca candidatos por ID exato"""
    resultados = []
    
    for idx, candidato in df.iterrows():
        candidato_id = candidato.get('candidato_id', '')
        if pd.notna(candidato_id) and str(candidato_id) == str(id_busca):
            resultados.append({
                'candidato': candidato,
                'matches': 1,
                'encontrado_em': {'id': ['ID do Candidato']},
                'tipo_busca': 'id'
            })
    
    return resultados

def buscar_candidatos(df, keywords=None, nome=None, id_candidato=None):
    """Busca candidatos usando os critérios fornecidos"""
    
    # Se nenhum critério foi fornecido, retornar lista vazia
    if not any([keywords, nome, id_candidato]):
        return []
    
    resultados = []
    
    # Buscar por habilidades (se keywords fornecidas)
    if keywords:
        resultados_habilidades = buscar_por_habilidades(df, keywords)
        resultados.extend(resultados_habilidades)
    
    # Buscar por nome (se nome fornecido)
    if nome:
        resultados_nome = buscar_por_nome(df, nome)
        # Evitar duplicados
        for resultado in resultados_nome:
            candidato_id = resultado['candidato'].get('candidato_id')
            if not any(r['candidato'].get('candidato_id') == candidato_id for r in resultados):
                resultados.append(resultado)
    
    # Buscar por ID (se ID fornecido)
    if id_candidato:
        resultados_id = buscar_por_id(df, id_candidato)
        # Evitar duplicados
        for resultado in resultados_id:
            candidato_id = resultado['candidato'].get('candidato_id')
            if not any(r['candidato'].get('candidato_id') == candidato_id for r in resultados):
                resultados.append(resultado)
    
    return resultados

def exibir_descricao_completa(candidato, keywords, encontrado_em, tipo_busca):
    """Exibe a descrição completa do candidato"""
    st.subheader(f"📄 Descrição Completa - {candidato.get('candidato_nome', 'Não informado')}")
    
    # Criar colunas para organização
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 👤 Informações Pessoais")
        st.write(f"**ID do Candidato:** {candidato.get('candidato_id', 'N/A')}")
        st.write(f"**Nome:** {candidato.get('candidato_nome', 'Não informado')}")
        st.write(f"**Situação:** {candidato.get('situacao_candidado', 'Não informado')}")
    
    with col2:
        st.write("### 📊 Informações da Busca")
        st.write(f"**Tipo de busca:** {tipo_busca.upper()}")
        
        if tipo_busca == 'habilidades':
            # Mostrar onde cada keyword foi encontrada
            st.write("**Onde as palavras foram encontradas:**")
            palavras_encontradas = 0
            for keyword in keywords:
                locais = encontrado_em.get(keyword, [])
                if locais:
                    palavras_encontradas += 1
                    st.write(f"- ✅ **{keyword}**: {', '.join(locais)}")
                else:
                    st.write(f"- ❌ **{keyword}**: Não encontrada")
            
            st.write(f"**Total:** {palavras_encontradas} de {len(keywords)} palavras encontradas")
        elif tipo_busca == 'nome':
            st.write("**Busca realizada por:** Nome do candidato")
        elif tipo_busca == 'id':
            st.write("**Busca realizada por:** ID do candidato")
    
    # Informações da Vaga (apenas para referência, não usadas na busca)
    st.write("### 💼 Informações da Vaga (apenas referência)")
    col_vaga1, col_vaga2 = st.columns(2)
    with col_vaga1:
        st.write(f"**Vaga:** {candidato.get('vaga_titulo', 'Não informado')}")
    with col_vaga2:
        st.write(f"**ID da Vaga:** {candidato.get('vaga_id', 'N/A')}")
    
    # Currículo Completo
    st.write("### 📝 Currículo Completo")
    cv_texto = candidato.get('candidato_cv', '')
    if cv_texto and cv_texto != 'Não informado':
        # Destacar as palavras-chave encontradas no CV (apenas para busca por habilidades)
        cv_destacado = cv_texto
        if tipo_busca == 'habilidades' and keywords:
            for keyword in keywords:
                cv_destacado = re.sub(
                    f'({re.escape(keyword)})', 
                    r'🎯**\1**', 
                    cv_destacado, 
                    flags=re.IGNORECASE
                )
        
        # Mostrar o CV em uma área de texto com scroll
        st.text_area(
            "Conteúdo do CV:",
            cv_destacado,
            height=400,
            key=f"cv_{candidato.get('candidato_id')}",
            label_visibility="collapsed"
        )
        
        # Estatísticas do CV
        col_size, col_lines = st.columns(2)
        with col_size:
            st.write(f"**📏 Tamanho do CV:** {len(cv_texto)} caracteres")
            st.write(f"**📄 Número de palavras:** {len(cv_texto.split())}")
        
        with col_lines:
            linhas = cv_texto.count('\n') + 1
            st.write(f"**📊 Número de linhas:** {linhas}")
        
        # Detalhamento das palavras-chave encontradas no CV (apenas para busca por habilidades)
        if tipo_busca == 'habilidades' and keywords:
            st.write("### 🔍 Detalhamento das Palavras-chave no CV:")
            
            keyword_details = []
            for keyword in keywords:
                count = cv_texto.lower().count(keyword.lower())
                keyword_details.append({
                    'keyword': keyword,
                    'count': count,
                    'encontrada_no_cv': count > 0
                })
            
            # Ordenar por quantidade de ocorrências
            keyword_details.sort(key=lambda x: x['count'], reverse=True)
            
            for detail in keyword_details:
                if detail['encontrada_no_cv']:
                    col_kw, col_count, col_bar = st.columns([2, 1, 3])
                    with col_kw:
                        st.write(f"✅ **{detail['keyword']}**")
                    with col_count:
                        st.write(f"{detail['count']}x")
                    with col_bar:
                        # Barra de progresso visual
                        max_count = max(kd['count'] for kd in keyword_details if kd['count'] > 0)
                        percent_width = min((detail['count'] / max_count) * 100, 100) if max_count > 0 else 0
                        st.progress(int(percent_width) / 100)
                else:
                    st.write(f"❌ **{detail['keyword']}**: 0 ocorrências no CV")
                
    else:
        st.warning("❌ CV não disponível ou não informado")
        if tipo_busca != 'habilidades':
            st.info("💡 Este candidato foi encontrado através de busca por nome ou ID.")
    
    # Botão para voltar
    st.divider()
    col_voltar1, col_voltar2, col_voltar3 = st.columns([1, 2, 1])
    with col_voltar2:
        if st.button("⬅️ Voltar para a Lista de Resultados", use_container_width=True):
            # Limpar o estado de visualização de detalhes
            st.session_state.mostrar_descricao = False
            st.session_state.candidato_selecionado = None
            st.session_state.encontrado_em = None
            st.session_state.tipo_busca = None
            # Forçar rerun para atualizar a interface
            st.rerun()

# Inicializar session state para controlar a exibição e paginação
if 'mostrar_descricao' not in st.session_state:
    st.session_state.mostrar_descricao = False
if 'candidato_selecionado' not in st.session_state:
    st.session_state.candidato_selecionado = None
if 'encontrado_em' not in st.session_state:
    st.session_state.encontrado_em = None
if 'tipo_busca' not in st.session_state:
    st.session_state.tipo_busca = None
if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = 1
if 'resultados_busca' not in st.session_state:
    st.session_state.resultados_busca = None

ITENS_POR_PAGINA = 10

df_completo = carregar_dados()

if df_completo is not None:
    # Se estamos no modo de visualização de descrição, mostrar o candidato selecionado
    if st.session_state.mostrar_descricao and st.session_state.candidato_selecionado is not None:
        exibir_descricao_completa(
            st.session_state.candidato_selecionado, 
            st.session_state.keywords_busca,
            st.session_state.encontrado_em,
            st.session_state.tipo_busca
        )
    
    else:
        # Modo normal de busca
        st.write("### 🔍 Critérios de Busca")
        st.info("💡 **Preencha um ou mais campos abaixo. Não é necessário preencher todos.**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("🔄 Por Habilidades")
            keywords_input = st.text_input(
                "Palavras-chave (separadas por vírgula)",
                placeholder="ex: python, java, gestão"
            )
            if keywords_input:
                st.caption("Busca nas informações do candidato (CV, nome, situação)")
        
        with col2:
            st.subheader("👤 Por Nome")
            nome_input = st.text_input(
                "Nome do candidato",
                placeholder="ex: Maria, João Silva"
            )
            if nome_input:
                st.caption("Busca parcial no nome do candidato")
        
        with col3:
            st.subheader("🆔 Por ID")
            id_input = st.text_input(
                "ID do candidato",
                placeholder="ex: 12345"
            )
            if id_input:
                st.caption("Busca exata pelo ID do candidato")
        
        # Botão de busca
        if st.button("🔍 Buscar Candidatos", type="primary", use_container_width=True):
            if any([keywords_input, nome_input, id_input]):
                # Preparar parâmetros da busca
                keywords = [key.strip() for key in keywords_input.split(',') if key.strip()] if keywords_input else None
                nome = nome_input.strip() if nome_input else None
                id_candidato = id_input.strip() if id_input else None
                
                # Guardar parâmetros na session state
                st.session_state.keywords_busca = keywords
                st.session_state.nome_busca = nome
                st.session_state.id_busca = id_candidato
                
                # Realizar busca
                resultados = buscar_candidatos(df_completo, keywords, nome, id_candidato)
                st.session_state.resultados_busca = resultados
                st.session_state.pagina_atual = 1
                
            else:
                st.warning("⚠️ Por favor, preencha pelo menos um campo de busca.")
        
        # Exibir resultados se existirem
        if st.session_state.resultados_busca is not None:
            resultados = st.session_state.resultados_busca
            
            # Mostrar critérios usados na busca
            st.write("---")
            st.write("### 📋 Critérios da Busca Atual")
            criterios = []
            if st.session_state.keywords_busca:
                criterios.append(f"**Habilidades:** {', '.join(st.session_state.keywords_busca)}")
            if st.session_state.nome_busca:
                criterios.append(f"**Nome:** {st.session_state.nome_busca}")
            if st.session_state.id_busca:
                criterios.append(f"**ID:** {st.session_state.id_busca}")
            
            if criterios:
                st.info(" | ".join(criterios))
            
            # Ordenar resultados (priorizar busca por habilidades)
            resultados.sort(key=lambda x: (x['tipo_busca'] == 'habilidades', x['matches']), reverse=True)
            
            # Paginação
            total_paginas = max(1, (len(resultados) + ITENS_POR_PAGINA - 1) // ITENS_POR_PAGINA)
            inicio = (st.session_state.pagina_atual - 1) * ITENS_POR_PAGINA
            fim = inicio + ITENS_POR_PAGINA
            resultados_pagina = resultados[inicio:fim]
            
            st.metric("Candidatos Encontrados", f"{len(resultados)}")
            
            if resultados:
                st.success(f"✅ Encontrados {len(resultados)} candidatos!")
                
                # Controles de paginação
                if total_paginas > 1:
                    col_pag_prev, col_pag_info, col_pag_next = st.columns([1, 2, 1])
                    with col_pag_prev:
                        if st.button("⏪ Página Anterior", disabled=st.session_state.pagina_atual == 1):
                            st.session_state.pagina_atual -= 1
                            st.rerun()
                    with col_pag_info:
                        st.write(f"Página {st.session_state.pagina_atual} de {total_paginas}")
                    with col_pag_next:
                        if st.button("Próxima Página ⏩", disabled=st.session_state.pagina_atual == total_paginas):
                            st.session_state.pagina_atual += 1
                            st.rerun()
                
                # Mostrar resultados em cards
                for i, resultado in enumerate(resultados_pagina):
                    candidato = resultado['candidato']
                    encontrado_em = resultado['encontrado_em']
                    tipo_busca = resultado['tipo_busca']
                    
                    with st.container(border=True):
                        col1, col2, col3, col4 = st.columns([3, 2, 1, 2])
                        
                        with col1:
                            # Badge do tipo de busca
                            if tipo_busca == 'habilidades':
                                st.markdown("🔄 **Por Habilidades**")
                            elif tipo_busca == 'nome':
                                st.markdown("👤 **Por Nome**")
                            elif tipo_busca == 'id':
                                st.markdown("🆔 **Por ID**")
                            
                            st.write(f"**{candidato.get('candidato_nome', 'Não informado')}**")
                            st.caption(f"ID: {candidato.get('candidato_id', 'N/A')}")
                            
                            # Mostrar informações específicas do tipo de busca
                            if tipo_busca == 'habilidades':
                                st.caption("📍 Palavras-chave encontradas nas informações do candidato")
                            elif tipo_busca == 'nome':
                                st.caption("📍 Encontrado por busca no nome")
                            elif tipo_busca == 'id':
                                st.caption("📍 Encontrado por busca no ID")
                        
                        with col2:
                            if tipo_busca == 'habilidades':
                                st.write(f"**Relevância:**")
                                progresso = min(resultado['matches'] / len(st.session_state.keywords_busca), 1.0)
                                st.progress(progresso)
                                st.write(f"{resultado['matches']} de {len(st.session_state.keywords_busca)} palavras")
                            else:
                                st.write(f"**Tipo:**")
                                st.write("Busca Direta ✅")
                        
                        with col3:
                            if tipo_busca == 'habilidades':
                                st.write("**Score:**")
                                score_percent = min((resultado['matches'] / len(st.session_state.keywords_busca)) * 100, 100)
                                st.write(f"**{int(score_percent)}%**")
                            else:
                                st.write("**Match:**")
                                st.write("**100%**")
                        
                        with col4:
                            if st.button("📄 Ver Descrição Completa", key=f"btn_{inicio + i}"):
                                st.session_state.mostrar_descricao = True
                                st.session_state.candidato_selecionado = candidato
                                st.session_state.encontrado_em = encontrado_em
                                st.session_state.tipo_busca = tipo_busca
                                st.rerun()
                
                # Mostrar estatísticas gerais
                st.divider()
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                with col_stats1:
                    # Contar por tipo de busca
                    por_habilidades = sum(1 for r in resultados if r['tipo_busca'] == 'habilidades')
                    por_nome = sum(1 for r in resultados if r['tipo_busca'] == 'nome')
                    por_id = sum(1 for r in resultados if r['tipo_busca'] == 'id')
                    st.metric("Por Habilidades", por_habilidades)
                with col_stats2:
                    st.metric("Por Nome", por_nome)
                with col_stats3:
                    st.metric("Por ID", por_id)
                    
            else:
                st.warning("❌ Nenhum candidato encontrado com os critérios fornecidos.")
                
                # Sugerir buscas alternativas
                st.info("💡 **Dicas para melhorar a busca:**")
                st.write("- Para busca por nome: use apenas parte do nome")
                st.write("- Para busca por ID: verifique se o ID está correto")
                st.write("- Para busca por habilidades: use palavras mais genéricas")