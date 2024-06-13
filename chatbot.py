import streamlit as st
from openai import OpenAI
import time
from create_update_assistant import create_or_update_assistant, evaluate_energy_profile
import os
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
assistant_id = st.secrets["assistant_id"]

client = OpenAI(api_key=OPENAI_API_KEY)

# Document paths for the assistant (adapt as needed)
file_paths = [
    "data/id.json",
    "data/meterings.json",
    "data/electricity_enduses.json",
    "data/hvac_systems.json"
]

def initialize_chat():
    if 'assistant_created' not in st.session_state:
        assistant = create_or_update_assistant(file_paths)
        st.session_state['assistant_created'] = True

    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state["thread_id"] = thread.id

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": "Hello! How can I help you today?"}]

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

        # If the assistant identifies a building
        if "building" in response.lower():
            building_id = extract_building_id(response)
            if building_id:
                st.session_state["selected_building_id"] = building_id

        # Extract meter data using Code Interpreter
        if st.session_state.get("selected_building_id"):
            building_id = st.session_state["selected_building_id"]
            result = evaluate_energy_profile(building_id)
            peak_power, primary_energy_use_intensity = parse_code_interpreter_result(result)
            st.session_state["peak_power"] = peak_power
            st.session_state["primary_energy_use_intensity"] = primary_energy_use_intensity

    except Exception as e:
        st.error(f"Error processing message: {e}")

def extract_building_id(response):
    with open('data/id.json', 'r') as f:
        id_data = json.load(f)
    for building in id_data:
        if building["address"].lower() in response.lower():
            return building["building_id"]
    return None

def parse_code_interpreter_result(result):
    peak_power = None
    primary_energy_use_intensity = None
    lines = result.split('\n')
    for line in lines:
        if "Peak Power (kW)" in line:
            peak_power = float(line.split(':')[1].strip())
        if "Primary Energy Use Intensity (kWh/Atemp)" in line:
            primary_energy_use_intensity = float(line.split(':')[1].strip())
    return peak_power, primary_energy_use_intensity



# Display results if available
if "peak_power" in st.session_state and "primary_energy_use_intensity" in st.session_state:
    st.subheader("Energy Profile")
    st.write(f"Peak Power (kW): {st.session_state['peak_power']}")
    st.write(f"Primary Energy Use Intensity (kWh/Atemp): {st.session_state['primary_energy_use_intensity']}")
