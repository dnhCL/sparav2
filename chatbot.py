import streamlit as st
from openai import OpenAI
import time
from create_update_assistant import create_or_update_assistant
import os
from dotenv import load_dotenv
import json
import re
from datetime import datetime

# Load environment variables
load_dotenv()
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
assistant_id = st.secrets["assistant_id"]

client = OpenAI(api_key=OPENAI_API_KEY)

# Document paths for the assistant (adapt as needed)
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
        st.session_state["messages"] = [{"role": "system", "content": "Hello, I am your building energy management assistant. How can I assist you today?"}]

def handle_user_input(prompt):
    if not prompt.strip():
        st.warning("Please enter a message.")
        return

    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        client.beta.threads.messages.create(thread_id=st.session_state["thread_id"],
                                            role="user",
                                            content=prompt)

        active_run = None
        try:
            runs = client.beta.threads.runs.list(thread_id=st.session_state["thread_id"])
            active_run = next((run for run in runs.data if run.status == 'active'), None)
        except Exception as e:
            st.error(f"Error fetching thread runs: {e}")

        if active_run:
            run = active_run
        else:
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

        # Save the conversation log
        save_conversation_log()

        # Encapsular cada paso y no avanzar hasta completar
        if "building_requested" not in st.session_state:
            st.session_state.messages.append({"role": "assistant", "content": "Please provide the name or address of the building you would like information about."})
            st.session_state["building_requested"] = True
            return

        if "building" not in st.session_state and "building_requested" in st.session_state:
            building_name = extract_building_name(response)
            building = get_building_by_name(building_name)
            if building:
                st.session_state["building"] = building
                st.session_state.messages.append({"role": "assistant", "content": f"The building information for '{building['buildingName']}' is as follows: {building_details(building)}"})
                del st.session_state["building_requested"]
            else:
                st.session_state.messages.append({"role": "assistant", "content": "I couldn't find the building. Please provide a valid building name or address."})
            return

        if "year_requested" not in st.session_state and "building" in st.session_state:
            st.session_state.messages.append({"role": "assistant", "content": "Which year would you like to inquire about for energy consumption?"})
            st.session_state["year_requested"] = True
            return

        if "year" not in st.session_state and "year_requested" in st.session_state:
            year = extract_year(response)
            if year:
                st.session_state["year"] = year
                st.session_state.messages.append({"role": "assistant", "content": f"Please wait while I retrieve the energy consumption data for the year {year}."})
                # Extract data and provide monthly consumption
                metering_data = extract_metering_data(st.session_state["building"]["building_id"], year)
                if metering_data:
                    monthly_consumption = format_monthly_consumption(metering_data)
                    st.session_state.messages.append({"role": "assistant", "content": monthly_consumption})
                    # Proveer análisis y recomendaciones
                    recommendations = generate_recommendations(metering_data)
                    st.session_state.messages.append({"role": "assistant", "content": recommendations})
                    # Preguntar sobre la generación de informes
                    st.session_state.messages.append({"role": "assistant", "content": "Would you like to receive a detailed report with all the data and recommendations?"})
            else:
                st.session_state.messages.append({"role": "assistant", "content": "Please provide a valid year."})

    except Exception as e:
        st.error(f"Error processing message: {e}")

def save_conversation_log():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"log_{timestamp}.txt"
    log_content = ""
    for message in st.session_state.messages:
        log_content += f"{message['role'].capitalize()}: {message['content']}\n"
    
    # Guardar el contenido en un archivo descargable
    b64 = base64.b64encode(log_content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{log_filename}">Download log file</a>'
    st.markdown(href, unsafe_allow_html=True)

def extract_building_name(response):
    for building in st.session_state["buildings"]:
        if building["buildingName"].lower() in response.lower():
            return building["buildingName"]
    return None

def get_building_by_name(name):
    for building in st.session_state["buildings"]:
        if building["buildingName"].lower() == name.lower():
            return building
    return None

def extract_year(response):
    match = re.search(r'\b(20\d{2})\b', response)
    if match:
        return int(match.group(0))
    return None

def extract_metering_data(building_id, year):
    meterings = st.session_state["meterings_data"]
    if str(building_id) in meterings and str(year) in meterings[str(building_id)]:
        return meterings[str(building_id)][str(year)]
    return None

def extract_electricity_enduses_data(building_id):
    enduses = st.session_state["electricity_enduses_data"]
    return next((item for item in enduses if item["building_id"] == building_id), None)

def extract_hvac_system_data(building_id):
    hvac = st.session_state["hvac_systems_data"]
    return next((item for item in hvac if item["building_id"] == building_id), None)

def format_monthly_consumption(metering_data):
    monthly_data = [f"{month['month']}: {month['electricity_use_property']} kWh" for month in metering_data]
    return "\n".join(monthly_data)

def generate_recommendations(metering_data):
    average_consumption = sum(month['electricity_use_property'] for month in metering_data) / len(metering_data)
    return f"Based on the provided data, your average monthly energy consumption is {average_consumption:.2f} kWh. Here are some recommendations to improve your building's energy efficiency: [recommendations]."

def building_details(building):
    details = (
        f"Number of Apartments: {building['numApartments']}\n"
        f"Number of Tenants: {building['numTenants']}\n"
        f"Net Area Residential: {building['netAreaResidential']} sq.m.\n"
        f"Net Area Non-Residential: {building['netAreaNonResidential']} sq.m.\n"
        f"Net Area Heated: {building['netAreaHeated']} sq.m.\n"
        f"Declared Energy Class: {building['energyClass']}\n"
        f"Energy Class kWh/m²: {building['energyClassKWhPerM2']}"
    )
    return details

# Botón para guardar el registro de conversación
if st.button('Save Conversation Log'):
    save_conversation_log()
