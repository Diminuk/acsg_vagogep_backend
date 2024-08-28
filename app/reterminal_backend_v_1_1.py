# ********** currently on reterminal **********

# import infra_control as il
import time
import json
import os 
import datetime
import sys

from fastapi import FastAPI, Query, WebSocket,HTTPException,WebSocketDisconnect
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI

import backend_variables
import process_component as process
import array_process_api as ap_api
import single_process_api as sp_api
import manual_control_gui as manual_gui
import file_component as file_api
import numpy as np

# ---------------------- API START ------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Replace "*" with your frontend URL in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# --------------- USERS -------------------
@app.post("/api/add_user")
async def add_user(data: dict):
    if "username" in data and "password" in data and "type" in data:
        return file_api.create_user(data['username'],data['password'],data['type'])
    else:
        return {"message":"ERROR\nMissing data for user creation"}

@app.get("/api/delete_user")
async def delete_user(username: str):
    if username == "admin":
        return {"message":"cannot delete admin"}
    return file_api.delete_userfile(username)

@app.get("/api/get_users")
async def get_users():
    users = []
    filenames = file_api.list_files_in_directory("./users")
    for file in filenames:
        with open(f"./users/{file}","r") as f:
            userdata = json.load(f)
            if "username" in userdata and "password" in userdata and "type" in userdata:
                users.append({
                    "username":userdata['username'],
                    "user_type":userdata["type"]
                })
    return {"data":users}

@app.post("/api/login")
async def login(data: dict):
    auth = await file_api.login(data)
    if auth[0]:
        backend_variables.websocket_payload['process_status']="IDLE"
        backend_variables.websocket_payload['process_stopped_imm']=False
        return {"message": auth[1]}
    else: 
        raise HTTPException(status_code=404, detail="Incorrect username or password")
        #return {"message": "Incorrect username or password"}

@app.get("/api/logout")
async def logout():
    backend_variables.state["logged_in"] = False,
    backend_variables.state["user_type"] = ""
    backend_variables.state["username"] = ""
    # stop all process
    if not backend_variables.TESTING:
        backend_variables.myservo.stop_path()
        backend_variables.myinfra.turn_infra(False)
        backend_variables.myrelay.turn_off_relay(0)
    backend_variables.websocket_payload['process_status']="LOGGED_OUT"
    backend_variables.websocket_payload['process_running']=False
    backend_variables.websocket_payload['null_cut']=False
    backend_variables.websocket_payload['process_stopped_imm']=True
    print(backend_variables.websocket_payload)
    await file_api.log(type="logout",
                message={"username":backend_variables.state["username"],
                        "user_type":backend_variables.state["user_type"]})
    return {"message":"success"}

# ---------------- MAIN WEBSOCKET -------------------------------
# update sensor data
old_state = None
async def check_state():
    global old_state
    if old_state != backend_variables.websocket_payload:
        old_state = backend_variables.websocket_payload.copy()
        return True
    else: 
        return False

websockets = []


# websocket manager class
class ConnectionManager:
    """Class defining socket events"""
    def __init__(self):
        """init method, keeping track of connections"""
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        """connect event"""
        await websocket.accept()
        self.active_connections.append(websocket)

    async def send_personal_message(self, message, websocket: WebSocket):
        """Direct Message"""
        await websocket.send_json(message)
    
    def disconnect(self, websocket: WebSocket):
        """disconnect event"""
        self.active_connections.remove(websocket)


manager = ConnectionManager()

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            #data = await websocket.receive_text()
            await manager.send_personal_message(backend_variables.websocket_payload,websocket)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Websocket disconnected")
        await manager.send_personal_message("Bye!!!",websocket)



async def monitor_state_change(websocket: WebSocket):
    
    while True:
        try:
            # Simulate reading from a peripheral
            if (backend_variables.last_websocket_payload != backend_variables.websocket_payload):
                print("Send websocket msg")
                await websocket.send_json(backend_variables.websocket_payload)
                backend_variables.last_websocket_payload = backend_variables.websocket_payload.copy()
                
        except Exception as e:
            print("Error during websocket send")
            print(e)
            break  # Exit the loop if there's an error

        await asyncio.sleep(0.1)  # Simulate a delay between reads

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        await monitor_state_change(websocket)
    except Exception as e:
        print(f"Connection closed: {e}")
    finally:
        await websocket.close()

