# train_model.py (Versão Final Verificada)
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score
from sentence_transformers import SentenceTransformer
import joblib
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)

# CONFIGURAÇÕES
PROCESSED_DATA_FILE = "dados_processados.parquet"
MODEL_OUTPUT_FILE = "modelo_contratacao.pkl"
COLUMNS_OUTPUT_FILE = "model_columns.pkl"
RANDOM_STATE = 42

def prepare_data_for_modeling(file_path):
    print(f"A carregar dados de '{file_path}'...")
    df = pd.read_parquet(file_path)
    df = df[df['sucesso'].isin([0, 1])] # Garantir que o alvo é binário
    y = df['sucesso'].astype(int)

    print("A gerar embeddings de texto para usar como features...")
    model_st = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model_st.encode(df["texto_completo"].tolist(), show_progress_bar=True)
    
    # Substituir 'Não informado' por 0 e converter para numérico
    numeric_cols = ['anos_experiencia', 'pretensao_salarial', 'candidato_nivel_ingles_num', 'candidato_nivel_academico_num']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    features_numericas = df[numeric_cols]
    
    X = np.concatenate([embeddings, features_numericas.values], axis=1)
    
    embedding_cols = [f'embed_{i}' for i in range(embeddings.shape[1])]
    all_cols = embedding_cols + numeric_cols
    
    return pd.DataFrame(X, columns=all_cols), y

def train_and_evaluate_model(X, y):
    print("A dividir dados e a treinar o modelo...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y)
    
    if len(y_train.value_counts()) < 2:
        raise ValueError("Apenas uma classe presente nos dados de treino. Não é possível treinar o modelo.")
        
    scale_pos_weight = y_train.value_counts().get(0, 0) / y_train.value_counts().get(1, 1) if y_train.value_counts().get(1, 0) > 0 else 1
    
    model = lgb.LGBMClassifier(objective='binary', random_state=RANDOM_STATE, scale_pos_weight=scale_pos_weight)
    model.fit(X_train, y_train)

    print("\n--- Avaliação do Modelo ---")
    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    accuracy = accuracy_score(y_test, model.predict(X_test))
    print(f"AUC Score (Teste): {auc:.4f}")
    print(f"Acurácia (Teste): {accuracy:.4f}")
    print("--------------------------\n")
    return model

def main():
    X, y = prepare_data_for_modeling(PROCESSED_DATA_FILE)
    trained_model = train_and_evaluate_model(X, y)
    
    print("A salvar modelo e colunas...")
    joblib.dump(trained_model, MODEL_OUTPUT_FILE)
    joblib.dump(X.columns.tolist(), COLUMNS_OUTPUT_FILE)
    print("\n✅ Treino concluído e modelo salvo com sucesso!")

if __name__ == "__main__":
    main()