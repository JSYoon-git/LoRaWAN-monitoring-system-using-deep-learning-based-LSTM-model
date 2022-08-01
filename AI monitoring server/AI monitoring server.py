import torch
import torch.nn

from flask import Flask, request, jsonify
from chirpstack_api.as_pb import integration
from struct import *
import requests

import os 
import csv
import time

from DL_model import Conv1d_LSTM
import SMS


record = True
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model = Conv1d_LSTM(num_layers=2, hidden_unit=200).to(device)
checkpoint_path = './model/' + 'inference.pt'
checkpoint = torch.load(checkpoint_path)
model.load_state_dict(checkpoint['model_state_dict'])
queue = []

app = Flask(__name__)

now = time.localtime()
fname = '%d%02d%02d_%02d%02d%02d' % (now.tm_year-2000, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)

fieldnames = ['timestamp','device_name','fcnt', 'dr', 'rssi', 'snr', 'channel', 'co2', 'humidity', 'temperature', 'PM1.0', 'PM2.5', 'PM10']
path = './data/'
file_name = path+fname+'.csv'

# thingboard
url = "https://demo.thingsboard.io/api/v1/"
token_access = "NWnTuXkLEW6QPNDqxCVW"
telemetry = "/telemetry"

tmp = url+token_access+telemetry

@app.route('/', methods=['POST'])
def recv():
    global queue
    current = time.localtime()
    timestamp = "%02d%02d%02d" % (current.tm_hour, current.tm_min, current.tm_sec)
    
    if request.args['event'] == "up":
        pl = integration.UplinkEvent()
        pl.ParseFromString(request.data)
        payload = unpack('<HHHHBBBBHH',pl.data)
    
        device_name = pl.device_name
        dr = pl.dr
        rssi = pl.rx_info[0].rssi
        snr = pl.rx_info[0].lora_snr
        channel = pl.rx_info[0].channel
        f_cnt = pl.f_cnt
        
        voc = payload[0]
        co2 = payload[1]
        humi = payload[2]
        temp = payload[3]
        pm1p0 = payload[4]
        pm2p5 = payload[5]
        pm10 = payload[6]
        now_r_ref_r = payload[7]
        ref_r = payload[8]
        now_r = payload[9]
        
        queue.append([co2, humi, temp, pm1p0, pm2p5, pm10])
        if len(queue) > 10:
            queue.pop(0)
        else:
            print(len(queue))
        if f_cnt == 0:
            queue = []
        if len(queue) ==20:
            x_tensor = torch.tensor(queue, dtype=torch.float32)
            model.eval()
            with torch.no_grad():
                data = x_tensor.reshape(-1, 10, 6)
                data = data.to(device)
                predicted_label = model.forward(data)
                _, test_pred_index = torch.max(predicted_label, 1)
                pred = test_pred_index.cpu().detach().numpy()[0]
                
                if pred > pm2p5:
                    SMS.send_SMS(pred)

        file_exists = os.path.isfile(file_name)
        with open(file_name, 'a', newline='\n') as csvfile:
            wr = csv.DictWriter(csvfile, delimiter=',', fieldnames=fieldnames)
            if not file_exists: wr.writeheader()
            wr.writerow({
                'timestamp': int(timestamp),
                'device_name':device_name,
                'fcnt':int(f_cnt),
                'dr':int(dr), 
                'rssi':int(rssi), 
                'snr':float(snr), 
                'channel':int(channel), 
                'co2':int(co2),
                'humidity':float(humi/100),
                'temperature':float(temp/100),
                'PM1.0':int(pm1p0),
                'PM2.5':int(pm2p5),
                'PM10':int(pm10)
                })
        body = '\"temperature\": \"{:.2f}\", \"humidity\" : \"{:.2f}\", \"voc\" : \"{}\", \"co2\" : \"{}\", \"pm1p0\" : \"{}\", \"pm2p5\" : \"{}\", \"pm10\" : \"{}\"'.format(temp/100,humi/100, voc, co2,pm1p0,pm2p5, pm10)
        body = "{" + body + "}"
        print(body)
        header = {"Content-Type":"application/json"}

        res = requests.post(tmp, headers=header, data=body)
        print(res)
        
        return jsonify(success=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090, debug=True)