# ------------------ CALIBRATE endpoint -----------------------
@app.post("/api/calibrate")
def calibrate(data: dict):
    done = False
    print(data)
    if 'Expected' in data and 'Measured' in data:
        backend_variables.state['path_param'] = backend_variables.state['path_param'] * (float(data['Expected']) / float(data['Measured']))
        print(f"NEW param: {backend_variables.state['path_param']:.10f}")
        filename = "path_param.txt"

        with open(filename, mode='w') as file:
            file.write(f"{backend_variables.state['path_param']:.10f}")
        print(f"Data successfully saved to {filename}")
        file.close()
        done = True
    # TODO save current state 
    else:
        print("Error")
        print(f"{data:.10f}")
    return {"message":done}


# ------------------ Process altering functions ----------------
@app.post("/api/update/process")
def update_process(data: dict):
    if 'Mode' in data:
        backend_variables.websocket_payload["mode"] = data['Mode']
    if 'AutoJump' in data:
        backend_variables.websocket_payload["autojump"] = data['AutoJump']
                

    return {"message": ""}

# operator process update
@app.post("/api/update/operatorprocess")
def update_operator_process(data: dict):
    if 'Spd' in data:
        backend_variables.websocket_payload["array_spd_modifier"] = data['Spd']
        tmp = backend_variables.websocket_payload["array_spd_modifier"]
        print(f"Operator Spd changed to: {tmp}")
    if 'Acc' in data:
        backend_variables.websocket_payload["array_acc_modifier"] = data['Acc']
        tmp = backend_variables.websocket_payload["array_acc_modifier"]
        print(f"Operator Acc changed to: {tmp}")
    if 'Dec' in data:
        backend_variables.websocket_payload["array_dec_modifier"] = data['Dec']
        tmp = backend_variables.websocket_payload["array_dec_modifier"]
        print(f"Operator Dec changed to: {tmp}")
    if 'Infp' in data:
        backend_variables.websocket_payload["array_infpercent_modifier"] = data['Infp'] * 10
        tmp = backend_variables.websocket_payload["array_infpercent_modifier"]
        print(f"Operator Infp changed to: {tmp}")
    if 'Infd' in data:
        backend_variables.websocket_payload["array_infdelay_modifier"] = data['Infd']
        tmp = backend_variables.websocket_payload["array_infdelay_modifier"]
        print(f"Operator Infd changed to: {tmp}")
    return {"message": "Success"}


# ---------- STARTUP EVENT -----------
async def sensor_read():
    uptime_helper = time.time()
    while True:
        try:
            sensor_array = backend_variables.myrelay.read_input()
            print(sensor_array)
            if sensor_array[-1] == 0:
                backend_variables.websocket_payload['cut_up'] = True
            else:
                backend_variables.websocket_payload['cut_up'] = False
            if sensor_array[-2] == 0:
                backend_variables.websocket_payload['cut_down'] = True
            else:
                backend_variables.websocket_payload['cut_down'] = False
            if sensor_array[0] == 0:
                backend_variables.websocket_payload['mat_begin'] = False
                backend_variables.websocket_payload['null_cut'] = False
            else:
                backend_variables.websocket_payload['mat_begin'] = True
            if sensor_array[2] == 0 or sensor_array[3] == 0 or sensor_array[4] == 1:
                backend_variables.websocket_payload["conveyor"] = False
            elif sensor_array[4] == 0:
                backend_variables.websocket_payload['conveyor'] = True
            
            #print(f"Data from relaycard: {sensor_array}")
        except Exception as e:
            if not backend_variables.TESTING:
                print("Sensor read error")
                print(e)
        tmp = time.time()
        if tmp - uptime_helper > 60:
            backend_variables.websocket_payload["total_up_time"] += tmp - uptime_helper
            uptime_helper = time.time()
        await asyncio.sleep(0.3)


