"""
RUGood? 
"""
# pyright: reportMissingImports=false
import gc
from esp8266 import *
from lcd import LCD
from utils import get_uuid

from websockets import client
import uasyncio
import json

gc.collect()

wifi_setup('Aarons Wifi', '1teddyGoofy')
uuid = get_uuid()

lcd = LCD(0x3F, 2, 16)
rgb_led = RGBLed(LED_R_PIN, LED_G_PIN, LED_B_PIN)

next = Button(NEXT_PIN)
prev = Button(PREV_PIN)
ping = Button(PING_PIN)
sync = Button(SYNC_PIN)

rgb_led.set(0, 255, 0)
lcd.print("ID: " + str(uuid), 1)

friends = []
friend_idx = 0

def handle_update():
  lcd.print(friends[friend_idx], 1)

async def connect_and_receive(loop):
  global friends
  global friend_idx

  websocket = await client.connect("ws://144.202.14.186:8080/box/" + uuid)
  loop.create_task(poll(websocket))
  while True:
    msg = await websocket.recv()
    obj = json.loads(msg)

    method = obj['method']
    if method == 'friends':
      friends = obj['friends']
      friend_idx = 0
      print(str(friends))
      handle_update()
    elif method == 'ping':
      friend = obj['from_username']
      lcd.clear()
      lcd.move_to(0, 0)
      lcd.print("---- PING ----", 1)
      lcd.print("From: " + friend, 2)

      rgb_led.set(255, 0, 0)
      await uasyncio.sleep(0.25)
      rgb_led.set(0, 0, 255)
      await uasyncio.sleep(0.25)
      rgb_led.set(0, 0, 255)
      await uasyncio.sleep(0.25)
      rgb_led.set(0, 255, 0)
      await uasyncio.sleep(1)
      handle_update()

toggle = False
async def poll(websocket):
  global friends
  global friend_idx
  global toggle

  while True:
    next_state = not next.value()
    prev_state = not prev.value()
    ping_state = not ping.value()
    sync_state = not sync.value()

    if next_state and next.did_change():
      if len(friends) == 0:
        continue
      
      if friend_idx == len(friends) - 1:
        friend_idx = 0
      else:
        friend_idx += 1
      handle_update()
    elif prev_state and prev.did_change():
      if len(friends) == 0:
        continue
      
      if friend_idx == 0:
        friend_idx = len(friends) - 1
      else:
        friend_idx -= 1
      handle_update()
    elif ping_state and ping.did_change():
      if len(friends) == 0:
        continue

      friend = friends[friend_idx]
      obj = {
        "method": "ping",
        "to_username": friend
      }
      await websocket.send(json.dumps(obj))
    elif sync_state and sync.did_change():
      if not toggle:
        lcd.clear()
        lcd.print("ID: " + uuid, 1)
        toggle = True
      else:
        toggle = False
        handle_update()
    await uasyncio.sleep(0.1)

loop = uasyncio.get_event_loop()
loop.create_task(connect_and_receive(loop))
loop.run_forever()
