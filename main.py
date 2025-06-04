from time import sleep
from packaging import version
import openai
from openai import OpenAI
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os

# ✅ Controllo versione OpenAI
required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
if current_version < required_version:
    raise ValueError(f"Error: OpenAI version {openai.__version__} is less than required 1.1.1")
else:
    print("OpenAI version is compatible.")

# ✅ Inizializza FastAPI
app = FastAPI()

# ✅ Abilita CORS
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

# ✅ Leggi API Key e Assistant ID dalle variabili di ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

# ✅ Modello richiesta
class ChatRequest(BaseModel):
    thread_id: str
    message: str

# ✅ Endpoint per iniziare conversazione
@app.get("/start")
async def start_conversation():
    try:
        thread = client.beta.threads.create()
        return {"thread_id": thread.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Endpoint per mandare messaggi
@app.post("/chat")
async def chat_request(chat_request: ChatRequest):
    thread_id = chat_request.thread_id
    user_input = chat_request.message

    if not thread_id:
        raise HTTPException(status_code=400, detail="Missing thread_id")

    try:
        # Invia messaggio utente
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_input
        )

        # Avvia assistente
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
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

        # Recupera messaggio risposta
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        response = messages.data[0].content[0].text.value
        return {"response": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



