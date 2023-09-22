import array, time
from machine import Pin
import rp2
from time import sleep
import _thread
from dmx import DMX_RX

LED_PIN = 16
LED_COUNT = 96
LED_BRIGHTNESS = 0.30 # 0.1 = darker, 1.0 = brightest
LED_SEGMENTS = 32

DMX_ADDRESS = 1
DMX_PIN = 1

LED_PER_SEGMENT = (LED_COUNT / LED_SEGMENTS)

# Define GPIO pin numbers for the 10 address bits
ABITS = [Pin(pin, Pin.IN, Pin.PULL_DOWN) for pin in range(6, 15)]
prev_abits_state = [ABITS[i].value() for i in range(9)]

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT,
             autopull=True, pull_thresh=24) # PIO configuration

# define WS2812 parameters
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()
    
# Create the StateMachine with the ws2812 program, outputting on pre-defined pin
# at the 8MHz frequency
state_mach = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(LED_PIN))

# Activate the state machine
state_mach.active(1)

# Range of LEDs stored in an array
pixel_array = array.array("I", [0 for _ in range(LED_COUNT)])

def update_pix(brightness_input=LED_BRIGHTNESS): # dimming colors and updating state machine (state_mach)
    dimmer_array = array.array("I", [0 for _ in range(LED_COUNT)])
    for ii,cc in enumerate(pixel_array):
        r = int(((cc >> 8) & 0xFF) * brightness_input) # 8-bit red dimmed to brightness
        g = int(((cc >> 16) & 0xFF) * brightness_input) # 8-bit green dimmed to brightness
        b = int((cc & 0xFF) * brightness_input) # 8-bit blue dimmed to brightness
        dimmer_array[ii] = (g<<16) + (r<<8) + b # 24-bit color dimmed to brightness
    state_mach.put(dimmer_array, 8) # update the state machine with new colors
    #time.sleep_ms(10)

def set_24bit(ii, r, g, b): # set colors to 24-bit format inside pixel_array
    pixel_array[ii] = (r<<16) + (g<<8) + b # set 24-bit color
    
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
def pixels_thread():
    global DMX_ADDRESS
    DMX_CHANNEL = DMX_ADDRESS
    
    DMX_IN = DMX_RX(pin=1)
    DMX_IN.start()
    
    last_frame = -1    
    while True:
        DMX_CHANNEL = DMX_ADDRESS
        current_frame = DMX_IN.frames_received
        
        #print("DMX_IN.channels length:", len(DMX_IN.channels))
        #print("Pixel Array", len(pixel_array))
        
        #r = DMX_IN.channels[DMX_CHANNEL + 1]
        #g = DMX_IN.channels[DMX_CHANNEL + 2]
        #b = DMX_IN.channels[DMX_CHANNEL + 3]
        
        #print("Channel:", DMX_CHANNEL, "R:", r, "G:", g, "B:", b)
        
        #sleep(1)

       #DMX_CHANNEL += 3
        #if DMX_CHANNEL >= 1 and DMX_CHANNEL + 2 < len(DMX_IN.channels):
         #   for i in range(3):
          #      r = DMX_IN.channels[DMX_CHANNEL]
           #     g = DMX_IN.channels[DMX_CHANNEL + 1]
            #    b = DMX_IN.channels[DMX_CHANNEL + 2]
                
             #   print("Channel:", DMX_CHANNEL, "R:", r, "G:", g, "B:", b)
                
                # set_24bit(i, r, g, b)
                
                #for s in range(1, LED_PER_SEGMENT):
                    #i += 1
                    
                    # set_24bit(i, r, g, b)
                    
                #DMX_CHANNEL += 3
            #update_pix()
        for i in range(17):
            r = DMX_IN.channels[DMX_CHANNEL + 1]
            g = DMX_IN.channels[DMX_CHANNEL + 2]
            b = DMX_IN.channels[DMX_CHANNEL + 3]
            #print("Channel:", DMX_CHANNEL, "R:", r, "G:", g, "B:", b)
            



second_thread = _thread.start_new_thread(pixels_thread, ())
dmx_thread()
            
