# rivpad
a [hackpad](https://hackpad.hackclub.com) macropad

## features
- 9 keys
- OLED display
- 16 RGB LEDs, intended as system monitors
- PCB-mount style, no top plate
- optional USB port for daisy chaining keyboards

## a note on the custom firmware
because i want to use the RGB LEDs to monitor system load, i had to write custom firmware, because neither qmk nor kmk supports getting info from the host like that.

## a note on the usb port
the USB port is optional. it's intended to forward HID packets from a second keyboard using pico-pio-usb. because this would require even more custom firmware, i don't plan to do it immediately but did break out the required pins on the PCB.

## BOM
- 1x XIAO RP2040
- 16x SK6812MINI-E RGB LEDs
- 9x Cherry MX-style switches
- 9x 1N4148 diodes
- 1x 0.91" OLED display
- 2x 4.7kΩ resistors
- 9x DSA keycaps
- 1x 3D-printed case
- 1x PCB
- 4x M3x10mm bolts
- 4x M3 heat-set inserts
- 4x anti-slip rubber feet
- *optional* 1x USB-A female connector