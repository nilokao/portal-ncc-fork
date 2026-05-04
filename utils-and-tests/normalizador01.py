import pandas as pd
import unicodedata
import os

def remover_acentos(texto):
    if not isinstance(texto, str):
        return str(texto)

    nfkd_form = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd_form if not unicodedata.combining(c))


def normalizar_valor(valor):
    if pd.isna(valor) or str(valor).strip() == "":
        return "NAN"

    texto = remover_acentos(str(valor)).strip()
    return texto.upper()


def normalizar_planilha():
    arquivos = [f for f in os.listdir(".") if f.endswith(".ods")]

    if not arquivos:
        print("erro: nenhum arquivo .ods encontrado na pasta.")
        return

    print("\n--- SELEÇÃO DE ARQUIVO ---")
    for i, arq in enumerate(arquivos):
        print(f"[{i}] {arq}")

    try:
        idx_arq = int(input("\nescolha o número do arquivo: "))
        nome_arquivo = arquivos[idx_arq]
    except (ValueError, IndexError):
        print("seleção inválida")
        return

    try:
        df = pd.read_excel(nome_arquivo, engine="odf")
    except Exception as e:
        print(f"erro ao ler o arquivo: {e}")
        return

    colunas_alteradas = set()

    while True:
        print("\n" + "=" * 30)
        print(f"ARQUIVO: {nome_arquivo}")
        print("COLUNAS DISPONÍVEIS:")

        for i, col in enumerate(df.columns):
            status = "[OK]" if col in colunas_alteradas else "    "
            print(f"{status} [{i}] {col}")

        print("\nOpções:")
        print(" - digite o número da coluna para normalizar")
        print(" - digite 'S' para salvar e sair")
        print(" - digite 'Q' para sair sem salvar")

        escolha = input("\no que deseja fazer? ").strip().upper()

        if escolha == "S":
            if not colunas_alteradas:
                print("nenhuma alteração feita")
            else:
                nome_saida = nome_arquivo.replace(".ods", "-NORMALIZADO.csv")
                df.to_csv(nome_saida, index=False, encoding="utf-8-sig")
                print(f"\narquivo '{nome_saida}' exportado")
            break

        if escolha == "Q":
            print("operação cancelada pelo user")
            break

        try:
            idx_col = int(escolha)
            coluna_alvo = df.columns[idx_col]

            print(f"normalizando coluna: {coluna_alvo}...")
            df[coluna_alvo] = df[coluna_alvo].apply(normalizar_valor)

            colunas_alteradas.add(coluna_alvo)
            print(f"coluna '{coluna_alvo}' processada com sucesso")

        except (ValueError, IndexError):
            print("\nopção inválida, tente o número da coluna, 'S' ou 'Q'")


if __name__ == "__main__":
    normalizar_planilha()