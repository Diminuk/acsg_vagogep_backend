from fastapi import APIRouter
import asyncio
import time
import os
import json
from file_component import list_files_in_directory
from fastapi import Query

#from backend_variables import current_process_array 
import backend_variables
router = APIRouter()

# --------------------- ARRAY CRUD functions ------------------
@router.post("/api/array/update")
def update_array(data: dict):
    print(data)
    filename = "./arrays/" + data['name'] + ".json"
    with open(filename,'w') as file:
        json.dump(data,file)
        #TODO check data validity
    # load to current array
    with open(filename,"r") as file:
        data = json.load(file)
        print("New data in memory:")
        backend_variables.current_process_array = data
        print(backend_variables.current_process_array)
    return {"message": "success"}

@router.get("/api/array/load")
async def load_array(filename: str = Query(...)):
    filename = f"./arrays/{filename}"
    print(backend_variables.current_process_array)
    print(filename)
    if os.path.exists(filename):
        with open(filename,"r") as file:
            response = json.load(file)
            print("Global array:")
            print(backend_variables.current_process_array)
            print("Response: ")
            print(response)
            backend_variables.current_process_array = response
            # debug
            print("Current process array is modified to:")
            print(backend_variables.current_process_array)
            return response
    else:
        return {"message" : "ERROR: file not found"}

    
@router.get("/api/array/files")
async def get_array_names():
    return {"files" : list_files_in_directory("./arrays/")}

@router.get("/api/get_current_array")
def get_current_array():
    return backend_variables.current_process_array