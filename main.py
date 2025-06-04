# ✅ main.py completo e sicuro con variabili d'ambiente e CORS
import asyncio
from packaging import version
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import openai
import os

# ✅ Controllo versione OpenAI
required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
if current_version < required_version:
    raise ValueError(f"OpenAI version {openai.__version__} is too old. Required: 1.1.1")
else:
    print("✅ OpenAI version is compatible.")

# ✅ Inizializza FastAPI
app = FastAPI()

# ✅ Abilita CORS per GitHub Pages
origins = [
    "https://fanta33333.github.io",
    "https://fanta33333.github.io/Luna-e-stelle",
    "https://fanta33333.github.io/Luna-e-stelle/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Prendi chiavi da variabili d'ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

# ✅ Schema richiesta
class ChatRequest(BaseModel):
    thread_id: str
    message: str

# ✅ Crea nuovo thread
@app.get("/start")
async def start_conversation():
    thread = client.beta.threads.create()
    return {"thread_id": thread.id}

# ✅ Invia messaggio e recupera risposta
@app.post("/chat")
async def chat(chat_request: ChatRequest):
    thread_id = chat_request.thread_id
    user_input = chat_request.message

    if not thread_id:
        raise HTTPException(status_code=400, detail="Missing thread_id")

    # Invia messaggio
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_input
    )

    # Esegui assistant
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
        if run_status.status in ["completed", "failed", "cancelled", "expired"]:
            break
        await asyncio.sleep(1)

    if run_status.status != "completed":
        raise HTTPException(status_code=500, detail=f"Run failed with status {run_status.status}")

    # Recupera risposta
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    response = messages.data[0].content[0].text.value
    return {"response": response}




