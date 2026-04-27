from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload, name='upload'),
    path('revisao/', views.revisao, name='revisao'),
    path('sucesso/', views.sucesso, name='sucesso'),

    path('mover-aluno/', views.mover_aluno, name='mover_aluno'),
    path('remover-aluno/', views.remover_aluno, name='remover_aluno'),
    path('confirmar-sync/', views.confirmar_sync, name='confirmar_sync'),
]