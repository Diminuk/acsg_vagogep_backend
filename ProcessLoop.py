ProcessState = {

}

from ProcessLogic import cut_process
import file_component as file_comp
import asyncio
import numpy as np
import backend_variables

# side note: very primitive approach may need some improvements later
def calc_eta(good: int,
             bad: int,
             total_length: float,
             avg_length: float,
             avg_time: float,
             elapsed_time: float):
    try:
        if good == 0:
            return -1
        optimal = total_length/avg_length * avg_time
        if bad == 0:
            return optimal
        return optimal + optimal * (bad/good) - elapsed_time
    except:
        return np.nan


async def ProcessLoop():
    if not backend_variables.state['null_cut']:
        print("Missing nullcut")
        #return 
    if backend_variables.websocket_payload["process_running"]:
        print("Process already running")
        return
    
    backend_variables.websocket_payload["process_running"] = True
    
    if backend_variables.websocket_payload['mode'] == False:
        print("*************SINGLE MODE***********")
        await asyncio.sleep(0.1)
        
        time_buffer = []
        elapsed_time = -1
        single_process_for = backend_variables.state["single_count"] - backend_variables.websocket_payload['single_current_count'] + 1
        print(f"DEBUG: --single process for: {single_process_for}")

        backend_variables.websocket_payload["single_remaining_length"] = single_process_for * backend_variables.state['single_cut_length']
        backend_variables.websocket_payload["single_total_remaining_time"] = -1
        backend_variables.websocket_payload["single_batch_remaining_time"] = -1

        for i in range(single_process_for):
            print(i)
            if not backend_variables.websocket_payload['process_stopped_imm']:
                elapsed_time = await cut_process(
                    spd_num=backend_variables.state['single_speed'],
                    acc_num=backend_variables.state['single_acceleration'],
                    dec_num=backend_variables.state['single_deceleration'],
                    length=backend_variables.state['single_cut_length'],
                    cut_delay=backend_variables.state['single_cut_delay'],
                    infra_percent=backend_variables.state['single_infra_percentage'],
                    infra_delay=backend_variables.state['single_infra_delay']
                )
                print("Cut process done")
                time_buffer.append(elapsed_time)
            if backend_variables.websocket_payload['process_stopped_imm']:
                print("Breaking single process")
                await file_comp.log(type='stop_imm',
                              message=None)
                break
            # ************ wait for approve ******
            backend_variables.websocket_payload['process_status'] = 'wait_for_approve'
            

            print("Wait for approve")
            #print(backend_variables.state)
            print(backend_variables.websocket_payload["manual_jump_trigger"])
            if not backend_variables.websocket_payload['process_stopped_imm']:
                if not backend_variables.websocket_payload['autojump']:
                    # wait for approve from frontend
                    print("Trigger frontend notification")
                    backend_variables.websocket_payload['manual_jump_trigger'] = True
                    
                    while backend_variables.websocket_payload["manual_jump_trigger"]:
                        await asyncio.sleep(0.05)
                        if backend_variables.websocket_payload['process_stopped_imm']:
                            print("Breaking single process")
                            await file_comp.log(type='stop_imm',
                              message=None)
                            break
            if backend_variables.websocket_payload['process_stopped_imm']:
                print("Breaking single process")
                await file_comp.log(type='stop_imm',
                              message=None)
                break

            
            quality = 'bad'
            # incerement current count states
            if not backend_variables.websocket_payload['process_stopped_imm'] and (backend_variables.state['manual_jump_good'] or backend_variables.websocket_payload['autojump']):
                backend_variables.websocket_payload["single_current_count"] = backend_variables.websocket_payload["single_current_count"]+1
                backend_variables.websocket_payload["single_current_batch"] = backend_variables.websocket_payload["single_current_batch"]+1
                backend_variables.websocket_payload["single_total_good"] = backend_variables.websocket_payload["single_total_good"] +1
                backend_variables.websocket_payload["single_total_length"] = backend_variables.websocket_payload["single_total_length"] + backend_variables.state['single_cut_length']
                backend_variables.websocket_payload["single_uptime"] = backend_variables.websocket_payload["single_uptime"] + elapsed_time
                backend_variables.websocket_payload["single_used_length_good"] = backend_variables.websocket_payload["single_used_length_good"] + backend_variables.state['single_cut_length']
                backend_variables.websocket_payload["single_process_good"] = backend_variables.websocket_payload["single_process_good"] + 1

                quality ='good'
            elif not (backend_variables.state['manual_jump_good'] or backend_variables.websocket_payload['autojump']):
                backend_variables.websocket_payload["single_total_bad"] = backend_variables.websocket_payload["single_total_bad"] +1
                backend_variables.websocket_payload["single_used_length_bad"] = backend_variables.websocket_payload["single_used_length_bad"] + backend_variables.state['single_cut_length']
                backend_variables.websocket_payload["single_proces_bad"] = backend_variables.websocket_payload["single_process_bad"] + 1

            print("log")
            await file_comp.log(type='single_cut',
                            message={
                            'quality':quality,
                            'single_infra_percentage':backend_variables.state['single_infra_percentage'],
                            'single_infra_delay':backend_variables.state['single_infra_delay'],
                            'single_count':backend_variables.state['single_count'],
                            'single_batch':backend_variables.state['single_count'],
                            'single_total_current':backend_variables.websocket_payload["single_current_count"],
                            'single_batch_current':backend_variables.websocket_payload["single_current_batch"] ,
                            'single_cut_length':backend_variables.state['single_cut_length'],
                            'single_cut_delay':backend_variables.state['single_cut_delay'],
                            'single_speed':backend_variables.state['single_speed'],
                            'single_acceleration':backend_variables.state['single_acceleration'],
                            'single_deceleration':backend_variables.state['single_deceleration'],
                            'single_milling_placeholder':backend_variables.state['single_milling_placeholder'],
                            'path_param':backend_variables.state['path_param'],
                            })
            print("log done")

            # TODO calc estimated remaining time and remaining length
            
            
            backend_variables.state['manual_jump_good'] = False 
            

            if not backend_variables.websocket_payload['process_stopped_imm']:
                if backend_variables.websocket_payload["single_current_batch"] -1 == backend_variables.state['single_batch']:
                    # batch finished, wait for batch zero from frontend
                    backend_variables.websocket_payload['batch_limit_reached'] = True
                    while backend_variables.websocket_payload["single_current_batch"] -1 == backend_variables.state['single_batch']:
                        await asyncio.sleep(0.05)
                        if backend_variables.state["process_stopped_imm"]:
                            print("Process stopped immidietly")
                            await file_comp.log(type='stop_imm',
                              message=None)
                            # turn off infra
                            break

            # TODO --change--
            backend_variables.websocket_payload["eta"] = calc_eta(backend_variables.websocket_payload['process_good'],
                                                backend_variables.websocket_payload['process_bad'],
                                                backend_variables.state['single_count'] * backend_variables.state['single_cut_length'],
                                                backend_variables.state['single_cut_length'],
                                                np.average(time_buffer),
                                                elapsed_time)
            
            
            if backend_variables.websocket_payload['process_stopped_imm']:
                await file_comp.log(type='stop_imm',
                              message=None)
                print("Breaking single process")
                break

            if backend_variables.websocket_payload["process_stopped_after"]:
                    print("Stopping process because of STOP_AFTER")
                    await file_comp.log(type='stop_after',
                              message=None)
                    break
    # ------------------------------ ARRAY MODE -------------------------------------
    else:
        print("*************ARRAY MODE*************")
        time_buffer = []
        array_good = True
        print(backend_variables.current_process_array)
        if backend_variables.current_process_array is None or backend_variables.current_process_array["elements"] is None or backend_variables.current_process_array['name'] is None:
            print("Current process array is empty")
            array_good = False

        # ignore bad array entirely
        if array_good:
            print("Starting array process")
            array_total_count = 0
            array_total_length = 0
            for item in backend_variables.current_process_array['elements']:
                array_total_count += int(item['count'])
                array_total_length += int(item['count']) * float(item['length'])
            array_avg_length = array_total_length / array_total_count

            print(f"Array total length: {array_total_length}")
            print(f"Array total count: {array_total_count}")

            num_elements = len(backend_variables.current_process_array["elements"])

            print(f"Elements in currently loaded array: {num_elements}")

            for element in backend_variables.current_process_array["elements"]:
                print("Next element:")
                print(element)
                if element is None:
                    print("element is none")
                    break
                if element['number'] < backend_variables.state['array_current_index']:
                    # skip if already done
                    print(f"Skipping: {element['number']}")
                    continue
                backend_variables.state["array_current_index"] = element['number']

                # modify element properties by operator modifications
                speed = int(element['speed'])
                acc = int(element['acc'])
                dec = int(element['dec'])
                length = float(element['length'])
                infpercent = int(element["infPercent"])

                num_count = int(element['count'])
                print(f"Count in currently processed element: {num_count}")

                for i in range(num_count):
                    iteration_good = False
                    while not iteration_good:
                        if not backend_variables.websocket_payload['process_stopped_imm']:
                            elapsed_time = await cut_process(
                                spd_num=speed,
                                acc_num=acc,
                                dec_num=dec,
                                length=length,
                                cut_delay=float(element['cutDelay']),
                                infra_percent=infpercent,
                                infra_delay=float(element['infDelay'])
                            )
                        if backend_variables.websocket_payload['process_stopped_imm']:
                            await file_comp.log(type='stop_imm',
                                        message=None)
                            print("Breaking array process")
                            break

                        backend_variables.websocket_payload['process_status'] = 'wait_for_approve'

                        if not backend_variables.websocket_payload['process_stopped_imm']:
                                if not backend_variables.websocket_payload['autojump']:
                                    # wait for approve from frontend
                                    print("Trigger frontend notification")
                                    backend_variables.websocket_payload['manual_jump_trigger'] = True
                                    while backend_variables.websocket_payload["manual_jump_trigger"]:
                                        await asyncio.sleep(0.05)
                                        if backend_variables.websocket_payload['process_stopped_imm']:
                                            print("Breaking single process")
                                            break
                        if backend_variables.websocket_payload['process_stopped_imm']:
                            await file_comp.log(type='stop_imm',
                                        message=None)
                            print("Breaking array process")
                            break
                        quality = 'bad'
                        # incerement current count states
                        if not backend_variables.websocket_payload['process_stopped_imm'] and (backend_variables.state['manual_jump_good'] or backend_variables.websocket_payload['autojump']):
                            backend_variables.websocket_payload['session_length'] += float(element['length'])
                            backend_variables.websocket_payload['process_length'] += float(element['length'])
                            backend_variables.websocket_payload['process_good'] += 1
                            backend_variables.websocket_payload['session_good'] += 1
                            print("Good")
                            iteration_good = True
                            quality =  'good'
                        else:
                            # decrease running var
                            backend_variables.websocket_payload['process_bad'] += 1
                            backend_variables.websocket_payload['session_bad'] += 1
                            iteration_good = False
                            print("Bad")
                        if backend_variables.websocket_payload['process_stopped_imm']:
                            await file_comp.log(type='stop_imm',
                                        message=None)
                            print("Breaking array process")
                            break
                        #backend_variables.websocket_payload["eta"] = calc_eta(backend_variables.websocket_payload['process_good'],
                        #                            backend_variables.websocket_payload['process_bad'],
                        #                            array_total_length,
                        #                            array_avg_length,
                        #                            np.average(time_buffer),
                        #                            elapsed_time)
                        
                        await file_comp.log(type='array_cut',
                                    message={
                                    'quality':quality,
                                    'name':backend_variables.current_process_array['name'],
                                    'id':backend_variables.current_process_array['id'],
                                    'path_param':backend_variables.state['path_param'],
                                    'path_data':element,
                                    })
                        if backend_variables.websocket_payload['process_stopped_imm']:
                            await file_comp.log(type='stop_imm',
                                        message=None)
                            print("Breaking array process")
                            break

                        # stop after process
                        if backend_variables.websocket_payload["process_stopped_after"]:
                            print("Stopping process because of STOP_AFTER")
                            file_comp.log(type='stop_after',
                                        message=None)
                            break
                
                if backend_variables.websocket_payload['process_stopped_imm']:
                    await file_comp.log(type='stop_imm',
                                message=None)
                    print("Breaking array process")
                    break

                # stop after process
                if backend_variables.websocket_payload["process_stopped_after"]:
                    print("Stopping process because of STOP_AFTER")
                    file_comp.log(type='stop_after',
                                message=None)
                    break

    """
        Cleaunp
    """
    print("Done")
    if backend_variables.websocket_payload['mode'] and (backend_variables.websocket_payload['process_stopped_after'] or backend_variables.websocket_payload['process_stopped_imm']):
        # array mode save current state
        backend_variables.state['array_current_count'] = 1
        backend_variables.state['array_current_index'] = 1
        print('Array process done')
        

    # stop everything for sure
    backend_variables.myinfra.turn_infra(False)
    backend_variables.myservo.stop_path()
    backend_variables.myrelay.turn_off_relay(0)

    print("Process done")
    backend_variables.websocket_payload['process_status'] = "IDLE"
    backend_variables.websocket_payload['eta'] = 0
    backend_variables.websocket_payload['process_length'] = 0
    backend_variables.websocket_payload['process_bad'] = 0
    backend_variables.websocket_payload['process_good'] = 0
    backend_variables.websocket_payload["process_running"] = False
    backend_variables.websocket_payload["process_paused"] = False
    backend_variables.websocket_payload["process_stopped_imm"] = False
    backend_variables.websocket_payload["process_stopped_after"] = False
    backend_variables.state['approve_manual_jump'] = False,
    backend_variables.state['manual_jump_good'] = False
    

    # TODO reset array vaiables as well
    return True
