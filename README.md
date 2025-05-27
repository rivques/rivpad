# rivpad
a [hackpad](https://hackpad.hackclub.com) macropad

## features
- 9 keys
- OLED display
- 16 RGB LEDs, intended as system monitors
- PCB-mount style, no top plate
- optional USB port for daisy chaining keyboards

## cad
The CAD is in an Onshape document available [here](https://cad.onshape.com/documents/859a6718b395782d916274d9/w/acb2d55d003e03c3719d4ca6/e/6f143904c3132775702816f5?renderMode=0&uiState=6834dff6784e7633979328d8).

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
- *optional* 4x anti-slip rubber feet
- *optional* 1x USB-A female connector

## screenshots
### overall
![image](https://github.com/user-attachments/assets/3efabe02-31a4-4a67-9546-6f19268824bf)
### case
![image](https://github.com/user-attachments/assets/e16de3be-e51c-4036-8cf8-bd1ad5a9fdc5)
### schematic
![image](https://github.com/user-attachments/assets/48244d1e-706e-4fa2-8b0e-a67a7d5fea0c)
### pcb
![image](https://github.com/user-attachments/assets/38cfee9a-ece0-47ab-bcb4-d871ab55d88d)
