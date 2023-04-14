#!/usr/bin/env python3
# encoding: utf-8
"""
eogScope.py

Part of InnovationLab.
http://eng.kuleuven.be/innolab

On Linux, if the system does not allow acces to the USB devices, you have
to add the following line to /etc/udev/rules.d:
SUBSYSTEM=="usb", ATTR{idVendor}=="2572", ATTR{idProduct}=="A001", MODE="666"

TODO:
- Better error handling
- Retry to connect to USB

Author: Wannes Meert.
Copyright (c) 2014-2021 KU Leuven. All rights reserved.
"""

import sys
import argparse
from array import array
import socket
import numpy as np
import time
import sys
import usb
import usb.core
import usb.util
import threading
import signal
from collections import deque
import logging
import random
import pathlib

logger = logging.getLogger(__name__)

try:
    import matplotlib.pyplot as plt
except ImportError as err:
    logger.warning("Did not find matplotlib, values will not be plotted")
    plt = None

# Settings
port = 42001
host = "127.0.0.1"
max_len = 200
no_plot = False
no_scratch = False
no_usb = False
sample_period = 0.005

# Global variables
scratchSock = None
scratchWS = None
dev = None
endpoint = None
thread = None
threadws = None
should_exit = False
valuews = {}
stopws = None
plot1 = deque([512] * max_len)
plot2 = deque([512] * max_len)


def connectToScratch():
    if no_scratch:
        return
    global scratchSock
    logger.info("Connecting to Scratch ...")
    try:
        scratchSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        scratchSock.connect((host, port))
        logger.info("Connected to Scratch")
    except Exception:
        logger.warning("Cannot connect to Scratch")
        scratchSock = None


def connectToScratchWS(use_ssl=False):
    global scratchWS
    global stopws
    protocol = "ws"
    if use_ssl:
        protocol = "wss"
    logger.info(f"Starting WS server for Scratch: {protocol}://{host}:{port} ...")
    import asyncio
    import websockets
    import json
    import ssl

    async def echo(websocket, path):
        async for message in websocket:
            # print(message)
            # print(valuews)
            await websocket.send(json.dumps(valuews))

    ssl_context = None
    if use_ssl:
        # No localhost support yet for self-signed certificates for websockets
        # https://letsencrypt.org/docs/certificates-for-localhost/
        # But WS seems to work find for Chrome, Firefox and Safari
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        localhost_pem = pathlib.Path(__file__).with_name("cert.pem")
        if not localhost_pem.exists():
            raise Exception(f"Certification not found: {localhost_pem}")
        ssl_context.load_cert_chain(localhost_pem)


    async def main():
        # async with websockets.serve(echo, host, port, ssl=ssl_context):
        #     await asyncio.Future()  # run forever
        global stopws
        loop = asyncio.get_running_loop()
        stopws = loop.create_future()
        # loop.add_signal_handler(signal.SIGTERM, stopws.set_result, None)
        async with websockets.serve(echo, host, port, ssl=ssl_context):
            # await stopws
            while not should_exit:
                await asyncio.sleep(1)

    asyncio.run(main())
    logger.info('Closed Scratch WebSockets server')



def sendScratchCommand(cmd):
    if no_scratch:
        return
    if scratchSock is None:
        logger.debug("Cannot send cmd to Scratch. Trying to reconnect...")
        connectToScratch()
    if scratchSock is None:
        logger.debug("Cannot connect to Scratch")
        return

    n = len(cmd)
    a = array('c')
    a.append(chr((n >> 24) & 0xFF))
    a.append(chr((n >> 16) & 0xFF))
    a.append(chr((n >>  8) & 0xFF))
    a.append(chr(n & 0xFF))
    scratchSock.send(a.tostring() + cmd)


def sendScratchCH(channel, value):
    sendScratchCommand("sensor-update eogDongle-CH{} {}".format(channel, value))


def connectToUSB():
    global dev
    global endpoint
    global should_exit
    if endpoint is not None:
        logger.debug("Already connected to USB")
        return
    try:
        dev = usb.core.find(idVendor=0x2572, idProduct=0xA001)
    except usb.core.NoBackendError as exc:
        logger.error("Cannot connect to USB")
        logger.error(exc)
        should_exit = True
        return
    reattach = False
    if dev.is_kernel_driver_active(0):
        reattach = True
        dev.detach_kernel_driver(0)

    dev.set_configuration()
    cfg = dev.get_active_configuration()

    interface_number = cfg[(0,0)].bInterfaceNumber
    try:
        alternate_settting = usb.control.get_interface(dev, interface_number)
    except usb.USBError as exc:
        logger.error("Cannot connect to USB:\n{}".format(exc))
        return
    intf = usb.util.find_descriptor(cfg, bInterfaceNumber = interface_number,
                                    bAlternateSetting = alternate_settting)

    endpoint = usb.util.find_descriptor(intf,custom_match = lambda e: \
        usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)

    # This is needed to release interface, otherwise attach_kernel_driver fails
    # due to "Resource busy"
    # usb.util.dispose_resources(dev)

    # It may raise USBError if there's e.g. no kernel driver loaded at all
    # if reattach:
    #     dev.attach_kernel_driver(0) 

