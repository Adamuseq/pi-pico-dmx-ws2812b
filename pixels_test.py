from neopixel import Neopixel
from machine import Pin
import machine
import ustruct
import _thread

LED_PIN = 16
LED_COUNT = 96
LED_BRIGHTNESS = 30 # 0.1 = darker, 1.0 = brightest
LED_SEGMENTS = 32

DMX_ADDRESS = 1
DMX_PIN = Pin(1)

LED_PER_SEGMENT = (LED_COUNT / LED_SEGMENTS)

strip = Neopixel(LED_COUNT, 0, LED_PIN, "RGB")

strip.brightness(LED_BRIGHTNESS)

ABITS = [Pin(pin, Pin.IN, Pin.PULL_DOWN) for pin in range(6, 15)]
prev_abits_state = [ABITS[i].value() for i in range(9)]

# Define the UART settings (adjust pins and baudrate as needed)
uart_tx_pin = 2  # Define the TX pin (use a valid pin number)
uart_rx_pin = 3  # Define the RX pin (use a valid pin number)
baudrate = 250000

uart = machine.UART(0, baudrate=250000, tx=None, rx=DMX_PIN, rxbuf=1024)

def dmx_thread():
    global prev_abits_state
    global DMX_ADDRESS
    global ABITS
    while True:
        current_abits_state = [ABITS[i].value() for i in range(9)]
        
        DMX_ADDRESS = sum(current_abits_state[i] * (2 ** i) for i in range(9))
        
        if current_abits_state != prev_abits_state:
            print("DMX Address changed to:", DMX_ADDRESS)
            prev_abits_state = current_abits_state

p0 = Pin(2, Pin.OUT)
p0.value(0)

def process_dmx_data(data):
    global DMX_ADDRESS
    DMX_CHANNEL = DMX_ADDRESS
    if data[0] == 0 and data[1] == 0:
        # DMX data starts with a break and mark-after-break
        dmx_data = data[2:]
        if len(dmx_data) >= ((led_count * 3) + DMX_CHANNEL):
            for i in range(17):
                # Each LED consumes 3 DMX channels (R, G, B)
    
                r = dmx_data[DMX_CHANNEL + 1]
                g = dmx_data[DMX_CHANNEL + 2]
                b = dmx_data[DMX_CHANNEL + 3]
                print("Recived:", dmx_data[DMX_CHANNEL + 1])
                
                # Update Neopixel colors
                strip.set_pixel(i, (r, g, b))
        strip.show()

# UART interrupt handler
def uart_isr(arg):
    data = uart.read()
    if data:
        process_dmx_data(data)
        
#uart.irq(trigger=machine.UART_RXANY, handler=uart_isr)
        
def strip_thread():
    data = uart.read(1)  # Read one byte at a time
    if data:
        process_dmx_data(data)
#     global DMX_ADDRESS
#     DMX_CHANNEL = DMX_ADDRESS
#     
#     DMX_IN = DMX_RX(pin=1)
#     DMX_IN.start()
#     
#     while True:
#         for i in range(17):
#             r = DMX_IN.channels[DMX_CHANNEL + 1]
#             g = DMX_IN.channels[DMX_CHANNEL + 2]
#             b = DMX_IN.channels[DMX_CHANNEL + 3]
#             strip.set_pixel(i, (r, g, b))
#         strip.show()
            
second_thread = _thread.start_new_thread(dmx_thread, ())
strip_thread()