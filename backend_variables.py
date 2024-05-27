import sys 
sys.path.append("./servo_control")
sys.path.append("./relay_control")
sys.path.append("./infra_control")

import servo_control as sc 
import relay_control as rc 
import infra_control as ic

def init():
    # Mock data storage
    global path_definitions
    path_definitions = {}
    global path_data
    path_data = {}
    global relay_status
    relay_status = {}
    global eop_status
    eop_status = False
    global glob_delay
    glob_delay = 2

    # peripherials 
    global myservo 
    myservo = sc.servo()
    global myrelay
    myrelay = rc.relay()
    global myinfra
    myinfra = ic.infra()

    # current array process
    global current_process_array 
    current_process_array = {
        'name': None,
        'user': None, 
        'created':None,
        'id': None,
        'elements':
        [
            {
                'number': 1,
                'count': None,
                'path_def':
                {
                    'spd': None, 
                    'acc': None, 
                    'dec': None,
                    'inf_percent': None, 
                    'inf_delay':None,
                    'cut_delay': None,
                    'milling': None
                },
                'path_length': None
            },
            {
                'number': 2,
                'count': None,
                'path_def':
                {
                    'spd': None, 
                    'acc': None, 
                    'dec': None,
                    'inf_percent': None, 
                    'inf_delay':None,
                    'cut_lenght': None, 
                    'cut_delay': None,
                    'milling': None
                },
                'path_length': None
            }
        ]
    }

    global current_process_status
    current_process_status = [
    "Waiting for start",
    "Infra heating",
    "Feed forward",
    "Cut down",
    "Cut up",
    "Milling",
    "Done",
    "Wait for approving"
    ]
    
    global websocket_payload
    websocket_payload = {
    "mat_begin":True,
    "mat_end":True,
    "mill":True,
    "infra":True,
    "door":True,
    "cut_up":True,
    "cut_down":False,
    "batch_limit_reached":False,
    "manual_jump_trigger":False,
    "process_status":"cut_down",
    "session_length":0,
    'process_length':0,
    "eta":0,
    "process_good":0,
    'process_bad':0,
    'session_good':0,
    'session_bad':0,

    'wait_nullcut_approve':False,

    'process_running':False,
    'process_paused':False,
    'process_stopped_after':False,
    'process_stopped_imm':False,
    'process_status':"IDLE",

    'errors': [
    ],

    "mode":False,
    "autojump":False,
    
    # single process state variables
    "single_current_count":1,
    "single_current_batch":1,
    "single_total_length":0,
    "single_remaining_length":0,
    "single_process_good":0,
    "single_process_bad":0,
    "single_total_remaining_time":0,
    "single_batch_remaining_time":0,
    "single_total_good":0,
    "single_total_bad":0,
    "single_uptime":0,
    "single_batch_remaining_length":0,
    "single_used_length_good":0,
    "single_used_length_bad":0,
    
    # array process state variables
    "array_current_number":1,
    "array_current_count":1,
    "array_process_remaining_length":0,
    "array_stack_remaining_length":0,
    "array_process_good":0,
    "array_porcess_bad":0,
    "array_total_good":0,
    "array_total_bad":0,
    "array_uptime":0,
    "array_process_remaining_time":0,
    "array_stack_remaining_time":0,
    "array_used_length_good":0,
    "array_used_length_bad":0,

    }
    
    global state
    # state
    state = {
        "logged_in" : False,
        "user_type" : "",
        "username": "",

        "path_param" : 409/10e6,

        "null_cut":False,

        "error":[],

        "process_running":False,
        
        "process_stopped_imm":False,
        "process_stopped_after":False,
        "process_paused":False,

        "manual_jump_good":False,    # bool for good/bad manual cut

        'single_infra_percentage':100,
        'single_infra_delay':3000,
        'single_count':100,
        'single_batch':20,
        'single_total_current':1,
        'single_batch_current':1,
        'single_cut_length':1000,
        'single_cut_delay':200,
        'single_speed':10,
        'single_acceleration':10,
        'single_deceleration':10,
        'single_milling_placeholder':100,

        "array_index_done":10,
        'array_index_max':100,
        'array_current_index':1,
        "array_current_count": 1,
        'array_current_length':100,
        'array_current_cutdelay':200,
        'array_current_infradelay':2000,
        'array_current_infrapercent':60,
        'array_current_speed':500,
        'array_current_acc':200,
        'array_current_dec':300,
        'array_processed_length':0,

        'array_spd_modifier' :0,
        'array_acc_modifier':0,
        'array_dec_modifier':0,
        'array_infpercent_modifier':0,
        'array_infdelay_modifier':0,

        'session_processed_length':0,

        # connections
        'infra_connection':False,
        'relay_connection':False,
        'servo_connection':False,
    }

    global parameters
    # parameters
    parameters = {
        'Speed':{
            1: 100,
            2: 200,
            3: 300,
            4: 400,
            5: 500,
            6: 600,
            7: 700,
            8: 800,
            9: 900,
            10: 1000,
            11: 1100,
            12: 1200,
            13: 1300,
            14: 1400,
            15: 1500,
            16: 1600
        },
        'Acceleration': {
            1: 100,
            2: 200,
            3: 300,
            4: 400,
            5: 500,
            6: 600,
            7: 700,
            8: 800,
            9: 900,
            10: 1000,
            11: 1100,
            12: 1200,
            13: 1300,
            14: 1400,
            15: 1500,
            16: 1600
        },
        'Deceleration': {
            1: 100,
            2: 200,
            3: 300,
            4: 400,
            5: 500,
            6: 600,
            7: 700,
            8: 800,
            9: 900,
            10: 1000,
            11: 1100,
            12: 1200,
            13: 1300,
            14: 1400,
            15: 1500,
            16: 1600
        }
    }
    global ws_notify
    ws_notify = False

    global TESTING
    TESTING = False
    
    global last_websocket_payload
    last_websocket_payload = {}