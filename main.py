"""
main.py

On Linux, if the system does not allow acces to the USB devices, you have
to add the following line to /etc/udev/rules.d:
SUBSYSTEM=="usb", ATTR{idVendor}=="2572", ATTR{idProduct}=="A001", MODE="666"

Author: Anton Lintermans.
Copyright (c) 2023 KU Leuven. All rights reserved.
"""

from flask import Flask, render_template, jsonify, Response, request
import threading
import time
import json
import random
import usb
import usb.core
import usb.util
import copy 
import RPi.GPIO as GPIO


################################# Settings #############################################
sample_period = 0.001
send_period = 0.200
error_send_period = 2
avg_sample_size = 20
max_len = 200
number_of_endpoints = 4
number_of_samples_between_calibration_checks = 20

transform_value = 5/1023

number_of_svg_points = 50

value_max_left = 2
value_min_right = 3

calibration_min = 2.2
calibration_max = 2.8


################################# Global Variables #############################################
#Endpoints
endpoints = [None, None, None, None]

#States
states = [None, None, None, None] #States can be None 'LEFT', 'CENTER', 'RIGHT', 'CALIBRATING'

#Values
values = [[], [], [], []]
svg_values = [[], [], [], []]

#Error message
error_message = ""

gpio_pins = [[19,26], [13,6], [21,20], [16,12]] # The left is mapped to the left button and right is mapped to the right button for the corresponding controller

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
    global error_message
    temp_values = [[], [], [], []] #unaveraged data flow
    number_added_samples_after_calibration_check = [0,0,0,0]
    number_added_samples_after_calibration = [0,0,0,0]
    current_data_point = 0
    while True:
        for i in range(0, number_of_endpoints):
            if states[i] is not None:
                try: 
                    data = endpoints[i].read(64, 100)
                    ch2 = data[0]+data[1]*256 ## This is normally the second channel 
                    current_data_point = data[2]+data[3]*256 
                    if error_message == "Error reading data from endpoint " + str(i):
                        error_message = ""
                except: 
                    print("Error reading data from endpoint", i)
                    error_message = "Error reading data from endpoint " + str(i)
                    current_data_point = 0
                    continue


                temp_values[i].append(current_data_point) 

                if len(temp_values[i]) == avg_sample_size:
                    averaged_value = mean(temp_values[i])*transform_value
                    if len(values[i]) == max_len:
                        values[i].pop(0)
                    
                    
                    values[i].append(averaged_value)
                    temp_values[i] = []

                    if states[i] == 'CALIBRATING':
                        if number_added_samples_after_calibration_check[i] >= number_of_samples_between_calibration_checks:
                            if checkIfCallibrated(i):
                                states[i] = 'CENTER'
                                control_car(i, averaged_value)
                                number_added_samples_after_calibration[i] = 0
                                number_added_samples_after_calibration_check[i] = 0
                            else:
                                number_added_samples_after_calibration_check[i] = 0
                        else:
                            number_added_samples_after_calibration_check[i] += 1
                        
                    else:
                        if number_added_samples_after_calibration[i] < number_of_svg_points:
                            number_added_samples_after_calibration[i] += 1
                        elif number_added_samples_after_calibration[i] == number_of_svg_points:
                            svg_values[i] = copy.deepcopy(values[i][-number_of_svg_points:])
                        control_car(i, averaged_value)
            # Sleep before taking the next sample
            time.sleep(sample_period)

def checkIfCallibrated(index):
    temp_values = values[index][-20:]
    
    mean = 0
    for i in temp_values:
        print(i)
        if i > value_min_right or i < value_max_left:
            return False
        mean += i
    
    mean = mean/len(temp_values)

    if mean < calibration_min or mean > calibration_max:
        return False
    
    return True
    
        

################################# Functions - Connecting the usb devices #############################################
def connectToUSB():
    global endpoints
    global error_message
    global number_of_endpoints
    vendor_id = 0x2572
    product_id = 0xA001

    try:
        dev = usb.core.find(find_all=True, idVendor=vendor_id, idProduct=product_id)
    except usb.core.NoBackendError as exc:
        print("Cannot connect to any USB")
        error_message = "Cannot connect to any USB"
        return

    i=0
    number_of_endpoints = 0

    for d in dev:
        if d.is_kernel_driver_active(0):
            d.detach_kernel_driver(0)

        d.set_configuration()
        cfg = d.get_active_configuration()

        interface_number = cfg[(0,0)].bInterfaceNumber
        try:
            alternate_setting = usb.control.get_interface(d, interface_number)
        except usb.USBError as exc:
            print("Cannot connect to USB:\n{}".format(exc))
            return
        intf = usb.util.find_descriptor(cfg, bInterfaceNumber=interface_number,
                                        bAlternateSetting=alternate_setting)

        endpoint = usb.util.find_descriptor(intf, custom_match=lambda e:
                                                usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)
        if endpoint is not None:
            endpoints[i] = endpoint
            print("Connected to endpoint", i)
            i += 1
            number_of_endpoints += 1

    if number_of_endpoints != 4:
        print("Error: only " + str(number_of_endpoints) + " out of 4 usb's are connected!")
        error_message = "Error: only " + str(number_of_endpoints) + " out of 4 usb's are connected!"
    else:
        error_message = ""


