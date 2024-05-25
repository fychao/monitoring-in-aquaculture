def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

station_ids = ['467300', '467350']

token = ""
org = ""
bucket = ""
client = InfluxDBClient(url="http://your_ip_of_influxdb:8086", token=token)

for station_id in station_ids:
    
    query = 'from(bucket: "sensor_data")' \
            '|> range(start: -120m)' \
            '|> filter(fn: (r) => r["_measurement"] == "CWA")' \
            f'|> filter(fn: (r) => r["StationId"] == "{station_id}")' \
            '|> filter(fn: (r) => r["_field"] == "AirPressure")'
    tables = client.query_api().query(query, org=org)
    
    # Parse the query results
    data = []
    for table in tables:
        for record in table.records:
            data.append({
                "time": record.get_time(),
                "value": record.get_value(),
                "field": record.get_field(),
                "measurement": record.get_measurement(),
                **record.values
            })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)


    wanted_df = df[(df['field'] == 'AirPressure') & (~df['StationId'].isna())]
    
    # Sort the DataFrame by 'time'
    wanted_df.sort_values(by='time', inplace=True)
    
    # Extract features
    wanted_df['hour'] = wanted_df['time'].dt.hour
    wanted_df['minute'] = wanted_df['time'].dt.minute
    wanted_df['second'] = wanted_df['time'].dt.second
    
    # Define input features and target variable
    X = wanted_df[['hour', 'minute', 'second']]
    y = wanted_df['value']
    
    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train the model
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(station_id, "\tMean Squared Error:", mse)
    
    
    predictions = []
    next_times = [wanted_df['time'].iloc[-1] + pd.Timedelta(minutes=10*i) for i in range(1, 11)]
    for time in next_times:
        next_hour = time.hour
        next_minute = time.minute
        next_second = time.second
        next_prediction = model.predict([[next_hour, next_minute, next_second]])
        predictions.append(next_prediction[0])
        print(f"Predicted air pressure for {time}: {next_prediction[0]}")
    
    
    # Write predicted data to InfluxDB
    
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    for i, time in enumerate(next_times):
        point = Point("predicted_data").time(time, WritePrecision.NS)
        point.field("estimated_airpressure", float(predictions[i]))
        point.tag("StationId", station_id)
        write_api.write(bucket, org, point)
    
    
    write_api.close()
