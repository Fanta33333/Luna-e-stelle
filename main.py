from time import sleep
import os
import asyncio
from dotenv import load_dotenv
from packaging import version
import openai
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ✅ Carica variabili da .env o Render Environment
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# ✅ Controllo versione OpenAI
required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
if current_version < required_version:
    raise ValueError(f"Errore: la versione di OpenAI è {openai.__version__}, inferiore alla richiesta 1.1.1")
else:
    print("✅ Versione OpenAI compatibile.")

# ✅ Inizializza FastAPI
app = FastAPI()

# ✅ Abilita CORS per consentire le richieste da GitHub Pages
origins = [
    "https://fanta33333.github.io",
    "https://fanta33333.github.io/Luna-e-stelle"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Inizializza client OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# ✅ Modello richiesta utente
class ChatRequest(BaseModel):
    thread_id: str
    message: str

# ✅ Endpoint per iniziare nuova conversazione
@app.get("/start")
async def start_conversation():
    try:
        thread = client.beta.threads.create()
        return {"thread_id": thread.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Endpoint per inviare messaggio e ottenere risposta
@app.post("/chat")
async def chat_request(chat_request: ChatRequest):
    try:
        # Invia messaggio dell'utente
        client.beta.threads.messages.create(
            thread_id=chat_request.thread_id,
            role="user",
            content=chat_request.message
        )

        # Esegui assistant
        run = client.beta.threads.runs.create(
            thread_id=chat_request.thread_id,
            assistant_id=ASSISTANT_ID
        )

        # Attendi completamento
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=chat_request.thread_id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status in ["failed", "cancelled", "expired"]:
                raise HTTPException(status_code=500, detail="Errore: run fallita o terminata.")
            await asyncio.sleep(1)

        # Estrai risposta
        messages = client.beta.threads.messages.list(thread_id=chat_request.thread_id)
        response = messages.data[0].content[0].text.value
        return {"response": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



