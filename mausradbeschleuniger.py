'''
Created on Mar 31, 2012

@author: droelf
'''
import sys
from uinput import UInputDevice
from pyinputevent import InputEvent, SimpleDevice
import select

class ForwardDevice(SimpleDevice):
    def __init__(self, udev, threshold, speedup, *args, **kwargs):
        SimpleDevice.__init__(self, *args, **kwargs)
        self.udev = udev # output device
        self.threshold = threshold  # if this the time between consecutive wheel events falls below this threshold, acceleration becomes active
        self.speedup = speedup # number of additional events to send
        self.olddir = 0
        self.oldtime = 0



    def receive(self, event):

        if event.etype == 2:    # etype 2: mouse 
            if event.ecode == 8:   # ecode 8: mouse wheel
                dir = event.evalue
                ts = event.timestamp
                tdiff = ts - self.oldtime
                self.oldtime = ts
                if (self.olddir == dir):
                    
                    

                    if (tdiff <= self.threshold):
                            
                        for i in range(self.speedup):
                            self.udev.send_event(InputEvent.new(2, 8, dir))
                            self.udev.send_event(InputEvent.new(0, 0, 0))
                        #print tdiff
                        
                        
                    if (self.speedup == 0): # debug
                        debugstr = str(tdiff * 1000)
                        if (tdiff <= self.threshold):
                            debugstr += " speedup"
                        print debugstr
                        
                self.olddir = dir

       

def main(indev, p_thres, p_mul):
    udev = UInputDevice("Virtual Input Device", 0x0, 0x1, 1)
    udev.create()
    udev.send_event(InputEvent.new(0,0,0))
    poll = select.poll()
    fds = {}
    dev = ForwardDevice(udev, float(p_thres)/1000, p_mul, indev, indev)
    poll.register(dev, select.POLLIN | select.POLLPRI)

    fds[dev.fileno()] = dev
    while True:
        for x,e in poll.poll():
            dev = fds[x]
            dev.read()


if __name__ == '__main__':
    #test()
    if len(sys.argv) != 4:
        print "usage: "
        print sys.argv[0], " <input device> <threshold (ms)> <speedup>"
        print "a speedup of 0 will enable debug mode"
    else:
        main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))