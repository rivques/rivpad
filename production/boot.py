import board
import digitalio
row_1 = digitalio.DigitalInOut(board.D10)
row_1.direction = digitalio.Direction.OUTPUT
row_1.value = False
col_1 = digitalio.DigitalInOut(board.D0)
col_1.direction = digitalio.Direction.INPUT
col_1.pull = digitalio.Pull.UP

if not col_1.value:
    # the top-left button is pressed
    # boot into safe mode by not doing the other stuff
    # and show that with all-red leds
    print("Booting into safe mode")
    import neopixel
    pixels = neopixel.NeoPixel(board.D3, 16, brightness=0.1)
    pixels.fill((255, 0, 0))  # Set all pixels to red
else:
    print("Booting normally")
    import supervisor
    # TODO: get a real PID
    supervisor.set_usb_identification(manufacturer="rivques", product="Rivpad Macropad", vid=0x1209, pid=0x0001) # pid.codes test PID
    import storage
    storage.disable_usb_drive()  # Disable USB mass storage
    import usb_cdc
    usb_cdc.enable(console=True, data=True)
    # this last bit doesn't appear to be needed
    #import usb_hid
    #usb_hid.enable((usb_hid.Device.KEYBOARD,))
    #usb_hid.set_interface_name("rivpad (macropad)")