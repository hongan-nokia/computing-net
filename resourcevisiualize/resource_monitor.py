# -*- coding: utf-8 -*-
"""
@Time : 
@Author: Honggang Yuan
@Email: hn_yuanhg@163.com
Description:
    
"""
from fastapi import FastAPI
import psutil

app = FastAPI()


@app.get("/cpu")
async def read_cpu():
    cpu_percent = psutil.cpu_percent(interval=1)
    return {"total": cpu_percent}


@app.get("/memory")
async def read_memory():
    memory = psutil.virtual_memory()
    return {
        "percent": memory.percent
    }


@app.get("/disk")
async def read_disk():
    disk_usage = psutil.disk_io_counters()
    return {
        "PhysicalDrive0": [
            {"disk_name": "PhysicalDrive0",
             "read_count": disk_usage.read_count,
             "write_count": disk_usage.write_count,
             "read_bytes": disk_usage.read_bytes,
             "write_bytes": disk_usage.write_bytes
             }
        ]
    }


@app.get("/net")
async def read_net():
    net_usage = psutil.net_io_counters(pernic=True)
    net_info_list = net_usage.values()
    tx_sum = 0
    rx_sum = 0
    for net_info in net_info_list:
        tx_sum += net_info.bytes_sent
        rx_sum += net_info.bytes_recv
    tx = tx_sum / len(net_info_list)
    rx = rx_sum / len(net_info_list)
    return {
        "Ethernet": [
            {
                "interface_name": "Ethernet",
                "rx": rx,
                "tx": tx,
            }
        ]
    }


@app.get("/synthetic")
async def read_performance_info():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk_usage = psutil.disk_io_counters()
    net_usage = psutil.net_io_counters(pernic=True)
    net_info_list = net_usage.values()
    tx_sum = 0
    rx_sum = 0
    for net_info in net_info_list:
        tx_sum += net_info.bytes_sent
        rx_sum += net_info.bytes_recv
    tx = tx_sum / len(net_info_list)
    rx = rx_sum / len(net_info_list)

    synthetic_info = {
        "cpu": cpu_percent,
        "mem": memory.percent,
        "disk": [disk_usage.read_bytes, disk_usage.write_bytes],
        "net": [tx, rx]
    }
    return synthetic_info


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
