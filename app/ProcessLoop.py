ProcessState = {

}

from ProcessLogic import cut_process
import file_component as file_comp
import asyncio
import numpy as np
import backend_variables

# side note: very primitive approach may need some improvements later
def calc_eta(
             total_length: float,
             timearray,
             lengtharray,
             boolarray):
    try:
        # Calculate the total length already cut that counts towards the goal
        completed_length = sum(length for length, is_good in zip(lengtharray, boolarray) if is_good)
        
        # Calculate the remaining length needed to reach the target
        remaining_length = total_length - completed_length
        
        # Calculate the average time per mm for good cuts
        good_cuts_time = sum(time for time, is_good in zip(timearray, boolarray) if is_good)
        good_cuts_length = sum(length for length, is_good in zip(lengtharray, boolarray) if is_good)
        bad_cuts_length = sum(length for length, is_good in zip(lengtharray, boolarray) if not is_good)
        
        # Avoid division by zero if no good cuts have been made
        if good_cuts_length == 0:
            return 0
        
        average_time_per_mm = good_cuts_time / good_cuts_length
        
        # Estimate the time needed to finish the remaining length
        estimated_time_to_finish = remaining_length * average_time_per_mm * (1+bad_cuts_length/good_cuts_length)
        
        # Total estimated time is the time already taken plus the estimated remaining time
        total_estimated_time =  estimated_time_to_finish 
        
        return total_estimated_time
    
    except Exception as e:
        # Handle any exceptions that may occur
        print(f"An error occurred: {e}")
        return 0


