import asyncio, httpx, json, os
from datetime import datetime
from detectanomaly import predict_anomaly

BASE_URL = "http://localhost:5000/live-sensors"
machine_ids = [ "R101", "R102", "R103", "R104", "R105" ]

async def hit_api(client, machine_id):
    try:
        url = f"{BASE_URL}/{machine_id}"   
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            prediction = predict_anomaly(machine_id, data['sensor_data']['sensors'])
            if prediction==-1:
                save_anomaly(machine_id, data['sensor_data']['sensors'])
                print(f"[{machine_id}] Anomaly detected!")
            else:
                print(f"[{machine_id}] No anomaly detected.")
        else:
            print(f"[{machine_id}] Error: {response.status_code}")
    except Exception as e:
        print(f"[{machine_id}] Error: {e}")
async def model_worker(client, machine_id):
    while True:
        await hit_api(client, machine_id)
        await asyncio.sleep(10) 

ANOMALY_FILE = "alerts.json"
def save_anomaly(machine_id, sensor_data):
    anomaly = {
        "timestamp": datetime.now().isoformat(),
        "machine_id": machine_id,
        "message": f"Anomaly detected in machine {machine_id}. The machine may be experiencing abnormal operating conditions. Please inspect the equipment and perform the necessary maintenance.",
        "assigned": False
    }
    if not os.path.exists(ANOMALY_FILE):
        with open(ANOMALY_FILE, "w") as f:
            json.dump([], f)

    with open(ANOMALY_FILE, "r") as f:
        anomalies = json.load(f)

    anomalies.append(anomaly)

    # Save back
    with open(ANOMALY_FILE, "w") as f:
        json.dump(anomalies, f, indent=4)  


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        tasks = [asyncio.create_task(model_worker(client, model)) for model in machine_ids]
        await asyncio.gather(*tasks)



if __name__ == "__main__":
    asyncio.run(main())