from fastapi import APIRouter
import asyncio
import time

import backend_variables

router = APIRouter()

@router.post("/api/update/single")
def update_single(data: dict):
    print(data)
    if 'Single_Infra_Percentage' in data:
        backend_variables.state["single_infra_percentage"] = int(data['Single_Infra_Percentage'])

    if 'Single_Infra_Delay' in data:
        backend_variables.state["single_infra_delay"] = int(data['Single_Infra_Delay'])

    if 'Single_Count' in data:
        backend_variables.state["single_count"] = int(data['Single_Count'])

    if 'Single_Batch' in data:
        backend_variables.state["single_batch"] = int(data['Single_Batch'])

    if 'Single_Cut_Length' in data:
        backend_variables.state["single_cut_length"] = int(data['Single_Cut_Length'])

    if 'Single_Cut_Delay' in data:
        backend_variables.state["single_cut_delay"] = int(data['Single_Cut_Delay'])

    if 'Single_Speed' in data:
        backend_variables.state["single_speed"] = int(data['Single_Speed'])

    if 'Single_Acceleration' in data:
        backend_variables.state["single_acceleration"] = int(data['Single_Acceleration'])

    if 'Single_Deceleration' in data:
        backend_variables.state["single_deceleration"] = int(data['Single_Deceleration'])

    if 'Single_Milling_Placeholder' in data:
        backend_variables.state["single_milling_placeholder"] = int(data['Single_Milling_Placeholder'])

    if 'Single_Total_Current' in data:
        #backend_variables.state["single_total_current"] = int(data['Single_Total_Current'])
        backend_variables.websocket_payload["single_current_count"] = int(data['Single_Total_Current'])

    if 'Single_Batch_Current' in data:
        backend_variables.state["single_batch_current"] = int(data['Single_Batch_Current'])
        backend_variables.websocket_payload["single_current_batch"] = int(data['Single_Batch_Current'])

    return {"message": "done"}