async def ProcessLoop():
    if not backend_variables.state['null_cut']:
        print("Missing nullcut")
        #return 
    if backend_variables.websocket_payload["process_running"]:
        print("Process already running")
        return
    
    backend_variables.websocket_payload["process_running"] = True
    
    # start conveyor
    backend_variables.websocket_payload["conveyor"] = True
    if not backend_variables.TESTING:
        backend_variables.myrelay.turn_off_relay(3)
        backend_variables.myrelay.turn_off_relay(2)
        backend_variables.myrelay.turn_on_relay(2)
        await asyncio.sleep(0.5)
        backend_variables.myrelay.turn_off_relay(2)
        # check if conveyor really started 
        if backend_variables.myrelay.read_input()[2] ==0 or backend_variables.myrelay.read_input()[3] != 0:
            backend_variables.websocket_payload["conveyor"] = False
            print("Problem starting conveyor")

    if backend_variables.websocket_payload['mode'] == False:
        print("*************SINGLE MODE***********")
        await asyncio.sleep(0.1)
        
        time_buffer = []
        bool_buffer = []
        length_buffer = []
        elapsed_time = -1
        single_process_for = backend_variables.state["single_count"] - backend_variables.websocket_payload['single_current_count'] + 1
        print(f"DEBUG: --single process for: {single_process_for}")

        backend_variables.websocket_payload["single_remaining_length"] = single_process_for * backend_variables.state['single_cut_length']
        
        backend_variables.websocket_payload['single_total_length'] = backend_variables.state['single_cut_length'] * backend_variables.state["single_count"]

        for i in range(single_process_for):
            if backend_variables.websocket_payload['process_stopped_imm']:
                print("break outer loop")
                break
            print(i)
            if not backend_variables.websocket_payload['process_stopped_imm']:
                elapsed_time = await cut_process(
                    spd_num=backend_variables.state['single_speed'],
                    acc_num=backend_variables.state['single_acceleration'],
                    dec_num=backend_variables.state['single_deceleration'],
                    length=backend_variables.state['single_cut_length'],
                    cut_delay=backend_variables.state['single_cut_delay'],
                    infra_percent=backend_variables.state['single_infra_percentage'],
                    infra_delay=backend_variables.state['single_infra_delay'],
                    infra_mod_percent=0,
                    speed_mod=0,
                    acc_mod=0,
                    dec_mod=0,
                    infra_mod_delay=0,
                )
                print("Cut process done")
                if elapsed_time:
                    time_buffer.append(elapsed_time)
                    length_buffer.append(backend_variables.state['single_cut_length'])
                    backend_variables.websocket_payload["single_cycle_time"] = np.sum(time_buffer) / len(time_buffer)
                    backend_variables.websocket_payload["total_work_time"] += elapsed_time
            if backend_variables.websocket_payload['process_stopped_imm']:
                print("Breaking single process")
                await file_comp.log(type='ERROR',
                              message="Stop-immediately")
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
                            await file_comp.log(type='ERROR',
                              message="Stop-immediately")
                            break
            if backend_variables.websocket_payload['process_stopped_imm']:
                print("Breaking single process")
                await file_comp.log(type='ERROR',
                              message="Stop-immediately")
                break

            
            quality = 'bad'
            # incerement current count states
            if not backend_variables.websocket_payload['process_stopped_imm'] and (backend_variables.state['manual_jump_good'] or backend_variables.websocket_payload['autojump']):
                backend_variables.websocket_payload["single_current_count"] = backend_variables.websocket_payload["single_current_count"]+1
                backend_variables.websocket_payload["single_current_batch"] = backend_variables.websocket_payload["single_current_batch"]+1
                backend_variables.websocket_payload["single_process_good_length"] = backend_variables.websocket_payload["single_process_good_length"] + backend_variables.state['single_cut_length']
                backend_variables.websocket_payload["total_good_length"] += backend_variables.state['single_cut_length']
                backend_variables.websocket_payload["total_length_used"] += backend_variables.state['single_cut_length']
                backend_variables.websocket_payload["single_process_good"] = backend_variables.websocket_payload["single_process_good"] + 1
                backend_variables.websocket_payload["single_remaining_length"] -= backend_variables.state['single_cut_length']
                backend_variables.websocket_payload['total_good_number'] += 1

                quality ='good'
            elif not (backend_variables.state['manual_jump_good'] or backend_variables.websocket_payload['autojump']):
                backend_variables.websocket_payload["single_process_bad_length"] = backend_variables.websocket_payload["single_process_bad_length"] + backend_variables.state['single_cut_length']
                backend_variables.websocket_payload["total_bad_length"] +=  backend_variables.state['single_cut_length']
                backend_variables.websocket_payload["total_length_used"] +=  backend_variables.state['single_cut_length']
                backend_variables.websocket_payload["single_proces_bad"] = backend_variables.websocket_payload["single_process_bad"] + 1
                backend_variables.websocket_payload['total_bad_number'] += 1
            if quality == 'bad':
                bool_buffer.append(False)
            elif quality == 'good':
                bool_buffer.append(True)
            else:
                print("Something went very very wrong..")
                bool_buffer.append(True)

            print("log")
            await file_comp.log(type='SINGLE',
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
                        if backend_variables.websocket_payload["process_stopped_imm"]:
                            print("Process stopped immidietly")
                            await file_comp.log(type='ERROR',
                              message="Stop-immediately")
                            # turn off infra
                            break
            
            
            if backend_variables.websocket_payload['process_stopped_imm']:
                await file_comp.log(type="ERROR",
                              message="Stop-immediately")
                print("Breaking single process")
                break

            if backend_variables.websocket_payload["process_stopped_after"]:
                    print("Stopping process because of STOP_AFTER")
                    await file_comp.log(type='ERROR',
                              message="Stop-after")
                    break
            
            # calc estimated time left
            backend_variables.websocket_payload["single_total_remaining_time"] = calc_eta(
                backend_variables.websocket_payload["single_total_length"],
                time_buffer,
                length_buffer,
                bool_buffer
            )
    # ------------------------------ ARRAY MODE -------------------------------------
    else:
        print("*************ARRAY MODE*************")
        time_buffer = []
        length_buffer = []
        bool_buffer = []
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
                #TODO take into account ignored and startfrom
                if item['number'] < backend_variables.websocket_payload['array_current_number']:
                    continue
                if int(item['number']) in  {int(key) for key in backend_variables.ignores.keys()}:
                    if backend_variables.ignores.get(str(int(item['number']))) == True:
                        print(f"Ignore element: {item['number']}")
                        continue
                if int(item['number']) in {int(key) for key in backend_variables.startfroms.keys()}:
                    if int(backend_variables.startfroms.get(str(int(item['number'])))) > 1:
                        array_total_count += int(int(item['count']) - int(backend_variables.startfroms.get(str(int(item['number'])))) +1)
                        array_total_length += (int(int(item['count']))+1-int(backend_variables.startfroms.get(str(int(item['number']))))) * float(item['length'])
                    else:
                        array_total_count += int(item['count'])
                        array_total_length += int(item['count']) * float(item['length'])
                else:
                    array_total_count += int(item['count'])
                    array_total_length += int(item['count']) * float(item['length'])
            if array_total_count > 0:
                array_avg_length = array_total_length / array_total_count

            backend_variables.websocket_payload["array_total_length"] = array_total_length
            backend_variables.websocket_payload["array_process_remaining_length"] = array_total_length

            print(f"Array total length: {array_total_length}")
            print(f"Array total count: {array_total_count}")

            num_elements = len(backend_variables.current_process_array["elements"])

            print(f"Elements in currently loaded array: {num_elements}")

            prev_broken_process_count = backend_variables.websocket_payload['array_current_count']
            first_after_continue = True

            for element in backend_variables.current_process_array["elements"]:
                print("Next element:")
                print(element)
                if element is None:
                    print("element is none")
                    break
                if element['number'] < backend_variables.websocket_payload['array_current_number'] :
                    #TODO take into account ignore and skip and also if the process start from stopped array process
                    print(f"Skipping: {element['number']}")
                    continue
                print(backend_variables.ignores)
                print(backend_variables.startfroms)
                if int(element['number']) in  {int(key) for key in backend_variables.ignores.keys()}:
                    if backend_variables.ignores.get(str(int(element['number']))) == True:
                        print(f"Ignore element: {element['number']}")
                        continue
                backend_variables.websocket_payload["array_current_number"] = element['number']

                # modify element properties by operator modifications
                speed = int(element['speed'])
                acc = int(element['acc'])
                dec = int(element['dec'])
                length = float(element['length'])
                infpercent = int(element["infPercent"])

                num_count = int(element['count'])
                print(f"Count in currently processed element: {num_count}")

                for i in range(num_count):
                    if backend_variables.websocket_payload['process_stopped_imm'] or backend_variables.websocket_payload['process_stopped_after']:
                        print("Break outer loop cause of stop")
                        break
                    # skip if restoring prev broken process
                    if first_after_continue and prev_broken_process_count > 1:
                        print("Ignoring previously done counts for this element")
                        if i == prev_broken_process_count-1:
                            first_after_continue = False
                        else:
                            continue
                    # skip if startfrom
                    if int(element['number']) in {int(key) for key in backend_variables.startfroms.keys()}:
                        if i+1 < int(backend_variables.startfroms.get(str(int(element['number'])))):
                            continue
                    backend_variables.websocket_payload["array_current_count"] = i+1
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
                                infra_delay=float(element['infDelay']),
                                infra_mod_percent=backend_variables.websocket_payload["array_infpercent_modifier"],
                                speed_mod=backend_variables.websocket_payload["array_spd_modifier"],
                                acc_mod=backend_variables.websocket_payload["array_acc_modifier"],
                                dec_mod=backend_variables.websocket_payload["array_dec_modifier"],
                                infra_mod_delay=backend_variables.websocket_payload["array_infdelay_modifier"]
                            )
                            if(elapsed_time):
                                time_buffer.append(elapsed_time)
                                length_buffer.append(length)
                                backend_variables.websocket_payload["total_work_time"] += elapsed_time
                                backend_variables.websocket_payload["array_cycle_time"] = np.sum(time_buffer) / len(time_buffer)
                        if backend_variables.websocket_payload['process_stopped_imm']:
                            await file_comp.log(type='ERROR',
                                        message="Stop-immediately")
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
                            await file_comp.log(type='ERROR',
                                        message="Stop-immediately")
                            print("Breaking array process")
                            break
                        quality = 'bad'
                        # incerement current count states
                        if not backend_variables.websocket_payload['process_stopped_imm'] and (backend_variables.state['manual_jump_good'] or backend_variables.websocket_payload['autojump']):
                            backend_variables.websocket_payload['array_used_length_good'] += float(element['length'])
                            backend_variables.websocket_payload['total_good_length'] += float(element['length'])
                            backend_variables.websocket_payload['array_process_good'] += 1
                            backend_variables.websocket_payload['total_good_number'] += 1
                            backend_variables.websocket_payload['array_process_remaining_length'] -= float(element['length'])
                            print("Good")
                            bool_buffer.append(True)
                            iteration_good = True
                            quality =  'good'
                        else:
                            # decrease running var
                            backend_variables.websocket_payload['array_used_length_bad'] += float(element['length'])
                            backend_variables.websocket_payload['total_bad_length'] += float(element['length'])
                            backend_variables.websocket_payload['total_bad_number'] += 1
                            backend_variables.websocket_payload['array_process_bad'] += 1
                            iteration_good = False
                            bool_buffer.append(False)
                            print("Bad")
                        if backend_variables.websocket_payload['process_stopped_imm']:
                            await file_comp.log(type='ERROR',
                                        message="Stop-immediately")
                            print("Breaking array process")
                            break
                        #backend_variables.websocket_payload["eta"] = calc_eta(backend_variables.websocket_payload['process_good'],
                        #                            backend_variables.websocket_payload['process_bad'],
                        #                            array_total_length,
                        #                            array_avg_length,
                        #                            np.average(time_buffer),
                        #                            elapsed_time)
                        
                        await file_comp.log(type='ARRAY',
                                    message={
                                    'quality':quality,
                                    'name':backend_variables.current_process_array['name'],
                                    'path_param':backend_variables.state['path_param'],
                                    'path_data':element,
                                    })
                        if backend_variables.websocket_payload['process_stopped_imm']:
                            await file_comp.log(type='ERROR',
                                        message="Stop-immediately")
                            print("Breaking array process")
                            break

                        # stop after process
                        if backend_variables.websocket_payload["process_stopped_after"]:
                            print("Stopping process because of STOP_AFTER")
                            file_comp.log(type='ERROR',
                                        message="Stop-immediately")
                            break

                        # calc remaining time
                        backend_variables.websocket_payload["array_process_remaining_time"] = calc_eta(
                            backend_variables.websocket_payload["array_total_length"],
                            time_buffer,
                            length_buffer,
                            bool_buffer
                        )
                
                if backend_variables.websocket_payload['process_stopped_imm']:
                    await file_comp.log(type='ERROR',
                                message="Stop-immediately")
                    print("Breaking array process")
                    break

                # stop after process
                if backend_variables.websocket_payload["process_stopped_after"]:
                    print("Stopping process because of STOP_AFTER")
                    file_comp.log(type='ERROR',
                                message="Stop-after")
                    break
        else:
            print("Badly formatted array - ignore it")

    """
        Cleaunp
    """

    # stop conveyor
    backend_variables.websocket_payload["conveyor"] = False
    if not backend_variables.TESTING:
        backend_variables.myrelay.turn_off_relay(3)
        backend_variables.myrelay.turn_off_relay(2)
        backend_variables.myrelay.turn_on_relay(3)
        await asyncio.sleep(0.5)
        backend_variables.myrelay.turn_off_relay(3)
        if backend_variables.myrelay.read_input()[2] !=0 or backend_variables.myrelay.read_input()[3] == 0:
            backend_variables.websocket_payload["conveyor"] = True
            print("Problem stopping conveyor")

    print("Done")
    if backend_variables.websocket_payload['mode'] and (backend_variables.websocket_payload['process_stopped_after'] or backend_variables.websocket_payload['process_stopped_imm']):
        # array mode save current state
        print(backend_variables.websocket_payload['array_current_number'])
        print(backend_variables.websocket_payload['array_current_count'])
        print('Exit from array process - progress saved')
    else:
        backend_variables.websocket_payload['array_current_count'] = 1
        backend_variables.websocket_payload['array_current_number'] = 1
        backend_variables.websocket_payload['array_used_length_bad'] = 0
        backend_variables.websocket_payload['array_used_length_good'] = 0
        backend_variables.websocket_payload['array_process_bad'] = 0
        backend_variables.websocket_payload['array_process_good'] = 0
        backend_variables.websocket_payload['array_process_remaining_time'] = 0
        backend_variables.websocket_payload['array_cycle_time'] = 0

        

    # stop everything for sure
    if not backend_variables.TESTING:
        backend_variables.myinfra.turn_infra(False)
        backend_variables.myservo.stop_path()
        backend_variables.myrelay.turn_off_relay(0)
    else:
        print("Stopped motor, knife, infra - Testing")

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
    backend_variables.websocket_payload["infra"] = False
    backend_variables.state['approve_manual_jump'] = False,
    backend_variables.state['manual_jump_good'] = False
    

    # TODO reset array vaiables as well
    return True
