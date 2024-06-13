import streamlit as st
from openai import OpenAI
import os
from assistant_instructions import instructions
from dotenv import load_dotenv
import json

# Cargar las variables de entorno
load_dotenv()
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# --------------------------------------------------------------
# Function to create a vector store and upload files
# --------------------------------------------------------------
def create_vector_store_with_files(paths):
    vector_store_response = client.beta.vector_stores.create(name="Spara_files")
    vector_store_id = vector_store_response.id

    for path in paths:
        with open(path, "rb") as file:
            file_response = client.files.create(file=file, purpose="assistants")
            client.beta.vector_stores.files.create(vector_store_id=vector_store_id,
                                                   file_id=file_response.id)

    return vector_store_id

# --------------------------------------------------------------
# Function to create or update the assistant
# --------------------------------------------------------------
def create_or_update_assistant(file_paths):
    assistant_name = "Spara"
    vector_store_id = create_vector_store_with_files(file_paths)

    existing_assistants = client.beta.assistants.list().data
    existing_assistant = next((a for a in existing_assistants if a.name == assistant_name), None)

    if existing_assistant:
        assistant_id = existing_assistant.id
        updated_assistant = client.beta.assistants.update(
            assistant_id=assistant_id,
            instructions=instructions,
            tools=[{
                "type": "file_search"
            }, {
                "type": "code_interpreter"
            }],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store_id]
                }
            })
        print(f"Updated existing assistant: {assistant_name}")
        return updated_assistant
    else:
        new_assistant = client.beta.assistants.create(name=assistant_name,
                                                      instructions=instructions,
                                                      model="gpt-3.5-turbo-0125",
                                                      tools=[{
                                                          "type": "file_search"
                                                      },{
                                                        "type": "code_interpreter"
                                                      }],
                                                      tool_resources={
                                                          "file_search": {
                                                              "vector_store_ids": [vector_store_id]
                                                          }
                                                      })
        print(f"Created new assistant: {assistant_name}")
        return new_assistant

# --------------------------------------------------------------
# Function to evaluate energy profile using code interpreter
# --------------------------------------------------------------
def evaluate_energy_profile(building_id):
    code = f"""
import json

def evaluate_energy_profile(building_id):
    with open('data/meterings.json', 'r') as f:
        meterings_data = json.load(f)
    
    year = 2023
    building_data = meterings_data.get(str(building_id), {{}})
    year_data = building_data.get(str(year), [])

    if not year_data:
        return None, None

    peak_power = max([month['electricity_use_property'] for month in year_data])
    primary_energy_use_intensity = sum([month['electricity_use_property'] for month in year_data])

    return peak_power, primary_energy_use_intensity

# Ejemplo de uso
building_id = {building_id}
peak_power, primary_energy_use_intensity = evaluate_energy_profile(building_id)
print(f"Peak Power (kW): {{peak_power}}")
print(f"Primary Energy Use Intensity (kWh/Atemp): {{primary_energy_use_intensity}}")
"""
    # Execute the code interpreter tool
    result = client.tools.code_interpreter.execute(code)
    return result

# Ejemplo de uso de la función
building_id = 1  # ID del edificio proporcionado
result = evaluate_energy_profile(building_id)
print(result)
