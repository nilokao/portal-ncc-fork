"""
views.py
--------
Fluxo: upload → revisão (mover/remover) → confirmar sync com Google Groups
"""

import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages

from .utils import processar_arquivo
from .google_service import sincronizar_grupos


# ------------------------------------------------------------------
# 1. Upload
# ------------------------------------------------------------------

def upload(request):
    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo')

        if not arquivo:
            messages.error(request, 'Nenhum arquivo enviado.')
            return render(request, 'portal/upload.html')

        extensao = arquivo.name.rsplit('.', 1)[-1].lower()
        if extensao not in ('csv', 'ods', 'xlsx'):
            messages.error(request, 'Formato não suportado. Use CSV, ODS ou XLSX.')
            return render(request, 'portal/upload.html')

        try:
            grupos = processar_arquivo(arquivo)
        except ValueError as e:
            messages.error(request, str(e))
            return render(request, 'portal/upload.html')

        request.session['grupos'] = grupos
        return redirect('revisao')

    return render(request, 'portal/upload.html')


# ------------------------------------------------------------------
# 2. Revisão
# ------------------------------------------------------------------

def revisao(request):
    grupos = request.session.get('grupos')

    if not grupos:
        messages.warning(request, 'Nenhum arquivo processado. Faça o upload primeiro.')
        return redirect('upload')

    contagens = {chave: len(membros) for chave, membros in grupos.items()}
    total = sum(contagens.values())

    # Metadados dos grupos: (chave, label legível, classe CSS do badge)
    grupos_meta = [
        ('matriculados_cc', 'Matriculados — Ciência da Computação', 'badge-mat'),
        ('matriculados_si', 'Matriculados — Sistemas de Informação', 'badge-mat'),
        ('egressos_cc',     'Egressos — Ciência da Computação',     'badge-egr'),
        ('egressos_si',     'Egressos — Sistemas de Informação',    'badge-egr'),
    ]

    return render(request, 'portal/revisao.html', {
        'grupos': grupos,
        'contagens': contagens,
        'total': total,
        'grupos_meta': grupos_meta,
    })


# ------------------------------------------------------------------
# 3. Endpoints AJAX chamados pelo JS da tela de revisão
# ------------------------------------------------------------------

@require_POST
def mover_aluno(request):
    """Move um aluno de um grupo para outro."""
    dados = json.loads(request.body)
    email       = dados.get('email')
    grupo_orig  = dados.get('de')
    grupo_dest  = dados.get('para')

    grupos = request.session.get('grupos', {})

    if grupo_orig not in grupos or grupo_dest not in grupos:
        return JsonResponse({'ok': False, 'erro': 'Grupo inválido.'}, status=400)

    aluno = next((a for a in grupos[grupo_orig] if a['email'] == email), None)
    if not aluno:
        return JsonResponse({'ok': False, 'erro': 'Aluno não encontrado.'}, status=404)

    grupos[grupo_orig].remove(aluno)
    grupos[grupo_dest].append(aluno)
    request.session['grupos'] = grupos          # força gravação na sessão
    request.session.modified = True

    return JsonResponse({'ok': True})


@require_POST
def remover_aluno(request):
    """Remove um aluno de um grupo (não vai para nenhum outro)."""
    dados = json.loads(request.body)
    email = dados.get('email')
    grupo = dados.get('grupo')

    grupos = request.session.get('grupos', {})

    if grupo not in grupos:
        return JsonResponse({'ok': False, 'erro': 'Grupo inválido.'}, status=400)

    antes = len(grupos[grupo])
    grupos[grupo] = [a for a in grupos[grupo] if a['email'] != email]

    if len(grupos[grupo]) == antes:
        return JsonResponse({'ok': False, 'erro': 'Aluno não encontrado.'}, status=404)

    request.session['grupos'] = grupos
    request.session.modified = True

    return JsonResponse({'ok': True})


# ------------------------------------------------------------------
# 4. Confirmar sincronização
# ------------------------------------------------------------------

@require_POST
def confirmar_sync(request):
    grupos = request.session.get('grupos')

    if not grupos:
        messages.error(request, 'Sessão expirada. Faça o upload novamente.')
        return redirect('upload')

    try:
        sincronizar_grupos(grupos)
    except Exception as e:
        messages.error(request, f'Erro ao sincronizar com o Google: {e}')
        return redirect('revisao')

    del request.session['grupos']
    messages.success(request, 'Grupos sincronizados com sucesso!')
    return redirect('sucesso')


def sucesso(request):
    return render(request, 'portal/sucesso.html')