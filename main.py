"""
main.py

Part of InnovationLab.
http://eng.kuleuven.be/innolab

On Linux, if the system does not allow acces to the USB devices, you have
to add the following line to /etc/udev/rules.d:
SUBSYSTEM=="usb", ATTR{idVendor}=="2572", ATTR{idProduct}=="A001", MODE="666"

Author: Anton Lintermans.
Copyright (c) 2023 KU Leuven. All rights reserved.
"""

from flask import Flask, render_template, jsonify, Response
import threading
import time
import json
import random
import usb
import usb.core
import usb.util

################################# Settings #############################################
sample_period = 0.005
send_period = 0.250
avg_sample_size = 10
max_len = 200
number_of_endpoints = 4

value_max_left = 400
value_min_right = 600


################################# Global Variables #############################################
#Endpoints
endpoints = [None, None, None, None]

#States
states = ['CENTER', 'CENTER', 'CENTER', 'CENTER'] #States can be None 'LEFT', 'CENTER', 'RIGHT'

#Values
values = [[], [], [], []]

gpio_pins = [[1,2], [3,4], [5,6], [7,8]] # The left is mapped to the left button and right is mapped to the right button for the corresponding controller

should_exit = False

app = Flask(__name__)      


################################# Functions - Sampling The Data #############################################

def mean(array):
    result = 0
    for i in range(len(array)):
        result+= array[i]
    
    return result/len(array)


# Thread function to sample data from devices
def sample_data():
    global endpoints
    global states
    global values
    temp_values = [[], [], [], []]

    current = 0
    
    while not should_exit:
        # Code to sample data from 4 devices
        # and update device_data list

        for i in range(0, number_of_endpoints):
            if states[i] is not None:
                current = random.randint(0, 1000)
                # data = endpoints[i].read(64, 100)
                # ch2 = data[0]+data[1]*256 ## This is normally the second channel 
                # current = data[2]+data[3]*256 
                temp_values[i].append(current)
                #print(temp_values)
                if len(temp_values[i]) == avg_sample_size:
                    averaged_value = mean(temp_values[i])
                    if len(values[i]) == max_len:
                        values[i].pop(0)
                    values[i].append(averaged_value)
                    temp_values[i] = []
                    #print(values[i])
                    #control_car(i, averaged_value)

        
        # Sleep before taking the next sample
        time.sleep(sample_period)
        

################################# Functions - Connecting the usb devices #############################################
def connectToUSB():
    global endpoints
    global should_exit
    for i in range(0, number_of_endpoints):
        device = None
        if endpoints[i] is not None:
            print("endpoint " + i + " is already connected")
            return
        try:
            dev = usb.core.find(idVendor=0x2572, idProduct=0xA001)
        except usb.core.NoBackendError as exc:
            print("Cannot connect to USB")
            should_exit = True
            return
        
        if dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)

        dev.set_configuration()
        cfg = dev.get_active_configuration()

        interface_number = cfg[(0,0)].bInterfaceNumber
        try:
            alternate_settting = usb.control.get_interface(dev, interface_number)
        except usb.USBError as exc:
            print("Cannot connect to USB:\n{}".format(exc))
            return
        intf = usb.util.find_descriptor(cfg, bInterfaceNumber = interface_number,
                                        bAlternateSetting = alternate_settting)

        endpoints[i] = usb.util.find_descriptor(intf,custom_match = lambda e: \
            usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)


################################# Functions - Controlling the cars #############################################
def control_car(index, new_value):
    global states

    if new_value >= value_min_right:
        if states[index] != 'RIGHT':
            states[index] = 'RIGHT'
            gpio_pin = gpio_pins[index][1]
            # Set the GPIO PIN TO HIGH
    elif new_value <= value_max_left:
        if states[index] != 'LEFT':
            states[index] = 'LEFT'
            gpio_pin = gpio_pins[index][0]
            # Set the GPIO PIN TO HIGH
    else:
        previous_state = states[index]
        states[index] = 'CENTER'

        if previous_state == 'LEFT':
            gpio_pin = gpio_pins[index][0]
            # Set the GPIO PIN TO LOW
        elif previous_state == 'RIGHT':
            gpio_pin = gpio_pins[index][1]
            # Set the GPIO PIN TO LOW

################################# Functions - Flask Server #############################################

# Thread function to run Flask web server
def run_server():
    app.run(port=3000)

# Flask route to display device data
@app.route('/')
def index():
    global values
    return render_template('index.html', data=values)

#Send the data to clients 
@app.route('/stream')
def stream():
    def generate():
        while True:
            
            data = {'value_1': values[0], 'value_2': values[1], 'value_3': values[2], 'value_4': values[3]}
            yield 'data: {}\n\n'.format(json.dumps(data)) 
            time.sleep(send_period)

    return Response(generate(), mimetype='text/event-stream')

################################# Main #############################################

if __name__ == '__main__':

    #connectToUSB()
    # Create and start the thread to sample data
    data_thread = threading.Thread(target=sample_data)
    data_thread.start()
    
    # Create and start the thread to run Flask web server
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
