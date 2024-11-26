from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

@app.route('/upload', methods=['POST'])
def upload_data():
    file = request.files['file']
    mode = request.form['mode']
    selected_date = request.form['selectedDate']

    # Завантаження CSV у DataFrame
    df = pd.read_csv(file)

    # Перетворення стовпця Datetime у формат datetime для фільтрації
    try:
        df['Datetime'] = pd.to_datetime(df['Datetime'], infer_datetime_format=True)
    except ValueError as e:
        print("Date conversion error:", e)
        return jsonify({"error": "Date conversion failed"}), 400

    # Обробка за вибраним режимом
    if mode == 'day':
        selected_date = pd.to_datetime(selected_date)
        df_filtered = df[df['Datetime'].dt.date == selected_date.date()]
        peaks = find_daily_peaks(df_filtered)
    elif mode == 'month':
        selected_month = pd.to_datetime(selected_date).month
        selected_year = pd.to_datetime(selected_date).year
        df_filtered = df[(df['Datetime'].dt.month == selected_month) & (df['Datetime'].dt.year == selected_year)]
        peaks = find_monthly_peaks(df_filtered)
    else:
        return jsonify({"error": "Invalid mode selected"}), 400

    return jsonify(peaks)

def find_daily_peaks(df):
    # Перетворення колонок споживання в числовий тип
    df[['PowerConsumption_Zone1', 'PowerConsumption_Zone2', 'PowerConsumption_Zone3']] = df[
        ['PowerConsumption_Zone1', 'PowerConsumption_Zone2', 'PowerConsumption_Zone3']
    ].apply(pd.to_numeric, errors='coerce').fillna(0)

    # Обчислення загального споживання та визначення порогу пікового значення
    total_consumption = df[['PowerConsumption_Zone1', 'PowerConsumption_Zone2', 'PowerConsumption_Zone3']].sum(axis=1)
    threshold = total_consumption.quantile(0.9)  # Новий поріг - 90-й перцентиль
    df['is_peak'] = total_consumption > threshold
    
    # Відбір пікових записів та повернення у форматі JSON
    peaks = df[df['is_peak'] == True]
    peaks['Total_Power'] = total_consumption
    return peaks[['Datetime', 'Total_Power', 'Temperature', 'Humidity', 'WindSpeed']].to_dict(orient='records')

def find_monthly_peaks(df):
    # Перетворення колонок споживання в числовий тип
    df[['PowerConsumption_Zone1', 'PowerConsumption_Zone2', 'PowerConsumption_Zone3']] = df[
        ['PowerConsumption_Zone1', 'PowerConsumption_Zone2', 'PowerConsumption_Zone3']
    ].apply(pd.to_numeric, errors='coerce').fillna(0)

    # Обчислення загального споживання та визначення порогу пікового значення
    total_consumption = df[['PowerConsumption_Zone1', 'PowerConsumption_Zone2', 'PowerConsumption_Zone3']].sum(axis=1)
    threshold = total_consumption.quantile(0.9)  # Новий поріг - 90-й перцентиль
    df['is_peak'] = total_consumption > threshold
    
    # Підрахунок піків за днями протягом місяця
    daily_peaks = df[df['is_peak'] == True].groupby(df['Datetime'].dt.date).size().reset_index(name='peak_count')
    return daily_peaks.to_dict(orient='records')

if __name__ == '__main__':
    app.run(debug=True)
