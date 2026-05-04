import csv
import io
from collections import Counter

import pandas as pd


COLUNA_CURSO = "COD_CURSO"
COLUNA_SITUACAO = "FORMA_EVASA0"
COLUNA_NOME = "NOME_PESSOA"
COLUNA_EMAIL = "DESCR_MAIL"

VALOR_MATRICULADO = "Estudante Regular"

VALOR_CC = "307"
VALOR_SI = "314"


def processar_arquivo(arquivo) -> dict:
    grupos = {
        "matriculados_cc": [],
        "matriculados_si": [],
        "egressos_cc": [],
        "egressos_si": [],
    }

    df = _ler_arquivo(arquivo)
    df = _normalizar_colunas(df)
    _validar_colunas(df)

    for _, row in df.iterrows():
        situacao = str(row.get(COLUNA_SITUACAO, "")).strip()
        curso = str(row.get(COLUNA_CURSO, "")).strip()
        nome = str(row.get(COLUNA_NOME, "")).strip()
        email = normalizar_email(row.get(COLUNA_EMAIL, ""))

        if not email:
            continue

        chave = _classificar(situacao, curso)

        if chave:
            grupos[chave].append({
                "nome": nome,
                "email": email,
            })

    return grupos


def _ler_arquivo(arquivo) -> pd.DataFrame:
    nome = arquivo.name.lower()

    if nome.endswith(".csv"):
        return _ler_csv(arquivo)

    if nome.endswith(".ods"):
        return pd.read_excel(arquivo, engine="odf", dtype=str)

    if nome.endswith(".xlsx"):
        return pd.read_excel(arquivo, engine="openpyxl", dtype=str)

    raise ValueError("Formato não suportado. Use CSV, ODS ou XLSX.")


def _ler_csv(arquivo) -> pd.DataFrame:
    conteudo = arquivo.read()

    try:
        texto = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = conteudo.decode("latin-1")

    linhas = texto.splitlines()
    primeira_linha = linhas[0] if linhas else ""

    sep = ";" if ";" in primeira_linha else ","

    return pd.read_csv(io.StringIO(texto), sep=sep, dtype=str)


def _normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df


def _validar_colunas(df: pd.DataFrame):
    obrigatorias = [
        COLUNA_CURSO,
        COLUNA_SITUACAO,
        COLUNA_NOME,
        COLUNA_EMAIL,
    ]

    faltando = [
        col for col in obrigatorias
        if col not in df.columns
    ]

    if faltando:
        raise ValueError(
            "Colunas obrigatórias não encontradas: "
            + ", ".join(faltando)
            + f". Colunas disponíveis: {list(df.columns)}"
        )


def normalizar_email(valor) -> str | None:
    email = str(valor or "").strip().lower()

    if email in ("", "nan", "none", "null"):
        return None

    if "@" not in email:
        return None

    usuario, dominio = email.split("@", 1)

    if dominio in ("gmail.com", "googlemail.com"):
        usuario = usuario.replace(".", "")
        dominio = "gmail.com"

    return f"{usuario}@{dominio}"


def _classificar(situacao: str, curso: str) -> str | None:
    s = situacao.lower()
    c = curso.strip()

    if VALOR_MATRICULADO.lower() in s:
        if c == VALOR_CC:
            return "matriculados_cc"

        if c == VALOR_SI:
            return "matriculados_si"

    else:
        if c == VALOR_CC:
            return "egressos_cc"

        if c == VALOR_SI:
            return "egressos_si"

    return None


def inspecionar_colunas(arquivo) -> dict:
    df = _ler_arquivo(arquivo)
    df = _normalizar_colunas(df)

    contagens = {}

    for col in df.columns:
        valores = df[col].fillna("NAN").astype(str)
        contagens[col] = Counter(valores)

    return {
        "colunas": list(df.columns),
        "contagens": contagens,
    }