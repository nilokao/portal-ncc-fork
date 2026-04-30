import os
import time
from collections import defaultdict

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.group.member"
]

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SA_FILE", "credentials.json")
ADMIN_EMAIL = os.getenv("GOOGLE_ADMIN_EMAIL")

GRUPOS_EMAIL = {
    "matriculados_cc": "matriculados-teste@inf.ufsm.br",
    "matriculados_si": "matriculados-teste@inf.ufsm.br",
    "egressos_cc": "egressos-teste@inf.ufsm.br",
    "egressos_si": "egressos-teste@inf.ufsm.br",
}


def _get_service():
    if not ADMIN_EMAIL:
        raise ValueError("GOOGLE_ADMIN_EMAIL não definido.")

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    ).with_subject(ADMIN_EMAIL)

    return build("admin", "directory_v1", credentials=creds)


def _listar_membros(service, grupo_email: str) -> set[str]:
    membros = set()

    req = service.members().list(groupKey=grupo_email)

    while req is not None:
        resp = req.execute()

        for membro in resp.get("members", []):
            email = membro.get("email")
            if email:
                membros.add(email.strip().lower())

        req = service.members().list_next(req, resp)

    return membros


def _remover_membro(service, grupo_email: str, email: str):
    try:
        service.members().delete(
            groupKey=grupo_email,
            memberKey=email,
        ).execute()

        print(f"removido: {email} de {grupo_email}")

    except HttpError as e:
        if e.resp.status == 404:
            print(f"já não estava no grupo: {email}")
            return

        raise


def _adicionar_membro(service, grupo_email: str, email: str):
    try:
        service.members().insert(
            groupKey=grupo_email,
            body={
                "email": email,
                "role": "MEMBER",
            },
        ).execute()

        print(f"adicionado: {email} em {grupo_email}")

    except HttpError as e:
        if e.resp.status == 409:
            print(f"já existe no grupo: {email}")
            return

        raise


def _montar_membros_por_grupo_email(grupos: dict) -> dict[str, set[str]]:
    membros_por_grupo_email = defaultdict(set)

    for chave, membros in grupos.items():
        grupo_email = GRUPOS_EMAIL.get(chave)

        if not grupo_email:
            raise ValueError(f"Grupo '{chave}' não configurado em GRUPOS_EMAIL.")

        for aluno in membros:
            email = aluno.get("email", "").strip().lower()

            if email:
                membros_por_grupo_email[grupo_email].add(email)

    return dict(membros_por_grupo_email)


def sincronizar_grupos(grupos: dict):
    service = _get_service()

    membros_por_grupo_email = _montar_membros_por_grupo_email(grupos)

    for grupo_email, emails_desejados in membros_por_grupo_email.items():
        print("=" * 60)
        print(f"sincronizando grupo real: {grupo_email}")
        print(f"membros desejados: {len(emails_desejados)}")

        emails_atuais = _listar_membros(service, grupo_email)

        print(f"membros atuais: {len(emails_atuais)}")

        print("removendo membros atuais...")
        for email in emails_atuais:
            _remover_membro(service, grupo_email, email)
            time.sleep(0.1)

        print("adicionando membros desejados...")
        for email in emails_desejados:
            _adicionar_membro(service, grupo_email, email)
            time.sleep(0.1)

    print("sincronização finalizada")