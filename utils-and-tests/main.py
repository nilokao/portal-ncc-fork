import csv
from schema import Aluno
from normalizador01 import remover_acentos

egressos: list[Aluno] = []
regulares: list[Aluno] = []

with open('Alunos CC e SI-NORMALIZADO.csv', mode='r', newline='', encoding='latin1') as file:
    reader = csv.reader(file)
    for row in reader:
        id_aluno = row[0]
        nome = row[1]
        sexo = row[2]
        data_nascimento = row[3]
        passaporte = row[4]
        tipo_ingresso = row[5]
        situacao = row[6]
        codigo_curso = row[7]
        nome_curso = row[8]
        matricula = row[9]
        ano_curriculo_curso = row[10]
        ano_ingresso_curso = row[11]
        semestre_ingresso_curso = row[12]
        semestre_evasao_curso = row[13]
        ano_evasao_curso = row[14]
        periodo_eva_curso = row[15]
        carater = row[16]
        nacionalidade = row[17]
        email = row[18]

        aluno = Aluno(
            id_aluno=id_aluno,
            nome=nome,
            sexo=sexo,
            data_nascimento=data_nascimento,
            passaporte=passaporte,  
            tipo_ingresso=tipo_ingresso,
            situacao=situacao,
            codigo_curso=codigo_curso,
            nome_curso=nome_curso,
            matricula=matricula,
            ano_curriculo_curso=ano_curriculo_curso,
            ano_ingresso_curso=ano_ingresso_curso,
            semestre_ingresso_curso=semestre_ingresso_curso,
            semestre_evasao_curso=semestre_evasao_curso,
            ano_evasao_curso=ano_evasao_curso,
            periodo_eva_curso=periodo_eva_curso,
            carater=carater,
            nacionalidade=nacionalidade,
            email=email
        )

        print("ID do Aluno:", id_aluno)
        print("Nome:", nome)
        print("Sexo:", sexo)
        print("Data de Nascimento:", data_nascimento)
        print("Passaporte:", passaporte)
        print("Tipo de Ingresso:", tipo_ingresso)
        print("Situação:", situacao)        
        print("Código do Curso:", codigo_curso)
        print("Nome do Curso:", nome_curso)
        print("Matrícula:", matricula)
        print("Ano do Currículo do Curso:", ano_curriculo_curso)
        print("Ano de Ingresso no Curso:", ano_ingresso_curso)
        print("Semestre de Ingresso no Curso:", semestre_ingresso_curso)
        print("Semestre de Evasão do Curso:", semestre_evasao_curso)
        print("Ano de Evasão do Curso:", ano_evasao_curso)
        print("Período de Evasão do Curso:", periodo_eva_curso)
        print("Caráter:", carater)
        print("Nacionalidade:", nacionalidade)
        print("Email:", email)
        print("-" * 40)

        # egressos_status = ["Abandono", "Formado", "Cancelamento de Matrícula", "Transferência Externa", "Transferência Interna", "Transferência", "Jubilamento", "Cancelamento Convênio", "Cancelamento de Matrícula e Vínculo - Resolução N. 033/2015", "Classificado(a) sem Matrícula"]
        # lista_maiuscula = [remover_acentos(item.upper()) for item in egressos_status]

        if situacao != "ESTUDANTE REGULAR":
            egressos.append(aluno)
        else:
            regulares.append(aluno)

        
print("Total de Egressos:", len(egressos))
print("Total de Regulares:", len(regulares))