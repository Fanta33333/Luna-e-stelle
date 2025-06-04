from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
from openai import OpenAI
from packaging import version
import openai

# ✅ Controllo versione OpenAI
required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
if current_version < required_version:
    raise ValueError(f"Errore: versione OpenAI ({openai.__version__}) è troppo vecchia")

# ✅ Leggi API key e assistant ID dalle variabili ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
if not OPENAI_API_KEY or not ASSISTANT_ID:
    raise ValueError("OPENAI_API_KEY o ASSISTANT_ID mancanti tra le variabili ambiente")

# ✅ Inizializza OpenAI e FastAPI
client = OpenAI(api_key=OPENAI_API_KEY)
app = FastAPI()

# ✅ Configura CORS per GitHub Pages
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

# ✅ Schema per la richiesta POST
class ChatRequest(BaseModel):
    thread_id: str
    message: str

# ✅ Crea nuova conversazione
@app.get("/start")
async def start_conversation():
    thread = client.beta.threads.create()
    return {"thread_id": thread.id}

# ✅ Invia messaggio e ricevi risposta
@app.post("/chat")
async def chat(chat_request: ChatRequest):
    thread_id = chat_request.thread_id
    message = chat_request.message

    try:
        # Invia il messaggio dell’utente
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )

        # Avvia la risposta dell’assistente
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        # Attendi che abbia finito
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status in ["failed", "cancelled", "expired"]:
                raise HTTPException(status_code=500, detail="Errore nel completare la risposta")
            await asyncio.sleep(1)

        # Leggi l’ultima risposta generata
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        risposta = messages.data[0].content[0].text.value

        return {"response": risposta}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





