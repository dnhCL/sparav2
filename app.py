import streamlit as st
from chatbot import initialize_chat, handle_user_input, extract_hvac_system_data, extract_electricity_enduses_data, extract_metering_data, extract_year
import pandas as pd
import json
import os
from report_generation import generate_report, generate_energy_usage_graph

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

# Inicializar variables de estado de la sesión
if "conversation_step" not in st.session_state:
    st.session_state["conversation_step"] = 1
if "selected_building_id" not in st.session_state:
    st.session_state["selected_building_id"] = None
if "selected_year" not in st.session_state:
    st.session_state["selected_year"] = None
if "recommendations" not in st.session_state:
    st.session_state["recommendations"] = []

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

# Sección de depuración para mostrar las variables de estado
st.sidebar.header("Debug Information")
st.sidebar.write(f"Conversation Step: {st.session_state.get('conversation_step')}")
st.sidebar.write(f"Selected Building ID: {st.session_state.get('selected_building_id')}")
st.sidebar.write(f"Selected Year: {st.session_state.get('selected_year')}")
st.sidebar.write(f"Recommendations: {st.session_state.get('recommendations')}")

# Flujo interactivo basado en pasos


if st.session_state["conversation_step"] == 1:
    user_input = st.session_state.get("input", "").strip()
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["conversation_step"] = 2
        st.session_state["messages"].append({"role": "assistant", "content": "Would you like to inquire about a specific building or do you have general energy-related questions?"})

elif st.session_state["conversation_step"] == 2:
    user_input = st.session_state.get("input", "").strip()
    if user_input.lower() == "specific building":
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["conversation_step"] = 3
        st.session_state["messages"].append({"role": "assistant", "content": "Please provide the name or address of the building you would like information about."})
    elif user_input.lower() == "general questions":
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["conversation_step"] = 99  # Manejar preguntas generales
        st.session_state["messages"].append({"role": "assistant", "content": "Please ask your general energy-related questions."})

elif st.session_state["conversation_step"] == 3:
    user_input = st.session_state.get("input", "").strip()
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        building_id = next((b['building_id'] for b in st.session_state["id_data"] if user_input.lower() in b['buildingName'].lower()), None)
        if building_id:
            st.session_state["selected_building_id"] = building_id
            building_info = next(b for b in st.session_state["id_data"] if b["building_id"] == building_id)
            st.session_state["messages"].append({"role": "assistant", "content": f"Your building has {building_info['apartments']} apartments and an energy class {building_info['declaredEnergyClass']}. Is this correct?"})
            st.session_state["conversation_step"] = 4
        else:
            st.session_state["messages"].append({"role": "assistant", "content": "I couldn't find the building. Please provide the correct name or address."})

elif st.session_state["conversation_step"] == 4:
    user_input = st.session_state.get("input", "").strip()
    if user_input.lower() in ["yes", "correct"]:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["conversation_step"] = 5
        st.session_state["messages"].append({"role": "assistant", "content": "Which year would you like to inquire about for energy consumption?"})
    elif user_input.lower() in ["no", "incorrect"]:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["conversation_step"] = 3
        st.session_state["messages"].append({"role": "assistant", "content": "Please provide the name or address of the building you would like information about."})

elif st.session_state["conversation_step"] == 5:
    user_input = st.session_state.get("input", "").strip()
    year = extract_year(user_input)  # Usar extract_year para capturar el año desde la entrada del usuario
    if year:
        st.session_state["messages"].append({"role": "user", "content": str(year)})
        st.session_state["selected_year"] = year
        building_id = st.session_state["selected_building_id"]
        metering_data = st.session_state["meterings_data"]
        data = metering_data.get(str(building_id))
        df = pd.DataFrame(data[str(year)]) if data and str(year) in data else pd.DataFrame()
        if not df.empty:
            st.session_state["messages"].append({"role": "assistant", "content": f"Here is the energy consumption data for your building in {year}:"})
            st.session_state["messages"].append({"role": "assistant", "content": df.to_string()})
        else:
            st.session_state["messages"].append({"role": "assistant", "content": f"No consumption data found for the year {year}."})
        st.session_state["conversation_step"] = 6

