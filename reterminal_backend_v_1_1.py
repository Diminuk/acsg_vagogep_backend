# ********** currently on reterminal **********

# import infra_control as il
import time
import json
import os 
import datetime

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
    allow_origins=["*"],  # Replace "*" with your frontend URL in production
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
    auth = file_api.login(data)
    if auth[0]:
        return {"message": auth[1]}
    else: 
        raise HTTPException(status_code=404, detail="Incorrect username or password")
        #return {"message": "Incorrect username or password"}

@app.get("/api/logout")
async def logout():
    backend_variables.state["logged_in"] = False,
    backend_variables.state["user_type"] = ""
    backend_variables.state["username"] = ""
    file_api.log(type="logout",
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
        # Simulate reading from a peripheral
        if backend_variables.last_websocket_payload != backend_variables.websocket_payload:  # Threshold for sending a message
            await websocket.send_json(backend_variables.websocket_payload)
        backend_variables.last_websocket_payload = backend_variables.websocket_payload.copy()
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

# ---------- STARTUP EVENT -----------
async def sensor_read():
    while True:
        try:
            sensor_array = backend_variables.myrelay.read_input()
            if sensor_array[-1] == 0:
                backend_variables.websocket_payload['cut_up'] = True
            else:
                backend_variables.websocket_payload['cut_up'] = False
            if sensor_array[-2] == 0:
                backend_variables.websocket_payload['cut_down'] = True
            else:
                backend_variables.websocket_payload['cut_down'] = False
            # TODO: add matbegin sensor 
            # TODO: if matbegin sensor is off set null_cut to False
            #print(f"Data from relaycard: {sensor_array}")
        except Exception as e:
            if not backend_variables.TESTING:
                print("Sensor read error")
                print(e)
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
        pass 
        # todo implement
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
    asyncio.create_task(reconnect())

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


@app.on_event("shutdown")
async def shutdown_event():
    # turn off everything
    # ...
    # log off 
    file_api.log("OFF",None)

# ------------------- end of on_event functions ----------------------
    
@app.get("/api/get_state")
def get_state():
    msg = {}
    msg['state'] = backend_variables.state 
    msg['websocket_payload'] = backend_variables.websocket_payload
    msg['parameters'] = backend_variables.parameters
    return msg
    
# routers
app.include_router(sp_api.router)
app.include_router(ap_api.router)
app.include_router(process.router)
app.include_router(manual_gui.router)
app.include_router(file_api.router)


if __name__ == "__main__":
    import uvicorn
    # init all the shared global variables
    backend_variables.init()
    uvicorn.run(app, host="0.0.0.0", port=8000)
