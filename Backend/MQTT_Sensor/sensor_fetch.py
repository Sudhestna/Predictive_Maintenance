import random
import json
import random
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import json
from fastapi.responses import JSONResponse
from ML_prediction.detectanomaly import predict_anomaly

app = FastAPI()


OPERATIONAL_LOG_FILE = "C:\\Users\\GenAIHYDSYPUSR35\\Desktop\\PNC_AI_TEAM\\MQTT_Sensor\\operational_logs.json"
SENSOR_FILE = "C:\\Users\\GenAIHYDSYPUSR35\\Desktop\\PNC_AI_TEAM\\MQTT_Sensor\\sensor_readings.json"
S_SENSOR_FILE = r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\MQTT_Sensor\s_sensor_readings.json"

def update_r101(machine):
    machine["hits"] += 1
    if machine["hits"] >= machine["change_frequency"]:
        machine["hits"] = 0
        if machine["state"] == "NORMAL":
            machine["state"] = "WARNING"
        elif machine["state"] == "WARNING":
            machine["state"] = "CRITICAL"
        elif machine["state"] == "CRITICAL":
            machine["state"] = "MAINTENANCE"
        elif machine["state"] == "MAINTENANCE":
            machine["state"] = "NORMAL"
            machine["maintenance_completed"] = False
    sensors = machine["sensors"]

    sensors["joint_temperature_c"] += random.uniform(-0.2, 0.3)
    sensors["motor_current_a"] += random.uniform(-0.1, 0.1)
    sensors["joint_vibration_mm_s"] += random.uniform(-0.01, 0.01)
    sensors["encoder_position_deg"] += random.uniform(-0.05, 0.05)
    sensors["torque_nm"] += random.uniform(-0.1, 0.2)

    sensors["joint_temperature_c"] = round(sensors["joint_temperature_c"], 2)
    sensors["motor_current_a"] = round(sensors["motor_current_a"], 2)
    sensors["joint_vibration_mm_s"] = round(sensors["joint_vibration_mm_s"], 3)
    sensors["encoder_position_deg"] = round(sensors["encoder_position_deg"], 2)
    sensors["torque_nm"] = round(sensors["torque_nm"], 2)


def update_r102(machine):

    machine["hits"] += 1
    if machine["hits"] >= machine["change_frequency"]:
        machine["hits"] = 0
        if machine["state"] == "NORMAL":
            machine["state"] = "WARNING"
        elif machine["state"] == "WARNING":
            machine["state"] = "CRITICAL"
        elif machine["state"] == "CRITICAL":
            machine["state"] = "MAINTENANCE"
        elif machine["state"] == "MAINTENANCE":
            machine["state"] = "NORMAL"
            machine["maintenance_completed"] = False

    sensors = machine["sensors"]

    sensors["welding_temperature_c"] += random.uniform(-2, 1)
    sensors["spindle_torque_nm"] += random.uniform(-2, 2)
    sensors["coolant_flow_rate_lpm"] += random.uniform(-0.03, 0.03)
    sensors["motor_current_a"] += random.uniform(-0.2, 0.2)
    sensors["vibration_mm_s"] += random.uniform(-0.02, 0.02)

    sensors["welding_temperature_c"] = round(sensors["welding_temperature_c"], 2)
    sensors["spindle_torque_nm"] = round(sensors["spindle_torque_nm"], 2)
    sensors["coolant_flow_rate_lpm"] = round(sensors["coolant_flow_rate_lpm"], 2)
    sensors["motor_current_a"] = round(sensors["motor_current_a"], 2)
    sensors["vibration_mm_s"] = round(sensors["vibration_mm_s"], 3)



