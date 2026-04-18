"""
utils.py
--------
Processa o arquivo CSV enviado pelo usuário e classifica cada aluno
nos 4 grupos usando o contador_instancias como base de inspeção.

IMPORTANTE: contador_instancias.py trabalha com filepath (str).
Aqui salvamos o upload em memória temporária para compatibilidade.
"""

import csv
import io
import tempfile
import os
from collections import Counter

# ------------------------------------------------------------------
# Constantes — ajuste conforme os valores reais do seu CSV
# ------------------------------------------------------------------

# Nome exato da coluna que indica o curso no CSV
COLUNA_CURSO    = "COLUNA_CURSO"          # ex: "CC" ou "SI"
COLUNA_SITUACAO = "FORMA_EVASA0"       # ex: "Matriculado" ou "Egresso"
COLUNA_NOME     = "NOME_PESSOA"
COLUNA_EMAIL    = "DESCR_MAIL"

# Valores que aparecem na coluna situacao
VALOR_MATRICULADO = "ESTUDANTE REGULAR"
VALOR_EGRESSO     = "ABANDONO"

# Valores que aparecem na coluna curso
VALOR_CC = "CIENCIA DA COMPUTACAO - BACHARELADO"
VALOR_SI = "BACHARELADO EM SISTEMAS DE INFORMACAO"

# ------------------------------------------------------------------
# Função principal
# ------------------------------------------------------------------

def processar_arquivo(arquivo) -> dict:
    """
    Recebe um InMemoryUploadedFile (Django) e retorna dict com 4 listas:
        {
            'matriculados_cc': [{'nome': ..., 'email': ...}, ...],
            'egressos_cc':     [...],
        }
    """
    grupos = {
        'matriculados_cc': [],
        'egressos_cc':     [],
    }

    # Lê o conteúdo do upload em memória
    conteudo = arquivo.read()

    # Tenta UTF-8 primeiro, cai em latin-1 (padrão de exports brasileiros)
    try:
        texto = conteudo.decode('utf-8')
    except UnicodeDecodeError:
        texto = conteudo.decode('latin-1')

    reader = csv.DictReader(io.StringIO(texto))

    # Valida se as colunas necessárias existem
    if reader.fieldnames is None:
        raise ValueError("Arquivo CSV vazio ou sem cabeçalho.")

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

        chave = _classificar(situacao, curso)
        if chave and email:
            grupos[chave].append({'nome': nome, 'email': email})

    return grupos


def _classificar(situacao: str, curso: str) -> str | None:
    """Retorna a chave do grupo ou None se não reconhecido."""
    s = situacao.lower()
    c = curso.upper()

    if VALOR_MATRICULADO.lower() in s:
        if c == VALOR_CC:
            return 'matriculados_cc'
    elif VALOR_EGRESSO.lower() in s:
        if c == VALOR_CC:
            return 'egressos_cc'
    return None


# ------------------------------------------------------------------
# Utilitário para inspecionar o CSV antes de processar
# (usa as funções do contador_instancias sem depender de filepath)
# ------------------------------------------------------------------

def inspecionar_colunas(arquivo) -> dict:
    """
    Retorna um resumo das colunas e valores únicos do CSV.
    Útil para depuração quando os nomes das colunas são desconhecidos.

    Retorna:
        {
            'colunas': ['col1', 'col2', ...],
            'contagens': {'col1': Counter({...}), ...}
        }
    """
    conteudo = arquivo.read()
    arquivo.seek(0)  # rebobina para processar_arquivo poder ler depois

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