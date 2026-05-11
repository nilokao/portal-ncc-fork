import json
import os
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .google_service import sincronizar_grupos
from .utils import processar_arquivo


GRUPOS_META_DICT = {
    "matriculados_cc": ("Matriculados — Ciência da Computação", "badge-mat"),
    "matriculados_si": ("Matriculados — Sistemas de Informação", "badge-mat"),
    "egressos_cc": ("Egressos — Ciência da Computação", "badge-egr"),
    "egressos_si": ("Egressos — Sistemas de Informação", "badge-egr"),
}

GRUPOS_POR_MODO = {
    "cc": ["matriculados_cc", "egressos_cc"],
    "si": ["matriculados_si", "egressos_si"],
    "ambos": ["matriculados_cc", "matriculados_si", "egressos_cc", "egressos_si"],
}


def _pasta_uploads_temp() -> Path:
    pasta = Path(settings.BASE_DIR) / "uploads_temp"
    pasta.mkdir(exist_ok=True)
    return pasta


def _limpar_arquivo_temp(request):
    caminho = request.session.get("arquivo_path")

    if caminho and os.path.exists(caminho):
        try:
            os.remove(caminho)
        except OSError:
            pass

    request.session.pop("arquivo_path", None)
    request.session.pop("arquivo_nome", None)


def _limpar_estado_fluxo(request, limpar_arquivo=False, limpar_resultado=False):
    request.session.pop("grupos", None)
    request.session.pop("modo_curso", None)
    request.session.pop("cursos_processados", None)

    if limpar_resultado:
        request.session.pop("resultado_sync", None)

    if limpar_arquivo:
        _limpar_arquivo_temp(request)

    request.session.modified = True


def _montar_grupos_meta(grupos: dict):
    grupos_meta = []

    for chave in grupos.keys():
        label, badge_class = GRUPOS_META_DICT[chave]
        grupos_meta.append((chave, label, badge_class))

    return grupos_meta


def _juntar_resultados_sync(resultado_anterior, resultado_novo):
    if not resultado_anterior:
        return resultado_novo or {}

    if not resultado_novo:
        return resultado_anterior or {}

    acumulado = resultado_anterior.copy()

    for grupo_email, info_nova in resultado_novo.items():
        if grupo_email not in acumulado:
            acumulado[grupo_email] = info_nova
            continue

        info_antiga = acumulado[grupo_email]

        for campo in ("desejados", "atuais_antes", "adicionados", "removidos"):
            info_antiga[campo] = info_antiga.get(campo, 0) + info_nova.get(campo, 0)

        info_antiga.setdefault("protegidos", [])
        info_antiga.setdefault("erros_adicao", [])
        info_antiga.setdefault("erros_remocao", [])

        info_antiga["protegidos"].extend(info_nova.get("protegidos", []))
        info_antiga["erros_adicao"].extend(info_nova.get("erros_adicao", []))
        info_antiga["erros_remocao"].extend(info_nova.get("erros_remocao", []))

    return acumulado


def upload(request):
    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")

        if not arquivo:
            messages.error(request, "Nenhum arquivo enviado.")
            return render(request, "portal/upload.html")

        extensao = arquivo.name.rsplit(".", 1)[-1].lower()

        if extensao not in ("csv", "ods", "xlsx"):
            messages.error(request, "Formato não suportado. Use CSV, ODS ou XLSX.")
            return render(request, "portal/upload.html")

        _limpar_estado_fluxo(request, limpar_arquivo=True, limpar_resultado=True)

        fs = FileSystemStorage(location=_pasta_uploads_temp())
        nome_salvo = fs.save(arquivo.name, arquivo)
        caminho_arquivo = fs.path(nome_salvo)

        request.session["arquivo_path"] = caminho_arquivo
        request.session["arquivo_nome"] = arquivo.name
        request.session["cursos_processados"] = []
        request.session.modified = True

        return redirect("escolher_curso")

    return render(request, "portal/upload.html")


def escolher_curso(request):
    if not request.session.get("arquivo_path"):
        messages.warning(request, "Nenhum arquivo enviado. Faça o upload primeiro.")
        return redirect("upload")

    return render(request, "portal/escolher_curso.html", {
        "arquivo_nome": request.session.get("arquivo_nome"),
    })


@require_POST
def selecionar_curso(request):
    modo = request.POST.get("modo")
    caminho_arquivo = request.session.get("arquivo_path")
    processados = request.session.get("cursos_processados", [])

    if not caminho_arquivo:
        messages.warning(request, "Sessão expirada. Faça o upload novamente.")
        return redirect("upload")

    if modo not in GRUPOS_POR_MODO:
        messages.error(request, "Escolha inválida.")
        return redirect("escolher_curso")

    if modo in ("cc", "si") and modo in processados:
        messages.warning(request, "Este curso já foi sincronizado neste fluxo.")
        return redirect("proximo_curso")

    try:
        grupos = processar_arquivo(caminho_arquivo, modo=modo)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("escolher_curso")

    request.session["modo_curso"] = modo
    request.session["grupos"] = grupos
    request.session.modified = True

    return redirect("revisao")


