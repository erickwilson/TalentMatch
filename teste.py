import json
import random

def gerar_amostra_de_dicionario_json(arquivo_entrada, arquivo_saida, tamanho_amostra):
    """
    Lê um arquivo JSON estruturado como um dicionário de usuários,
    extrai uma amostra aleatória e a salva em um novo arquivo JSON,
    mantendo a estrutura original.

    Args:
        arquivo_entrada (str): O caminho para o arquivo JSON original.
        arquivo_saida (str): O caminho para o novo arquivo com a amostra.
        tamanho_amostra (int): O número de usuários a serem incluídos na amostra.
    """
    try:
        # 1. Abrir e ler o arquivo JSON original
        print(f"Lendo o arquivo '{arquivo_entrada}'...")
        with open(arquivo_entrada, 'r', encoding='utf-8') as f:
            dados_originais = json.load(f)

        # 2. Verificar se o arquivo é de fato um dicionário
        if not isinstance(dados_originais, dict):
            print("Erro: A estrutura do JSON não é um dicionário como esperado.")
            return

        # 3. Obter a lista de chaves (IDs dos usuários)
        lista_de_ids = list(dados_originais.keys())
        total_usuarios = len(lista_de_ids)
        print(f"Total de {total_usuarios} usuários encontrados.")

        # 4. Validar se o tamanho da amostra é viável
        if total_usuarios < tamanho_amostra:
            print(f"Erro: O arquivo original tem apenas {total_usuarios} usuários, "
                  f"o que é menos que o tamanho da amostra desejado ({tamanho_amostra}).")
            return

        # 5. Selecionar aleatoriamente as chaves para a amostra
        print(f"Gerando amostra aleatória de {tamanho_amostra} usuários...")
        ids_da_amostra = random.sample(lista_de_ids, tamanho_amostra)

        # 6. Construir o novo dicionário com os dados da amostra
        dados_da_amostra = {
            user_id: dados_originais[user_id] for user_id in ids_da_amostra
        }

        # 7. Salvar a amostra em um novo arquivo
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            # indent=4 para formatar o JSON de forma legível
            # ensure_ascii=False para garantir a codificação correta de caracteres especiais
            json.dump(dados_da_amostra, f, ensure_ascii=False, indent=4)

        print("-" * 30)
        print(f"Sucesso! Amostra com {len(dados_da_amostra)} usuários salva em '{arquivo_saida}'.")

    except FileNotFoundError:
        print(f"Erro: O arquivo de entrada '{arquivo_entrada}' não foi encontrado.")
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{arquivo_entrada}' não é um JSON válido.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")


# --- Como usar ---
if __name__ == "__main__":
    # Defina os nomes dos arquivos e o tamanho da amostra aqui
    arquivo_json_original = 'applicants.json'
    arquivo_json_amostra = 'amostra_applicants.json'
    numero_de_amostras = 5000

    gerar_amostra_de_dicionario_json(arquivo_json_original, arquivo_json_amostra, numero_de_amostras)