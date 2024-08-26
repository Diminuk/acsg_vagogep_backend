import asyncio
import time
import numpy as np

import backend_variables




# ------- SERVO PATH FUNCTIONS -------------
def push_path_def(path_num: int, spd_num: int, dly_num: int, auto_num: int, type_num: int, acc_num: int,
                     dec_num: int, spd_mod : int, acc_mod: int, dec_mod: int):
    print("Path def writing parameters:")
    print(f"Path num: {path_num} | Speed num: {spd_num} | Dly num: {dly_num} | Auto num: {auto_num} | Type num: {type_num} | Acc num: {acc_num} | Dec num: {dec_num}")
    print(f"Modifiers: Spd: {spd_mod} | Acc: {acc_mod} | Dec: {dec_mod}")
    # Logic to configure path definition
    backend_variables.path_definitions[path_num] = {
        "spd_num": spd_num,
        "dly_num": dly_num,
        "auto_num": auto_num,
        "type_num": type_num,
        "acc_num": acc_num,
        "dec_num": dec_num
    }
    modified_spd = spd_num + spd_mod 
    if modified_spd >= 16: modified_spd = 16
    if modified_spd <= 1: modified_spd = 1

    modified_acc = acc_num + acc_mod
    if modified_acc >= 16: modified_acc = 16
    if modified_acc <= 1: modified_acc = 1

    modified_dec = dec_num + dec_mod
    if modified_dec >= 16: modified_dec = 16
    if modified_dec <= 1: modified_dec = 1

    if not backend_variables.TESTING:
        backend_variables.myservo.config_path_def(path_num,
                                modified_spd,
                                dly_num,
                                auto_num,
                                type_num,
                                modified_acc,
                                modified_dec)
    print(f"Modified spd: {modified_spd} | Modified acc: {modified_acc} | Modified dec: {modified_dec}")
    print("PUSH PATH DEF COMPLETE")

def push_path_data(path_num: int, length):
    # Logic to configure path data
    backend_variables.path_data[path_num] = {"length": length}
    if not backend_variables.TESTING:
        backend_variables.myservo.config_path_data(path_num,
                                -length)
    print("PUSH PATH DATA COMPLETE")

time_names_array = [
    "config_infra_percentage",
    "knife_up",
    "config_path_data",
    "config_path_def",
    "feedfwd",
    "cut_down"
]

async def cut_process(spd_num,
                acc_num,
                dec_num,
                length,
                cut_delay,
                infra_percent,
                infra_delay,
                infra_mod_percent,
                speed_mod,
                acc_mod,
                dec_mod,
                infra_mod_delay
                ):

    time_array = np.array([])
    print("Starting cut process")
    time_array = np.append(time_array, time.time())

    print("Turn infra OFF")
    infra_off_start_time = time.time()
    await asyncio.sleep(0.1)
    if not backend_variables.TESTING:
        backend_variables.myinfra.turn_infra(False)
    print(f"Infra off time: {time.time() - infra_off_start_time}")

    if not backend_variables.TESTING:
        print("Set infra percentage")
        if not backend_variables.TESTING:
            modified_infra_percent = infra_percent + infra_mod_percent
            if modified_infra_percent >= 95 : modified_infra_percent = 95
            if modified_infra_percent <= 1 : modified_infra_percent = 1
            backend_variables.myinfra.config_percentage(modified_infra_percent)
        await asyncio.sleep(0.2)
        time_array = np.append(time_array, time.time())
        print(f"Infra: {infra_percent}")

    # pause
    #if backend_variables.websocket_payload["process_paused"]:
    #    print("Process paused")
    #    backend_variables.websocket_payload['process_status'] = "paused_cut"
    #    while backend_variables.websocket_payload["process_paused"]:
    #        await asyncio.sleep(0.05)
    #        if backend_variables.websocket_payload["process_stopped_imm"]:
    #            print("Process stopped immidietly")
    #            return None
    #    backend_variables.websocket_payload['process_status'] = "cut"
