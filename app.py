import streamlit as st
from chatbot import initialize_chat, handle_user_input, extract_hvac_system_data, extract_electricity_enduses_data, extract_metering_data
import matplotlib.pyplot as plt
import pandas as pd
import json
import os
from fpdf import FPDF

# Initialize chat session
initialize_chat()

# Application title
st.title("Building Energy Assistant")

# Load building data
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Load data
st.session_state["meterings_data"] = load_json("data/meterings.json")
st.session_state["electricity_enduses_data"] = load_json("data/electricity_enduses.json")
st.session_state["hvac_systems_data"] = load_json("data/hvac_systems.json")
st.session_state["id_data"] = load_json("data/id.json")
st.session_state["buildings"] = st.session_state["id_data"]

# Hide the sidebar showing the conversation and adjust chat style
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

# Function to handle user input and clear input field
def handle_input():
    if "input" in st.session_state and st.session_state.input.strip():
        user_input = st.session_state.input
        handle_user_input(user_input)
        st.session_state.input = ""  # Clear input field

# Encapsulate the chat area in a container
st.subheader("Assistant Chat")
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state["messages"]:
        role = "User" if msg["role"] == "user" else "Assistant"
        st.markdown(f"**{role}:** {msg['content']}")
    st.markdown('</div>', unsafe_allow_html=True)

# User input section with button /// Remember: Problem when the message is send using the button.
user_input_col, button_col = st.columns([5, 1])
with user_input_col:
    st.text_input("Type your message here:", key="input", label_visibility="collapsed", on_change=handle_input)
with button_col:
    st.button("Send", on_click=handle_input)

# Function to generate the energy usage graph
def generate_energy_usage_graph(building_id, year, show_plot=True):
    data = st.session_state["meterings_data"].get(str(building_id))
    if data and str(year) in data:
        df = pd.DataFrame(data[str(year)])
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df["month"], df["electricity_use_property"], label='Property Electricity')

        ax.set_xlabel('Month')
        ax.set_ylabel('Electricity Consumption (kWh)')
        ax.set_title(f'Monthly Electricity Consumption in {year}')
        ax.legend()
        graph_path = os.path.join("data", f"graph_{building_id}_{year}.png")
        plt.savefig(graph_path)
        if show_plot:
            st.pyplot(fig)
        plt.close(fig)
        return graph_path
    return None

# Function to generate a PDF report
def generate_report(building_id, year):
    building_info = next(b for b in st.session_state["id_data"] if b["building_id"] == building_id)
    data = st.session_state["meterings_data"].get(str(building_id))
    df = pd.DataFrame(data[str(year)]) if data and str(year) in data else pd.DataFrame()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add building information
    pdf.cell(200, 10, txt=f"Energy Report for Building: {building_info['buildingName']}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Building ID: {building_id}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Energy Class: {building_info['declaredEnergyClass']}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Average Energy Consumption: {building_info['EnergyClassKwhM2']} kWh/m²", ln=True, align='C')
    pdf.ln(10)
    
    # Add energy consumption data
    if not df.empty:
        avg_consumption = df["electricity_use_property"].mean()
        pdf.cell(200, 10, txt=f"Average Property Electricity Consumption in {year}: {avg_consumption:.2f} kWh", ln=True, align='C')
        pdf.ln(10)
        
        # Generate and add the graph
        graph_path = generate_energy_usage_graph(building_id, year, show_plot=False)
        if graph_path:
            pdf.image(graph_path, x=10, y=None, w=180)
            pdf.ln(10)
        
        # Monthly details
        pdf.cell(200, 10, txt="Monthly Electricity Consumption Details:", ln=True, align='C')
        pdf.ln(10)
        for index, row in df.iterrows():
            row_text = f"{row['month']}: Property={row['electricity_use_property']} kWh, Station={row['electricity_use_charging_station']} kWh, Hot Water={row['electricity_use_water_heating_and_tap_hot_water']} kWh"
            pdf.cell(200, 10, txt=row_text, ln=True, align='L')
    else:
        pdf.cell(200, 10, txt=f"No consumption data found for the year {year}.", ln=True, align='C')
    
    # Add HVAC and Electricity Enduses data
    hvac_data = extract_hvac_system_data(building_id)
    enduses_data = extract_electricity_enduses_data(building_id)
    
    if hvac_data:
        pdf.ln(10)
        pdf.cell(200, 10, txt="HVAC Systems:", ln=True, align='C')
        for key, value in hvac_data.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True, align='L')
            
    if enduses_data:
        pdf.ln(10)
        pdf.cell(200, 10, txt="Electricity Enduses:", ln=True, align='C')
        for key, value in enduses_data.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True, align='L')
    
    # Save the report to a PDF file
    report_path = os.path.join("data", f"building_report_{building_id}_{year}.pdf")
    pdf.output(report_path)
    
    return report_path

# Check if the assistant has identified the building and year
if st.session_state.get("selected_building_id") and st.session_state.get("selected_year"):
    building_id = st.session_state["selected_building_id"]
    year = st.session_state["selected_year"]
    building_info = next(b for b in st.session_state["id_data"] if b["building_id"] == building_id)

    st.subheader(f"Energy Consumption for {building_info['buildingName']} in {year}")
    generate_energy_usage_graph(building_id, year)  # Display the graph in the chat window
    
    # Generate and display the report
    report_path = generate_report(building_id, year)
    with open(report_path, "rb") as file:
        btn = st.download_button(
            label="Download Report",
            data=file,
            file_name=os.path.basename(report_path),
            mime="application/pdf"
        )

