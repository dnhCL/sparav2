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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("assistant_id")

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
    print("[Chat Initialization] Initializing chat...")
    if 'assistant_created' not in st.session_state:
        assistant = create_or_update_assistant(file_paths)
        st.session_state['assistant_created'] = True
        print("[Chat Initialization] Assistant created.")
    else:
        print("[Chat Initialization] Assistant already created.")

    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state["thread_id"] = thread.id
        print(f"[Chat Initialization] Thread created with ID: {thread.id}")

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": "Hello! How can I help you today?"}]
        print("[Chat Initialization] Initial message added to session.")

def handle_user_input(prompt):
    print(f"[Handle User Input] Handling user input: {prompt}")
    if not prompt.strip():
        st.warning("Please enter a message.")
        print("[Handle User Input] No input provided.")
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    print(f"[Handle User Input] User message added to session: {prompt}")

    try:
        client.beta.threads.messages.create(thread_id=st.session_state["thread_id"],
                                            role="user",
                                            content=prompt)
        print("[Handle User Input] User message sent to assistant.")

        active_run = None
        try:
            runs = client.beta.threads.runs.list(thread_id=st.session_state["thread_id"])
            active_run = next((run for run in runs.data if run.status == 'active'), None)
            print("[Handle User Input] Active run fetched.")
        except Exception as e:
            st.error(f"Error fetching thread runs: {e}")
            print(f"[Handle User Input] Error fetching thread runs: {e}")

        if active_run:
            run = active_run
        else:
            run = client.beta.threads.runs.create(thread_id=st.session_state["thread_id"],
                                                  assistant_id=assistant_id)
            print(f"[Handle User Input] New run created with ID: {run.id}")

        # Limitar el tiempo de espera a 30 segundos
        start_time = time.time()
        timeout = 30  # 30 segundos

        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=st.session_state["thread_id"],
                                                           run_id=run.id)
            if run_status.status == 'completed':
                print("[Handle User Input] Run completed.")
                break
            if time.time() - start_time > timeout:
                print("[Handle User Input] Run timeout reached.")
                st.error("The operation timed out. Please try again.")
                return
            print("[Handle User Input] Waiting for run to complete...")
            time.sleep(1)

        messages = client.beta.threads.messages.list(thread_id=st.session_state["thread_id"])
        response = messages.data[0].content[0].text.value
        st.session_state.messages.append({"role": "assistant", "content": response})
        print(f"[Handle User Input] Assistant response added to session: {response}")

        # If the assistant identifies a building
        if "building" in response.lower():
            building_id = extract_building_id(response)
            if building_id:
                st.session_state["selected_building_id"] = building_id
                print(f"[Handle User Input] Building identified: {building_id}")

        # If the assistant identifies a year
        if "year" in response.lower():
            year = extract_year(response)
            if year:
                st.session_state["selected_year"] = year
                print(f"[Handle User Input] Year identified: {year}")

        # If the assistant identifies a request for a report
        if "report" in response.lower():
            st.session_state["report_requested"] = True
            print("[Handle User Input] Report requested by user.")

        # Extract meter data using Python and check if data has been sent already
        if st.session_state.get("selected_building_id") and st.session_state.get("selected_year"):
            building_id = st.session_state["selected_building_id"]
            year = st.session_state["selected_year"]
            if "data_sent" not in st.session_state or not st.session_state["data_sent"]:
                metering_data = extract_metering_data(building_id)
                electricity_enduses_data = extract_electricity_enduses_data(building_id)
                hvac_system_data = extract_hvac_system_data(building_id)
                if metering_data:
                    print(f"[Handle User Input] Metering data extracted for building {building_id} and year {year}.")
                    # Send data to the assistant for analysis
                    full_data = {
                        "metering_data": metering_data,
                        "electricity_enduses_data": electricity_enduses_data,
                        "hvac_system_data": hvac_system_data
                    }
                    client.beta.threads.messages.create(thread_id=st.session_state["thread_id"],
                                                        role="user",
                                                        content=json.dumps(full_data))
                    print("[Handle User Input] Full data sent to assistant for analysis.")
                    st.session_state["data_sent"] = True
    except Exception as e:
        st.error(f"Error processing message: {e}")
        print(f"[Handle User Input] Error processing message: {e}")

def extract_building_id(response):
    print("[Extract Building ID] Extracting building ID from response...")
    for building in st.session_state["buildings"]:
        if building["buildingName"] in response:
            print(f"[Extract Building ID] Building ID found: {building['building_id']}")
            return building["building_id"]
    print("[Extract Building ID] No building ID found.")
    return None

def extract_year(response):
    print("[Extract Year] Extracting year from response...")
    match = re.search(r'\b(20\d{2})\b', response)
    if match:
        year = int(match.group(0))
        print(f"[Extract Year] Year found: {year}")
        return year
    print("[Extract Year] No year found.")
    return None

def extract_metering_data(building_id):
    print(f"[Extract Metering Data] Extracting metering data for building ID: {building_id} and year 2023...")
    year = 2023
    meterings_data = st.session_state["meterings_data"]
    if str(building_id) in meterings_data and str(year) in meterings_data[str(building_id)]:
        print(f"[Extract Metering Data] Metering data found for building {building_id} in year {year}.")
        return meterings_data[str(building_id)][str(year)]
    print(f"[Extract Metering Data] No metering data found for building {building_id} in year {year}.")
    return None

def extract_electricity_enduses_data(building_id):
    print(f"[Extract Electricity Enduses Data] Extracting electricity enduses data for building ID: {building_id}...")
    enduses = st.session_state["electricity_enduses_data"]
    result = next((item for item in enduses if item["building_id"] == building_id), None)
    if result:
        print(f"[Extract Electricity Enduses Data] Electricity enduses data found for building {building_id}.")
    else:
        print(f"[Extract Electricity Enduses Data] No electricity enduses data found for building {building_id}.")
    return result

def extract_hvac_system_data(building_id):
    print(f"[Extract HVAC System Data] Extracting HVAC system data for building ID: {building_id}...")
    hvac = st.session_state["hvac_systems_data"]
    result = next((item for item in hvac if item["building_id"] == building_id), None)
    if result:
        print(f"[Extract HVAC System Data] HVAC system data found for building {building_id}.")
    else:
        print(f"[Extract HVAC System Data] No HVAC system data found for building {building_id}.")
    return result
