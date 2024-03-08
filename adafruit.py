# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple GPS module demonstration.
# Will wait for a fix and print a message every second with the current location
# and other details.
import time
import datetime

# import board
# import busio
import serial

import adafruit_gps

# date tine, serial#
# $PMTK705,AXN_5.1.6_3333_18041700,0005,1616D,1.0*6F
# PMTK705,ReleaseStr,Build_ID,Internal_USE_1,( Internal_USE_2)
# Create a serial connection for the GPS connection using default speed and
# a slightly higher timeout (GPS modules typically update once a second).
# These are the defaults you should use for the GPS FeatherWing.
# For other boards set RX = GPS module TX, and TX = GPS module RX pins.
# uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)

# for a computer, use the pyserial library for uart access
# import serial
uart = serial.Serial("COM4", baudrate=9600, timeout=10)
gps = adafruit_gps.GPS(uart)  # Use UART/pyserial

gps.send_command(b"PMTK104*37")  # DO a COLD stafrt
gps.send_command(b'PMTK314,-1*04')  # Default settings
gps.send_command(b"PMTK605")  # request firmware version
timestamp = time.monotonic()


# gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
# Turn on just minimum info (RMC only, location):
# gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
# Turn off everything:
# gps.send_command(b'PMTK314,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
# Tuen on everything (not all of it is parsed!)
gps.send_command(b'PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0')

# Set update rate to once a second (1hz) which is what you typically want.
gps.send_command(b"PMTK220,1000")
# Or decrease to once every two seconds by doubling the millisecond value.
# Be sure to also increase your UART timeout above!
# gps.send_command(b'PMTK220,2000')
# You can also speed up the rate, but don't go too fast or else you can lose
# data during parsing.  This would be twice a second (2hz, 500ms delay):
# gps.send_command(b'PMTK220,500')

# Main loop runs forever printing data as it comes in
timestamp = time.monotonic()
while True:
    data = gps.read(32)  # read up to 32 bytes
    # print(data)  # this is a bytearray type

    if data is not None:
        # convert bytearray to string
        data_string = "".join([chr(b) for b in data])
        #         time,        serial#,                HW version, FWVersion, SW version
        cur_str = ''
        if "\n" in data_string:
            cur_time = datetime.datetime.now().isoformat()
            # cur_str = cur_time + ",AXN_5.1.6_3333_18041700,0005,FW786786,SW156523,"
        # print(cur_str+data_string, end="")
        for b in data:
            cur_char = chr(b)
            if cur_char == '$':
                cur_time = datetime.datetime.now().isoformat()
                print(cur_time, ",AXN_5.1.6_3333_18041700,0005,FW786786,SW156523,", end="")
            print(cur_char, end="")

    if time.monotonic() - timestamp > 5:
        # every 5 seconds...
        gps.send_command(b"PMTK605")  # request firmware version
        timestamp = time.monotonic()
