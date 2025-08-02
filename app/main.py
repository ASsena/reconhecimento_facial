from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
import shutil
import os
import face_recognition
from fastapi.middleware.cors import CORSMiddleware
import base64
from io import BytesIO
from PIL import Image
import numpy as np
from app.db import Database # Importa a classe Database que gerencia a conexão MySQL



app = FastAPI()

# Permite CORS para acesso via navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Arquivos estáticos e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pasta de imagens
IMAGE_FOLDER = "images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Conexão com o banco de dados MySQL
db = Database()

# Criação da tabela se não existir
db.execute_query('''CREATE TABLE IF NOT EXISTS alunos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    imagem_path VARCHAR(255) NOT NULL,
    dias_permitidos TEXT NOT NULL
)''')

class ImagemBase64(BaseModel):
    imagem: str

@app.get("/", response_class=HTMLResponse)
async def cadastro_page(request: Request):
    return templates.TemplateResponse("cadastro.html", {"request": request})

@app.get("/verificar", response_class=HTMLResponse)
async def verificar_page(request: Request):
    return templates.TemplateResponse("verificar.html", {"request": request})

@app.post("/cadastrar")
async def cadastrar_aluno(nome: str = Form(...), dias: str = Form(...), imagem: UploadFile = Form(...)):
    caminho_imagem = os.path.join(IMAGE_FOLDER, imagem.filename)
    with open(caminho_imagem, "wb") as buffer:
        shutil.copyfileobj(imagem.file, buffer)

    db.execute_query("INSERT INTO alunos (nome, imagem_path, dias_permitidos) VALUES (%s, %s, %s)",
                     (nome, caminho_imagem, dias))
    return {"status": "aluno cadastrado com sucesso"}


import time


@app.post("/verificar-rosto")
async def verificar_rosto(payload: ImagemBase64):
    inicio_total = time.time()
    try:
        # Extrai base64 da imagem
        imagem_base64 = payload.imagem.split(",")[1] if "," in payload.imagem else payload.imagem
        imagem_bytes = base64.b64decode(imagem_base64)

        # Converte em imagem PIL e redimensiona para acelerar processamento
        imagem_pil = Image.open(BytesIO(imagem_bytes)).convert("RGB")
        imagem_pil = imagem_pil.resize((400, 400))  # redimensionar acelera
        imagem_np = np.array(imagem_pil)

        print(f"[INFO] Tempo para preparar imagem: {time.time() - inicio_total:.2f}s")

        # Detecta e codifica rosto
        inicio_face = time.time()
        try:
            encoding_desconhecido = face_recognition.face_encodings(imagem_np)[0]
        except IndexError:
            return JSONResponse(status_code=400, content={"mensagem": "Nenhum rosto detectado."})
        print(f"[INFO] Tempo para codificar rosto: {time.time() - inicio_face:.2f}s")

    except Exception as e:
        return JSONResponse(status_code=400, content={"mensagem": f"Erro ao processar imagem: {str(e)}"})

    # Busca alunos do banco de dados
    alunos = db.fetch_all("SELECT nome, imagem_path, dias_permitidos FROM alunos")
    dia_semana = datetime.today().strftime('%a').lower()

    # Compara com os rostos cadastrados
    inicio_comparacao = time.time()
    for nome, path, dias in alunos:
        try:
            imagem_aluno = face_recognition.load_image_file(path)
            encoding_cadastrado = face_recognition.face_encodings(imagem_aluno)[0]
        except IndexError:
            continue  # Ignora se não conseguir extrair encoding

        resultado = face_recognition.compare_faces([encoding_cadastrado], encoding_desconhecido)

        if resultado[0]:
            dias_lista = dias.lower().split(",")
            if dia_semana in dias_lista:
                print(f"[INFO] Verificação total: {time.time() - inicio_total:.2f}s")
                return {"mensagem": f"Acesso permitido para {nome}."}
            else:
                print(f"[INFO] Verificação total: {time.time() - inicio_total:.2f}s")
                return {"mensagem": f"Acesso negado para {nome}: dia não permitido."}

    print(f"[INFO] Tempo total comparação: {time.time() - inicio_comparacao:.2f}s")
    print(f"[INFO] Verificação total: {time.time() - inicio_total:.2f}s")
    return {"mensagem": "Aluno não reconhecido."}


@app.get("/verificar", response_class=HTMLResponse)
async def pagina_verificacao(request: Request):
    return templates.TemplateResponse("verificar.html", {"request": request})
