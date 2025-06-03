from time import sleep
from packaging import version
import openai
from openai import OpenAI
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import asyncio

# ✅ Controlliamo che la versione di OpenAI sia corretta
required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
OPENAI_API_KEY = "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"
if current_version < required_version:
    raise ValueError(f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1")
else:
    print("OpenAI version is compatible.")

# ✅ Inizializziamo l'app FastAPI
app = FastAPI()

# ✅ Inizializziamo il client di OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# ✅ Inseriamo direttamente l'ID dell'assistente
assistant_id = "asst_RhwAObwqzKB6LqxScKyRh9ZC"

# ✅ Definiamo il modello di richiesta per la chat
class ChatRequest(BaseModel):
    thread_id: str
    message: str

# ✅ Endpoint per iniziare una nuova conversazione
@app.get("/start")
async def start_conversation():
    print("Starting a new conversation...")
    thread = client.beta.threads.create()
    print(f"New thread created with ID: {thread.id}")
    return {"thread_id": thread.id}

# ✅ Endpoint per gestire la chat
@app.post("/chat")
async def chat_request(chat_request: ChatRequest):
    thread_id = chat_request.thread_id
    user_input = chat_request.message

    if not thread_id:
        print("Error: Missing thread_id")
        raise HTTPException(status_code=400, detail="Missing thread_id")

    print(f"Received message: {user_input} for thread ID: {thread_id}")

    # Invia il messaggio dell'utente al thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_input
    )

    # Avvia la run dell'assistente
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    end = False

    # Polling fino al completamento
    while not end:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        if run_status.status in ["completed", "cancelled", "expired", "requires_action"]:
            end = True
        elif run_status.status == "failed":
            print(run_status.last_error)
            raise HTTPException(status_code=500, detail="Run failed")
        else:
            await asyncio.sleep(1)

    # Estrai il messaggio di risposta
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    response = messages.data[0].content[0].text.value

    print(f"Assistant response: {response}")
    return {"response": response}
