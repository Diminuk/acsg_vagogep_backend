from fastapi import APIRouter
import asyncio
import time
import numpy

import backend_variables
import file_component as file_comp

from ProcessLoop import ProcessLoop

router = APIRouter()

@router.get("/api/start_process")
async def start_process():
    if backend_variables.websocket_payload["process_running"]:
        return {"message": "Process already running"}

    #asyncio.create_task(async_start_process())  
    asyncio.create_task(ProcessLoop())  
    return {"message": "Process started successfully"}

# side note: very primitive approach may need some improvements later
def calc_eta(good: int,
             bad: int,
             total_length: float,
             avg_length: float,
             avg_time: float,
             elapsed_time: float):
    if good == 0:
        return -1
    optimal = total_length/avg_length * avg_time
    if bad == 0:
        return optimal
    return optimal + optimal * (bad/good) - elapsed_time

# --------- MAIN PROCESS LOGIC -----------
async def async_start_process():
    if not backend_variables.state['null_cut']:
        return {'message': 'Missing NullCut'}
    if backend_variables.websocket_payload["process_running"]:
        print("Process already running")
        return {"message":"Process already running"}
    
    start_time = time.time()
    elapsed_time = 0
    time_buffer = []
    
    backend_variables.websocket_payload["process_running"] = True
    backend_variables.websocket_payload['process_status'] = 1
    # cut up
    backend_variables.myrelay.turn_off_relay(0)
    if not backend_variables.state['process_stopped_imm']:
        while(backend_variables.myrelay.read_input()[0] != 0):
            backend_variables.myrelay.turn_off_relay(0)
            await asyncio.sleep(0.05)
            # stop imm
            if backend_variables.state["process_stopped_imm"]:
                print("Process stopped immidietly")
                break
            # pause
            if backend_variables.state["process_paused"]:
                print("Process paused")
                # turn off infra
                while backend_variables.state["process_paused"]:
                    await asyncio.sleep(0.05)
    
    
    
    # switch between modes
    if(backend_variables.state["mode"] == False):
        # single length mode
        
        # loop for single values
        for i in range(backend_variables.state["single_count"]):

            single_start_time = time.time()

            # config path 
            push_path_def(path_num=1,
                        spd_num=backend_variables.state["single_speed"],
                        dly_num=0,
                        auto_num=0,
                        type_num=2,
                        acc_num=backend_variables.state['single_acceleration'],
                        dec_num=backend_variables.state['single_deceleration'])
            push_path_data(path_num=1,
                        length=backend_variables.state['single_cut_length'])
            
            backend_variables.myinfra.config_percentage(backend_variables.state['single_infra_percentage'])

            backend_variables.websocket_payload['process_status'] = 2

            if not backend_variables.state['process_stopped_imm']:
                if backend_variables.state["single_batch_current"] -1 == backend_variables.state['single_batch']:
                    # batch finished, wait for batch zero from frontend
                    backend_variables.state['batch_limit_reached'] = True
                    while backend_variables.state["single_batch_current"] -1 == backend_variables.state['single_batch']:
                        await asyncio.sleep(0.05)
                        if backend_variables.state["process_stopped_imm"]:
                            print("Process stopped immidietly")
                            # turn off infra
                            break

            print(f"Single Process Element: {i}")
            print(f"Infra delay: {backend_variables.state['single_infra_delay']}")
            print(f"Infra percentage: {backend_variables.state['single_infra_percentage']}")
            print(f"Cut length: {backend_variables.state['single_cut_length']}")
            print(f"Cut delay: {backend_variables.state['single_cut_delay']}")
            print(f"Speed: {backend_variables.state['single_speed']}")
            print(f"Acceleration: {backend_variables.state['single_acceleration']}")
            print(f"Deceleration: {backend_variables.state['single_deceleration']}")
            print(f"Milling placeholder: {backend_variables.state['single_milling_placeholder']}")
            
            # ******* infra *********
            backend_variables.websocket_payload['process_status'] = 3
            if not backend_variables.state['process_stopped_imm']:
                # start infra
                backend_variables.myinfra.turn_infra(True)
                infra_start_time = time.time()
                while time.time() - infra_start_time < backend_variables.state["single_infra_delay"]/1000.0:
                    await asyncio.sleep(0.05)
                    if backend_variables.state["process_paused"]:
                        print("Process paused")
                        backend_variables.myinfra.turn_infra(False)
                        while backend_variables.state["process_paused"]:
                            await asyncio.sleep(0.05)
                            infra_start_time = time.time()

                    if backend_variables.state["process_stopped_imm"]:
                        print("Process stopped immidietly")
                        backend_variables.myinfra.turn_infra(False)
                        break
            if backend_variables.state['process_stopped_imm']:
                print("Breaking single process")
                backend_variables.myinfra.turn_infra(False)
                break

            # ********** feed fwd ***********
            backend_variables.websocket_payload['process_status'] = 4
            if not backend_variables.state['process_stopped_imm']:
                # start working path
                start_pos = backend_variables.myservo.get_axis_pos()
                backend_variables.myservo.start_path(1)
                await asyncio.sleep(0.1)
                while(int(backend_variables.myservo.poll_eop()) != 1):
                    await asyncio.sleep(0.05)
                    # stop imm
                    if backend_variables.state["process_stopped_imm"]:
                        print("Process stopped immidietly")
                        backend_variables.myservo.start_path(1000)
                        break
                    # pause
                    if backend_variables.state["process_paused"]:
                        print("Process paused")
                        # stop motor
                        backend_variables.myservo.start_path(1000)
                        await asyncio.sleep(2)
                        pause_pos = backend_variables.myservo.get_axis_pos()
                        print(pause_pos)
                        print(start_pos)
                        remaining_length = abs(backend_variables.state['single_cut_length'] - abs(int(pause_pos)-int(start_pos))*backend_variables.state["path_param"])
                        print(remaining_length)
                        while backend_variables.state["process_paused"]:
                            await asyncio.sleep(0.05)
                        push_path_data(path_num=1,
                                       length=remaining_length)
                        backend_variables.myservo.start_path(1)
                        await asyncio.sleep(0.5)
            if backend_variables.state['process_stopped_imm']:
                print("Breaking single process")
                break

            backend_variables.websocket_payload['process_status'] = 5 
            # *********** cut ************** 
            if not backend_variables.state['process_stopped_imm']:
                backend_variables.myrelay.turn_on_relay(0)
                while(backend_variables.myrelay.read_input()[1] != 0):
                    backend_variables.myrelay.turn_on_relay(0)
                    await asyncio.sleep(0.1)
                    # stop imm
                    if backend_variables.state["process_stopped_imm"]:
                        print("Process stopped immidietly")
                        break
                    # pause
                    if backend_variables.state["process_paused"]:
                        print("Process paused")
                        while backend_variables.state["process_paused"]:
                            await asyncio.sleep(0.05)
            if backend_variables.state['process_stopped_imm']:
                print("Breaking single process")
                break

            # wait after cut
            start_tmp = time.time()
            if not backend_variables.state['process_stopped_imm']:
                while((time.time() - start_tmp)*1000 < backend_variables.state['single_cut_delay']):
                    await asyncio.sleep(0.1)
                    # stop imm
                    if backend_variables.state["process_stopped_imm"]:
                        print("Process stopped immidietly")
                        break
                    # pause
                    if backend_variables.state["process_paused"]:
                        print("Process paused")
                        while backend_variables.state["process_paused"]:
                            await asyncio.sleep(0.05)
            if backend_variables.state['process_stopped_imm']:
                print("Breaking single process")
                break

            backend_variables.websocket_payload['process_status'] = 6
            # cut up
            if not backend_variables.state['process_stopped_imm']:
                backend_variables.myrelay.turn_off_relay(0)
                while(backend_variables.myrelay.read_input()[0] != 0):
                    backend_variables.myrelay.turn_off_relay(0)
                    await asyncio.sleep(0.1)
                    # stop imm
                    if backend_variables.state["process_stopped_imm"]:
                        print("Process stopped immidietly")
                        break
                    # pause
                    if backend_variables.state["process_paused"]:
                        print("Process paused")
                        while backend_variables.state["process_paused"]:
                            await asyncio.sleep(0.05)
            if backend_variables.state['process_stopped_imm']:
                print("Breaking single process")
                break

            backend_variables.websocket_payload['process_status'] = 7
            # ************ milling **********
            if not backend_variables.state['process_stopped_imm']:
                pass
            if backend_variables.state['process_stopped_imm']:
                print("Breaking single process")
                break

            single_stop_time = time.time()
            elapsed_time += single_stop_time - single_start_time
            time_buffer.append(single_stop_time-single_start_time)

            # ************ wait for approve ******
            if not backend_variables.state['process_stopped_imm']:
                if not backend_variables.state['autojump']:
                    # wait for approve from frontend
                    backend_variables.websocket_payload['manual_jump_trigger'] = True
                    backend_variables.websocket_payload['process_status'] = 8 
                    while backend_variables.websocket_payload["manual_jump_trigger"]:
                        await asyncio.sleep(0.05)
                        if backend_variables.state['process_stopped_imm']:
                            print("Breaking single process")
                            break
            if backend_variables.state['process_stopped_imm']:
                print("Breaking single process")
                break

            backend_variables.websocket_payload['process_status'] = 9

            quality = 'bad'
            # incerement current count states
            if not backend_variables.state['process_stopped_imm'] and (backend_variables.state['manual_jump_good'] or backend_variables.state['autojump']):
                backend_variables.state['single_total_current'] = backend_variables.state['single_total_current'] + 1
                backend_variables.state['single_batch_current'] = backend_variables.state['single_batch_current'] + 1
                quality ='good'

            file_comp.log(type='single_cut',
                            message={
                            'quality':quality,
                            'single_infra_percentage':backend_variables.state['single_infra_percentage'],
                            'single_infra_delay':backend_variables.state['single_infra_delay'],
                            'single_count':backend_variables.state['single_count'],
                            'single_batch':backend_variables.state['single_count'],
                            'single_total_current':backend_variables.state['single_total_current'],
                            'single_batch_current':backend_variables.state['single_batch_current'],
                            'single_cut_length':backend_variables.state['single_cut_length'],
                            'single_cut_delay':backend_variables.state['single_cut_delay'],
                            'single_speed':backend_variables.state['single_speed'],
                            'single_acceleration':backend_variables.state['single_acceleration'],
                            'single_deceleration':backend_variables.state['single_deceleration'],
                            'single_milling_placeholder':backend_variables.state['single_milling_placeholder'],
                            'path_param':backend_variables.state['path_param'],
                            })
            
            backend_variables.state['manual_jump_good'] = False 

            if not backend_variables.state['process_stopped_imm']:
                if backend_variables.state["single_batch_current"] -1 == backend_variables.state['single_batch']:
                    # batch finished, wait for batch zero from frontend
                    backend_variables.state['batch_limit_reached'] = True
                    while backend_variables.state["single_batch_current"] -1 == backend_variables.state['single_batch']:
                        await asyncio.sleep(0.05)
                        if backend_variables.state["process_stopped_imm"]:
                            print("Process stopped immidietly")
                            # turn off infra
                            break
            backend_variables.websocket_payload["eta"] = calc_eta(backend_variables.websocket_payload['process_good'],
                                                backend_variables.websocket_payload['process_bad'],
                                                backend_variables.state['single_count'] * backend_variables.state['single_cut_length'],
                                                backend_variables.state['single_cut_length'],
                                                numpy.average(time_buffer),
                                                elapsed_time)
            

                    

            if backend_variables.state["process_stopped_after"]:
                print("Stopping process because of STOP_AFTER")
                file_comp.log(type='stop_after',
                              message=None)
                break


    else:
        # **************** ARRAY MODE !!! ***********************
        # loop for array values
        if backend_variables.current_process_array is None or backend_variables.current_process_array["data"] is None:
            print("Current process array is empty")

        array_total_count = 0
        array_total_length = 0
        for item in backend_variables.current_process_array['data']:
            array_total_count += item['count']
            array_total_length += item['count'] * item['path_length']
        array_avg_length = array_total_length / array_total_count

        for element in backend_variables.current_process_array["data"]:
            if element is None:
                break
            if element['number'] < backend_variables.state['array_current_index']:
                # skip if already done
                continue
                
            array_start_time = time.time()

            # update current index
            backend_variables.state["array_current_index"] = element['number']
            # config path def and length
            backend_variables.websocket_payload['process_status'] = 2
            push_path_def(path_num=1,
                        spd_num=element['path_def']['spd'],
                        dly_num=0,
                        auto_num=0,
                        type_num=2,
                        acc_num=element['path_def']['acc'],
                        dec_num=element['path_def']['dec'])
            push_path_data(path_num=1,
                        length=element['path_length'])
            
            backend_variables.myinfra.config_percentage(element["inf_percent"])
            
            for i in range(element['count'] + 1):
                if i == 0:
                    # very barbaric solution but works
                    continue
                if i < backend_variables.state['array_current_count']:
                    # skip if already done
                    continue
                backend_variables.state["array_current_count"] = i
                print(f"Number: {backend_variables.state['array_current_index']} | Count: {i}/{element['count']}")

                backend_variables.websocket_payload['process_status'] = 1
                # [1] make sure the knife is in the upper position
                backend_variables.myrelay.turn_off_relay(0)
                if not backend_variables.state['process_stopped_imm']:
                    while(backend_variables.myrelay.read_input()[0] != 0):
                        backend_variables.myrelay.turn_off_relay(0)
                        await asyncio.sleep(0.05)
                        # stop imm
                        if backend_variables.state["process_stopped_imm"]:
                            print("Process stopped immidietly")
                            break
                        # pause
                        if backend_variables.state["process_paused"]:
                            print("Process paused")
                            # turn off infra
                            while backend_variables.state["process_paused"]:
                                await asyncio.sleep(0.05)

                backend_variables.websocket_payload['process_status'] = 3
                # [2] TURN ON INFRA for given percentage and delay
                if not backend_variables.state['process_stopped_imm']:
                    infra_start_time = time.time()
                    backend_variables.myinfra.turn_infra(True)
                    while time.time() - infra_start_time < element['path_def']['inf_delay']/1000.0:
                        await asyncio.sleep(0.05)
                        if backend_variables.state["process_paused"]:
                            print("Process paused")
                            # turn off infra
                            backend_variables.myinfra.turn_infra(False)
                            while backend_variables.state["process_paused"]:
                                await asyncio.sleep(0.05)
                                infra_start_time = time.time()

                        if backend_variables.state["process_stopped_imm"]:
                            print("Process stopped immidietly")
                            # turn off infra
                            backend_variables.myinfra.turn_infra(False)
                            break
                if backend_variables.state['process_stopped_imm']:
                    backend_variables.myinfra.turn_infra(False)
                    print("Breaking single process")
                    break

                backend_variables.websocket_payload['process_status'] = 4
                # [3] FEED FORWARD  
                if not backend_variables.state['process_stopped_imm']:
                    # start working path
                    start_pos = backend_variables.myservo.get_axis_pos()
                    backend_variables.myservo.start_path(1)
                    await asyncio.sleep(0.1)
                    while(int(backend_variables.myservo.poll_eop()) != 1):
                        await asyncio.sleep(0.05)
                        # stop imm
                        if backend_variables.state["process_stopped_imm"]:
                            print("Process stopped immidietly")
                            backend_variables.myservo.start_path(1000)
                            break
                        # pause
                        if backend_variables.state["process_paused"]:
                            print("Process paused")
                            # stop motor
                            backend_variables.myservo.start_path(1000)
                            await asyncio.sleep(2)
                            pause_pos = backend_variables.myservo.get_axis_pos()
                            print(pause_pos)
                            print(start_pos)
                            remaining_length = abs(element['path_length'] - abs(int(pause_pos)-int(start_pos))*backend_variables.state["path_param"])
                            print(remaining_length)
                            while backend_variables.state["process_paused"]:
                                await asyncio.sleep(0.05)
                            push_path_data(path_num=1,
                                        length=remaining_length)
                            backend_variables.myservo.start_path(1)
                            await asyncio.sleep(0.5)
                if backend_variables.state['process_stopped_imm']:
                    print("Breaking single process")
                    break       

                backend_variables.websocket_payload['process_status'] = 5
                # [4] CUT  
                if not backend_variables.state['process_stopped_imm']:
                    backend_variables.myrelay.turn_on_relay(0)
                    while(backend_variables.myrelay.read_input()[1] != 0):
                        backend_variables.myrelay.turn_on_relay(0)
                        await asyncio.sleep(0.1)
                        # stop imm
                        if backend_variables.state["process_stopped_imm"]:
                            print("Process stopped immidietly")
                            break
                        # pause
                        if backend_variables.state["process_paused"]:
                            print("Process paused")
                            while backend_variables.state["process_paused"]:
                                await asyncio.sleep(0.05)
                if backend_variables.state['process_stopped_imm']:
                    print("Breaking single process")
                    break     

                # [5] WAIT AFTER CUT
                start_tmp = time.time()
                if not backend_variables.state['process_stopped_imm']:
                    while((time.time() - start_tmp)*1000 < element['path_def']['cut_delay']):
                        await asyncio.sleep(0.1)
                        # stop imm
                        if backend_variables.state["process_stopped_imm"]:
                            print("Process stopped immidietly")
                            break
                        # pause
                        if backend_variables.state["process_paused"]:
                            print("Process paused")
                            while backend_variables.state["process_paused"]:
                                await asyncio.sleep(0.05)
                if backend_variables.state['process_stopped_imm']:
                    print("Breaking single process")
                    break

                backend_variables.websocket_payload['process_status'] = 6
                # [6] CUT UP
                if not backend_variables.state['process_stopped_imm']:
                    backend_variables.myrelay.turn_off_relay(0)
                    while(backend_variables.myrelay.read_input()[0] != 0):
                        backend_variables.myrelay.turn_off_relay(0)
                        await asyncio.sleep(0.1)
                        # stop imm
                        if backend_variables.state["process_stopped_imm"]:
                            print("Process stopped immidietly")
                            break
                        # pause
                        if backend_variables.state["process_paused"]:
                            print("Process paused")
                            while backend_variables.state["process_paused"]:
                                await asyncio.sleep(0.05)
                if backend_variables.state['process_stopped_imm']:
                    print("Breaking array process")
                    break

                backend_variables.websocket_payload['process_status'] = 7
                # [7] MILLING
                if not backend_variables.state['process_stopped_imm']:
                    pass
                if backend_variables.state['process_stopped_imm']:
                    print("Breaking array process")
                    break

                array_stop_time = time.time()
                elapsed_time += array_stop_time - array_start_time
                time_buffer.append(array_stop_time-array_start_time)

                # [8] WAIT FOR APPROVE 
                if not backend_variables.state['process_stopped_imm']:
                    if not backend_variables.state['autojump']:
                        backend_variables.websocket_payload['process_status'] = 8
                        # wait for approve from frontend
                        backend_variables.websocket_payload['manual_jump_trigger'] = True
                        while backend_variables.websocket_payload["manual_jump_trigger"]:
                            await asyncio.sleep(0.05)
                            if backend_variables.state['process_stopped_imm']:
                                print("Breaking single process")
                                break
                if backend_variables.state['process_stopped_imm']:
                    print("Breaking array process")
                    break
                quality = 'bad'
                # incerement current count states
                if not backend_variables.state['process_stopped_imm'] and (backend_variables.state['manual_jump_good'] or backend_variables.state['autojump']):
                    backend_variables.websocket_payload['process_status'] = 9
                    backend_variables.websocket_payload['session_length'] += element['path_length']
                    backend_variables.websocket_payload['process_length'] += element['path_length']
                    backend_variables.websocket_payload['process_good'] += 1
                    backend_variables.websocket_payload['session_good'] += 1
                    quality =  'good'
                else:
                    # decrease running var
                    backend_variables.websocket_payload['process_bad'] += 1
                    backend_variables.websocket_payload['session_bad'] += 1
                    i -= 1

                backend_variables.websocket_payload["eta"] = calc_eta(backend_variables.websocket_payload['process_good'],
                                            backend_variables.websocket_payload['process_bad'],
                                            array_total_length,
                                            array_avg_length,
                                            numpy.average(time_buffer),
                                            elapsed_time)
                
                file_comp.log(type='array_cut',
                            message={
                            'quality':quality,
                            'name':backend_variables.current_process_array['name'],
                            'id':backend_variables.current_process_array['id'],
                            'path_param':backend_variables.state['path_param'],
                            'path_data':element,
                            })


                # stop after process
                if backend_variables.state["process_stopped_after"]:
                    print("Stopping process because of STOP_AFTER")
                    file_comp.log(type='stop_after',
                              message=None)
                    break



    # ------------------------ CLEAR UP ON END PROCESS ------------------
    #TODO : if stopped during array process remember last backend_variables.state 
    if backend_variables.state['process_stopped_imm']:
        file_comp.log(type='stop_imm',
                              message=None)
    if backend_variables.state['mode'] and (backend_variables.state['process_stopped_after'] or backend_variables.state['process_stopped_imm']):
        # array mode save current backend_variables.state
        backend_variables.state['array_current_count'] = 1
        backend_variables.state['array_current_index'] = 1
        print('Array process done')


    print("Process done")
    backend_variables.websocket_payload['process_status'] = 0
    backend_variables.websocket_payload['eta'] = 0
    backend_variables.websocket_payload['process_length'] = 0
    backend_variables.websocket_payload['process_bad'] = 0
    backend_variables.websocket_payload['process_good'] = 0
    backend_variables.websocket_payload["process_running"] = False
    backend_variables.websocket_payload["process_paused"] = False
    backend_variables.state["process_stopped_imm"] = False
    backend_variables.state["process_stopped_after"] = False
    backend_variables.state['approve_manual_jump'] = False,
    backend_variables.state['manual_jump_good'] = False

    # TODO reset array vaiables as well
    return


# ------- SERVO PATH FUNCTIONS -------------
def push_path_def(path_num: int, spd_num: int, dly_num: int, auto_num: int, type_num: int, acc_num: int,
                     dec_num: int):
    # Logic to configure path definition
    backend_variables.path_definitions[path_num] = {
        "spd_num": spd_num,
        "dly_num": dly_num,
        "auto_num": auto_num,
        "type_num": type_num,
        "acc_num": acc_num,
        "dec_num": dec_num
    }
    backend_variables.myservo.config_path_def(path_num,
                            spd_num,
                            dly_num,
                            auto_num,
                            type_num,
                            acc_num,
                            dec_num)
    print("PUSH PATH DEF COMPLETE")

def push_path_data(path_num: int, length):
    # Logic to configure path data
    backend_variables.path_data[path_num] = {"length": length}
    backend_variables.myservo.config_path_data(path_num,
                             -length)
    print("PUSH PATH DATA COMPLETE")