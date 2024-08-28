from fastapi import APIRouter
import asyncio
import json
import os
import datetime
import hashlib
from fastapi import HTTPException

import backend_variables
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import date
from typing import Dict
import httpx

router = APIRouter()


# --------------- FILE MANAGEMENT --------------------
def list_files_in_directory(directory):
    if os.path.exists(directory):
        filenames = os.listdir(directory)
        return filenames
    else:
        print(f"Directory '{directory}' does not exist.")
        return []
    
def load_json_file(filename):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON in file '{filename}'.")
        return None
    
def create_directories_if_not_exist(directories):
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Directory '{directory}' created.")
        else:
            print(f"Directory '{directory}' already exists.")


async def login(data: dict):
    if "username" in data and "password" in data:
        username = data['username']
        if os.path.exists(f"/data/users/{username}.txt"):
            with open(f"/data/users/{username}.txt","r") as file:
                userdata = json.load(file)
                if "username" in userdata and "password" in userdata and "type" in userdata:
                    if userdata["username"] != data["username"]:
                        return [False, None] 
                    if userdata['password'] == hashlib.md5(data["password"].encode()).hexdigest():
                        #state["logged_in"] = True
                        print(userdata)
                        backend_variables.state["user_type"] = userdata["type"]
                        backend_variables.state["username"] = userdata["username"]
                        await log(type="LOGIN",
                            message={"username":userdata["username"],
                                     "user_type":userdata["type"]})
                        return [True, userdata["type"]]
                    else:
                        return [False, None]
                else:
                    return [False, None]
        else:
            return [False, None]
    else:
        return [False, None]

def delete_userfile(username: str):
    if os.path.exists(f"/data/users/{username}.txt"):
        os.remove(f"/data/users/{username}.txt") 
        return {"message":"User deleted successfully"}
    else:
        return {"message":"ERROR\nNon-existing user"}

def create_user(username: str,
                password: str,
                type: str):
    if os.path.exists(f"/data/users/{username}.txt"):
        return {"message": "ERROR\nUsername already taken"}
    else:
        with open(f"/data/users/{username}.txt","w") as file:
            json.dump({"username":username,
                       "password":hashlib.md5(password.encode()).hexdigest(),
                       "type":type
                       }, file)
        file.close()
        return {"message":"User created successfully"}
directories = [
    "/data/users",
    "/data/log",
    "/data/arrays"
]
async def init_filesystem():
    # init dicts and files if not found
    create_directories_if_not_exist(directories)
    print("File system init done")

async def save_state():
    with open("/data/state", 'w') as json_file:
        json.dump(backend_variables.state, json_file)
        print("state saved to file")

async def load_state():
    try:
        with open("/data/state", 'r') as json_file:
            data = json.load(json_file)
            backend_variables.state['path_param'] = data['path_param']
    except:
        print("Missing file")

async def get_local_processes():
    return list_files_in_directory("/data/arrays/")

async def load_local_process(filename):
    return load_json_file(filename)

async def load_history_filename():
    return list_files_in_directory("/data/log/")

async def load_history(filename):
    return load_json_file(filename)

# -------------- LOG ---------------------
def get_current_filename():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y_%m_%d")
    print(f"formatted time: {formatted_time}")
    return formatted_time
def get_current_date():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d-%H:%M:%S")
    return formatted_time
def write_json_to_file(filename, json_data):
    try:
        with open(filename, 'r+') as file:
            # Read existing content
            file_content = file.read()

            # Remove any trailing closing brackets
            file_content = file_content.rstrip(']')

            # Check if the file has any content
            if file_content:
                # If the file is not empty, add a comma to separate objects
                file_content += ','

            # Write the JSON data to the file
            file_content += json.dumps(json_data)

            # Add a closing bracket at the end
            file_content += ']'

            # Move the cursor to the beginning of the file and overwrite its content
            file.seek(0)
            file.write(file_content)
    except FileNotFoundError:
        # If the file doesn't exist, create it and write the JSON data wrapped within square brackets
        with open(filename, 'w') as file:
            file.write(json.dumps([json_data]))  # Wrap the data within square brackets


