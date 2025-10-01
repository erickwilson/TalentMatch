# ✨ TalentMatch AI

Este projeto é uma plataforma de Análise de Talentos construída com Streamlit, projetada para otimizar o processo de recrutamento. A ferramenta utiliza processamento de linguagem natural para calcular a compatibilidade entre as competências de uma vaga e os currículos dos candidatos, além de oferecer dashboards interativos para análise de dados.

## 🚀 Funcionalidades Principais

  * **Análise de Compatibilidade por IA (`App.py`):** Calcule um score de compatibilidade entre a descrição de uma vaga e o currículo de cada candidato, utilizando `Sentence-Transformers` para gerar embeddings e calcular a similaridade de cosseno.
  * **Busca Avançada de Candidatos (`2_Busca_de_Candidatos.py`):** Um motor de busca que permite filtrar e encontrar candidatos na base de dados por nome, ID ou palavras-chave presentes no currículo.
  * **Dashboard de Contratados (`3_Perfil_Contratados.py`):** Uma página de análise de dados que exibe o perfil detalhado dos candidatos que foram contratados, com gráficos sobre anos de experiência, nível de formação, competências técnicas mais comuns e mais.


## ⚙️ Fluxo de Dados e Arquitetura

A aplicação funciona com um fluxo de dados bem definido para garantir performance e organização:

1.  **Dados Brutos:** O processo inicia com três arquivos JSON (`vagas.json`, `prospects.json`, `applicants.json`) que contêm as informações de vagas, prospecções e candidatos.
2.  **Pré-processamento:** O script `preprocess.py` é executado para ler, unificar e limpar os dados brutos.
3.  **Base de Dados Otimizada:** O resultado do pré-processamento é salvo em um único arquivo, `dados_processados.parquet`, que serve como a fonte de dados principal para a aplicação.
4.  **Aplicação Interativa:** A interface do Streamlit (composta pelos arquivos `App.py`, `2_...` e `3_...`) lê o arquivo `.parquet` para alimentar todas as visualizações, buscas e análises.

## 🛠️ Tecnologias Utilizadas

  * **Backend & Frontend:** [Streamlit](https://streamlit.io/)
  * **Análise de Dados:** [Pandas](https://pandas.pydata.org/)
  * **Gráficos e Visualizações:** [Plotly Express](https://plotly.com/python/plotly-express/)
  * **Inteligência Artificial (NLP):** [Sentence-Transformers](https://www.sbert.net/)

## 📋 Como Executar o Projeto

Siga os passos abaixo para configurar e executar a aplicação em seu ambiente local.

### **Pré-requisitos**

  * Python 3.8 ou superior
  * Git

### **1. Clone o Repositório**

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

### **2. Crie um Ambiente Virtual e Ative-o**

É uma boa prática isolar as dependências do projeto.

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### **3. Instale as Dependências**

Crie um arquivo `requirements.txt` com as bibliotecas necessárias.

```txt
# requirements.txt
streamlit
pandas
pyarrow
plotly
sentence-transformers
```

Em seguida, instale-as com o pip:

```bash
pip install -r requirements.txt
```

### **4. Prepare os Dados Iniciais**

1.  Crie uma pasta chamada `data` na raiz do projeto.

2.  Coloque os três arquivos JSON (`vagas.json`, `prospects.json`, `applicants.json`) dentro desta pasta.

3.  **Importante:** Verifique se o script `preprocess.py` está configurado para ler os arquivos desta pasta. Se necessário, ajuste os caminhos no início do script.

    ```python
    # Exemplo de ajuste em preprocess.py
    VAGAS_JSON = "data/vagas.json"
    PROSPECTS_JSON = "data/prospects.json"
    APPLICANTS_JSON = "data/applicants.json"
    OUTPUT_FILE = "dados_processados.parquet"
    ```

### **5. Execute o Script de Pré-processamento**

Este passo só precisa ser executado uma vez (ou sempre que os dados brutos forem atualizados).

```bash
python preprocess.py
```

Este comando irá gerar o arquivo `dados_processados.parquet` na raiz do projeto.

### **6. Inicie a Aplicação Streamlit**

Com o arquivo `.parquet` gerado, inicie a aplicação:

```bash
streamlit run App.py
```

Seu navegador abrirá automaticamente com a aplicação em funcionamento\!

## 📂 Estrutura do Projeto (Sugestão)

Para uma melhor organização, especialmente com as páginas do Streamlit, a seguinte estrutura é recomendada:

```
talentmatch-ai/
├── 📂 data/
│   ├── applicants.json
│   ├── prospects.json
│   └── vagas.json
├── 📂 pages/
│   ├── 2_Busca_de_Candidatos.py
│   └── 3_Perfil_Contratados.py
├── 📜 App.py                  # Página principal
├── 📜 preprocess.py
├── 📜 requirements.txt
└── 📜 README.md
```

**Nota:** Para que o menu de páginas funcione, o Streamlit espera que as páginas secundárias estejam dentro de uma pasta chamada `pages`.

## 📜 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