def mean(array):
    result = 0
    for i in range(len(array)):
        result+= array[i]
    
    return result/len(array)


def connect(ws=False):
    if not no_scratch:
        if ws:
            pass
        else:
            connectToScratch()
    if not no_usb:
        connectToUSB()

    else:
        logger.warning('No connection is being made with USB, sending dummy values for testing')

    cnt1 = 0
    temp_data = []
    try:
        while not should_exit:
            if no_usb:
                ch1 = random.randrange(0, 1024)
                ch2 = random.randrange(0, 1024)
            else:
                data = endpoint.read(64, 100)
                #print(data)
                ch1 = data[0]+data[1]*256
                ch2 = data[2]+data[3]*256
                temp_data.append(ch1)
                # ch1 = 1024*random.random()
                # ch2 = 1024*random.random()
            
            if len(temp_data) == 5:
                data_toshow = mean(temp_data)
                # Store last max_len samples
                if len(plot1) >= max_len:
                    plot1.pop()
                plot1.appendleft(data_toshow)
                if len(plot2) >= max_len:
                    plot2.pop()
                plot2.appendleft(ch2)
                temp_data = []

            

            logger.debug("({:<5},{:<5})".format(ch1, ch2))
            if ws:
                valuews[1] = ch1
                valuews[2] = ch2
            else:
                sendScratchCH(1, ch1)
                sendScratchCH(2, ch2)
            if should_exit:
                break

            # time.sleep(0.00005) # 500 microseconds
            time.sleep(sample_period)
    except Exception as err:
        logger.error("Error while reading data:\n{}".format(err))

    # This is needed to release interface, otherwise attach_kernel_driver fails 
    # due to "Resource busy"
    if endpoint is not None:
        usb.util.dispose_resources(dev)


def plot():
    if plt is None:
        logger.info('Matplotlib is not available, not plotting')
        return

    # Setup plot
    logger.info('Show plot')
    fig, (ax1, ax2) = plt.subplots(1, 2)
    # ax = plt.axes(xlim=(0,max_len), ylim=(0,1023))
    ax1.set_xlim(0, max_len)
    ax1.set_ylim(0, 1023)
    ax2.set_xlim(0, max_len)
    ax2.set_ylim(0, 1023)
    ax1.set_ylabel('Kanaal 1')
    ax2.set_ylabel('Kanaal 2')
    ax1.set_xlabel('Metingen')
    ax2.set_xlabel('Metingen')
    a0, = ax1.plot(range(max_len), plot1)
    a1, = ax2.plot(range(max_len), plot2)
    fig.tight_layout()
    plt.ion()
    plt.show()

    cnt2 = 0
    while not should_exit:
        # print("Update plot")
        a0.set_data(range(max_len), plot1)
        a1.set_data(range(max_len), plot2)
        plt.draw()
        plt.pause(0.001)
        fig.canvas.draw()
        time.sleep(0.25)


def main(argv=None):
    global host
    global port

    description = 'Forward InnovationLab EOG dongle input to Scratch'
    epilog = '\nFor more information visit http://eng.kuleuven.be/innovationlab'
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument('--verbose', '-v', action='count', default=0, help='Verbose output')
    parser.add_argument('--quiet', '-q', action='count', default=0, help='Quiet output')
    parser.add_argument('--host', help=f"Host where Scratch runs (default: {host})")
    parser.add_argument('--port', type=int, help=f"Port where Scratch runs (default: {port})")
    parser.add_argument('--noplot', action='store_true', help="Disable plotting")
    parser.add_argument('--noscratch', action='store_true', help="Do not try to connect with Scratch")
    parser.add_argument('--nousb', action='store_true', help='Do not connect to USB, send dummy values for testing')
    parser.add_argument('--ws', action='store_true', help='Use websockets for Scratch 3.0')
    parser.add_argument('--ssl', action='store_true', help='Use secure websockets (WSS)')

    args = parser.parse_args(argv)
    logger.setLevel(max(logging.INFO - 10 * (args.verbose - args.quiet), logging.DEBUG))
    logger.addHandler(logging.StreamHandler(sys.stdout))


    global no_plot
    global plt
    no_plot = args.noplot
    if no_plot:
        plt = None

    global no_scratch
    no_scratch = args.noscratch

    global no_usb
    if usb is None:
        no_usb = True
    else:
        no_usb = args.nousb

    if args.host is not None:
        host = args.host
    if args.port is not None:
        port = args.port


    global thread
    global threadws
    thread = threading.Thread(target=connect, args=(args.ws,))
    thread.start()
    if args.ws:
        threadws = threading.Thread(target=connectToScratchWS, args=(args.ssl,))
        threadws.start()
    if not no_plot:
        plot()

    while True:
        thread.join(5)
        if not thread.is_alive():
            if not threadws is None and threadws.is_alive():
                logger.info('Stopping websockets thread')
                should_exit = True
                # threadws.join()
            thread = None
            break

def signal_handler(signal, frame):
    logger.error("Process interupted (SIGINT): exit")
    global should_exit
    should_exit = True
    if stopws is not None:
        # TODO: does not work
        stopws.set_result(True)
        stopws.cancel()
    # sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    sys.exit(main())

