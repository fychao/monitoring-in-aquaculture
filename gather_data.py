from pyCIOT.data import *
from datetime import datetime

a = Air().get_source()

# 使用 Air 類別的 get_data 函式，指定資料來源和檢測站ID，來獲取該檢測站的空氣品質資料
f = Air().get_data(src="OBS:EPA_IoT", stationID="11613429495")
# 顯示所得的空氣品質資料
data = {}
data['pm2dot5'] = f[0]['data'][0]['values'][0]['value']
data['humidity'] = f[0]['data'][1]['values'][0]['value']
data['temperature'] = f[0]['data'][1]['values'][0]['value']


from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# You can generate a Token from the "Tokens Tab" in the UI
token = ""
org = ""
bucket = ""

client = InfluxDBClient(url="http://your_ip_of_influxdb:8086", token=token)

write_api = client.write_api(write_options=SYNCHRONOUS)

for ele in data:
    print(data[ele])
    point = Point("EPA_IoT").tag("station", "11613429495").field(ele, data[ele]).time(f[0]['data'][1]['values'][0]['timestamp'], WritePrecision.NS)

    write_api.write(bucket, org, point)

def isPenghu(location):
    #23.786427003055625, 119.21833555473914
    #23.173029958028042, 119.75396762373913
    box_area = [23.786427003055625, 119.21833555473914, 23.173029958028042, 119.75396762373913]
    if (location['latitude'] < box_area[0] and location['latitude'] > box_area[2]) and (location['longitude'] < box_area[3] and location['longitude'] > box_area[1]):
        return True
    else: 
        return False
    

# 使用 Weather 類別的 get_station 函式，並指定資料來源為 "RAINFALL:CWB"，來獲取雨量站列表
w = Weather().get_station(src="RAINFALL:CWB")
# 顯示所得的雨量站列表

penghu_stations = []
for ele in w:
    if isPenghu(ele['location']):
        penghu_stations.append( (ele['properties']['stationName'], ele['properties']['stationID']) )


dataset = "RAINFALL:CWB"

for station in penghu_stations:
    station_id = station[1]
    print(station)
    
    w = Weather().get_data(src=dataset, stationID=station_id)
    
    for ele in w[0]['data']:
        point = Point(dataset).tag("station", station_id).field(ele['name'], float(ele['values'][0]['value'])).time(ele['values'][0]['timestamp'], WritePrecision.NS)
        write_api.write(bucket, org, point)



import requests


api_token = ""

base_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={api_token}&StationId=467350,467300&locationName=%E6%BE%8E%E6%B9%96%E7%B8%A3"


resp = requests.get(url=base_url)
data = resp.json() 

for ele in data['records']['Station']:

    keep_fields = ['SunshineDuration', 'WindDirection', 'WindSpeed', 'AirTemperature', 'RelativeHumidity', 'AirPressure', 'UVIndex']

    print(ele['StationId'])
    for ele1 in keep_fields:
        print("\t", ele1, float(ele['WeatherElement'][ele1]))
        point = Point("CWA").tag("StationId", ele['StationId']).field(ele1, float(ele['WeatherElement'][ele1])).time(ele['ObsTime']['DateTime'], WritePrecision.NS)
        write_api.write(bucket, org, point)
