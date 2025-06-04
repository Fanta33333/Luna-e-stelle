# ✅ main.py completo con CORS abilitato
from time import sleep
from packaging import version
import openai
from openai import OpenAI
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

# ✅ Controlliamo versione OpenAI
required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
OPENAI_API_KEY = "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"
if current_version < required_version:
    raise ValueError(f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1")
else:
    print("OpenAI version is compatible.")

# ✅ Inizializza FastAPI
app = FastAPI()

# ✅ Abilita CORS per permettere l'accesso da GitHub Pages
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

# ✅ Inizializza OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)
assistant_id = "asst_RhwAObwqzKB6LqxScKyRh9ZC"

# ✅ Modello richiesta
class ChatRequest(BaseModel):
    thread_id: str
    message: str

# ✅ Nuovo thread
@app.get("/start")
async def start_conversation():
    thread = client.beta.threads.create()
    return {"thread_id": thread.id}

# ✅ Gestione chat
@app.post("/chat")
async def chat_request(chat_request: ChatRequest):
    thread_id = chat_request.thread_id
    user_input = chat_request.message

    if not thread_id:
        raise HTTPException(status_code=400, detail="Missing thread_id")

    # Invia messaggio utente
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_input
    )

    # Avvia assistente
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # Attendi completamento
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        if run_status.status in ["completed", "cancelled", "expired", "requires_action"]:
            break
        elif run_status.status == "failed":
            raise HTTPException(status_code=500, detail="Run failed")
        else:
            await asyncio.sleep(1)

    # Prendi risposta
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    response = messages.data[0].content[0].text.value
    return {"response": response}

