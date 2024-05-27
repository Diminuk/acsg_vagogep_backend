import requests, time

server_address = "169.254.188.91:8000"

def send_get_request(server_address, endpoint, params=None):
    try:
        response = requests.get(f"http://{server_address}/api/{endpoint}", params=params)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    while(True):
        response = send_get_request(server_address, "start_process")
        time.sleep(0.1)