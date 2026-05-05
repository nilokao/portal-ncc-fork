import os
import re
import time
import random

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.group.member"
]

CLIENT_SECRET_FILE = os.getenv("GOOGLE_CLIENT_SECRET_FILE", "client_secret.json")
TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")

SLEEP_ENTRE_CHAMADAS = 0.5
MAX_TENTATIVAS = 5

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ------------ ALTERAR AQUI ------------ #
GRUPOS_EMAIL = {
    "matriculados_cc": "matriculados-teste@inf.ufsm.br",
    "matriculados_si": "matriculados-teste@inf.ufsm.br",
    "egressos_cc": "egressos-teste@inf.ufsm.br",
    "egressos_si": "egressos-teste@inf.ufsm.br",
}

def _get_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                raise FileNotFoundError(
                    f"arquivo OAuth não encontrado: {CLIENT_SECRET_FILE}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                SCOPES,
            )

            creds = flow.run_local_server(
                port=0,
                prompt="consent",
            )

        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("admin", "directory_v1", credentials=creds)

def _email_valido(email: str) -> bool:
    return bool(EMAIL_RE.match(email.strip().lower()))

def _normalizar_email(email: str) -> str | None:
    email = (email or "").strip().lower()

    if not email:
        return None

    if not _email_valido(email):
        print(f"email inválido ignorado: {email}")
        return None

    usuario, dominio = email.split("@", 1)

    if dominio in ("gmail.com", "googlemail.com"):
        usuario = usuario.replace(".", "")
        dominio = "gmail.com"

    return f"{usuario}@{dominio}"

def _modo_da_chave(chave: str) -> str:
    if chave.startswith("matriculados"):
        return "sync_exato"

    if chave.startswith("egressos"):
        return "somente_adicionar"

    raise ValueError(f"tipo de grupo desconhecido: {chave}")

def _montar_planejamento(grupos: dict) -> dict:
    planejamento = {}

    for chave, membros in grupos.items():
        grupo_email = GRUPOS_EMAIL.get(chave)

        if not grupo_email:
            raise ValueError(f"grupo '{chave}' não configurado em GRUPOS_EMAIL.")

        modo = _modo_da_chave(chave)

        if grupo_email not in planejamento:
            planejamento[grupo_email] = {
                "modo": modo,
                "emails": set(),
                "origens": set(),
            }

        modo_existente = planejamento[grupo_email]["modo"]

        if modo_existente != modo:
            raise ValueError(
                f"o grupo real '{grupo_email}' recebeu grupos lógicos com modos diferentes: "
                f"{modo_existente} e {modo}. revise o GRUPOS_EMAIL."
            )

        planejamento[grupo_email]["origens"].add(chave)

        for aluno in membros:
            email = _normalizar_email(aluno.get("email", ""))

            if email:
                planejamento[grupo_email]["emails"].add(email)

    return planejamento

def _executar_com_retry(request, descricao: str, tentativas: int = MAX_TENTATIVAS):
    for tentativa in range(1, tentativas + 1):
        try:
            return request.execute()

        except HttpError as e:
            status = e.resp.status

            if status in (403, 429, 500, 502, 503, 504):
                espera = min(60, (2 ** tentativa) + random.uniform(0, 1))
                print(
                    f"[retry {tentativa}/{tentativas}] {descricao} falhou com HTTP {status}. "
                    f"aguardando {espera:.1f}s..."
                )
                time.sleep(espera)
                continue

            raise

        except (ConnectionResetError, TimeoutError, OSError) as e:
            espera = min(60, (2 ** tentativa) + random.uniform(0, 1))
            print(
                f"[retry {tentativa}/{tentativas}] {descricao} falhou com conexão: {repr(e)}. "
                f"aguardando {espera:.1f}s..."
            )
            time.sleep(espera)

    raise RuntimeError(f"falhou após {tentativas} tentativas: {descricao}")

def _listar_membros(service, grupo_email: str) -> dict[str, str]:
    membros = {}

    req = service.members().list(groupKey=grupo_email)

    while req is not None:
        resp = _executar_com_retry(req, f"listar membros de {grupo_email}")

        for membro in resp.get("members", []):
            email = _normalizar_email(membro.get("email", ""))
            role = membro.get("role", "MEMBER")

            if email:
                membros[email] = role

        req = service.members().list_next(req, resp)

    return membros