def revisao(request):
    grupos = request.session.get("grupos")

    if not grupos:
        messages.warning(request, "Escolha o curso antes de revisar.")
        return redirect("escolher_curso")

    contagens = {chave: len(membros) for chave, membros in grupos.items()}
    total = sum(contagens.values())

    grupos_meta = _montar_grupos_meta(grupos)
    grupos_chaves = list(grupos.keys())

    return render(request, "portal/revisao.html", {
        "grupos": grupos,
        "contagens": contagens,
        "total": total,
        "grupos_meta": grupos_meta,
        "grupos_chaves_json": json.dumps(grupos_chaves),
    })


@require_POST
def mover_aluno(request):
    dados = json.loads(request.body)

    email = dados.get("email")
    grupo_orig = dados.get("de")
    grupo_dest = dados.get("para")

    grupos = request.session.get("grupos", {})

    if grupo_orig not in grupos or grupo_dest not in grupos:
        return JsonResponse({"ok": False, "erro": "Grupo inválido."}, status=400)

    aluno = next((a for a in grupos[grupo_orig] if a["email"] == email), None)

    if not aluno:
        return JsonResponse({"ok": False, "erro": "Aluno não encontrado."}, status=404)

    grupos[grupo_orig].remove(aluno)
    grupos[grupo_dest].append(aluno)

    request.session["grupos"] = grupos
    request.session.modified = True

    return JsonResponse({"ok": True})


@require_POST
def remover_aluno(request):
    dados = json.loads(request.body)

    email = dados.get("email")
    grupo = dados.get("grupo")

    grupos = request.session.get("grupos", {})

    if grupo not in grupos:
        return JsonResponse({"ok": False, "erro": "Grupo inválido."}, status=400)

    antes = len(grupos[grupo])
    grupos[grupo] = [aluno for aluno in grupos[grupo] if aluno["email"] != email]

    if len(grupos[grupo]) == antes:
        return JsonResponse({"ok": False, "erro": "Aluno não encontrado."}, status=404)

    request.session["grupos"] = grupos
    request.session.modified = True

    return JsonResponse({"ok": True})


@require_POST
def confirmar_sync(request):
    grupos = request.session.get("grupos")
    modo = request.session.get("modo_curso")

    if not grupos or not modo:
        messages.error(request, "Sessão expirada. Faça o upload novamente.")
        return redirect("upload")

    try:
        resultado_novo = sincronizar_grupos(grupos)
    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f"Erro ao sincronizar com o Google: {repr(e)}")
        return redirect("revisao")

    resultado_anterior = request.session.get("resultado_sync", {})
    request.session["resultado_sync"] = _juntar_resultados_sync(resultado_anterior, resultado_novo)

    request.session.pop("grupos", None)

    if modo in ("cc", "si"):
        processados = request.session.get("cursos_processados", [])

        if modo not in processados:
            processados.append(modo)

        request.session["cursos_processados"] = processados
        request.session.pop("modo_curso", None)
        request.session.modified = True

        if set(processados) == {"cc", "si"}:
            _limpar_estado_fluxo(request, limpar_arquivo=True)
            messages.success(request, "Todos os grupos foram sincronizados.")
            return redirect("sucesso")

        return redirect("proximo_curso")

    _limpar_estado_fluxo(request, limpar_arquivo=True)
    messages.success(request, "Grupos sincronizados.")
    return redirect("sucesso")


def proximo_curso(request):
    caminho_arquivo = request.session.get("arquivo_path")
    processados = request.session.get("cursos_processados", [])

    if not caminho_arquivo:
        return redirect("upload")

    restantes = []

    if "cc" not in processados:
        restantes.append(("cc", "Ciência da Computação"))

    if "si" not in processados:
        restantes.append(("si", "Sistemas de Informação"))

    if not restantes:
        _limpar_estado_fluxo(request, limpar_arquivo=True)
        messages.success(request, "Todos os grupos foram sincronizados.")
        return redirect("sucesso")

    proximo, label = restantes[0]

    return render(request, "portal/proximo_curso.html", {
        "proximo": proximo,
        "label": label,
        "arquivo_nome": request.session.get("arquivo_nome"),
    })


def finalizar(request):
    _limpar_estado_fluxo(request, limpar_arquivo=True)
    messages.success(request, "Fluxo finalizado.")
    return redirect("sucesso")


def sucesso(request):
    resultado_sync = request.session.pop("resultado_sync", None)

    erros = []

    if resultado_sync:
        for grupo_email, info in resultado_sync.items():
            for erro in info.get("erros_adicao", []):
                erros.append(erro)

            for erro in info.get("erros_remocao", []):
                erros.append(erro)

    return render(request, "portal/sucesso.html", {
        "erros_sync": erros,
        "qtd_erros_sync": len(erros),
    })

def voltar_upload(request):
    messages.success(request, "Dados exportados com sucesso.")
    return redirect("upload")