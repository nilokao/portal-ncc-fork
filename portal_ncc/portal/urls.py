from django.urls import path
from . import views

urlpatterns = [
    path("", views.upload, name="upload"),
    path("escolher-curso/", views.escolher_curso, name="escolher_curso"),
    path("selecionar-curso/", views.selecionar_curso, name="selecionar_curso"),
    path("proximo-curso/", views.proximo_curso, name="proximo_curso"),
    path("finalizar/", views.finalizar, name="finalizar"),
    path("voltar-upload/", views.voltar_upload, name="voltar_upload"),
    path("revisao/", views.revisao, name="revisao"),
    path("sucesso/", views.sucesso, name="sucesso"),
    path("mover-aluno/", views.mover_aluno, name="mover_aluno"),
    path("remover-aluno/", views.remover_aluno, name="remover_aluno"),
    path("confirmar-sync/", views.confirmar_sync, name="confirmar_sync"),
]
