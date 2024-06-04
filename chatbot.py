import streamlit as st
from openai import OpenAI
import time
from create_update_assistant import create_or_update_assistant
import os
from dotenv import load_dotenv
# Cargar las variables de entorno
load_dotenv()
# Cargar las variables de entorno y configurar el cliente OpenAI
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
assistant_id = st.secrets["assistant_id"]

client = OpenAI(api_key=OPENAI_API_KEY)

# Rutas de documentos para el asistente (adaptar según sea necesario)
file_paths = [
    "data\Q.txt",
    "data\meterings.json",
    "data\electricity_enduses.json",
    "data\hvac_systems.json",
    "data\id.json"
]

def initialize_chat():
    if 'assistant_created' not in st.session_state:
        assistant = create_or_update_assistant(file_paths)
        st.session_state['assistant_created'] = True

    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state["thread_id"] = thread.id

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": "Hola!, ¿Como puedo ayudarte el dia de hoy?"}]

    for msg in st.session_state["messages"]:
        role = "User" if msg["role"] == "user" else "Assistant"
        st.sidebar.write(f"{role}: {msg['content']}")

def handle_user_input(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.sidebar.write(f"User: {prompt}")

    client.beta.threads.messages.create(thread_id=st.session_state["thread_id"],
                                        role="user",
                                        content=prompt)
    run = client.beta.threads.runs.create(thread_id=st.session_state["thread_id"],
                                          assistant_id=assistant_id)

    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=st.session_state["thread_id"],
                                                       run_id=run.id)
        if run_status.status == 'completed':
            break
        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=st.session_state["thread_id"])
    response = messages.data[0].content[0].text.value
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.sidebar.write(f"Assistant: {response}")