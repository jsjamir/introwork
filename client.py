import argparse
import re
import numpy as np
import binascii
import sys
import socket
import time
import json
from random import *
from struct import *

def arguments():
    argument_debug = 0;
    sensor_id = None;
    temp_float = [None]*2;
    batt_float = [None]*2;
    humid_int = [None]*2;

    "Gets the arguments of the command line statement"
    template_f = re.compile(r'^(\d+(\.\d+)?)(,\d+(\.\d+)?)$') #used for float parsing must must be two comma-separated float values
    template_i = re.compile(r'^(\d+,\d+)$') #used for int parsing must be two comma-separated float values
    parser = argparse.ArgumentParser()
    parser.add_argument("sensor_id", type=int, help="8 bit unique sensor id (0-255)")
    parser.add_argument("-t", "--temp", help="temperature in float. use format -t min,max.")
    parser.add_argument("-u", "--humid", help="temperature in float. use format -t min,max.")
    parser.add_argument("-b", "--batt", help="battery voltage in float. use format -b min,max.")
    args = parser.parse_args()

    sensor_id = args.sensor_id
    temp = args.temp
    batt = args.batt
    humid = args.humid

    if not 0 <= sensor_id <= 255:
        print "ERROR: sensor_id must be INT between 0 and 255"
        quit()

    if temp:
        if not template_f.match(args.temp):
            print "ERROR: temperature must be in FLOAT,FLOAT"
            quit()
        temp_float = [float(x) for x in temp.split(',')]
        if temp_float[0] >= temp_float[1]:
            print "ERROR: temperature first argument should be less than second argument"
            quit()

    if humid:
        if not template_i.match(args.humid):
            print "ERROR: humidity must be in INT,INT"
            quit()
        humid_int = [int(x) for x in humid.split(',')]
        if humid_int[0] >= humid_int[1]:
            print "ERROR: humidity first argument should be less than second argument"
            quit()
        if humid_int[0] < 0 or humid_int[1] > 65535:
            print "ERROR: humidity must be between 0 and 65536"
            quit()

    if batt:
        if not template_f.match(args.batt):
            print "ERROR: battery voltage must be in FLOAT,FLOAT"
            quit()
        batt_float = [float(x) for x in batt.split(',')]
        if batt_float[0] >= batt_float[1]:
            print "ERROR: battery first argument should be less than second argument"
            quit()

    if argument_debug:
        print "sensor_id: %s" % sensor_id
        print "temp_min: %s, temp_max" % temp_float[0], temp_float[1]
        print "humid_min: %s, humid_max" % humid_int[0], humid_int[1]
        print "batt_min: %s, batt_max" % batt_float[0], batt_float[1]

    if temp is not None:
        temp = 1
    if humid is not None:
        humid = 2
    if batt is not None:
        batt = 3
    return [sensor_id, temp, temp_float, humid, humid_int, batt, batt_float]
def remove_none(data):
    for x in (0, 1, 3, 5):
        if data[x] == None:
            data[x] = 0
            data[x+1] = [0, 0]
    return data
def get_random_data(p):
    sensor_id = p[0]
    temp_flag = p[1]
    temp = uniform(p[2][0], p[2][1])
    humid_flag = p[3]
    humid = randrange(p[4][0], p[4][1]+1)
    batt_flag = p[5]
    batt = uniform(p[6][0], p[6][1])
    data = [sensor_id, temp_flag, temp, humid_flag, humid, batt_flag, batt]
    return data
##ENCODING
def float_to_int16(data, (minval, maxval)):
    int16 = float((data - minval)) / (maxval-minval)
    int16 = int16 * 2**16
    return int(int16)
    floor()
def float_to_int16_list(sorted_data, boundaries):
    offset = len(sorted_data)/2
    for i in range(offset):
        if sorted_data[i + offset] != 2:
            sorted_data[i] = float_to_int16(
            sorted_data[i], boundaries[sorted_data[i+offset]] )
    return sorted_data
def sort_data(data):
    sorted_data = []
    for i in range(1, len(data), 2):
        if data[i] != 0:
            sorted_data.append(data[i+1])

    for i in range(1, len(data), 2):
        if data[i] != 0:
            sorted_data.append(data[i])

    sorted_data.append(data[0])
    return sorted_data
def get_pack_format(sort_data):
    length = len(sort_data)/2
    pack_format = 'H' * length + 'B' * (length+1)
    return pack_format
def encode_data(data, boundaries):
    sorted_data = sort_data(data)
    sent_data = float_to_int16_list(sorted_data, boundaries)
    pack_format = get_pack_format(sorted_data)
    packed_data = pack(pack_format, *sent_data)
    return packed_data
def get_boundaries(parameters):
    boundaries = {}
    for i in range(1, len(parameters), 2):
        boundaries[parameters[i]] = parameters[i+1]
    return boundaries

def main():
    parameters = arguments()             #parse command line arguments
    parameters = remove_none(parameters) #convert None to 0
    boundaries = get_boundaries(parameters)
    print "parameters", parameters
    #start of sending
    UDP_IP_ADDRESS = "127.0.0.1"
    UDP_PORT_NO = 6789
    clientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #create socket
    clientSock.sendto(json.dumps(parameters), (UDP_IP_ADDRESS, UDP_PORT_NO))
    print "sent: ", json.dumps(parameters)

    while True:
        time.sleep(2)
        data = get_random_data(parameters)
        encoded_data = encode_data(data, boundaries)
        clientSock.sendto(encoded_data, (UDP_IP_ADDRESS, UDP_PORT_NO))
        print "sent: %s" % encoded_data
        print "data: %s" % data

if __name__ == "__main__":
    main()
