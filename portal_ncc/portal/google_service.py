"""
google_service.py
-----------------
Sincroniza os 4 grupos do Google Workspace via Admin SDK.

Pré-requisitos:
  1. Criar Service Account no Google Cloud Console
  2. Habilitar "Admin SDK API" no projeto
  3. No Google Workspace Admin > Segurança > Controles de API >
     Delegação de toda a organização: adicionar o client_id da
     Service Account com o escopo:
       https://www.googleapis.com/auth/admin.directory.group.member
  4. Definir as variáveis de ambiente abaixo (ou preencher direto)
"""

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/admin.directory.group.member']

# -- Configuração via variáveis de ambiente (recomendado) ----------
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SA_FILE', 'credentials.json')
ADMIN_EMAIL          = os.getenv('GOOGLE_ADMIN_EMAIL', 'portal-ncc@inf.ufsm.br')

# Emails dos grupos no Google Workspace
# Preencha com os endereços reais ou defina como env vars
GRUPOS_EMAIL = {
    'matriculados_cc': 'matriculados-teste@inf.ufsm.br',
    'egressos_cc':     'egressos-teste@inf.ufsm.br',
}


def _get_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    ).with_subject(ADMIN_EMAIL)
    return build('admin', 'directory_v1', credentials=creds)


def sincronizar_grupos(grupos: dict):
    """
    Para cada grupo: busca membros atuais no Google,
    adiciona novos e remove quem saiu (diff).
    """
    service = _get_service()

    for chave, membros in grupos.items():
        grupo_email = GRUPOS_EMAIL.get(chave)
        if not grupo_email:
            raise ValueError(
                f"Email do grupo '{chave}' não configurado em GRUPOS_EMAIL."
            )

        emails_novos = {m['email'].lower() for m in membros}

        # Busca membros atuais (paginado)
        emails_atuais = set()
        req = service.members().list(groupKey=grupo_email)
        while req:
            resultado = req.execute()
            for m in resultado.get('members', []):
                emails_atuais.add(m['email'].lower())
            req = service.members().list_next(req, resultado)

        # Adiciona quem entrou
        for email in emails_novos - emails_atuais:
            service.members().insert(
                groupKey=grupo_email,
                body={'email': email, 'role': 'MEMBER'}
            ).execute()

        # Remove quem saiu
        for email in emails_atuais - emails_novos:
            service.members().delete(
                groupKey=grupo_email,
                memberKey=email
            ).execute()