################################# Functions - Controlling the cars #############################################
def setup_gpio_pins():
    GPIO.setmode(GPIO.BCM) 
    for left, right in gpio_pins:
        print(left)
        print(right)
        GPIO.setup(left, GPIO.OUT)
        GPIO.setup(right, GPIO.OUT)
        GPIO.output(left, GPIO.LOW)
        GPIO.output(right, GPIO.LOW)
    

def control_car(index, new_value):
    global states

    #States can only be RIGHT, LEFT or CENTER if the state is None or CALIBRATING, this function shouldn't be called. 
    if new_value >= value_min_right:
        if states[index] != 'RIGHT':
            states[index] = 'RIGHT'
            gpio_pin = gpio_pins[index][1]
            # Set the GPIO PIN TO HIGH
            GPIO.output(gpio_pin, GPIO.HIGH)
    elif new_value <= value_max_left:
        if states[index] != 'LEFT':
            states[index] = 'LEFT'
            gpio_pin = gpio_pins[index][0]
            # Set the GPIO PIN TO HIGH
            GPIO.output(gpio_pin, GPIO.HIGH)
    elif states[index] != 'CALIBRATING' and states[index] is not None:
        previous_state = states[index]
        states[index] = 'CENTER'

        if previous_state == 'LEFT':
            gpio_pin = gpio_pins[index][0]
            # Set the GPIO PIN TO LOW
            GPIO.output(gpio_pin, GPIO.LOW)
        elif previous_state == 'RIGHT':
            gpio_pin = gpio_pins[index][1]
            # Set the GPIO PIN TO LOW
            GPIO.output(gpio_pin, GPIO.LOW)

################################# Functions - Flask Server #############################################

# Thread function to run Flask web server
def run_server():
    app.run(host='0.0.0.0', port=3000)

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
            
            data = {'value_1': values[0], 
                    'value_2': values[1], 
                    'value_3': values[2], 
                    'value_4': values[3], 
                    'state_1': states[0],
                    'state_2': states[1],
                    'state_3': states[2],
                    'state_4': states[3],
                    }
            yield 'data: {}\n\n'.format(json.dumps(data)) 
            time.sleep(send_period)

    return Response(generate(), mimetype='text/event-stream')

#Send the error message
@app.route('/error_stream')
def error_stream():
    def generate():
        while True:
            
            data = {'message': error_message}
            yield 'data: {}\n\n'.format(json.dumps(data)) 
            time.sleep(error_send_period)

    return Response(generate(), mimetype='text/event-stream')

@app.route('/start_button_pressed')
def start_button_pressed():
    global error_message
    button_index = int(request.args.get('value'))
    states[button_index] = 'CALIBRATING'

    return jsonify({'message': 'Start Button pressed!', 'value': button_index})

@app.route('/stop_button_pressed')
def stop_button_pressed():
    global error_message
    button_index = int(request.args.get('value'))
    states[button_index] = None
    values[button_index] = []
    svg_values[button_index] = []
    left, right = gpio_pins[button_index]
    GPIO.output(left, GPIO.LOW)
    GPIO.output(right, GPIO.LOW)

    return jsonify({'message': 'Stop Button pressed!', 'value': button_index})

@app.route('/download_svg_pressed')
def download_svg_pressed():
    button_index = int(request.args.get('value'))

    return jsonify({'message': 'Download SVG Button pressed!', 'value': svg_values[button_index]})

@app.route('/reset_usb_button_pressed')
def reset_usb_button_pressed():
    global error_message
    error_message = "USB is being reset..."
    time.sleep(1)
    connectToUSB()

    return jsonify({'message': 'Reset USB Button pressed!'})


################################# Main #############################################

if __name__ == '__main__':
    # Setup GPIO pins
    GPIO.setwarnings(False)
    setup_gpio_pins()
    time.sleep(1)
    connectToUSB()
    time.sleep(1)
    # Create and start the thread to sample data
    data_thread = threading.Thread(target=sample_data)
    data_thread.start()
    
    # Create and start the thread to run Flask web server
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
