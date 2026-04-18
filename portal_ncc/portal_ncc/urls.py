"""
urls.py — app portal
"""
from django.urls import path
from .. import views

urlpatterns = [
    path('',               views.upload,         name='upload'),
    path('revisao/',       views.revisao,         name='revisao'),
    path('mover/',         views.mover_aluno,     name='mover_aluno'),
    path('remover/',       views.remover_aluno,   name='remover_aluno'),
    path('confirmar/',     views.confirmar_sync,  name='confirmar_sync'),
    path('sucesso/',       views.sucesso,          name='sucesso'),
]