import os
import json

caminho = os.getenv("GOOGLE_SA_FILE", "credentials.json")
admin = os.getenv("GOOGLE_ADMIN_EMAIL")

print("GOOGLE_SA_FILE:", caminho)
print("GOOGLE_ADMIN_EMAIL:", admin)
print("arquivo existe?", os.path.exists(caminho))

with open(caminho, "r", encoding="utf-8") as f:
    dados = json.load(f)

print("type:", dados.get("type"))
print("project_id:", dados.get("project_id"))
print("client_email:", dados.get("client_email"))
print("client_id:", dados.get("client_id"))