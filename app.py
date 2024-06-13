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

# User input section with button
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
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Energy Efficiency Report for HSB BRF Sjöresan i Stockholm', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_report(building_id, year):
    building_info = next(b for b in st.session_state["id_data"] if b["building_id"] == building_id)
    data = st.session_state["meterings_data"].get(str(building_id))
    df = pd.DataFrame(data[str(year)]) if data and str(year) in data else pd.DataFrame()

    pdf = PDF()
    pdf.add_page()

    pdf.set_font("Arial", size=12)
    
    # General Information
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "General Information", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Building Address: {building_info['buildingName']}", ln=True)
    pdf.cell(0, 10, f"BRF: HSB BRF Sjöresan i Stockholm", ln=True)
    pdf.cell(0, 10, f"Energy Class: {building_info.get('declaredEnergyClass', 'Not specified')}", ln=True)
    pdf.cell(0, 10, f"Average Energy Consumption: {building_info.get('EnergyClassKwhM2', 'Not specified')} kWh/m²", ln=True)
    pdf.ln(10)
    
    # Monthly Energy Consumption
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Monthly Energy Consumption in {year}", ln=True)
    pdf.ln(10)
    
    if not df.empty:
        pdf.set_font("Arial", size=12)
        for index, row in df.iterrows():
            row_text = f"{row['month']}: Property={row['electricity_use_property']} kWh, Station={row['electricity_use_charging_station']} kWh, Hot Water={row['electricity_use_water_heating_and_tap_hot_water']} kWh"
            pdf.cell(0, 10, row_text, ln=True)
    else:
        pdf.cell(0, 10, f"No consumption data found for the year {year}.", ln=True)
    pdf.ln(10)
    
    # Graph of Monthly Consumption
    graph_path = generate_energy_usage_graph(building_id, year, show_plot=False)
    if graph_path:
        pdf.image(graph_path, x=10, y=None, w=180)
        pdf.ln(10)
    
    # HVAC Systems
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "HVAC Systems", ln=True)
    pdf.ln(10)
    
    hvac_data = extract_hvac_system_data(building_id)
    pdf.set_font("Arial", size=12)
    if hvac_data:
        for key, value in hvac_data.items():
            pdf.cell(0, 10, f"{key}: {value}", ln=True)
    else:
        pdf.cell(0, 10, "No HVAC data available.", ln=True)
    pdf.ln(10)
    
    # Electricity Enduses
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Electricity Enduses", ln=True)
    pdf.ln(10)
    
    enduses_data = extract_electricity_enduses_data(building_id)
    pdf.set_font("Arial", size=12)
    if enduses_data:
        for key, value in enduses_data.items():
            pdf.cell(0, 10, f"{key}: {value}", ln=True)
    else:
        pdf.cell(0, 10, "No electricity enduses data available.", ln=True)
    pdf.ln(10)
    
    # Conclusion
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Conclusion", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Please do not hesitate to ask additional questions to me.", ln=True)
    pdf.cell(0, 10, "Now I recommend you to send this report to Reza Tehrani, your Senior Energy and Climate Advisor to get a full breakdown.", ln=True)
    pdf.cell(0, 10, "Sincerely,", ln=True)
    pdf.cell(0, 10, "Spara, your Junior Energy and Climate Advisor", ln=True)
    
    # Save the report to a PDF file
    report_path = os.path.join("data", f"building_report_{building_id}_{year}.pdf")
    pdf.output(report_path)
    
    return report_path
def generate_recommendations(id):
    # Dummy implementation for recommendation generation
    recommendations = [
        {"measure": "Upgrade to LED lighting", "energy_saving": 15, "investment_cost": 5000, "payback_time": 3},
        {"measure": "Install solar panels", "energy_saving": 20, "investment_cost": 20000, "payback_time": 5},
        {"measure": "Improve insulation", "energy_saving": 10, "investment_cost": 10000, "payback_time": 4},
        {"measure": "Upgrade HVAC system", "energy_saving": 18, "investment_cost": 15000, "payback_time": 6},
        {"measure": "Install energy-efficient windows", "energy_saving": 12, "investment_cost": 12000, "payback_time": 4}
    ]
    return recommendations

# Check if the assistant has identified the building, year, and if report is requested
#and st.session_state.get("report_requested") to consider report
if st.session_state.get("selected_building_id") and st.session_state.get("selected_year") :
    building_id = st.session_state["selected_building_id"]
    year = st.session_state["selected_year"]
    building_info = next(b for b in st.session_state["id_data"] if b["building_id"] == building_id)

    st.subheader(f"Energy Consumption for {building_info['buildingName']} in {year}")
    

    # Generate and display the report
    report_path = generate_report(building_id, year)
    with open(report_path, "rb") as file:
        btn = st.download_button(
            label="Download Report",
            data=file,
            file_name=os.path.basename(report_path),
            mime="application/pdf"
        )

    # Analysis and Recommendations (Step 9)
    if st.button("Get Recommendations"):
        # Perform calculations and provide recommendations
        recommendations = generate_recommendations(building_id)
        st.session_state["recommendations"] = recommendations
        st.write(recommendations)


