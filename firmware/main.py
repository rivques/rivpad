# Custom firmware for the rivpad macropad.
# In addition to sending keycodes, it also uses neopixels and an OLED to show system resource utilization.

import board
import neopixel
import displayio
import usb_cdc
import adafruit_displayio_ssd1306
import i2cdisplaybus
from lib.adafruit_display_text.label import Label
import terminalio
import usb_hid
from lib.adafruit_hid.keyboard import Keyboard
from lib.adafruit_hid.keycode import Keycode
import keypad

keyboard = Keyboard(usb_hid.devices)

matrix = keypad.KeyMatrix(row_pins=[board.D10, board.D9, board.D8], column_pins=[board.D0, board.D1, board.D2])

pixels = neopixel.NeoPixel(board.D3, 16, brightness=0.1, auto_write=False)
pixel_map = [15, 14, 13, 12, 8, 9, 10, 11, 7, 6, 5, 4, 0, 1, 2, 3]

displayio.release_displays()  # Release any existing displays
oled_bus = i2cdisplaybus.I2CDisplayBus(board.I2C(), device_address=0x3C)
oled = adafruit_displayio_ssd1306.SSD1306(oled_bus, width=128, height=32)
group = displayio.Group()
oled.root_group = group
label = Label(terminalio.FONT, text="    Rivpad Macropad   ", color=0xFFFFFF, x=0, y=12, scale=1)
group.append(label)

# keycodes from https://github.com/jtroo/kanata/blob/main/parser/src/keys/mod.rs
base_kbd_layer = [
    "layer", # the layer change key
    Keycode.KEYPAD_ONE, # mute microphone (handled by cinnamon shortcut)
    Keycode.KEYPAD_TWO, # toggle audio output device (handled by kanata)
    Keycode.KEYPAD_THREE, # open terminal (handled by cinnamon shortcut)
    Keycode.KEYPAD_FOUR, # open file manager (handled by cinnamon shortcut)
    Keycode.KEYPAD_FIVE, # open browser (handled by cinnamon shortcut)
    (Keycode.SHIFT, Keycode.GUI), # super+shift to push windows, handled by cinnamon natively
    Keycode.KEYPAD_SEVEN, # toggle maximize window (handled by cinnamon shortcut)
    Keycode.KEYPAD_EIGHT, # take screenshot to clipboard (handled by cinnamon shortcut)
]

power_kbd_layer = [
    "layer", # the layer change key
    None, 
    Keycode.KEYPAD_ZERO, # sleep (handled by cinnamon shortcut)
    None,
    None,
    None,
    None,
    None,
    Keycode.POWER, # open power menu (handled by cinnamon natively)
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
        "hue": 50,  # Orange
    },
    {
        "name": "RAM",
        "hue": 100,  # Yellow
    },
    {
        "name": "Disk",
        "hue": 200,  # Cyan
    },
    {
        "name": "Net",
        "hue": 150,  # Green
    },
    {
        "name": "GPU",
        "hue": 300,  # Magenta
    },
    {
        "name": "VRAM",
        "hue": 250,  # Blue
    },
]

def hsv_to_rgb_raw(hue, saturation=1.0, value=1.0):
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

def hsv_to_rgb(hue, saturation=1.0, value=1.0):
    """Convert HSV to RGB color space and scale to 0-255 range."""
    r, g, b = hsv_to_rgb_raw(hue, saturation, value)
    return (int(r * 255), int(g * 255), int(b * 255))

while True:
    # Check for key presses
    event = matrix.events.get()
    if event:
        key_number = event.key_number
        key = base_kbd_layer[key_number] if not power_layer_active else power_kbd_layer[key_number]
        print(f"Key {key_number} {'pressed' if event.pressed else 'released'} on {'base' if not power_layer_active else 'power'}: {key}")  # Debug output
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
            print(f"Error: Expected {len(system_resources)} values, got {len(data)}. Data: {data}")
            continue

        # pick the biggest 4 values and grab their corresponding names/hues
        cpu_av_index = 0
        cpu_pk_index = 1
        top_resources = sorted(zip(resource_values, system_resources), reverse=True, key=lambda x: x[0])[:5]
        # trim the list to 4, either by eliminating the lower of CPUav or CPUpk, or by removing the lowest value if both aren't present
        cpu_av_present = any(resource["name"] == "CPUav" for _, resource in top_resources)
        cpu_pk_present = any(resource["name"] == "CPUpk" for _, resource in top_resources)
        if cpu_av_present and cpu_pk_present:
            # both are present, keep the one with the higher value
            if resource_values[cpu_av_index] > resource_values[cpu_pk_index] - 20:
                top_resources = [r for r in top_resources if r[1]["name"] != "CPUpk"]
            else:
                top_resources = [r for r in top_resources if r[1]["name"] != "CPUav"]
        else:
            # neither is present, just keep the top 4
            top_resources = top_resources[:4]

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
            print(f"Resource {resource['name']}: {value}% - RGB: {pixel_values} at index {i}")  # Debug output
            for pix_idx in range(i * 4, i * 4 + 4):
                if pix_idx > 15:
                    print(f"Warning: pix_idx {pix_idx} is out of range for pixel_map (len {len(pixel_map)})")
                    print(f"i: {i}, num_full_pixels: {num_full_pixels}, value: {value}, resource: {resource}")
                    print(f"data: {data}, resource_values: {resource_values}")
                    continue
                try:
                    pixels[pixel_map[pix_idx]] = pixel_values[pix_idx % 4]
                except IndexError:
                    print(f"IndexError: Either pix_idx {pix_idx} is out of range for pixel_map (len {len(pixel_map)}),")
                    print(f"there aren't enough pixel_values (len {len(pixel_values)}) for the pixel at index {pix_idx},")
                    print(f"or the mapped value {pixel_map[pix_idx]} is out of range for pixels (len 16)")
        pixels.show()

        # update the OLED display
        label_text = "|".join(f"{resource['name']}" for _, resource in top_resources)
        label_text += "\n" + "|".join(f"{value:^{len(resource['name'])-1}}%" for value, resource in top_resources)
        label.text = label_text
