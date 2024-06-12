import streamlit as st
from chatbot import initialize_chat, handle_user_input, extract_hvac_system_data, extract_electricity_enduses_data, extract_metering_data
import json
import os
from report_generation import generate_report

# Inicializar la sesión de chat
initialize_chat()

# Título de la aplicación
st.title("Building Energy Assistant")

# Función para cargar datos desde un archivo JSON
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Cargar datos
st.session_state["meterings_data"] = load_json("data/meterings.json")
st.session_state["electricity_enduses_data"] = load_json("data/electricity_enduses.json")
st.session_state["hvac_systems_data"] = load_json("data/hvac_systems.json")
st.session_state["id_data"] = load_json("data/id.json")
st.session_state["buildings"] = st.session_state["id_data"]

# Ocultar la barra lateral de la conversación y ajustar el estilo del chat
st.markdown("""
    <style>
    .css-1y0tads {
        display: none;
    }
    .stTextInput {
        position: fixed;
        bottom: 3%;
        width: 50%;
        left: 25%;
    }
    .stButton {
        position: fixed;
        bottom: 3%;
        left: 76%;
    }
    .chat-container {
        max-height: 70vh;
        overflow-y: auto;
        padding-bottom: 5rem; /* Space for input bar */
    }
    </style>
    """, unsafe_allow_html=True)

# Función para manejar la entrada del usuario y limpiar el campo de entrada
def handle_input():
    if "input" in st.session_state and st.session_state.input.strip():
        user_input = st.session_state.input
        handle_user_input(user_input)
        st.session_state.input = ""  # Limpiar el campo de entrada

# Encapsular el área de chat en un contenedor
st.subheader("Assistant Chat")
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state["messages"]:
        role = "User" if msg["role"] == "user" else "Assistant"
        st.markdown(f"**{role}:** {msg['content']}")
    st.markdown('</div>', unsafe_allow_html=True)

# Sección de entrada del usuario con botón
user_input_col, button_col = st.columns([5, 1])
with user_input_col:
    st.text_input("Type your message here:", key="input", label_visibility="collapsed", on_change=handle_input)
with button_col:
    st.button("Send", on_click=handle_input)

# Verificar si el asistente ha identificado el edificio y el año
if st.session_state.get("selected_building_id") and st.session_state.get("selected_year"):
    building_id = st.session_state["selected_building_id"]
    year = st.session_state["selected_year"]
    building_info = next(b for b in st.session_state["id_data"] if b["building_id"] == building_id)

    st.subheader(f"Energy Consumption for {building_info['buildingName']} in {year}")
    metering_data = st.session_state["meterings_data"]
    hvac_data = extract_hvac_system_data(building_id)
    enduses_data = extract_electricity_enduses_data(building_id)
    
    # Suponiendo que las recomendaciones se obtienen de los mensajes del asistente
    recommendations = [msg['content'] for msg in st.session_state["messages"] if msg['role'] == 'assistant']
    
    # Generar y mostrar el reporte
    report_path = generate_report(building_id, year, building_info, metering_data, hvac_data, enduses_data, recommendations)
    with open(report_path, "rb") as file:
        btn = st.download_button(
            label="Download Report",
            data=file,
            file_name=os.path.basename(report_path),
            mime="application/pdf"
        )
