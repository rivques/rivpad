# Custom firmware for the rivpad macropad.
# In addition to sending keycodes, it also uses neopixels and an OLED to show system resource utilization.

import board
import neopixel
import displayio
import usb_cdc
import adafruit_displayio_ssd1306
import i2cdisplaybus
from adafruit_display_text.label import Label
import terminalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import keypad

keyboard = Keyboard(usb_hid.devices)

matrix = keypad.KeyMatrix(row_pins=[board.D10, board.D9, board.D8], column_pins=[board.D0, board.D1, board.D2])

pixels = neopixel.NeoPixel(board.D3, 16, brightness=0.2, auto_write=False, pixel_order=neopixel.GRB)

oled_bus = i2cdisplaybus.I2CDisplayBus(board.I2C(), device_address=0x3C)
oled = adafruit_displayio_ssd1306.SSD1306(oled_bus, width=128, height=32)
group = displayio.Group()
oled.root_group = group
label = Label(terminalio.FONT, text="    Rivpad Macropad   ", color=0xFFFFFF, x=0, y=12, scale=1)
group.append(label)

# keycodes from https://github.com/jtroo/kanata/blob/main/parser/src/keys/mod.rs
base_kbd_layer = [
    "layer", # the layer change key
    0xF8, # mute microphone
    154, # select window
    140, # open terminal
    144, # open file manager
    150, # open browser
    (Keycode.SHIFT, Keycode.GUI), # super+shift to push windows
    372, # toggle maximize window
    212, # take screenshot to clipboard
]

power_kbd_layer = [
    "layer", # the layer change key
    None, 
    142, # sleep
    None,
    None,
    None,
    None,
    None,
    116, # power off
]

power_layer_active = False

if usb_cdc.data is None:
    raise RuntimeError("USB CDC data port not available. Ensure boot.py is on the board and ran successfully.")
usb_cdc.data.timeout = 0.1  # Set a timeout for reading data

system_resources = [
    {
        "name": "CPUav",
        "hue": 0,  # Red
    },
    {
        "name": "CPUpk",
        "hue": 30,  # Orange
    },
    {
        "name": "RAM",
        "hue": 60,  # Yellow
    },
    {
        "name": "Disk",
        "hue": 180,  # Cyan
    },
    {
        "name": "Net",
        "hue": 120,  # Green
    },
    {
        "name": "GPU",
        "hue": 300,  # Magenta
    },
    {
        "name": "VRAM",
        "hue": 240,  # Blue
    },
]

def hsv_to_rgb(hue, saturation=1.0, value=1.0):
    """Convert HSV to RGB color space."""
    hue = float(hue) / 360.0  # Normalize hue to [0, 1)
    if saturation == 0.0:
        return (value, value, value)
    i = int(hue * 6.0)  # hue is in [0, 1), multiply by 6
    f = (hue * 6.0) - i
    p = value * (1.0 - saturation)
    q = value * (1.0 - f * saturation)
    t = value * (1.0 - (1.0 - f) * saturation)
    i %= 6
    if i == 0:
        return (value, t, p)
    elif i == 1:
        return (q, value, p)
    elif i == 2:
        return (p, value, t)
    elif i == 3:
        return (p, q, value)
    elif i == 4:
        return (t, p, value)
    elif i == 5:
        return (value, p, q)
    else:
        # unreachable
        return (0, 0, 0)

while True:
    # Check for key presses
    event = matrix.events.get()
    if event:
        key_number = event.key_number
        key = base_kbd_layer[key_number] if not power_layer_active else power_kbd_layer[key_number]
        if event.pressed:
            if key == "layer":
                power_layer_active = True
                keyboard.release_all()
            elif isinstance(key, tuple):
                keyboard.press(*key)
            elif key is not None:
                keyboard.press(key)
        else:
            if key == "layer":
                power_layer_active = False
                keyboard.release_all()
            elif isinstance(key, tuple):
                keyboard.release(*key)
            elif key is not None:
                keyboard.release(key)
    
    # get system resource utilization from the serial port, if available
    if usb_cdc.data.in_waiting > 0:
        data_raw = usb_cdc.data.readline(32)
        data = data_raw.decode('utf-8').strip().split(',')
        # a daemon running on the host is expected to send a comma-separated list of utilization percents
        # like "30,90,48,3,5,15,30\n" for CPUav, CPUpk, RAM, Disk, Net, GPU, VRAM
        resource_values = [int(x) for x in data if x.isdigit()]
        if len(data) != len(system_resources):
            # there was an error in the data, skip this iteration
            continue

        # pick the biggest 4 values and grab their corresponding names/hues
        cpu_av_index = 0
        cpu_pk_index = 1
        if resource_values[cpu_pk_index] > resource_values[cpu_av_index] * 1.2:
            # Remove CPUav if CPUpk is significantly higher
            resource_values.pop(cpu_av_index)
            system_resources.pop(cpu_av_index)
        else:
            # Remove CPUpk otherwise
            resource_values.pop(cpu_pk_index)
            system_resources.pop(cpu_pk_index)
        top_resources = sorted(zip(resource_values, system_resources), reverse=True)[:4]

        # update the neopixels
        for i, (value, resource) in enumerate(top_resources):
            hue = resource["hue"]
            rgb_full = hsv_to_rgb(hue, saturation=1.0, value=1.0)
            rgb_last = hsv_to_rgb(hue, saturation=1.0, value=(value / 25.0) % 1.0)
            num_full_pixels = int(value / 25.0)
            pixel_values = []
            for j in range(4):
                if j < num_full_pixels:
                    pixel_values.append(rgb_full)
                elif j == num_full_pixels:
                    pixel_values.append(rgb_last)
                else:
                    pixel_values.append((0, 0, 0))
            pixels[i * 4:i * 4 + 4] = pixel_values
        pixels.show()

        # update the OLED display
        label.text = "|".join(f"{resource['name']}" for _, resource in top_resources)
