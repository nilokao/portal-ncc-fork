import csv
import io
import tempfile
import os
from collections import Counter

# Nome exato da coluna que indica o curso no CSV
COLUNA_CURSO    = "NOME_CURSO"          # CC ou SI
COLUNA_SITUACAO = "FORMA_EVASA0"        # Matriculado ou Egresso
COLUNA_NOME     = "NOME_PESSOA"
COLUNA_EMAIL    = "DESCR_MAIL"

# Valores que aparecem na coluna situacao
VALOR_MATRICULADO = "ESTUDANTE REGULAR"

# Valores que aparecem na coluna curso
VALOR_CC = "CIENCIA DA COMPUTACAO - BACHARELADO"
VALOR_SI = "BACHARELADO EM SISTEMAS DE INFORMACAO"

def processar_arquivo(arquivo) -> dict:
    grupos = {
        'matriculados_cc': [],
        'matriculados_si': [],
        'egressos_cc': [],
        'egressos_si': [],
    }
    conteudo = arquivo.read()

    try:
        texto = conteudo.decode('utf-8')
    except UnicodeDecodeError:
        texto = conteudo.decode('latin-1')

    reader = csv.DictReader(io.StringIO(texto))

    if reader.fieldnames is None:
        raise ValueError("Arquivo vazio ou sem cabeçalho.")

    colunas = [c.strip() for c in reader.fieldnames]
    for col in [COLUNA_CURSO, COLUNA_SITUACAO, COLUNA_NOME, COLUNA_EMAIL]:
        if col not in colunas:
            raise ValueError(
                f"Coluna '{col}' não encontrada. "
                f"Colunas disponíveis: {colunas}"
            )

    for row in reader:
        situacao = row.get(COLUNA_SITUACAO, "").strip()
        curso    = row.get(COLUNA_CURSO,    "").strip()
        nome     = row.get(COLUNA_NOME,     "").strip()
        email    = row.get(COLUNA_EMAIL,    "").strip()

        chave = _classificar(situacao, curso, email)
        if chave and email:
            grupos[chave].append({'nome': nome, 'email': email})

    return grupos


def _classificar(situacao: str, curso: str, email: str) -> str | None:
    s = situacao.lower()
    c = curso.upper()
    e = email.upper()

    if e != 'NAN':
        if VALOR_MATRICULADO.lower() in s:
            if c == VALOR_CC:
                return 'matriculados_cc'
            if c == VALOR_SI:
                return 'matriculados_si'

        else:
            if c == VALOR_CC:
                return 'egressos_cc'
            if c == VALOR_SI:
                return 'egressos_si'

    return None

def inspecionar_colunas(arquivo) -> dict:
    conteudo = arquivo.read()
    arquivo.seek(0)

    try:
        texto = conteudo.decode('utf-8')
    except UnicodeDecodeError:
        texto = conteudo.decode('latin-1')

    reader = csv.DictReader(io.StringIO(texto))
    headers = list(reader.fieldnames or [])
    rows = [dict(row) for row in reader]

    contagens = {}
    for col in headers:
        contagens[col] = Counter(row[col] for row in rows)

    return {'colunas': headers, 'contagens': contagens}