async def log(type,
              message,
              ):
    print("Logging")
    print("Type:", type)
    print("Msg:", message)

    filename = f"{get_current_filename()}.txt"
    date = get_current_date()


    if type == "LOGIN":
        json_msg = {
            "date": date,
            "type": "LOGIN",
            "user": message['username'],
        }
        write_json_to_file(f"/data/log/{filename}",json_msg )
        return
    elif type == "ON":
        json_msg = {
            "date": date,
            "type": "ON",
        }
        write_json_to_file(f"/data/log/{filename}",json_msg )
        return

    elif type == "OFF":
        json_msg = {
            "date": date,
            "type": "OFF",
        }
        write_json_to_file(f"/data/log/{filename}",json_msg)
        return

    elif type == "SINGLE":
        json_msg = {
            "date": date,
            "type": "SINGLE",
            "data": message,
            "user":backend_variables.state["username"]
        }
        write_json_to_file(f"/data/log/{filename}",json_msg)
        return

    elif type == "ARRAY":
        json_msg = {
            "date": date,
            "type": "ARRAY",
            "data": message,
            "user":backend_variables.state["username"]
        }
        write_json_to_file(f"/data/log/{filename}",json_msg)
        return

    elif type == "ERROR":
        json_msg = {
            "date": date,
            "type": "ERROR",
            "cause": message,
            "user":backend_variables.state["username"]
        }
        write_json_to_file(f"/data/log/{filename}",json_msg)
        return
    
    else:
        print("Wrong type")
        print(type)


# endpoints
        
@router.get('/api/get_day_log')
async def get_day_log(date: str):
    if not date:
        return JSONResponse(content={"data": {}})
    data = load_json_file(f"/data/log/{date}.txt")
    if data is None:
        return JSONResponse(content={"data": {}})
        
    return JSONResponse(content={"data": data})

@router.get('/api/get_log_days')
async def get_log_days():
    filenames = list_files_in_directory("/data/log")
    if filenames is None:
        raise HTTPException(status_code=400, detail="Error during loading dates")
    data = []
    for file in filenames:
        data.append({'value':file,'label':file[:-4]})
    return {'data': data}

# export
class ExportLogRequest(BaseModel):
    endpoint: str
    startdate: datetime.datetime
    enddate: datetime.datetime

LOG_DIR = '/data/log'  # Directory where log files are stored

@router.post('/api/export')
async def export_log(data: ExportLogRequest):
    endpoint = data.endpoint
    startdate = data.startdate
    enddate = data.enddate

    # Validation to ensure startdate is before enddate
    if startdate > enddate:
        raise HTTPException(status_code=400, detail="Start date must be before end date")

    # Read and combine the log files
    combined_data = []
    for filename in os.listdir(LOG_DIR):
        if filename.endswith('.txt'):
            try:
                file_date_str = filename.split('.')[0]  # Strip the '.txt' extension
                print(f"Debug: file_date_str = '{file_date_str}'")
                file_date = datetime.datetime.strptime(file_date_str, '%Y_%m_%d')

                if startdate.date() <= file_date.date() <= enddate.date():
                    file_path = os.path.join(LOG_DIR, filename)
                    with open(file_path, 'r') as file:
                        file_data = json.load(file)
                        combined_data.extend(file_data)
            except:
                print("Something went wrong")

    print(combined_data)

    # Post the combined data to the external endpoint
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(endpoint, json=combined_data)
            if response.status_code == 200:
                return {"status": "success", "message": "Data successfully exported"}
            else:
                return {"status": "failure", "message": f"Failed to export data. Status code: {response.status_code}"}
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Request failed: {e}")