def update_r103(machine):

    machine["hits"] += 1

    if machine["hits"] >= machine["change_frequency"]:
        machine["hits"] = 0
        if machine["state"] == "NORMAL":
            machine["state"] = "WARNING"
        elif machine["state"] == "WARNING":
            machine["state"] = "CRITICAL"
        elif machine["state"] == "CRITICAL":
            machine["state"] = "MAINTENANCE"
        elif machine["state"] == "MAINTENANCE":
            machine["state"] = "NORMAL"
            machine["maintenance_completed"] = False

    sensors = machine["sensors"]
    sensors["pneumatic_pressure_bar"] += random.uniform(-0.1, 0.1)
    sensors["riveting_force_kn"] += random.uniform(-0.5, 0.5)
    sensors["motor_current_a"] += random.uniform(-0.1, 0.1)
    sensors["vibration_mm_s"] += random.uniform(-0.01, 0.01)
    sensors["encoder_position_deg"] += random.uniform(-0.05, 0.05)

    sensors["pneumatic_pressure_bar"] = round(sensors["pneumatic_pressure_bar"], 2)
    sensors["riveting_force_kn"] = round(sensors["riveting_force_kn"], 2)
    sensors["motor_current_a"] = round(sensors["motor_current_a"], 2)
    sensors["vibration_mm_s"] = round(sensors["vibration_mm_s"], 3)
    sensors["encoder_position_deg"] = round(sensors["encoder_position_deg"], 2)


def update_r104(machine):

    machine["hits"] += 1
    if machine["hits"] >= machine["change_frequency"]:
        machine["hits"] = 0
        if machine["state"] == "NORMAL":
            machine["state"] = "WARNING"
        elif machine["state"] == "WARNING":
            machine["state"] = "CRITICAL"
        elif machine["state"] == "CRITICAL":
            machine["state"] = "MAINTENANCE"
        elif machine["state"] == "MAINTENANCE":
            machine["state"] = "NORMAL"
            machine["maintenance_completed"] = False

    sensors = machine["sensors"]

    sensors["paint_pressure_bar"] += random.uniform(-0.1, 0.1)
    sensors["paint_flow_rate_lpm"] += random.uniform(-1, 1)
    sensors["nozzle_temperature_c"] += random.uniform(-1, 2)
    sensors["pump_current_a"] += random.uniform(-0.1, 0.1)
    sensors["robot_speed_mm_s"] += random.uniform(-2, 2)

    sensors["paint_pressure_bar"] = round(sensors["paint_pressure_bar"], 2)
    sensors["paint_flow_rate_lpm"] = round(sensors["paint_flow_rate_lpm"], 2)
    sensors["nozzle_temperature_c"] = round(sensors["nozzle_temperature_c"], 2)
    sensors["pump_current_a"] = round(sensors["pump_current_a"], 2)
    sensors["robot_speed_mm_s"] = round(sensors["robot_speed_mm_s"], 2)

def update_r105(machine):

    machine["hits"] += 1
    if machine["hits"] >= machine["change_frequency"]:
        machine["hits"] = 0
        if machine["state"] == "NORMAL":
            machine["state"] = "WARNING"
        elif machine["state"] == "WARNING":
            machine["state"] = "CRITICAL"
        elif machine["state"] == "CRITICAL":
            machine["state"] = "MAINTENANCE"
        elif machine["state"] == "MAINTENANCE":
            machine["state"] = "NORMAL"
            machine["maintenance_completed"] = False

    sensors = machine["sensors"]

    sensors["camera_temperature_c"] += random.uniform(-0.1, 0.1)
    sensors["laser_thickness_sensor_um"] += random.uniform(-1, 1)
    sensors["lighting_intensity_lux"] += random.uniform(-1, 1)
    sensors["cpu_temperature_c"] += random.uniform(-0.01, 0.01)
    sensors["camera_position_encoder_deg"] += random.uniform(-0.01, 0.01)

    sensors["camera_temperature_c"] = round(sensors["camera_temperature_c"], 2)
    sensors["laser_thickness_sensor_um"] = round(sensors["laser_thickness_sensor_um"], 2)
    sensors["lighting_intensity_lux"] = round(sensors["lighting_intensity_lux"], 2)
    sensors["cpu_temperature_c"] = round(sensors["cpu_temperature_c"], 2)
    sensors["camera_position_encoder_deg"] = round(sensors["camera_position_encoder_deg"], 2)