elif st.session_state["conversation_step"] == 6:
    building_id = st.session_state["selected_building_id"]
    hvac_data = extract_hvac_system_data(building_id)
    enduses_data = extract_electricity_enduses_data(building_id)
    
    recommendations = [
        "Consider installing a ground source heat pump with exhaust air recovery.",
        "Consider installing solar thermal panels to reduce water heating costs.",
        "Optimize the use of property heating to reduce electricity consumption.",
        "Regularly maintain HVAC systems to ensure optimal performance.",
        "Implement energy-efficient lighting solutions."
    ]

    dynamic_recommendations = []
    if "heat_pump" not in hvac_data:
        dynamic_recommendations.append(recommendations[0])
    if "solar_panels" not in hvac_data:
        dynamic_recommendations.append(recommendations[1])
    if enduses_data.get("heating") > 20:
        dynamic_recommendations.append(recommendations[2])
    if hvac_data.get("maintenance_status") != "optimal":
        dynamic_recommendations.append(recommendations[3])
    if "led_lighting" not in hvac_data:
        dynamic_recommendations.append(recommendations[4])

    st.session_state["recommendations"] = dynamic_recommendations
    st.session_state["messages"].append({"role": "assistant", "content": "Based on the provided data, here are some recommendations to improve your building's energy efficiency:"})
    for rec in dynamic_recommendations:
        st.session_state["messages"].append({"role": "assistant", "content": f"- {rec}"})
    
    st.session_state["conversation_step"] = 7

elif st.session_state["conversation_step"] == 7:
    user_input = st.session_state.get("input", "").strip()
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["messages"].append({"role": "assistant", "content": "Which of the suggested measures have been completed in the last 10 years?"})
        st.session_state["conversation_step"] = 8

elif st.session_state["conversation_step"] == 8:
    user_input = st.session_state.get("input", "").strip()
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        # Actualizar las recomendaciones según la respuesta del usuario
        completed_measures = user_input.split(", ")
        remaining_recommendations = [rec for rec in st.session_state["recommendations"] if rec.split(": ")[0] not in completed_measures]
        st.session_state["recommendations"] = remaining_recommendations

        st.session_state["messages"].append({"role": "assistant", "content": "Now, I will calculate the ROI and annual energy savings for the remaining measures."})
        for rec in remaining_recommendations:
            # Aquí puedes insertar el cálculo real del ROI y ahorro energético basado en los datos disponibles.
            st.session_state["messages"].append({"role": "assistant", "content": f"{rec}: Expected savings: X kWh, ROI: Y years."})
        
        st.session_state["conversation_step"] = 9

elif st.session_state["conversation_step"] == 9:
    user_input = st.session_state.get("input", "").strip()
    if user_input.lower() == "generate report":
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["conversation_step"] = 10
        building_id = st.session_state["selected_building_id"]
        year = st.session_state["selected_year"]
        building_info = next(b for b in st.session_state["id_data"] if b["building_id"] == building_id)
        metering_data = st.session_state["meterings_data"]
        hvac_data = extract_hvac_system_data(building_id)
        enduses_data = extract_electricity_enduses_data(building_id)
        recommendations = st.session_state["recommendations"]
        report_path = generate_report(building_id, year, building_info, metering_data, hvac_data, enduses_data, recommendations)
        with open(report_path, "rb") as file:
            st.download_button(
                label="Download Report",
                data=file,
                file_name=os.path.basename(report_path),
                mime="application/pdf"
            )
        st.session_state["messages"].append({"role": "assistant", "content": "Here is your detailed report."})
        st.session_state["conversation_step"] = 11

elif st.session_state["conversation_step"] == 11:
    st.session_state["messages"].append({"role": "assistant", "content": "Is there anything else I can help you with today?"})

elif st.session_state["conversation_step"] == 99:
    user_input = st.session_state.get("input", "").strip()
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        # Aquí puedes manejar las preguntas generales.
        st.session_state["messages"].append({"role": "assistant", "content": "Here is the information you requested: [general information]."})
        st.session_state["conversation_step"] = 11
