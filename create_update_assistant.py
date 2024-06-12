import streamlit as st
from openai import OpenAI
import os
from assistant_instructions import instructions
from dotenv import load_dotenv
# Cargar las variables de entorno
load_dotenv()
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]


client = OpenAI(api_key=OPENAI_API_KEY)


# --------------------------------------------------------------
# Function to create a vector store and upload files
# --------------------------------------------------------------
def create_vector_store_with_files(paths):
  # Creating the vector store
  vector_store_response = client.beta.vector_stores.create(name="Sparabotv3_files")
  vector_store_id = vector_store_response.id

  # Upload files and associate them with the vector store
  for path in paths:
    with open(path, "rb") as file:
      # Update the purpose to 'assistants' from 'vector-search'
      file_response = client.files.create(file=file, purpose="assistants")
      client.beta.vector_stores.files.create(vector_store_id=vector_store_id,
                                             file_id=file_response.id)

  return vector_store_id


# --------------------------------------------------------------
# Function to create or update the assistant
# --------------------------------------------------------------
def create_or_update_assistant(file_paths):
  assistant_name = "Sparabotv3"
  vector_store_id = create_vector_store_with_files(file_paths)

  # Retrieve list of existing assistants
  existing_assistants = client.beta.assistants.list().data
  existing_assistant = next(
      (a for a in existing_assistants if a.name == assistant_name), None)

  if existing_assistant:
    assistant_id = existing_assistant.id
    # Update the existing assistant
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
    # Create a new assistant
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
                                                          "vector_store_ids":
                                                          [vector_store_id]
                                                      }
                                                  })
    print(f"Created new assistant: {assistant_name}")
    return new_assistant
#-------------------------------------------------------------------------------------------------