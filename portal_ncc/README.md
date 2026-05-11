# Portal NCC

Aplicação em Django para processar uma planilha de alunos, separar os registros em grupos acadêmicos e sincronizar os membros com grupos do Google Workspace.

O sistema usa login manual do Google. Ou seja: o professor que for usar a aplicação deve fazer login no navegador com a conta Google Workspace que tem permissão para gerenciar os grupos.

---

## Requisitos

Antes de começar, instale:

- Python 3.12 ou superior
- Git
- Google Chrome ou outro navegador
- Acesso à conta Google Workspace autorizada a gerenciar os grupos
- O arquivo OAuth `client_secret.json`

---

## Instalação

Clone o projeto:

```bash
git clone https://github.com/nilokao/portal-ncc-fork.git
cd portal-ncc-fork/portal_ncc
```

Crie e ative o ambiente virtual.

No Windows CMD:

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

No Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

Rode as migrations:

```bash
python manage.py migrate
```

Inicie o servidor:

```bash
python manage.py runserver
```

Abra no navegador:

```txt
http://127.0.0.1:8000/
```

---

## Configuração do Google

A aplicação precisa do arquivo:

```txt
client_secret.json
```

Esse arquivo deve ficar na mesma pasta do `manage.py`:

```txt
portal_ncc/
├── manage.py
├── client_secret.json
├── portal/
└── portal_ncc/
```

O `client_secret.json` deve ser uma credencial OAuth do tipo **Desktop App**.

Ao abrir o arquivo, ele deve começar assim:

```json
{
  "installed": {
```

Se começar com `"web"`, a credencial foi criada no tipo errado.

Preciso enviar para o professor por algum meio seguro, não pode ser público.

---

## Primeiro acesso do professor

Na primeira sincronização, o navegador abrirá uma tela de login do Google.

O professor deve entrar com a conta institucional autorizada, por exemplo:

```txt
usuario@inf.ufsm.br
```

Depois do login, será criado automaticamente o arquivo:

```txt
token.json
```

Esse arquivo guarda a autenticação localmente. Nas próximas execuções, o sistema usará esse token e não deve pedir login de novo.

Se for necessário trocar a conta Google usada, apague o arquivo:

```cmd
del token.json
```

Depois rode o sistema novamente e faça login com a conta correta.

---

## Arquivos que não devem ir para o GitHub

Não envie estes arquivos para o repositório:

```txt
client_secret.json
token.json
credentials.json
db.sqlite3
venv/
```

O `.gitignore` deve conter:

```gitignore
venv/
__pycache__/
*.pyc
db.sqlite3

client_secret.json
token.json
credentials.json
*.json
```

---

## Uso da aplicação

1. Abra `http://127.0.0.1:8000/`
2. Envie a planilha de alunos
3. Revise os grupos gerados
4. Mova ou remova alunos, se necessário
5. Clique em **Confirmar e sincronizar**
6. Faça login no Google, se solicitado
7. Aguarde o processo finalizar

A sincronização pode levar alguns minutos.

---

## Regras de sincronização

### Matriculados

Os grupos de matriculados refletem a planilha atual:

- Se está na planilha e não está no grupo, adiciona
- Se está no grupo e não está na planilha, remove
- Se já está no grupo e também está na planilha, mantém

### Egressos

Os grupos de egressos são acumulativos:

- Se está na planilha e não está no grupo, adiciona
- Se já está no grupo, mantém
- Se não está mais na planilha, não remove

---

## Configuração dos grupos

Os e-mails dos grupos ficam em:

```txt
portal/google_service.py
```

No dicionário:

```python
GRUPOS_EMAIL = {
    "matriculados_cc": "matriculados-cc@inf.ufsm.br",
    "matriculados_si": "matriculados-si@inf.ufsm.br",
    "egressos_cc": "egressos-cc@inf.ufsm.br",
    "egressos_si": "egressos-si@inf.ufsm.br",
}
```

Altere os valores conforme os grupos reais do Google Workspace, no `google_service.py`, pois os emails estão os de teste, já foram devidamente testados.
AVISO: NÃO SE ESQUEÇA DE ALTERAR OS ADMINISTRADORES DOS GRUPOS DE MATRÍCULADOS.

---

## Problemas comuns

### `No module named django`

Ative a venv e instale as dependências:

```bash
python -m pip install -r requirements.txt
```

### `No module named google_auth_oauthlib`

Instale novamente as dependências:

```bash
python -m pip install -r requirements.txt
```

### `redirect_uri_mismatch`

O `client_secret.json` provavelmente foi criado como **Web Application**.

Crie uma nova credencial OAuth do tipo **Desktop App**.

### Login com conta errada

Apague o token:

```cmd
del token.json
```

Depois rode o sistema novamente e faça login com a conta correta.

---

## Comandos principais

```bash
cd portal-ncc-fork/portal_ncc
venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
