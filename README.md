<h1 ID="pusher"> Remote-controllable button pusher for IQ recorder (R&S <code>IQR-100</code>)</h1>

This repo includes a **GUI** remote controller for IQ recorder `buttonPusher_GUI.py`, a **CLI** remote controller `buttonPusher_monitor.py` and the program to command the step motor on raspberry pi `buttonPusher_Slave.py`. The mechanism for the pusher is a simple **cam**. Since the vaild range for the movement is very short, we choose a small section of reciprocation with 20 steps instead of the full circular motion. 

The controller communicates with `raspberry pi` using the **socket**. Once boot the `raspberry pi`, the server will automatically be established waiting for the controller to send commands.

## Device set-up
- `step motor` (35BYJ46, 5 wires)
- `motor driver board` (ULN2003)
- `power supply` (12V/1.5A)
- `raspberry pi` (model B+)

The first time to use the controller, you need to upload the `buttonPusher_Slave.py` to the `raspberry pi`.
Add the following line above `exit 0` to the `/etc/rc.local` to execute the script at boot. 
```
python3 /path/to/file/buttonPusher_Slave.py &
```

Set the static ip of your `raspberry pi`. (system: *Debian-jessie*)
Add the following line to the `/etc/dhcpcd.conf`
```
interface eth0
    static ip_address=10.10.91.96/24
    static routers=10.10.91.1
    static domain_name_servers=10.10.91.1
```
See more for [*static ip setting <b>dhcpcd</b> vs <b>/etc/network/interfaces</b>*](https://raspberrypi.stackexchange.com/questions/39785/dhcpcd-vs-etc-network-interfaces)

## Usage
1. connect all the devices, and boot the `raspberry pi`
2. using **CLI**: launch the `buttonPusher_monitor.py`, then input as the explanation of the feedback. <br/>
   using **GUI**: launch the `buttonPusher_GUI.py`, then choose the press mode and press the button. Using key combination `ctrl-w` or red cross on the right top corner will quit the controller.

## Press mode
- `short press`: used for the normal operation of "power on" or "power off" <br/> 
  (the rod move forward 20 steps, wait for 0.5 seconds then move backward to the starting point)
- `long press`: used for the freezing status of `IQR-100` to shutdown <br/> 
  (the rod move forward 20 steps, wait for 2 seconds then move backward to the starting point)
- `debug` (hidden mode in **GUI**, shown with the key combination `ctrl-h`): used for calibrating the rod's position <br/>
  (the rod move with the input steps in the selected direction while the position shows the differences with the starting point)

See [Wiki](https://github.com/SchottkySpectroscopyIMP/remote-buttonpusher/wiki/Mini-Button-Pusher) for more explanations.
