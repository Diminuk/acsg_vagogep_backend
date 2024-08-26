import sys 
sys.path.append("./servo_control")
sys.path.append("./relay_control")
sys.path.append("./infra_control")

from servo_control import servo_control as sc 
from relay_control import relay_control as rc 
from infra_control import infra_control as ic


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
    "mat_begin":False,
    "mat_end":False,
    "mill":False,
    "infra":False,
    "conveyor":False,
    "door":False,
    "cut_up":True,
    "cut_down":False,
    "batch_limit_reached":False,
    "manual_jump_trigger":False,
    "process_status":"IDLE",


    "eta":0,

    "session_length":0,
    'session_good':0,
    'session_bad':0,
    'session_good_length':0,
    'session_bad_length':0,


    'wait_nullcut_approve':False,

    'process_running':False,
    'process_paused':False,
    'process_stopped_after':False,
    'process_stopped_imm':False,
    'process_status':"IDLE",
    'null_cut': False,

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
    "single_process_good_length":0,
    "single_process_bad_length":0,
    "single_total_remaining_time":0,
    "single_batch_remaining_time":0,
    "single_batch_remaining_length":0,
    "single_cycle_time":0,
    
    # array process state variables
    "array_current_number":1,
    "array_current_count":1,
    "array_process_remaining_length":0,
    "array_process_good":0,
    "array_process_bad":0,
    "array_total_good":0,
    "array_total_bad":0,
    "array_uptime":0,
    "array_process_remaining_time":0,
    "array_stack_remaining_time":0,
    "array_used_length_good":0,
    "array_used_length_bad":0,
    "array_total_length":0,
    "array_cycle_time":0,

    # session variables
    "total_length_used":0,
    "total_good_number":0,
    "total_bad_number":0,
    "total_good_length":0,
    "total_bad_length":0,
    "total_up_time":0,
    "total_work_time":0,

    'array_spd_modifier' :0,
    'array_acc_modifier':0,
    'array_dec_modifier':0,
    'array_infpercent_modifier':0,
    'array_infdelay_modifier':0,

    

    }

    global ignores
    ignores = {}

    global startfroms
    startfroms = {}
    
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
            1: 20,
            2: 50,
            3: 100,
            4: 200,
            5: 300,
            6: 500,
            7: 600,
            8: 800,
            9: 1000,
            10: 1300,
            11: 1500,
            12: 1800,
            13: 2000,
            14: 2300,
            15: 2500,
            16: 3000
        },
        'Acceleration': {
            1: 200,
            2: 300,
            3: 500,
            4: 600,
            5: 800,
            6: 900,
            7: 1000,
            8: 1200,
            9: 1500,
            10: 2000,
            11: 2500,
            12: 3000,
            13: 5000,
            14: 8000,
            15: 50,
            16: 30
        },
        'Deceleration': {
            1: 200,
            2: 300,
            3: 500,
            4: 600,
            5: 800,
            6: 900,
            7: 1000,
            8: 1200,
            9: 1500,
            10: 2000,
            11: 2500,
            12: 3000,
            13: 5000,
            14: 8000,
            15: 50,
            16: 30
        }
    }
    global ws_notify
    ws_notify = False

    global test_variables
    test_variables = {
        "materialsensor": False,
        "emergency_stop":False
    }


    # !!!!!!!!!! important variable !!!!!!!!!!!
    global TESTING
    TESTING = False
    
    global last_websocket_payload
    last_websocket_payload = {}


