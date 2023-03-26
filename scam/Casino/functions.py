import asyncio
import json
import requests

async def worker_sharee(profit):
    if profit == None:
        return float(0.80)
    else:
        return float(0.70)

async def pays(p2p_secret_key, comment):
    all_head = {"Authorization": f"Bearer {p2p_secret_key}", "Accept": "application/json"}
    req = requests.get(f'https://api.qiwi.com/partner/bill/v1/bills/{comment}', headers=all_head).json()
    try:
        if req['status']['value'] == 'PAID':
            return True
        else:
            return False
    except:
        return False