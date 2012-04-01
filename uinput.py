import struct
import os
import time
import fcntl
import scancodes

#define UINPUT_MAX_NAME_SIZE    80
#struct uinput_user_dev {
#        char name[UINPUT_MAX_NAME_SIZE];
#        struct input_id id;
#        int ff_effects_max;
#        int absmax[ABS_MAX + 1];
#        int absmin[ABS_MAX + 1];
#        int absfuzz[ABS_MAX + 1];
#        int absflat[ABS_MAX + 1];
#};

UI_DEV_CREATE  = 0x5501
UI_DEV_DESTROY = 0x5502

UI_SET_EVBIT   = 0x40045564
UI_SET_KEYBIT  = 0x40045565
UI_SET_RELBIT  = 0x40045566
UI_SET_ABSBIT  = 0x40045567

EV_SYN = 0x00
EV_KEY = 0x01
EV_REL = 0x02
EV_ABS = 0x03
EV_MSC = 0x04

REL_X = 0x00
REL_Y = 0x01
REL_WHEEL = 0x08

ABS_X = 0x00
ABS_Y = 0x01

BUS_USB = 0x03

BTN_MOUSE = BTN_LEFT = 0x110
BTN_RIGHT = 0x111
BTN_MIDDLE = 0x112
BTN_SIDE = 0x113
BTN_EXTRA = 0x114
BTN_FORWARD = 0x115
BTN_BACK = 0x116
BTN_TASK = 0x117
BTN_TOUCH = 0x14a
BTN_TOOL_PEN = 0x140
BTN_TOOL_FINGER = 0x145
BTN_TOOL_MOUSE = 0x146
BTN_STYLUS = 0x14b

SYN_REPORT = 0

ButtonDefaults = (BTN_LEFT, BTN_RIGHT, BTN_MIDDLE, BTN_SIDE, BTN_EXTRA,
                  BTN_FORWARD, BTN_BACK, BTN_TASK)
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
UINPUT_STRUCT = "80sHHHHi" + 64*4*'I'

class UInputDevice(object):
    __slots__ = ('_uinputpath', '_keys', '_mouserel', '_mouseabs', '_name',
                 '_vendor', '_product', '_version', '_UINPUT_STRUCT', '_fd')

    def __init__(self, name, vendor, product, version, mouserel=True,
                 mouseabs=False, keys=True, uinputpath="/dev/uinput",
                 uinputstruct=UINPUT_STRUCT):
        self._name = name
        self._vendor = vendor
        self._product = product
        self._version = version
        self._mouserel = mouserel
        self._mouseabs = mouseabs
        self._keys = keys
        self._uinputpath = uinputpath
        self._UINPUT_STRUCT = UINPUT_STRUCT

    def create(self, ff_effects_max=0x0, UUD_extra=None):
        """Create the device"""
        if not UUD_extra:
            UUD_extra = []
            for f in range(64*1):  #absmin
                UUD_extra.append(0x00)
            for f in range(64*1):  #absmax
                #UUD.append(0x400)
                UUD_extra.append(0x00)
            for f in range(64*2):   #absfuzz,absflat
                UUD_extra.append(0x00)
        UUD = struct.pack(self._UINPUT_STRUCT,
            self._name,
            BUS_USB,
            self._vendor,
            self._product,
            self._version,
            ff_effects_max,
            *UUD_extra)
        self._fd = fd = os.open(self._uinputpath, os.O_RDWR)
        os.write(fd, UUD)
        self.send_ioctls()
        # and now, actually create the device
        fcntl.ioctl(fd, UI_DEV_CREATE, 0x0)

    def destroy(self):
        """Destroy the device"""
        fcntl.ioctl(self._fd, UI_DEV_DESTROY, 0x0)
        os.close(self._fd)

    def send_ioctls(self):
        """Define all the events that this device will send"""
        fd = self._fd
        fcntl.ioctl(fd, UI_SET_EVBIT, EV_SYN) # 0,0,0
        if self._keys: # can be an iterable
            fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY) # is keyboard
            fcntl.ioctl(fd, UI_SET_EVBIT, EV_MSC) # used, but ?
            if getattr(self._keys, '__iter__', False):
                for v in self._keys:
                    fcntl.ioctl(fd, UI_SET_KEYBIT, v)
            else:
                KEY_MAX = 767 # 0x2ff
                for k,v in scancodes.__dict__.items():
                    # add every recognised key
                    if v < KEY_MAX and k.startswith('KEY_'):
                        fcntl.ioctl(fd, UI_SET_KEYBIT, v)
        if self._mouserel: # enable relative mouse movement
            fcntl.ioctl(fd, UI_SET_EVBIT, EV_REL) # is relative device
            fcntl.ioctl(fd, UI_SET_RELBIT, REL_X)
            fcntl.ioctl(fd, UI_SET_RELBIT, REL_Y)
            fcntl.ioctl(fd, UI_SET_RELBIT, REL_WHEEL)
        if self._mouseabs:
            fcntl.ioctl(fd, UI_SET_EVBIT, EV_ABS) # is absolute device
            if getattr(self._mouseabs, '__iter__', False):
                for v in self._mouseabs:
                    fcntl.ioctl(fd, UI_SET_KEYBIT, v)
            else:
                fcntl.ioctl(fd, UI_SET_KEYBIT, BTN_TOUCH)
                fcntl.ioctl(fd, UI_SET_KEYBIT, BTN_STYLUS)
                fcntl.ioctl(fd, UI_SET_KEYBIT, BTN_TOOL_PEN)
                fcntl.ioctl(fd, UI_SET_KEYBIT, BTN_TOOL_FINGER)
                fcntl.ioctl(fd, UI_SET_KEYBIT, BTN_TOOL_MOUSE)
        if self._mouserel or self._mouseabs:
            for v in ButtonDefaults:
                fcntl.ioctl(fd, UI_SET_KEYBIT, v)

    def send_event(self, event):
        if type(event) == str:
            os.write(self._fd, event)
        elif hasattr(event, 'pack'):
            os.write(self._fd, event.pack())
        else:
            print >>sys.stderr, "Don't know what to do to send %r" % (event,)

if __name__ == '__main__':
    udev = UInputDevice("Test", 0x0, 0x1, 1)
    udev.create()
    from pyinputevent import InputEvent
    import sys
    udev.send_event(InputEvent.new(0,0,0))
    i = 100
    while i:
        i = i - 1
        sys.stdout.flush()
        #udev.send_event(InputEvent.new(4,4,20))
        #udev.send_event(InputEvent.new(1,20,1))
        #udev.send_event(InputEvent.new(0,0,0))
        #udev.send_event(InputEvent.new(4,4,20))
        #udev.send_event(InputEvent.new(1,20,0))
        #udev.send_event(InputEvent.new(0,0,0))
        #udev.send_event(InputEvent.new(EV_REL, 0, 4))
        #udev.send_event(InputEvent.new(EV_REL, 1, 4))
        udev.send_event(InputEvent.new(EV_REL, 8, 4))
        #udev.send_event(InputEvent.new(EV_REL, 1, 4))
        udev.send_event(InputEvent.new(0,0,0))
        time.sleep(0.005)
    udev.destroy()
