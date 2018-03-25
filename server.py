import socket
import struct
import numpy as np
import json

from time import sleep, ctime
import time
import threading, os, sys
from struct import *

UDP_IP_ADDRESS = "127.0.0.1"
UDP_PORT_NO = 6789

def initialize_socket():
    serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSock.bind((UDP_IP_ADDRESS, UDP_PORT_NO))
    return serverSock
def new_writerthread_withpipe(sensor_id ):
    new_r, new_w = os.pipe() #create new new_pipe
    new_w = os.fdopen(new_w,'w',0) #make file object
    new_thread = threading.Thread(
    target = writer, args=(sensor_id, new_r)) #create new thread
    new_thread.setDaemon(True)
    new_thread.start()
    return new_w
def writer(sensor_id, readpipe):
    time.sleep(0.5)
    print "Sensor_id:", sensor_id, "created."
    r = os.fdopen(readpipe,'r',0)
    while True:
        message = r.readline().rstrip('\n')
        print 'sensor_id:', sensor_id, "| message:", message
        filename = sensor_id + '.txt'
        file_write(filename, message)
    print "Sensor_id:", sensor_id, "exited."
def file_write(filename, message):
    f = open(filename, 'a')
    f.write(message)
    f.write('\n')
    f.close()
def get_pack_format(length):
    length = (length-1)/3
    pack_format = 'H' * length + 'B' * (length+1)
    return pack_format
def unsort_data(sorted_data):
    unsorted_data = [sorted_data[-1]]
    offset = len(sorted_data)/2
    for i in range(offset):
        unsorted_data.append(sorted_data[offset+i])
        unsorted_data.append(sorted_data[i])
    return unsorted_data
def int16_to_float(data, (minval, maxval)):
    data = float(data) / 2**16 * (maxval-minval) + minval
    return data
def int16_to_float_list(sorted_data, boundaries):
    offset = len(sorted_data)/2
    for i in range(offset):
        if sorted_data[i + offset] != 2:
            sorted_data[i] = int16_to_float(
            sorted_data[i], boundaries[sorted_data[i+offset]] )
    return sorted_data
def decode_data(packed_data, boundaries):
    pack_format = get_pack_format(len(packed_data))
    unpacked_data = list(unpack(pack_format, packed_data))
    received_data = int16_to_float_list(unpacked_data, boundaries)
    unsorted_data = unsort_data(received_data)
    return unsorted_data
def get_boundaries(parameters):
    boundaries = {}
    for i in range(1, len(parameters), 2):
        boundaries[parameters[i]] = parameters[i+1]
    return boundaries
def csvdata(data):
    message = ""
    for i in data[1:]:
        message = message + str(i) + ','
    return message.rstrip(',')

def main():
    sensor_ids = {} #sensor_id:write_pipe dictionary
    serverSock = initialize_socket()
    sensor_id_boundaries = {}
    sensor_id_writepipe = {}
    while True:
        data = serverSock.recvfrom(1024)[0]
        if len(data) > 20: #it is a first time sensor
            parameters = json.loads(data)
            boundaries = get_boundaries(parameters)
            sensor_id = parameters[0]
            if sensor_id in sensor_id_boundaries:
                pass
            else:
                print "New Sensor! ID:", sensor_id
                sensor_id_boundaries[sensor_id] = boundaries
                sensor_id_writepipe[sensor_id] = new_writerthread_withpipe(str(sensor_id))
            print sensor_id_boundaries
        else:
            unpack_format = len(data) * 'B'
            parse_id = unpack(unpack_format, data)
            sensor_id = parse_id[-1]
            message = decode_data(data, sensor_id_boundaries[sensor_id])
            print message
            message = csvdata(message)
            print message
            print >>sensor_id_writepipe[sensor_id], message



if __name__ == '__main__':
    main()
