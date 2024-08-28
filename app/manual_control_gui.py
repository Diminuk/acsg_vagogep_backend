from fastapi import APIRouter
import asyncio
import time
from fastapi import  Query
from fastapi import HTTPException

#from backend_variables import *
import backend_variables
from process_component import push_path_data
from process_component import push_path_def

router = APIRouter()

# ------------------------- GUI FUNCTIONS -------------------------
@router.get("/api/unload")
def unload():
    print(f"Unload")
    push_path_def(path_num=1,
                        spd_num=3,
                        dly_num=0,
                        auto_num=0,
                        type_num=2,
                        acc_num=5,
                        dec_num=5)
    push_path_data(path_num=1,
                length=-500)
    backend_variables.myservo.start_path(1)
    backend_variables.state["null_cut"] = False
    backend_variables.websocket_payload["null_cut"] = False
    return {"message": "success"}

@router.get("/api/load")
def load():
    print(f"Load")
    push_path_def(path_num=1,
                        spd_num=3,
                        dly_num=0,
                        auto_num=0,
                        type_num=2,
                        acc_num=5,
                        dec_num=5)
    push_path_data(path_num=1,
                length=500)
    backend_variables.websocket_payload["null_cut"] = False
    if not backend_variables.TESTING:
        backend_variables.myservo.start_path(1)
    return {"message": "success"}

@router.get("/api/cut_up")
def cut_up():
    print(f"Cut up")
    if not backend_variables.TESTING:
        backend_variables.myrelay.turn_off_relay(0)
    return {"message": "success"}

@router.get("/api/cut_down")
def cut_down():
    print(f"Cut down")
    if not backend_variables.TESTING:
        backend_variables.myrelay.turn_on_relay(0)
    return {"message": "success"}

@router.get("/api/feed")
def feed(length: int = Query(..., title="Length")):
    print(f"Feed: {length}")
    push_path_def(path_num=1,
                        spd_num=3,
                        dly_num=0,
                        auto_num=0,
                        type_num=2,
                        acc_num=5,
                        dec_num=5)
    push_path_data(path_num=1,
                length=length)
    backend_variables.websocket_payload["null_cut"] = False
    backend_variables.myservo.start_path(1)
    return {"message": "success"}

@router.get("/api/pause")
def pause():
    print("Pause process")
    # pause logic
    backend_variables.websocket_payload["process_paused"] = True
    return {"message": "success"}

@router.get("/api/resume")
def resume():
    print("Resume process")
    # resume logic
    backend_variables.websocket_payload["process_paused"] = False
    return {"message": "success"}

@router.get("/api/stop_after")
def stop_after():
    print("Stop process after")
    backend_variables.websocket_payload['process_stopped_after'] = True
    return {"message": "success"}

@router.get("/api/stop_immidietly")
def stop_imm():
    print("Stop process immidietly")
    backend_variables.websocket_payload['process_stopped_imm'] = True
    backend_variables.websocket_payload['null_cut'] = False
    return {"message": "success"}

@router.get("/api/reset_batch_popup")
def reset_batch():
    print("Reset batch popup")
    backend_variables.websocket_payload['batch_limit_reached'] = False
    return {"message": "success"}

@router.get("/api/reset_manual_jump_trigger")
def reset_manual_jump(success: bool = Query(..., title="Success")):
    print("Reset manualjump popup")
    print(backend_variables.websocket_payload['manual_jump_trigger'])
    backend_variables.state['manual_jump_good'] = success
    backend_variables.websocket_payload['manual_jump_trigger'] = False
    return {"message": "success"}

@router.post("/api/set_infra")
def reset_batch(data: dict):
    if 'state' in data:
        if data["state"] == "ON":
            # set infra on
            # todo
            backend_variables.websocket_payload["infra"] = True
            backend_variables.myinfra.config_percentage(50)
            backend_variables.myinfra.turn_infra(True)
            return {"message":"ok"} 
        else:
            # set infra off
            # todo
            backend_variables.websocket_payload["infra"] = False
            backend_variables.myinfra.config_percentage(0)
            backend_variables.myinfra.turn_infra(False)
            return {"message":"ok"} 
    else:
        return {"message":"error"}
    
