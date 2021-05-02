#
# ESP8266 Micropython Interface
#

# pyright: reportMissingImports=false
import network
from machine import Pin, PWM, I2C

# Pins
LED_R_PIN = 14 
LED_G_PIN = 12
LED_B_PIN = 13

PREV_PIN = 0
NEXT_PIN = 2
PING_PIN = 15
SYNC_PIN = 16

# GPIO
class Button:
  def __init__(self, pin, mode = 0):
    self.pin = Pin(pin, Pin.IN, mode)
    self.curr = 0
    self.last = 0

  def value(self):
    self.last = self.curr
    self.curr = self.pin.value()
    return self.curr

  def did_change(self):
    return self.curr != self.last

class RGBLed:
  def __init__(self, r_pin, g_pin, b_pin):
    self.pin_r = PWM(Pin(r_pin, Pin.OUT))
    self.pin_g = PWM(Pin(g_pin, Pin.OUT))
    self.pin_b = PWM(Pin(b_pin, Pin.OUT))
    self.pin_r.freq(500)
    self.pin_g.freq(500)
    self.pin_b.freq(500)
    self.set(0, 0, 0)
    
  def set(self, r, g, b):
    self.r = int(r)
    self.g = int(g)
    self.b = int(b)
    self.duty()

  def duty(self):
    self.pin_r.duty(self._range_conv(self.r))
    self.pin_g.duty(self._range_conv(self.g))
    self.pin_b.duty(self._range_conv(self.b))

  def _range_conv(self, n):
    n = 255 - n
    return int((float(n) / 255) * 1023)

# I2C
class I2CDevice:
  def __init__(self, addr):
    self.i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
    self.addr = addr

  def read(self, size):
    return self.i2c.readfrom(self.addr, size)

  def write(self, buf):
    if not isinstance(buf, str) and not isinstance(buf, list) and not isinstance(buf, bytearray):
      buf = [buf]
    self.i2c.writeto(self.addr, bytearray(buf))

# Networking

def wifi_setup(ssid, password):
  sta_if = network.WLAN(network.STA_IF)
  if not sta_if.isconnected():
    print('connecting to network...')
    sta_if.active(True)
    sta_if.connect(ssid, password)
    while not sta_if.isconnected():
      pass
    print('network config:', sta_if.ifconfig())

