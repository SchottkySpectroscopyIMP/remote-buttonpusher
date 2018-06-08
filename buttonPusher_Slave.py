#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
A remote controlable button pusher for R&S IQR100
Devices:
    - step motor (35BYJ46) 
    - motor driver board (ULN2003)
    - power supply (12V/1.5A)
Operation mode:
    - Long press (for system freezing): 
        the rod goes forward and waits for 2 seconds, then goes backward to the starting point
    - Short press (for manually shutdown and restart):
        the rod goes forward and waits for 0.5 seconds, then goes backward to the starting point
    - free:
        select the direction of movement and step
"""

import RPi.GPIO as GPIO
import time, readline, subprocess,socket, signal, logging


logging.basicConfig(
        level       = logging.INFO,
        format      = '%(asctime)s %(name)-5s %(message)s',
        datefmt     = '%Y-%m-%d %H:%M:%S',
        filename    = __file__[:-2] + 'log',
        filemode    = 'a'
        )

class ControlServer():
    def __init__(self, IP, port, logger):
        self.IP = IP
        self.port = port
        self.logger = logger
        self.connect()
    
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.IP, self.port))
        self.sock.listen(5)
        logging.getLogger("root").info("socket server has established")

    def disconnect(self):
        self.sock.close()

    def accept(self):
        self.client, addr = self.sock.accept()
        self.logger.info("build a connection with main server")

    def write(self, cmd):
        self.client.send(cmd.encode("utf-8"))

    def read(self):
        data = self.client.recv(4096)
        return data.decode("utf-8")

class PusherController(ControlServer):
    def __init__(self):
        super(PusherController, self).__init__("0.0.0.0", 5052, logging.getLogger("socket"))
        self.IN1 = 11
        self.IN2 = 12
        self.IN3 = 13
        self.IN4 = 15
        
        self.forward_seq = ['1000', '0100', '0010', '0001']
        self.reverse_seq = ['0001', '0010', '0100', '1000']

    def setup(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.IN1, GPIO.OUT)
        GPIO.setup(self.IN2, GPIO.OUT)
        GPIO.setup(self.IN3, GPIO.OUT)
        GPIO.setup(self.IN4, GPIO.OUT)

    def destroy(self):
        GPIO.cleanup()

    def setStep(self, step):
        GPIO.output(self.IN1, int(step[0]))
        GPIO.output(self.IN2, int(step[1]))
        GPIO.output(self.IN3, int(step[2]))
        GPIO.output(self.IN4, int(step[3]))

    def stop(self):
        self.setStep('0000')

    def forward(self, delay, steps):
        for i in range(0, steps):
            for step in self.forward_seq:
                self.setStep(step)
                time.sleep(delay)

    def backward(self, delay, steps):
        for i in range(0, steps):
            for step in self.reverse_seq:
                self.setStep(step)
                time.sleep(delay)

class killer():
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGTERM, self.exit)
    def exit(self, signum, frame):
        kill_now = True

class powerCheck():
    def __init__(self):
        self.iqr_ip = "10.10.91.93"

    # ping IP of IQR to get the current status
    def statusCheck(self):
        with subprocess.Popen(['ping', '-c1', '-W1', self.iqr_ip], stdout=subprocess.PIPE)as p:
            data = p.communicate()[0].decode("utf-8")
            if "100% packet loss" in data:
                return 0
            else:
                return 1

    # check if the IQR status change or not
    def statusChange(self, status):
        while True:
            status_new = self.statusCheck()
            if status_new == status:
                status = status_new
            else:
                break
            time.sleep(5)


if __name__=="__main__":
    # initial the controller
    control = PusherController()
    iqrStatus = powerCheck()
    control.setup()

    while True:
        killer_peacefull = False
        # start a new connection
        control.accept()
        while True:
            msg = control.read()
            if msg == "init":
                break
        iqr_status = iqrStatus.statusCheck()
        if iqr_status:
            # power on
            logging.getLogger("IQR").info("power on")
            control.write("11")
        else:
            # power off
            logging.getLogger("IQR").info("power off")
            control.write("10")

        while True:
            mode = control.read()
            if mode == "1":
                # monitor the status of IQR
                logging.getLogger("controller").info("mode 1: long press")
                iqr_status = iqrStatus.statusCheck()
                # start press
                logging.getLogger("controller").info("start press!")
                control.write("1")
                control.forward(0.005, 20)
                control.stop()
                time.sleep(5)
                control.backward(0.005, 20)
                control.stop()
                # stop press
                logging.getLogger("controller").info("stop press!")
                control.write("0")
                time.sleep(5)
                iqrStatus.statusChange(iqr_status)
                if iqr_status:
                    # power off
                    logging.getLogger("IQR").info("power off")
                    control.write("10")
                else:
                    # power on
                    logging.getLogger("IQR").info("power on")
                    control.write("11")
            elif mode == "2":
                # monitor the status of IQR
                logging.getLogger("controller").info("mode 2: short press")
                iqr_status = iqrStatus.statusCheck()
                # start press
                logging.getLogger("controller").info("start press!")
                control.write("1")
                control.forward(0.005, 20)
                control.stop()
                time.sleep(0.5)
                control.backward(0.005, 20)
                control.stop()
                # stop press
                logging.getLogger("controller").info("stop press!")
                control.write("0")
                time.sleep(5)
                iqrStatus.statusChange(iqr_status)
                if iqr_status:
                    # power off
                    logging.getLogger("IQR").info("power off")
                    control.write("10")
                else:
                    # power on
                    logging.getLogger("IQR").info("power on")
                    control.write("11")
            elif mode == "3":
                logging.getLogger("controller").info("mode 3: free mode")
                inputOperation = control.read()
                operation, step = map(int, inputOperation.split(","))
                if operation == 1:
                    logging.getLogger("controller").info("forward , step: {:d}".format(step))
                    logging.getLogger("controller").info("start press!")
                    control.write("1")
                    control.forward(0.005, step)
                    control.stop()
                    logging.getLogger("controller").info("stop press!")
                    control.write("0")
                elif operation == 2:
                    logging.getLogger("controller").info("backward , step: {:d}".format(step))
                    logging.getLogger("controller").info("start press!")
                    control.write("1")
                    control.backward(0.005, step)
                    control.stop()
                    logging.getLogger("controller").info("stop press!")
                    control.write("0")
                else:
                    pass
                time.sleep(5)
                # monitor the status of IQR
                iqr_status = iqrStatus.statusCheck()
                if iqr_status:
                    # power on
                    logging.getLogger("IQR").info("power on")
                    control.write("11")
                else:
                    # power off
                    logging.getLogger("IQR").info("power off")
                    control.write("10")
            elif not mode:
                logging.getLogger("socket").info("close a connection with main server")
                break
            elif mode == "kill":
                killer_peacefull = True
                break
            else:
                pass
        if killer_peacefull:
            logging.getLogger("root").info("socket server close")
            control.destroy()
            break
    control.disconnect()



