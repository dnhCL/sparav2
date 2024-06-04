import streamlit as st
import os
from chatbot import initialize_chat, handle_user_input

# Inicialización del asistente
initialize_chat()

st.title("Asistente de Energy Building")
st.write("Bienvenido al asistente de Energy Building. Por favor, ingrese su consulta.")

# Input de usuario
user_input = st.text_input("Escribe tu consulta aquí:")

if st.button("Enviar"):
    if user_input:
        handle_user_input(user_input)
    else:
        st.write("Por favor, ingrese una consulta.")

# Información del edificio
st.sidebar.title("Información del Edificio")

building_name = st.sidebar.text_input("Nombre del Edificio")
number_of_apartments = st.sidebar.number_input("Número de Apartamentos", min_value=0)
number_of_tenants = st.sidebar.number_input("Número de Inquilinos", min_value=0)
net_area_residential = st.sidebar.number_input("Área Neta Residencial (m2)", min_value=0)
net_area_non_residential = st.sidebar.number_input("Área Neta No Residencial (m2)", min_value=0)
net_area_heated = st.sidebar.number_input("Área Neta Calefaccionada (m2)", min_value=0)
declared_energy_class = st.sidebar.selectbox("Clase de Energía Declarada", ["A", "B", "C", "D", "E", "F", "G"])
energy_class_kwh_m2 = st.sidebar.number_input("Clase de Energía kWh/m2", min_value=0)

if st.sidebar.button("Guardar Información del Edificio"):
    building_data = {
        "building_name": building_name,
        "number_of_apartments": number_of_apartments,
        "number_of_tenants": number_of_tenants,
        "net_area_residential": net_area_residential,
        "net_area_non_residential": net_area_non_residential,
        "net_area_heated": net_area_heated,
        "declared_energy_class": declared_energy_class,
        "energy_class_kwh_m2": energy_class_kwh_m2
    }
    st.sidebar.write("Información del edificio guardada:")
    st.sidebar.json(building_data)
