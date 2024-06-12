from fpdf import FPDF
import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt

def generate_energy_usage_graph(building_id, year, data, show_plot=True):
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
            plt.show()
        plt.close(fig)
        return graph_path
    return None

def generate_report(building_id, year, building_info, metering_data, hvac_data, enduses_data, recommendations):
    data = metering_data.get(str(building_id))
    df = pd.DataFrame(data[str(year)]) if data and str(year) in data else pd.DataFrame()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # Título
    pdf.cell(200, 10, txt=f"Energy Report for Building: {building_info['buildingName']}", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
    pdf.ln(10)
    
    # Información General del Edificio
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="General Information about the Building", ln=True, align='L')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Building ID: {building_id}", ln=True, align='L')
    pdf.cell(200, 10, txt=f"Energy Class: {building_info['declaredEnergyClass']}", ln=True, align='L')
    pdf.cell(200, 10, txt=f"Average Energy Consumption: {building_info['EnergyClassKwhM2']} kWh/m²", ln=True, align='L')
    pdf.ln(10)
    
    # Consumo Energético
    if not df.empty:
        avg_consumption = df["electricity_use_property"].mean()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Proposed Measures and Reduction Potential", ln=True, align='L')
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Average Property Electricity Consumption in {year}: {avg_consumption:.2f} kWh", ln=True, align='L')
        pdf.ln(10)
        pdf.cell(200, 10, txt="Monthly Electricity Consumption Details:", ln=True, align='L')
        pdf.ln(10)
        for index, row in df.iterrows():
            row_text = f"{row['month']}: Property={row['electricity_use_property']} kWh, Station={row['electricity_use_charging_station']} kWh, Hot Water={row['electricity_use_water_heating_and_tap_hot_water']} kWh"
            pdf.cell(200, 10, txt=row_text, ln=True, align='L')
        
        # Generar y añadir el gráfico
        graph_path = generate_energy_usage_graph(building_id, year, metering_data, show_plot=False)
        if graph_path:
            pdf.image(graph_path, x=10, y=None, w=180)
            pdf.ln(10)
    else:
        pdf.cell(200, 10, txt=f"No consumption data found for the year {year}.", ln=True, align='L')
    
    # Sistemas HVAC y Usos Finales de la Electricidad
    if hvac_data:
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="HVAC Systems:", ln=True, align='L')
        pdf.set_font("Arial", size=12)
        for key, value in hvac_data.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True, align='L')
            
    if enduses_data:
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Electricity Enduses:", ln=True, align='L')
        pdf.set_font("Arial", size=12)
        for key, value in enduses_data.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True, align='L')
    
    # Recomendaciones
    if recommendations:
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Recommendations:", ln=True, align='L')
        pdf.set_font("Arial", size=12)
        for recommendation in recommendations:
            pdf.cell(200, 10, txt=f"- {recommendation}", ln=True, align='L')
    
    # Potencial de Reducción Total y Ahorros Anuales Estimados
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Total Reduction Potential and Annual Estimated Savings", ln=True, align='L')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Total Reduction Potential: [total_reduction] kWh", ln=True, align='L')
    pdf.cell(200, 10, txt=f"Annual Estimated Savings: [annual_savings] kSEK", ln=True, align='L')
    pdf.cell(200, 10, txt=f"ROI for all Measures: [roi]", ln=True, align='L')
    pdf.cell(200, 10, txt=f"Investment Cost: [investment_cost] kSEK", ln=True, align='L')
    pdf.cell(200, 10, txt=f"Annual Saving per Apartment: [annual_saving_per_apartment] kSEK", ln=True, align='L')
    
    # Mensaje Final
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(200, 10, txt="Please do not hesitate to ask additional questions to me, now I recommend you to send this report to Reza Tehrani, your Senior Energy and Climate Advisor to get a full breakdown.", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt="Sincerely,", ln=True, align='C')
    pdf.cell(200, 10, txt="Spara, your Junior Energy and Climate Advisor", ln=True, align='C')
    
    # Guardar el reporte en un archivo PDF
    report_path = os.path.join("data", f"building_report_{building_id}_{year}.pdf")
    pdf.output(report_path)
    
    return report_path