#
    #if backend_variables.websocket_payload["process_stopped_imm"]:
    #    print("Process stopped immidietly")
    #    return None

    # knife up
    backend_variables.websocket_payload['process_status'] = "knifeup_first"
    if not backend_variables.TESTING:
        backend_variables.myrelay.turn_off_relay(0)
    else:
        print("knife up first")
        await asyncio.sleep(0.5)
    if not backend_variables.websocket_payload['process_stopped_imm']:
        if not backend_variables.TESTING:
            while(backend_variables.myrelay.read_input()[-1] != 0):
                print(backend_variables.myrelay.read_input())
                backend_variables.myrelay.turn_off_relay(0)
                await asyncio.sleep(0.1)
                print("debug 1")
                # stop imm
                if backend_variables.websocket_payload["process_stopped_imm"]:
                    print("Process stopped immidietly")
                    return 0
                # pause
                if backend_variables.websocket_payload["process_paused"]:
                    print("Process paused")
                    backend_variables.websocket_payload['process_status'] = "paused_knifeup_first"
                    # turn off infra
                    while backend_variables.websocket_payload["process_paused"]:
                        await asyncio.sleep(0.1)
            await asyncio.sleep(0.1)
        else:
            await asyncio.sleep(2)
    time_array = np.append(time_array, time.time())

    # config path data
    print("Writing path definition")
    if not backend_variables.TESTING:
        push_path_def(path_num=1,
                            spd_num=spd_num,
                            dly_num=0,
                            auto_num=0,
                            type_num=2,
                            acc_num=acc_num,
                            dec_num=dec_num,
                            spd_mod=speed_mod,
                            acc_mod=acc_mod,
                            dec_mod=dec_mod)
    else:
        print("Push path def - testing")
    await asyncio.sleep(0.1)
    time_array = np.append(time_array, time.time())
    print("Writing path data")
    if not backend_variables.TESTING:
        push_path_data(path_num=1,
                    length=length)
    else:
        print("Write path data - testing")
    await asyncio.sleep(0.1)
    time_array = np.append(time_array, time.time())


    if backend_variables.websocket_payload["process_stopped_imm"]:
        print("Process stopped immidietly")
        return 0

    # infra
    backend_variables.websocket_payload['process_status'] = "infra"
    if not backend_variables.websocket_payload['process_stopped_imm']:
        # start infra
        print("Infra ON")
        if not backend_variables.TESTING:
            await asyncio.sleep(0.1)
            backend_variables.myinfra.turn_infra(True)
            backend_variables.websocket_payload["infra"] = True
        else:
            await asyncio.sleep(0.1)
            print("Turn infra on - testing")

    # pause
    if backend_variables.websocket_payload["process_paused"]:
        print("Process paused")
        backend_variables.websocket_payload['process_status'] = "paused_infra"
        while backend_variables.websocket_payload["process_paused"]:
            await asyncio.sleep(0.05)
            if backend_variables.websocket_payload["process_stopped_imm"]:
                print("Process stopped immidietly")
                return 0
        backend_variables.websocket_payload['process_status'] = "infra"

    if backend_variables.websocket_payload["process_stopped_imm"]:
        print("Process stopped immidietly")
        return 0
            
        
    if backend_variables.websocket_payload['process_stopped_imm']:
        print("Process stopped")
        if not backend_variables.TESTING:
            print("Turn infra off")
            await asyncio.sleep(0.1)
            backend_variables.myinfra.turn_infra(False)
            backend_variables.websocket_payload["infra"] = False
        else:
            print("Infra off - testing")
            backend_variables.websocket_payload["infra"] = False
        return 0

    # feed fwd
    backend_variables.websocket_payload['process_status'] = "feedfwd"
    if not backend_variables.websocket_payload['process_stopped_imm']:
        # start working path
        if not backend_variables.TESTING:
            start_pos = backend_variables.myservo.get_axis_pos()
            backend_variables.myservo.start_path(1)
        else:
            print("Wait for EOP - testing")
            await asyncio.sleep(0.1)
        await asyncio.sleep(0.1)
        if not backend_variables.TESTING:
            while(int(backend_variables.myservo.poll_eop()) != 1):
                # check if material end reached

                if (backend_variables.myrelay.read_input()[0] == 0) or backend_variables.test_variables['materialsensor']:
                    print("Material end reached - break process")
                    if not backend_variables.TESTING:
                        backend_variables.myservo.stop_path()
                        backend_variables.myinfra.turn_infra(False)
                        backend_variables.myrelay.turn_off_relay(2)
                        backend_variables.myrelay.turn_off_relay(3)
                        backend_variables.myrelay.turn_on_relay(3)
                        backend_variables.myrelay.turn_off_relay(3)
                    backend_variables.websocket_payload["process_stopped_imm"] = True



                await asyncio.sleep(0.05)
                # stop imm
                if backend_variables.websocket_payload["process_stopped_imm"]:
                    print("Process stopped immidietly")
                    if not backend_variables.TESTING:
                        backend_variables.myservo.start_path(1000)
                    return 0
                # pause
                if backend_variables.websocket_payload["process_paused"]:
                    print("Process paused")
                    # infra off
                    await asyncio.sleep(0.1)
                    backend_variables.myinfra.turn_infra(False)
                    backend_variables.websocket_payload['process_status'] = "paused_feedfwd"
                    # stop motor
                    if not backend_variables.TESTING:
                        backend_variables.myservo.start_path(1000)
                    await asyncio.sleep(0.5)
                    if not backend_variables.TESTING:
                        pause_pos = backend_variables.myservo.get_axis_pos()
                        print(pause_pos)
                        print(start_pos)
                        remaining_length = abs(length - abs(int(pause_pos)-int(start_pos))*backend_variables.state["path_param"])
                        print(remaining_length)
                    while backend_variables.websocket_payload["process_paused"]:
                        await asyncio.sleep(0.05)
                    if not backend_variables.TESTING:
                        # infra ON
                        await asyncio.sleep(0.1)
                        backend_variables.myinfra.turn_infra(True)
                        push_path_data(path_num=1,
                                        length=remaining_length)
                        backend_variables.myservo.start_path(1)
                        backend_variables.websocket_payload['process_status'] = "feedfwd"
                    await asyncio.sleep(0.3)
        else:
            test_time_var = time.time()
            while(time.time() - test_time_var < 5):
                if (backend_variables.test_variables['materialsensor'] == False):
                    print("Material end reached - break process")
                    backend_variables.websocket_payload["process_stopped_imm"] = True
                await asyncio.sleep(0.05)
   
            
                
    if backend_variables.websocket_payload['process_stopped_imm']:
        print("Process stopped")
        # infra OFF
        await asyncio.sleep(0.1)
        if not backend_variables.TESTING:
            backend_variables.myinfra.turn_infra(False)
            backend_variables.websocket_payload["infra"] = False
        else:
            print("Infra turned off - testing")
        return 0
    # feedfwd timestamp
    time_array = np.append(time_array, time.time())
    # infra OFF
    await asyncio.sleep(0.1)
    if not backend_variables.TESTING:
        backend_variables.myinfra.turn_infra(False)
    else:
        print("Infra turned off before cut - testing")
    backend_variables.websocket_payload['process_status'] = "cut"

    if not backend_variables.websocket_payload['process_stopped_imm']:
        if not backend_variables.TESTING:
            backend_variables.myrelay.turn_on_relay(0)
            while(backend_variables.myrelay.read_input()[-2] != 0):
                backend_variables.myrelay.turn_on_relay(0)
                await asyncio.sleep(0.1)
                # stop imm
                if backend_variables.websocket_payload["process_stopped_imm"]:
                    print("Process stopped immidietly")
                    return 0
                # pause
                if backend_variables.websocket_payload["process_paused"]:
                    print("Process paused")
                    backend_variables.websocket_payload['process_status'] = "paused_cut"
                    while backend_variables.websocket_payload["process_paused"]:
                        await asyncio.sleep(0.05)
                    backend_variables.websocket_payload['process_status'] = "cut"
    if backend_variables.websocket_payload['process_stopped_imm']:
        print("Breaking single process")
        return 0
    
    # cut down timestamp
    time_array = np.append(time_array, time.time())
    
    backend_variables.websocket_payload['process_status'] = "wait_after_cut"

    start_tmp = time.time()
    if not backend_variables.websocket_payload['process_stopped_imm']:
        while((time.time() - start_tmp)*1000 < cut_delay):
            await asyncio.sleep(0.1)
            # stop imm
            if backend_variables.websocket_payload["process_stopped_imm"]:
                print("Process stopped immidietly")
                
                return 0
            # pause
            if backend_variables.websocket_payload["process_paused"]:
                print("Process paused")
                #
                backend_variables.websocket_payload['process_status'] = "paused_wait_after_cut"
                while backend_variables.websocket_payload["process_paused"]:
                    await asyncio.sleep(0.05)
                backend_variables.websocket_payload['process_status'] = "wait_after_cut"
                # infra ON
                
    if backend_variables.websocket_payload['process_stopped_imm']:
        print("Breaking single process")  
        return 0
    

    backend_variables.websocket_payload['process_status'] = "knife_up_second"
    # cut up
    if not backend_variables.websocket_payload['process_stopped_imm']:
        if not backend_variables.TESTING:
            backend_variables.myrelay.turn_off_relay(0)
            while(backend_variables.myrelay.read_input()[-1] != 0):
                backend_variables.myrelay.turn_off_relay(0)
                await asyncio.sleep(0.1)
                # stop imm
                if backend_variables.websocket_payload["process_stopped_imm"]:
                    print("Process stopped immidietly")
                    # infra OFF
                    
                    return 0
                # pause
                if backend_variables.websocket_payload["process_paused"]:
                    print("Process paused")
                    # infra OFF
                    
                    backend_variables.websocket_payload['process_status'] = "paused_knife_up_second"
                    while backend_variables.websocket_payload["process_paused"]:
                        await asyncio.sleep(0.05)
                    backend_variables.websocket_payload['process_status'] = "knife_up_second"
                    
    if backend_variables.websocket_payload['process_stopped_imm']:
        print("Process stopped")
        # infra OFF
        
        return 0

    time_array = np.append(time_array, time.time())

    for i in range(len(time_names_array)):
        print(f"{time_names_array[i]} : {np.diff(time_array)[i]}")
    
    return time.time() - time_array[0]