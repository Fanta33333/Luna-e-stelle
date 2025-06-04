from time import sleep
from packaging import version
import openai
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os

# ✅ Prendi le variabili d’ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# ✅ Controlla versione SDK OpenAI
required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
if current_version < required_version:
    raise ValueError(f"La versione di OpenAI SDK ({openai.__version__}) è inferiore a quella richiesta (1.1.1)")
else:
    print("✅ Versione OpenAI compatibile.")

# ✅ Inizializza FastAPI
app = FastAPI()

# ✅ Abilita CORS per accesso da GitHub Pages
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

# ✅ Inizializza OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

# ✅ Modello per la richiesta POST
class ChatRequest(BaseModel):
    thread_id: str
    message: str

# ✅ Endpoint per iniziare una nuova conversazione
@app.get("/start")
async def start_conversation():
    try:
        thread = client.beta.threads.create()
        return {"thread_id": thread.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Endpoint per inviare un messaggio
@app.post("/chat")
async def chat_request(chat_request: ChatRequest):
    thread_id = chat_request.thread_id
    user_input = chat_request.message

    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id mancante")

    try:
        # Invia messaggio utente
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_input
        )

        # Avvia il run
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        # Attendi il completamento
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run_status.status in ["completed", "cancelled", "expired", "requires_action"]:
                break
            elif run_status.status == "failed":
                raise HTTPException(status_code=500, detail="Run fallito")
            await asyncio.sleep(1)

        # Recupera la risposta
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        response = messages.data[0].content[0].text.value
        return {"response": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




