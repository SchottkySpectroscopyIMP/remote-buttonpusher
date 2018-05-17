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

IN1 = 11
IN2 = 12
IN3 = 13
IN4 = 15

iqr_ip = "10.10.91.93"

forward_seq = ['1000', '0100', '0010', '0001']
reverse_seq = ['0001', '0010', '0100', '1000']

logging.basicConfig(
        level       = logging.INFO,
        format      = '%(asctime)s %(name)-5s %(message)s',
        datefmt     = '%Y-%m-%d %H:%M:%S',
        filename    = __file__[:-2] + 'log',
        filemode    = 'a'
        )

class killer():
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGTERM, self.exit)
    def exit(self, signum, frame):
        kill_now = True


def setStep(step):
    GPIO.output(IN1, int(step[0]))
    GPIO.output(IN2, int(step[1]))
    GPIO.output(IN3, int(step[2]))
    GPIO.output(IN4, int(step[3]))

def stop():
    setStep('0000')

def forward(delay, steps):
    for i in range(0, steps):
        for step in forward_seq:
            setStep(step)
            time.sleep(delay)

def backward(delay, steps):
    for i in range(0, steps):
        for step in reverse_seq:
            setStep(step)
            time.sleep(delay)

def setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(IN1, GPIO.OUT)
    GPIO.setup(IN2, GPIO.OUT)
    GPIO.setup(IN3, GPIO.OUT)
    GPIO.setup(IN4, GPIO.OUT)

def destroy():
    GPIO.cleanup()


# ping IP of IQR to get the current status
def statusCheck():
    with subprocess.Popen(['ping', '-c1', '-W1', iqr_ip], stdout=subprocess.PIPE)as p:
        data = p.communicate()[0].decode("utf-8")
        if "100% packet loss" in data:
            return 0
        else:
            return 1

# check if the IQR status change or not
def statusChange(status):
    while True:
        status_new = statusCheck()
        if status_new == status:
            status = status_new
        else:
            break
        time.sleep(5)


def loop():
    socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "10.10.91.96"
    port = 5052
    socketServer.bind((host, port))
    socketServer.listen(5)
    logging.getLogger("root").info("socket server has established")

    while True:
        killer_peacefull = False
        # start a new connection
        clientSocket, addr = socketServer.accept()
        #print("new connection")
        logging.getLogger("socket").info("build a connection with main server")
        while True:
            msg = clientSocket.recv(1024).decode("utf-8")
            if msg == "init":
                break
        iqr_status = statusCheck()
        if iqr_status:
            # power on
            logging.getLogger("IQR").info("power on")
            clientSocket.send("11".encode("utf-8"))
        else:
            # power off
            logging.getLogger("IQR").info("power off")
            clientSocket.send("10".encode("utf-8"))

        while True:
            mode = clientSocket.recv(1024).decode("utf-8")
            if mode == "1":
                # monitor the status of IQR
                logging.getLogger("controller").info("mode 1: long press")
                iqr_status = statusCheck()
                # start press
                logging.getLogger("controller").info("start press!")
                clientSocket.send("1".encode("utf-8"))
                forward(0.005, 20)
                stop()
                time.sleep(2)
                backward(0.005, 20)
                stop()
                # stop press
                logging.getLogger("controller").info("stop press!")
                clientSocket.send("0".encode("utf-8"))
                time.sleep(5)
                statusChange(iqr_status)
                if iqr_status:
                    # power off
                    logging.getLogger("IQR").info("power off")
                    clientSocket.send("10".encode("utf-8"))
                else:
                    # power on
                    logging.getLogger("IQR").info("power on")
                    clientSocket.send("11".encode("utf-8"))
            elif mode == "2":
                # monitor the status of IQR
                logging.getLogger("controller").info("mode 2: short press")
                iqr_status = statusCheck()
                # start press
                logging.getLogger("controller").info("start press!")
                clientSocket.send("1".encode("utf-8"))
                forward(0.005, 20)
                stop()
                time.sleep(0.5)
                backward(0.005, 20)
                stop()
                # stop press
                logging.getLogger("controller").info("stop press!")
                clientSocket.send("0".encode("utf-8"))
                time.sleep(5)
                statusChange(iqr_status)
                if iqr_status:
                    # power off
                    logging.getLogger("IQR").info("power off")
                    clientSocket.send("10".encode("utf-8"))
                else:
                    # power on
                    logging.getLogger("IQR").info("power on")
                    clientSocket.send("11".encode("utf-8"))
            elif mode == "3":
                logging.getLogger("controller").info("mode 3: free mode")
                inputOperation = clientSocket.recv(1024).decode("utf-8")
                operation, step = map(int, inputOperation.split(","))
                if operation == 1:
                    logging.getLogger("controller").info("forward , step: {:d}".format(step))
                    logging.getLogger("controller").info("start press!")
                    clientSocket.send("1".encode("utf-8"))
                    forward(0.005, step)
                    stop()
                    logging.getLogger("controller").info("stop press!")
                    clientSocket.send("0".encode("utf-8"))
                elif operation == 2:
                    logging.getLogger("controller").info("backward , step: {:d}".format(step))
                    logging.getLogger("controller").info("start press!")
                    clientSocket.send("1".encode("utf-8"))
                    backward(0.005, step)
                    stop()
                    logging.getLogger("controller").info("stop press!")
                    clientSocket.send("0".encode("utf-8"))
                else:
                    pass
                time.sleep(5)
                # monitor the status of IQR
                iqr_status = statusCheck()
                if iqr_status:
                    # power on
                    logging.getLogger("IQR").info("power on")
                    clientSocket.send("11".encode("utf-8"))
                else:
                    # power off
                    logging.getLogger("IQR").info("power off")
                    clientSocket.send("10".encode("utf-8"))
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
            destroy()
            break
    socketServer.close()


if __name__=="__main__":
    setup()
    loop()

