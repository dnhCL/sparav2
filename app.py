import streamlit as st
from chatbot import initialize_chat, handle_user_input
import matplotlib.pyplot as plt
import pandas as pd
import json
import os
import requests
from energy_estimation import get_electricity_price, calculate_energy_savings

# Inicializar la sesión del chat
initialize_chat()

# Título de la aplicación
st.title("Asistente de Energía para Edificios")

# Cargar datos de los edificios
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Cargar datos
st.session_state["meterings_data"] = load_json("data/meterings.json")
st.session_state["electricity_enduses_data"] = load_json("data/electricity_enduses.json")
st.session_state["hvac_systems_data"] = load_json("data/hvac_systems.json")
st.session_state["id_data"] = load_json("data/id.json")
st.session_state["buildings"] = st.session_state["id_data"]

# Ocultar la barra lateral que muestra la conversación y ajustar el estilo del chat
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
        padding-bottom: 5rem; /* Espacio para la barra de entrada */
    }
    </style>
    """, unsafe_allow_html=True)

# Función para manejar la entrada del usuario y limpiar el campo de entrada
def handle_input():
    if "input" in st.session_state and st.session_state.input.strip():
        user_input = st.session_state.input
        handle_user_input(user_input)
        st.session_state.input = ""  # Clear input field

# Encapsular el área del chat en un contenedor
st.subheader("Chat del Asistente")
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state["messages"]:
        role = "Usuario" if msg["role"] == "user" else "Asistente"
        st.markdown(f"**{role}:** {msg['content']}")
    st.markdown('</div>', unsafe_allow_html=True)

# Sección de entrada de usuario con botón
user_input_col, button_col = st.columns([5, 1])
with user_input_col:
    st.text_input("Escribe tu mensaje aquí:", key="input", label_visibility="collapsed", on_change=handle_input)
with button_col:
    st.button("Enviar", on_click=handle_input)

# Función para visualizar datos de consumo de energía en un gráfico
def plot_energy_usage(building_id, year):
    data = st.session_state["meterings_data"].get(str(building_id))
    if data and str(year) in data:
        df = pd.DataFrame(data[str(year)])
        plt.figure(figsize=(10, 5))
        plt.plot(df["month"], df["electricity_use_property"], label='Electricidad Propiedad')
        plt.plot(df["month"], df["electricity_use_charging_station"], label='Estación de Carga')
        plt.plot(df["month"], df["electricity_use_water_heating_and_tap_hot_water"], label='Agua Caliente')
        plt.xlabel('Mes')
        plt.ylabel('Consumo de Electricidad (kWh)')
        plt.title(f'Consumo de Electricidad por Mes en {year}')
        plt.legend()
        st.pyplot(plt)

# Función para generar un reporte
def generate_report(building_id, year):
    report_content = []
    building_info = next(b for b in st.session_state["id_data"] if b["building_id"] == building_id)
    report_content.append(f"Reporte de Energía para el Edificio: {building_info['buildingName']}\n")
    report_content.append(f"ID del Edificio: {building_id}\n")
    report_content.append(f"Clase de Energía: {building_info['declaredEnergyClass']}\n")
    report_content.append(f"Consumo Energético Promedio: {building_info['EnergyClassKwhM2']} kWh/m²\n")

    data = st.session_state["meterings_data"].get(str(building_id))
    if data and str(year) in data:
        df = pd.DataFrame(data[str(year)])
        avg_consumption = df["electricity_use_property"].mean()
        report_content.append(f"Consumo Promedio de Electricidad de la Propiedad en {year}: {avg_consumption:.2f} kWh\n")
        
        # Obtener el precio de la electricidad para el año
        price_data = get_electricity_price(f"{year}-01-01")
        if price_data:
            avg_price_sek = sum([hour["price_sek"] for hour in price_data]) / len(price_data)
            report_content.append(f"Precio Promedio de Electricidad en {year}: {avg_price_sek:.2f} SEK/kWh\n")

            # Cálculos de ahorro de energía y ROI
            try:
                savings = calculate_energy_savings(building_id, year, avg_consumption)
                for result in savings:
                    report_content.append(f"\nMedida: {result['Measure']}")
                    report_content.append(f"\nAhorro Anual de Energía: {result['Annual Energy Savings (kWh)']:.2f} kWh")
                    report_content.append(f"\nAhorro Anual en Costos: {result['Annual Cost Savings (SEK)']:.2f} SEK")
                    report_content.append(f"\nRetorno de Inversión: {result['ROI (years)']:.2f} años")
            except Exception as e:
                report_content.append(f"\nError en el cálculo de ahorros: {e}")

    report_path = os.path.join("data", f"reporte_edificio_{building_id}_{year}.txt")
    with open(report_path, 'w', encoding='utf-8') as report_file:
        report_file.writelines(report_content)
    
    return report_path

# Verificar si el asistente ha identificado el edificio y el año
if st.session_state.get("selected_building_id") and st.session_state.get("selected_year"):
    building_id = st.session_state["selected_building_id"]
    year = st.session_state["selected_year"]
    building_info = next(b for b in st.session_state["id_data"] if b["building_id"] == building_id)

    st.subheader(f"Consumo de Energía para {building_info['buildingName']} en {year}")
    plot_energy_usage(building_id, year)

    # Generar y mostrar el reporte
    report_path = generate_report(building_id, year)
    st.markdown(f"[Descargar Reporte]({report_path})")


