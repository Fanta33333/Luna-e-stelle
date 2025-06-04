from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
from openai import OpenAI
import os
import asyncio

# ✅ Leggi variabili d'ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

if not OPENAI_API_KEY or not ASSISTANT_ID:
    raise RuntimeError("OPENAI_API_KEY o ASSISTANT_ID non trovati tra le variabili d'ambiente.")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

# ✅ CORS GitHub Pages
app.add_middleware(
    CORSMiddleware,
   origins = [
    "https://fanta33333.github.io",
    "https://fanta33333.github.io/Luna-e-stelle/",
    "https://fanta33333.github.io/Luna-e-stelle"
]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Modello richiesta
class ChatRequest(BaseModel):
    thread_id: str
    message: str

# ✅ Endpoint per creare un nuovo thread
@app.get("/start")
async def start_conversation():
    try:
        thread = client.beta.threads.create()
        return {"thread_id": thread.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore creando il thread: {str(e)}")

# ✅ Endpoint per inviare messaggi
@app.post("/chat")
async def chat_request(chat_request: ChatRequest):
    try:
        # Invia messaggio utente
        client.beta.threads.messages.create(
            thread_id=chat_request.thread_id,
            role="user",
            content=chat_request.message
        )

        # Avvia assistente
        run = client.beta.threads.runs.create(
            thread_id=chat_request.thread_id,
            assistant_id=ASSISTANT_ID
        )

        # Attesa completamento
        while True:
            status = client.beta.threads.runs.retrieve(
                thread_id=chat_request.thread_id,
                run_id=run.id
            )
            if status.status in ["completed", "failed"]:
                break
            await asyncio.sleep(1)

        if status.status == "failed":
            raise HTTPException(status_code=500, detail="L'esecuzione dell'assistente è fallita.")

        # Recupera risposta
        messages = client.beta.threads.messages.list(thread_id=chat_request.thread_id)
        reply = messages.data[0].content[0].text.value
        return {"response": reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante la chat: {str(e)}")