def _adicionar_membro(service, grupo_email: str, email: str) -> bool:
    try:
        req = service.members().insert(
            groupKey=grupo_email,
            body={
                "email": email,
                "role": "MEMBER",
            },
        )

        _executar_com_retry(req, f"adicionar {email} em {grupo_email}")

        print(f"adicionado: {email} em {grupo_email}")
        return True

    except HttpError as e:
        status = e.resp.status

        if status == 409:
            print(f"já estava no grupo, pulando: {email}")
            return True

        if status == 404:
            print(
                f"email não encontrado ou externo não permitido, ignorando: "
                f"{email} em {grupo_email}"
            )
            return False

        if status == 400:
            print(f"email inválido, ignorando: {email} em {grupo_email}")
            return False

        if status == 403:
            print(
                f"sem permissão para adicionar {email} em {grupo_email}. "
                f"talvez o grupo não permita membros externos."
            )
            return False

        print(f"erro ao adicionar {email} em {grupo_email}: {status} - {e}")
        return False

    except Exception as e:
        print(f"erro inesperado ao adicionar {email} em {grupo_email}: {repr(e)}")
        return False

def _remover_membro(service, grupo_email: str, email: str) -> bool:
    try:
        req = service.members().delete(
            groupKey=grupo_email,
            memberKey=email,
        )

        _executar_com_retry(req, f"remover {email} de {grupo_email}")

        print(f"removido: {email} de {grupo_email}")
        return True

    except HttpError as e:
        status = e.resp.status

        if status == 404:
            print(f"já não estava no grupo, pulando remoção: {email}")
            return True

        print(f"erro ao remover {email} de {grupo_email}: {status} - {e}")
        return False

    except Exception as e:
        print(f"erro inesperado ao remover {email} de {grupo_email}: {repr(e)}")
        return False

def _sincronizar_matriculados(service, grupo_email: str, emails_desejados: set[str]):
    membros_atuais = _listar_membros(service, grupo_email)
    emails_atuais = set(membros_atuais.keys())

    adicionar = emails_desejados - emails_atuais
    remover = emails_atuais - emails_desejados

    print(f"membros atuais: {len(emails_atuais)}")
    print(f"adicionar: {len(adicionar)}")
    print(f"remover: {len(remover)}")

    erros_adicao = []
    erros_remocao = []
    protegidos = []

    print("adicionando novos matriculados...")
    for email in sorted(adicionar):
        ok = _adicionar_membro(service, grupo_email, email)

        if not ok:
            erros_adicao.append(email)

        time.sleep(SLEEP_ENTRE_CHAMADAS)

    print("removendo quem não está mais como matriculado...")
    for email in sorted(remover):
        role = membros_atuais.get(email)

        if role in ("OWNER", "MANAGER"):
            print(f"não removido por segurança: {email} tem role {role}")
            protegidos.append(email)
            continue

        ok = _remover_membro(service, grupo_email, email)

        if not ok:
            erros_remocao.append(email)

        time.sleep(SLEEP_ENTRE_CHAMADAS)

    return {
        "modo": "sync_exato",
        "desejados": len(emails_desejados),
        "atuais_antes": len(emails_atuais),
        "adicionados": len(adicionar) - len(erros_adicao),
        "removidos": len(remover) - len(erros_remocao) - len(protegidos),
        "protegidos": protegidos,
        "erros_adicao": erros_adicao,
        "erros_remocao": erros_remocao,
    }

def _sincronizar_egressos(service, grupo_email: str, emails_desejados: set[str]):
    membros_atuais = _listar_membros(service, grupo_email)
    emails_atuais = set(membros_atuais.keys())

    adicionar = emails_desejados - emails_atuais

    print(f"membros atuais: {len(emails_atuais)}")
    print(f"novos egressos para adicionar: {len(adicionar)}")
    print("não será removido ninguém dos egressos.")

    erros_adicao = []

    for email in sorted(adicionar):
        ok = _adicionar_membro(service, grupo_email, email)

        if not ok:
            erros_adicao.append(email)

        time.sleep(SLEEP_ENTRE_CHAMADAS)

    return {
        "modo": "somente_adicionar",
        "desejados": len(emails_desejados),
        "atuais_antes": len(emails_atuais),
        "adicionados": len(adicionar) - len(erros_adicao),
        "removidos": 0,
        "erros_adicao": erros_adicao,
        "erros_remocao": [],
    }


def sincronizar_grupos(grupos: dict):
    service = _get_service()
    planejamento = _montar_planejamento(grupos)

    resultado = {}

    for grupo_email, info in planejamento.items():
        modo = info["modo"]
        emails_desejados = info["emails"]
        origens = ", ".join(sorted(info["origens"]))

        print("=" * 60)
        print(f"grupo real: {grupo_email}")
        print(f"grupos lógicos: {origens}")
        print(f"modo: {modo}")
        print(f"emails desejados: {len(emails_desejados)}")

        if modo == "sync_exato":
            resultado[grupo_email] = _sincronizar_matriculados(
                service,
                grupo_email,
                emails_desejados,
            )

        elif modo == "somente_adicionar":
            resultado[grupo_email] = _sincronizar_egressos(
                service,
                grupo_email,
                emails_desejados,
            )

        else:
            raise ValueError(f"modo inválido: {modo}")

    print("=" * 60)
    print("sincronização finalizada")
    print(resultado)

    return resultado