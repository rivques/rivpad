import usb_cdc
import usb_hid
usb_cdc.enable(console=True, data=True)
usb_hid.enable((usb_hid.Device.KEYBOARD,))
usb_hid.set_interface_name("rivpad macropad")