def update_sensor_values(machine_id: str, machine: dict):

    if machine_id == "R101":
        update_r101(machine)

    elif machine_id == "R102":
        update_r102(machine)

    elif machine_id == "R103":
        update_r103(machine)

    elif machine_id == "R104":
        update_r104(machine)

    elif machine_id == "R105":
        update_r105(machine)


@app.get("/live-sensors/{machine_id}")
async def get_live_sensor_data(machine_id: str):

    try:

        with open(S_SENSOR_FILE, "r") as f:
            sensor_data = json.load(f)

        if machine_id not in sensor_data:

            return JSONResponse(
                status_code=404,
                content={
                    "message": f"Machine '{machine_id}' not found."
                }
            )

        machine = sensor_data[machine_id]
        machine["timestamp"] = datetime.now(timezone.utc).isoformat()

        update_sensor_values(machine_id, machine)

        with open(SENSOR_FILE, "w") as f:
            json.dump(sensor_data, f, indent=4)

        return JSONResponse(
            status_code=200,
            content={"sensor_data":machine}
        )

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "message": str(e)
            }
        )

from pydantic import BaseModel
from fastapi.responses import JSONResponse
import json


class SensorSimulationRequest(BaseModel):
    machine_id: str
    sensor_name: str
    reading: float


@app.post("/simulate-sensor")
async def simulate_sensor(request: SensorSimulationRequest):

    try:

        with open(SENSOR_FILE, "r") as f:
            data = json.load(f)

        if request.machine_id not in data:
            return JSONResponse(
                status_code=404,
                content={"message": "Machine not found"}
            )

        machine = data[request.machine_id]

        if request.sensor_name not in machine["sensors"]:
            return JSONResponse(
                status_code=404,
                content={"message": "Sensor not found"}
            )

        # Update sensor reading
        machine["sensors"][request.sensor_name] = request.reading

        # Save updated JSON
        with open(SENSOR_FILE, "w") as f:
            json.dump(data, f, indent=4)

        ###################################################
        # ML Prediction
        ###################################################

        sensors = machine["sensors"]
        prediction = predict_anomaly(request.machine_id,sensors)  

        response = []

        for machine_id in data.keys():

            response.append(
                {
                    "machine_id": machine_id,
                    "prediction": "No Anomaly detected"
                }
            )

        if prediction == -1:
            for item in response:
                if item["machine_id"] == request.machine_id:
                    item["prediction"] = "Anomaly detected"
                    break 

        return JSONResponse(
            status_code=200,
            content={
                "data":response
            }
        )
        

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={"message": str(e)}
        )



@app.get("/current-sensors")
async def get_current_sensors():

    try:

        with open(SENSOR_FILE, "r") as f:
            data = json.load(f)

        return JSONResponse(
            status_code=200,
            content={"sensor_data":data}
        )

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={"message": str(e)}
        )

    

@app.get("/operational-logs/{machine_id}")
async def get_operational_logs(machine_id: str):

    try:

        with open(OPERATIONAL_LOG_FILE, "r") as f:
            logs = json.load(f)

        if machine_id not in logs:

            return JSONResponse(
                status_code=404,
                content={
                    "message": f"Machine '{machine_id}' not found."
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "machine_id": machine_id,
                "total_records": len(logs[machine_id]),
                "logs": logs[machine_id][-5:]
            }
        )

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "message": str(e)
            }
        )


@app.get("/machine-sensors/{machine_id}")
def machine_sensors(machine_id: str):

    try:

        with open(SENSOR_FILE, "r") as f:
            sensor_data = json.load(f)

        if machine_id not in sensor_data:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "Machine not found."
                }
            )

        return JSONResponse(
            status_code=200,
            content={"sensors":sensor_data[machine_id]["sensors"]}
        )

    except json.JSONDecodeError:
        return JSONResponse(
            status_code=200,
            content={}
        )

    except FileNotFoundError:
        return JSONResponse(
            status_code=200,
            content={}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "message": str(e)
            }
        )