# --------- RECONNECT EVENT -----------
async def reconnect():
    while True:
        try:
            if(not backend_variables.myinfra.connected):
                backend_variables.myinfra.begin()
                await asyncio.sleep(0.1)
                backend_variables.myinfra.turn_infra(False)
                await asyncio.sleep(0.1)
                #print(f"Infra: {myinfra.connected}")
            if(not backend_variables.myservo.connected):
                backend_variables.myservo.begin()
                await asyncio.sleep(0.1)
                backend_variables.myservo.stop_path()
                await asyncio.sleep(0.1)
                #print(f"Servo: {myservo.connected}")
            if(not backend_variables.myrelay.connected):
                backend_variables.myrelay.begin()
                await asyncio.sleep(0.1)
                backend_variables.myrelay.turn_off_relay(0)
                await asyncio.sleep(0.1)
                #print(f"Relay: {myrelay.connected}")
        except:
            print(f"Servo: {backend_variables.myservo.connected} | Infra: {backend_variables.myinfra.connected} | Relay: {backend_variables.myrelay.connected}")
        await asyncio.sleep(0.5)
        
# --------- SAFETY EVENT ------------
async def safety_monitor():
    while True:
        try:
            if not backend_variables.TESTING:
                if(backend_variables.myrelay.read_input()[1] == 1): # emergency stop 
                    print("Emergency stop!")
                    backend_variables.websocket_payload["door"] = False
                    if(backend_variables.websocket_payload['process_running']):
                        backend_variables.websocket_payload['process_stopped_imm'] = True
                        backend_variables.myinfra.turn_infra(False)
                        backend_variables.myservo.stop_path()
                        backend_variables.myrelay.turn_off_relay(0)
                        backend_variables.myrelay.turn_off_relay(2)
                        backend_variables.myrelay.turn_off_relay(3)
                        backend_variables.myrelay.turn_on_relay(3)
                        backend_variables.myrelay.turn_off_relay(3)
                else:
                    backend_variables.websocket_payload["door"] = True
            else:
                if(backend_variables.test_variables["emergency_stop"] == False):
                    if(backend_variables.websocket_payload['process_running']):
                        print("Stopping process - emergency")
                        backend_variables.websocket_payload['process_stopped_imm'] = True
            # todo implement
        except:
            print("Some error occured during safety monitor")
        await asyncio.sleep(0.1)


# TODO: change to use lifespan events 
@app.on_event("startup")
async def startup_event():
    # init filesystem
    await file_api.init_filesystem()

    # log on 
    await file_api.log("ON",None)
    # read sensors continiously
    # start reconnect process
    #asyncio.create_task(reconnect())

    if not backend_variables.TESTING:
        backend_variables.myrelay.begin()
        await asyncio.sleep(0.1)
        backend_variables.myservo.begin()
        await asyncio.sleep(0.1)
        backend_variables.myinfra.begin()
        await asyncio.sleep(0.1)
        
        backend_variables.myinfra.turn_infra(False)
        await asyncio.sleep(0.1)
        backend_variables.myservo.stop_path()
        await asyncio.sleep(0.1)
        backend_variables.myrelay.turn_off_relay(0)
    print("OK")

    asyncio.create_task(sensor_read())
    asyncio.create_task(safety_monitor())


@app.on_event("shutdown")
async def shutdown_event():
    # turn off everything
    # ...
    # log off 
    pass
    

@app.post("/api/shutdown")
def shutdown():
    file_api.log("OFF",None)
    if not backend_variables.TESTING:
        try:
            backend_variables.myrelay.turn_off_relay(3)
            backend_variables.myrelay.turn_off_relay(2)
            backend_variables.myrelay.turn_on_relay(3)
            time.sleep(0.5)
            backend_variables.myrelay.turn_off_relay(3)
        except:
            print("Error with relay communication during shutdown")
        try:
            backend_variables.myinfra.turn_infra(False)
            backend_variables.myservo.stop_path()
            backend_variables.myrelay.turn_off_relay(0)
        except:
            print("Error with stop processes communication during shutdown")

    os.system('sudo shutdown -h now')

# ------------------- end of on_event functions ----------------------
    
@app.get("/api/get_state")
def get_state():
    #msg = {}
    #msg['state'] = backend_variables.state 
    #msg['websocket_payload'] = backend_variables.websocket_payload
    #msg['parameters'] = backend_variables.parameters
    return {'data':backend_variables.websocket_payload}
    
# routers
app.include_router(sp_api.router)
app.include_router(ap_api.router)
app.include_router(process.router)
app.include_router(manual_gui.router)
app.include_router(file_api.router)


if __name__ == "__main__":
    import uvicorn
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    # Change the current working directory to the script's directory
    os.chdir(script_dir)

    # init all the shared global variables
    backend_variables.init()
    uvicorn.run(app, host="0.0.0.0", port=8000)
