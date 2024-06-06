import requests
import json

# Función para obtener precios de electricidad
def get_electricity_price(date):
    url = f"https://mgrey.se/espot?format=json&date={date}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["SE3"]
    else:
        raise Exception("Error al obtener los precios de la electricidad.")

# Función para cargar datos desde un archivo JSON
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Función para calcular el ahorro de energía y ROI
def calculate_energy_savings(building_id, year, avg_consumption):
    energy_savings_json = load_json("data/energy_savings.json")
    price_data = get_electricity_price(f"{year}-01-01")
    
    if price_data:
        avg_price_sek = sum([hour["price_sek"] for hour in price_data]) / len(price_data)
        
        savings_results = []
        
        for measure, details in energy_savings_json.items():
            annual_savings_kwh = avg_consumption * (details["Expected Energy Savings (%)"] / 100)
            annual_cost_savings_sek = annual_savings_kwh * avg_price_sek
            roi_years = details["Estimated Investment Cost (SEK)"] / annual_cost_savings_sek
            
            savings_results.append({
                "Measure": measure,
                "Annual Energy Savings (kWh)": annual_savings_kwh,
                "Annual Cost Savings (SEK)": annual_cost_savings_sek,
                "ROI (years)": roi_years
            })
        
        return savings_results
    else:
        raise Exception("No se pudo obtener el precio de la electricidad para los cálculos.")

# Ejemplo de uso
if __name__ == "__main__":
    building_id = 1
    year = 2023
    avg_consumption = 16000  # Ejemplo de consumo promedio de electricidad en kWh

    try:
        savings = calculate_energy_savings(building_id, year, avg_consumption)
        for result in savings:
            print(f"Medida: {result['Measure']}")
            print(f"Ahorro Anual de Energía: {result['Annual Energy Savings (kWh)']:.2f} kWh")
            print(f"Ahorro Anual en Costos: {result['Annual Cost Savings (SEK)']:.2f} SEK")
            print(f"Retorno de Inversión: {result['ROI (years)']:.2f} años\n")
    except Exception as e:
        print(f"Error: {e}")
