#!/usr/bin/env python3

import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = "10.10.91.96"
port = 5052
client.connect((host, port))

def loop():
    print("Welcome to use the remote button pusher[input 'exit' for exit]")
    while True:
        print("select the mode(1/2/3) for operation:\n" + "1. long press\n".rjust(4," ") + "2. short press\n".rjust(4, " ") + "3. free".rjust(4, " "))
        mode = input("mode(1/2/3/exit): ")
        if mode == "1" or mode == "2":
            client.send(mode.encode("utf-8"))
            while True:
                msg = client.recv(1024).decode("utf-8")
                print(msg)
                if msg == "11" or msg == "10":
                    break
        elif mode == "3":
            client.send(mode.encode("utf-8"))
            inputOperation = input("operation, steps/quit:")
            if inputOperation == "quit":
                print("end!")
            else:
                client.send(inputOperation.encode("utf-8"))
                while True:
                    msg = client.recv(1024).decode("utf-8") 
                    print(msg)
                    if msg == "11" or msg == "10":
                        print(msg)
                        break
        elif mode == "exit":
            break
        elif mode == "kill":
            client.send(mode.encode("utf-8"))
            break
        else:
            print("invaild input!")
        print("\n")
    client.close()

if __name__=="__main__":
    loop()
