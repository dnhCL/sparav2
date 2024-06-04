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
    "data/Q.txt",
    "data/meterings.json",
    "data/electricity_enduses.json",
    "data/hvac_systems.json",
    "data/id.json"
]

def initialize_chat():
    if 'assistant_created' not in st.session_state:
        assistant = create_or_update_assistant(file_paths)
        st.session_state['assistant_created'] = True

    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state["thread_id"] = thread.id

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": "Hola!, ¿Cómo puedo ayudarte el día de hoy?"}]

    for msg in st.session_state["messages"]:
        role = "Usuario" if msg["role"] == "user" else "Asistente"
        st.sidebar.write(f"{role}: {msg['content']}")

def handle_user_input(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.sidebar.write(f"Usuario: {prompt}")

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
    st.sidebar.write(f"Asistente: {response}")

    # Si el asistente identifica un edificio
    if "edificio" in response.lower():
        building_id = extraer_id_edificio(response)
        if building_id:
            st.session_state["selected_building_id"] = building_id

def extraer_id_edificio(response):
    # Implementar lógica para extraer el building_id de la respuesta
    # Esto es un ejemplo y debería adaptarse a la estructura real de la respuesta
    for building in st.session_state["buildings"]:
        if building["buildingName"] in response:
            return building["building_id"]
    return None
