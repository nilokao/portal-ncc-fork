"""
google_service.py
-----------------
simulação local da sincronização dos grupos.

por enquanto não integra com google workspace.
apenas gera um arquivo JSON com o resultado da sincronização.
"""

import json
from pathlib import Path
from datetime import datetime


GRUPOS_EMAIL = {
    'matriculados_cc': 'matriculados-cc-simulado@inf.ufsm.br',
    'matriculados_si': 'matriculados-si-simulado@inf.ufsm.br',
    'egressos_cc': 'egressos-cc-simulado@inf.ufsm.br',
    'egressos_si': 'egressos-si-simulado@inf.ufsm.br',
}


def sincronizar_grupos(grupos: dict):
    """
    simula a sincronização dos grupos.

    em vez de chamar a api do google, salva o estado final em:
    simulacoes/sync_YYYYMMDD_HHMMSS.json
    """

    pasta = Path("simulacoes")
    pasta.mkdir(exist_ok=True)

    resultado = {
        "simulado": True,
        "data_hora": datetime.now().isoformat(timespec="seconds"),
        "grupos": {},
    }

    for chave, membros in grupos.items():
        grupo_email = GRUPOS_EMAIL.get(chave, f"{chave}@grupo-simulado.local")

        resultado["grupos"][chave] = {
            "grupo_email": grupo_email,
            "total_membros": len(membros),
            "membros": membros,
        }

    nome_arquivo = datetime.now().strftime("sync_%Y%m%d_%H%M%S.json")
    caminho = pasta / nome_arquivo

    with caminho.open("w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    return resultado