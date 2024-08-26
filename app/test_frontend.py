import tkinter as tk
from tkinter import messagebox, simpledialog
import requests

# fehér: A
# kék : B

# sárga B

# Function to send GET requests
def send_get_request(server_address, endpoint, params=None):
    try:
        response = requests.get(f"http://{server_address}/api/{endpoint}", params=params)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Function to send POST requests
def send_post_request(server_address, endpoint, data=None):
    try:
        response = requests.post(f"http://{server_address}/api/{endpoint}", params=data)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Function to handle button click events
def button_click(server_address, endpoint):
    if endpoint == "stop_motor":
        response = send_get_request(server_address, "stop_motor")
    elif endpoint == "get_relay":
        response = send_get_request(server_address, "get_relay?relay_num=0")
    elif endpoint == "get_eop":
        response = send_get_request(server_address, "get_eop")
    elif endpoint == "zero_pos":
        response = send_get_request(server_address, "zero_pos")
    elif endpoint == "get_pos":
        response = send_get_request(server_address, "get_axis_pos")
    elif endpoint == "start_process":
        response = send_get_request(server_address, "start_process")
    elif endpoint == "config_relay_delay":
        delay = simpledialog.askinteger("Relay Delay", "Enter delay in seconds.")
        if delay is not None:
            response = send_post_request(server_address, "config_relay_delay", {"delay": delay})
    elif endpoint == "config_path_data":
        path_num = simpledialog.askinteger("Path Number", "Enter path number:")
        length = simpledialog.askinteger("Length", "Enter length:")
        if path_num is not None and length is not None:
            response = send_post_request(server_address, "config_path_data", {"path_num": path_num, "length": length})
    elif endpoint == "config_path_def":
        path_num = simpledialog.askinteger("Path Number", "Enter path number:")
        spd_num = simpledialog.askinteger("Speed Number", "Enter speed number:")
        dly_num = simpledialog.askinteger("Delay Number", "Enter delay number:")
        auto_num = simpledialog.askinteger("Auto Number", "Enter auto number:")
        type_num = simpledialog.askinteger("Type Number", "Enter type number:")
        acc_num = simpledialog.askinteger("Acceleration Number", "Enter acceleration number:")
        dec_num = simpledialog.askinteger("Deceleration Number", "Enter deceleration number:")
        if all(param is not None for param in [path_num, spd_num, dly_num, auto_num, type_num, acc_num, dec_num]):
            response = send_post_request(server_address, "config_path_def", {
                "path_num": path_num,
                "spd_num": spd_num,
                "dly_num": dly_num,
                "auto_num": auto_num,
                "type_num": type_num,
                "acc_num": acc_num,
                "dec_num": dec_num
            })
    elif endpoint == "start_path":
        response = send_get_request(server_address, "start_path?path_number=1")
    elif endpoint == "relay_on":
        response = send_get_request(server_address, "relay?relay_num=0&status=true")
    elif endpoint == "relay_off":
        response = send_get_request(server_address, "relay?relay_num=0&status=false")
    elif endpoint == "get_inputs":
        response = send_get_request(server_address, "get_inputs")
    elif endpoint == "config_path_param":
        path_param = simpledialog.askfloat("Path Param", "Enter path param:")
        if path_param > 0:
            response = send_post_request(server_address, "config_path_param", {
                "path_param" : path_param
            })
    # Add more endpoints here

    # Update response text widget
    response_text.delete(1.0, tk.END)
    response_text.insert(tk.END, str(response))

# Create main Tkinter window
root = tk.Tk()
root.title("API Tester")

# Create buttons for endpoints
buttons = [
    "stop_motor",
    "start_process",
    "get_relay",
    "get_eop",
    "config_relay_delay",
    "config_path_data",
    "config_path_def",
    "start_path",
    "relay_on",
    "relay_off",
    "get_inputs",
    "config_path_param",
    "get_pos",
    "zero_pos"
    # Add more endpoints here
]

server_address = "192.168.1.141:8000"  # Default server address

for button_text in buttons:
    tk.Button(root, text=button_text.replace("_", " ").title(),
              command=lambda btn=button_text: button_click(server_address, btn)).pack()

# Create text widget to display responses
response_text = tk.Text(root, height=10, width=50)
response_text.pack()

root.mainloop()
