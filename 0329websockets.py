'''
Created on 2021年3月25日

@author: style
'''
#!/usr/bin/env python

# WS server example that synchronizes state across clients

import asyncio
import json
import logging
import websockets
import numpy as np

logging.basicConfig()

STATE = {"value": 0}

USERS = set()
boardSize = 19
Board = np.zeros((boardSize, boardSize), dtype="uint8")

#返回随机点位信息字符串不重复
def get_point():
    put = list(np.random.randint(19,size=2))
    while Board[put[1]][put[0]] != 0:
        put = list(np.random.randint(19,size=2))
    print(put)
    res = ""
    for i in range(2):
        if put[i]<10:res += "0"+str(put[i])
        else:res += str(put[i])
    return res

def tran_point(a):
    print("你发送的点位是：",a)
    x = int(a[:2])
    y = int(a[2:])

    if x>18 or y>18:
        print("error：点位超过18")
        return 0
    if Board[x][y] != 0:
        print("error:该位置已有棋子")
    else:Board[x][y] = 1


def state_event():
    return json.dumps({"type": "state", **STATE})


def users_event():
    return json.dumps({"type": "users", "count": len(USERS)})


async def notify_state():
    if USERS:  # asyncio.wait doesn't accept an empty list
        message = state_event()
        await asyncio.wait([user.send(message) for user in USERS])


async def notify_users():
    if USERS:  # asyncio.wait doesn't accept an empty list
        message = users_event()
        await asyncio.wait([user.send(message) for user in USERS])


async def register(websocket):
    USERS.add(websocket)
    await notify_users()


async def unregister(websocket):
    USERS.remove(websocket)
    await notify_users()

async def counter(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        await websocket.send(state_event())
        async for message in websocket:
            data = json.loads(message)
            #html通过minus命令获取棋手下棋位
            if data["action"] == "minus":
                # STATE["value"] = get_point()
                STATE["value"] = "[B\[{}]]".format(get_point())
                await notify_state()
            #html通过plus传给python点位位置,判断传入四个字符，就将字符转换为数字
            elif len(data["action"]) == 4:
                tran_point(data["action"])
                await notify_state()
            else:
                logging.error("unsupported event: {}", data)
    finally:
        await unregister(websocket)

start_server = websockets.serve(counter, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()