@router.post("/api/conveyor")
async def reset_batch(data: dict):
    if 'Conveyor' in data:
        if data["Conveyor"]:
            # start belt
            backend_variables.websocket_payload["conveyor"] = True
            if not backend_variables.TESTING:
                backend_variables.myrelay.turn_off_relay(3)
                backend_variables.myrelay.turn_off_relay(2)
                backend_variables.myrelay.turn_on_relay(2)
                await asyncio.sleep(0.5)
                backend_variables.myrelay.turn_off_relay(2)
                await asyncio.sleep(0.1)
                # check if conveyor really started 
                if backend_variables.myrelay.read_input()[2] ==0 or backend_variables.myrelay.read_input()[3] != 0:
                    backend_variables.websocket_payload["conveyor"] = False
                    print("Problem starting conveyor")
            return {"message":"conveyor started"} 
        else:
            # stop belt
            backend_variables.websocket_payload["conveyor"] = False
            if not backend_variables.TESTING:
                backend_variables.myrelay.turn_off_relay(3)
                backend_variables.myrelay.turn_off_relay(2)
                backend_variables.myrelay.turn_on_relay(3)
                await asyncio.sleep(0.5)
                backend_variables.myrelay.turn_off_relay(3)
                await asyncio.sleep(0.1)
                if backend_variables.myrelay.read_input()[2] !=0 or backend_variables.myrelay.read_input()[3] == 0:
                    backend_variables.websocket_payload["conveyor"] = True
                    print("Problem stopping conveyor")
            return {"message":"conveyor stopped"} 
    else:
        raise HTTPException(status_code=400, detail="Incorrect POST parameters")


# parameter endpoints 
@router.post("/api/update/parameter")
def update_parameter(data: dict):
    if 'speed' in data:
        return backend_variables.myservo.change_speed_table(data['speed'])
    if 'acc' in data:
        return backend_variables.myservo.change_speed_table(data['acc'])

@router.get("/api/get_params")
def get_params():
    data = {}
    data['speed'] = backend_variables.myservo.get_speed_table()
    data['acc'] = backend_variables.myservo.get_acc_table()
    return data

@router.get("/api/reset_current_array")
def reset_current_array():
    try:
        backend_variables.state['array_current_index'] = 1
        backend_variables.state['array_current_count'] = 1
        return {"status":"done"}
    except:
        raise HTTPException(status_code=400, detail="Some error occured")
    
@router.post("/api/nullcut")
def nullcut():
    backend_variables.websocket_payload['wait_nullcut_approve'] = True
    backend_variables.websocket_payload['null_cut'] = True
    if not backend_variables.TESTING:
        backend_variables.myrelay.turn_on_relay(0)
    return {"message":'OK'}

@router.post("/api/preheat")
async def preheat():

    preheat_time = 10

    backend_variables.websocket_payload['infra'] = True
    if not backend_variables.TESTING:
        backend_variables.myinfra.config_percentage(50)
        backend_variables.myinfra.turn_infra(True)
    await asyncio.sleep(10)
    if not backend_variables.TESTING:
        backend_variables.myinfra.config_percentage(0)
        backend_variables.myinfra.turn_infra(False)
    backend_variables.websocket_payload['infra'] = False



@router.post("/api/approve_nullcut")
def approve_nullcut(data: dict):
    if 'approve' in data:
        if data["approve"] == True:
            backend_variables.state["null_cut"] = True 
            backend_variables.websocket_payload["wait_nullcut_approve"] = False
            return {"message":"ok"} 
        else:
            backend_variables.state["null_cut"] = False 
            backend_variables.websocket_payload["wait_nullcut_approve"] = False
            return {"message": "ok"}
    else: 
        return {"message":"not_ok"} 
    
@router.post("/api/reset_current_array")
def reset_current_array():
    backend_variables.websocket_payload['array_current_count'] = 1
    backend_variables.websocket_payload['array_current_number'] = 1
    backend_variables.websocket_payload['array_used_length_bad'] = 0
    backend_variables.websocket_payload['array_used_length_good'] = 0
    backend_variables.websocket_payload['array_process_bad'] = 0
    backend_variables.websocket_payload['array_process_good'] = 0
    backend_variables.websocket_payload['array_process_remaining_time'] = 0
    backend_variables.websocket_payload['array_cycle_time'] = 0
    backend_variables.websocket_payload['array_process_remaining_length'] = 0
            


@router.get("/api/testing/change/materialsensor")
def testing_change_materialsensor():
    backend_variables.test_variables['materialsensor'] = not backend_variables.test_variables['materialsensor']
    backend_variables.websocket_payload['mat_begin'] = backend_variables.test_variables['materialsensor']
    return {"msg":"success"}
@router.get("/api/testing/change/emergency_stop")
def testing_change_emergency_stop():
    backend_variables.test_variables['emergency_stop'] = not backend_variables.test_variables['emergency_stop']
    backend_variables.websocket_payload['door'] = backend_variables.test_variables['emergency_stop']
    return {"msg":"success"}