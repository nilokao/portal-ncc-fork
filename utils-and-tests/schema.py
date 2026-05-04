class Aluno:
    def __init__(self, id_aluno, nome, sexo, data_nascimento, passaporte,
                 tipo_ingresso, situacao, codigo_curso, nome_curso, matricula,
                 ano_curriculo_curso, ano_ingresso_curso, semestre_ingresso_curso,
                 semestre_evasao_curso, ano_evasao_curso, periodo_eva_curso,
                 carater, nacionalidade, email):
        
        self.id_aluno = id_aluno
        self.nome = nome
        self.sexo = sexo
        self.data_nascimento = data_nascimento
        self.passaporte = passaporte
        self.tipo_ingresso = tipo_ingresso
        self.situacao = situacao
        self.codigo_curso = codigo_curso
        self.nome_curso = nome_curso
        self.matricula = matricula
        self.ano_curriculo_curso = ano_curriculo_curso
        self.ano_ingresso_curso = ano_ingresso_curso
        self.semestre_ingresso_curso = semestre_ingresso_curso
        self.semestre_evasao_curso = semestre_evasao_curso
        self.ano_evasao_curso = ano_evasao_curso
        self.periodo_eva_curso = periodo_eva_curso
        self.carater = carater
        self.nacionalidade = nacionalidade
        self.email = email