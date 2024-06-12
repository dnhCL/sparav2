import streamlit as st
from openai import OpenAI
import time
from create_update_assistant import create_or_update_assistant
import os
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()
# Load environment variables and set up the OpenAI client
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

        # If the assistant identifies a building
        if "building" in response.lower():
            building_id = extract_building_id(response)
            if building_id:
                st.session_state["selected_building_id"] = building_id

        # If the assistant identifies a year
        if "year" in response.lower():
            year = extract_year(response)
            if year:
                st.session_state["selected_year"] = year

        # Extract meter data using Python /// Remember: It is not working very well this point
        if st.session_state.get("selected_building_id") and st.session_state.get("selected_year"):
            building_id = st.session_state["selected_building_id"]
            year = st.session_state["selected_year"]
            metering_data = extract_metering_data(building_id, year)
            electricity_enduses_data = extract_electricity_enduses_data(building_id)
            hvac_system_data = extract_hvac_system_data(building_id)
            if metering_data:
                # Send data to the assistant for analysis
                full_data = {
                    "metering_data": metering_data,
                    "electricity_enduses_data": electricity_enduses_data,
                    "hvac_system_data": hvac_system_data
                }
                client.beta.threads.messages.create(thread_id=st.session_state["thread_id"],
                                                    role="user",
                                                    content=json.dumps(full_data))
    except Exception as e:
        st.error(f"Error processing message: {e}")

def extract_building_id(response):
    for building in st.session_state["buildings"]:
        if building["buildingName"] in response:
            return building["building_id"]
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
