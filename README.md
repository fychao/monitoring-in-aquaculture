# monitoring-in-aquaculture

create venv to and install packages

```
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
```

modify influxdb ip address and token in script, then register your python code to crontab like this

```
*/1 * * * * /home/ubuntu/gather_data/.venv/bin/python /home/ubuntu/gather_data/gather_data.py >> work.log 2>&1
*/1 * * * * /home/ubuntu/gather_data/.venv/bin/python /home/ubuntu/gather_data/realtime_ml.py >> work1.log 2>&1
```
