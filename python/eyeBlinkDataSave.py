#!/usr/bin/env python
#
#  read_save_aduino_data
#  Text
#  ----------------------------------
#  Developed with embedXcode
#
#  Project  eye-Blink_Conditioning
#  Created by   Kambadur Ananthamurthy on 04/08/15
#  Copyright    2015 Kambadur Ananthamurthy
#  License  <#license#>
#

""" Flow

0. Connect to a serial port, given or search.
1. Ask user for 3 inputs:
    mouse-number : int
    session-type : int (0, 1, or 2)
    session-number : any positive integer.

2. Wait till user press start on board.
3. Dump data into given outfile (generated using mouse-number
, session-type and session-number).

"""

from __future__ import print_function

import os
import sys
import time
import serial
from collections import defaultdict
import datetime
import warnings
import argparse
import re

import logging
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M',
    filename='eye_blink.log',
    filemode='w')

# Global argument.
args_ = {}

class ExpState():

    def __init__(self):
        self.mouseName = None
        self.session = []
        self.sessionNo = None
        self.state = None
        self.trialNo = None
    
    def current_state(self):
        """get the current state"""
        if self.mouseName and self.session:
            self.state = "WAITING_FOR_DATA"
        elif self.mouseName:
            self.state = "WAITING_FOR_SESSION_INFO"
        else:
            self.state = "WAITING_FOR_MOUSE_INFO"
        return self.state

exp_ = ExpState()

# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
_logger = logging.getLogger('')
_logger.addHandler(console)

DATA_BEGIN_MARKER = "["
DATA_END_MARKER = "]"
COMMENT_MARKER = "#"
TRIAL_DATA_MARKER = "@"
PROFILING_DATA_MARKER = "$"
START_OF_SESSION_MARKER = "<"
END_OF_SESSION_MARKER = ">"

def inform_user(msg):
    info = None
    if type(msg) == list:
        info = "[INFO] %s" % "\n\t|-".join(msg)
    else:
        info = "[INFO] %s" % msg
    print(info)


def get_default_ports():
    import platform
    pName = platform.system()
    if 'Linux' in pName:
        ports = [ "/dev/ttyACM%s" % x for x in range(5) ]
    else:
        print("[WARN] Not implemented for os type: %s" % pName)
        print("[INFO] Kindly pass the port path using --port option")
        quit()
    return ports

def getSerialPort(portPath, baudRate = 9600, timeout = 1):
    """If portPath is given, connet to it. Else try few default ports"""
    ports = [ ]
    if not portPath:
        ports = get_default_ports()
    else:
        ports = [ portPath ]

    serialPort = None
    for i, p in enumerate(ports):
        print("[INFO] Trying to connect to %s" % ports[i])
        try:
            serialPort = serial.Serial(ports[i], baudRate, timeout =0.5)
            break
        except Exception as e:
            if "resource busy" in e.message:
                inform_user(["Port %s is read by some other process" % ports[i]
                    , "Close it and try again."])
            else:
                pass

    if not serialPort:
        print("[ERROR] I could not connect. Tried: %s" % ports)
        quit()

    print("[INFO] Connected to %s" % serialPort)
    return serialPort

def writeTrialData(serialPort, saveDirec, trialsDict = {}):
    runningTrial, csType = serialPort.readline().split()
    while serialPort.readline() != DATA_BEGIN_MARKER:
        continue

    while True:
        line = serialPort.readline()
        if line is DATA_END_MARKER:
            break
        else:
            timeStamp, blinkValue = line.split()
            trialsDict[runningTrial].append((timeStamp, blinkValue))

    outfile = os.path.join(saveDirec, "Trial" + runningTrial + ".csv")
    print("[INFO] Writing to %s" % outfile)
    with open(outfile, 'w') as f:
        f.writeline("# 3rd row values are trial index, cs type.")
        f.writeline("# Actual trial data starts from row 4")
        line = runningTrial + "," + csType
        f.writeline(line)
        data = [ timeStamp + "," + blinkValue
                for (timeStamp, blinkValue) in trialsDict[runningTrial]]
        f.write("\n".join(trialsDict[runningTrial]))
        print("++ Wrote %s, %s" % (line, data))


def writeProfilingData(serialPort, saveDirec, profilingDict = {}):
    while serialPort.readline() != DATA_BEGIN_MARKER:
        continue
    while True:
        line = serialPort.readline()
        print("Line is: %s" % line)
        if line is DATA_END_MARKER:
            break
        else:
            bin, counts = line.split()
            profilingDict[bin] = counts

    with open(os.path.join(saveDirec, "profilingData.csv"), 'w') as f:
        data = profilingDict.items()
        data = [bin + "," + count for (bin, count) in data]
        f.write("\n".join(data))

def writeData(serialPort, saveDirec, trialsDict, profilingDict):
    operationMap = { TRIAL_DATA_MARKER : lambda port, direc: writeTrialData(port, direc, trialsDict)
        , PROFILING_DATA_MARKER : lambda port, direc: writeProfilingData(port, direc, profilingDict)
        }
    print("A")
    print("AA: %s" % serialPort.readline())
    arduinoData = serialPort.readline()
    while not arduinoData.strip():
        print("[WARN] Nothing is read from serial port. Waiting for data ... ")
        time.sleep(0.1)
        arduinoData = serialPort.readline()

    # FIXME: Don't know what it does.
    #while serialPort.readline() != START_OF_SESSION_MARKER:
    #    continue

    while True:
        arduinoData = serialPort.readline()
        print("C: %s" % arduinoData)
        if END_OF_SESSION_MARKER == arduinoData:
            return
        elif arduinoData.startswith(COMMENT_MARKER):
            print("[DEBUG] Inside writeData: %s" % arduinoData)
            operationMap[arduinoData](serialPort, saveDirec)
        else:
            print("B %s" % arduinoData)

def process_data(port, **kwargs):
    global args_
    global exp_
    while True:
        line = port.readline().strip()
        if not line:
            continue
        mousePat = re.compile(r'Mouse(?P<name>\w\d)')
        sesPat = re.compile(r'Session(?P<sno>\d+)\:\s*(?P<stype>(Cntrl|Delay|Trace))')
        if exp_.current_state() == "WAITING_FOR_MOUSE_INFO":
            m = mousePat.search(line)
            if m:
                exp_.mouseName = m.group('name')
                inform_user("Got mouse : %s" % exp_.mouseName)
        elif exp_.current_state() == "WAITING_FOR_SESSION_INFO":
            m = sesPat.search(line)
            if m:
                exp_.session = [m.group('sno'), m.group('stype')]
                inform_user("Session: %s" % exp_.session)
        elif exp_.current_state() == "WAITING_FOR_DATA":
            print(line)
        else:
            print("[TODO] Fix me here")



def write_data( serial_port):
    """Main function responsible for writing data.
    """
    global args__
    line = serial_port.readline()
    userInformed = False
    while True:
        line = serial_port.readline()
        if not line.strip():
            if not userInformed:
                userInformed = True
                msg = ["Waiting for trial to start.", "Press SELECT on board" ]
                inform_user(msg)
            else:
                print(".", end='')
                sys.stdout.flush()
        else:
            process_data(serial_port)

def init_storage():
    """
    Initialize the data-directory
    """
    global args_
    inform_user([ "Initializing storage " ])
    outdir = args_.get('outdir', os.getcwd())
    stamp = datetime.datetime.now().strftime("%Y%m%d")
    dataDir = os.path.join(outdir, stamp)
    if not os.path.isdir(dataDir):
        _logger.info("Creating directory %s" % dataDir)
        os.makedirs(dataDir)
    else:
        inform_user("Directory %s already exists. Using it" % dataDir)
    args_['data_dir'] = dataDir

def main():
    global args_
    init_storage()
    serialPort = getSerialPort( args_['port'] )
    try:
        write_data(serialPort)
    except KeyboardInterrupt as e:
        print("Recieved interrupt from keyboard. Closing port")
        serialPort.close()

if __name__ == "__main__":
    import argparse
    # Argument parser.
    description = '''Eye blink behaviour'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--port', '-p'
        , required = False
        , help = 'Name of the serial port'
        )
    parser.add_argument('--outdir', '-d'
        , required = False
        , default = os.getcwd()
        , help = 'Path to directory for storing data, default = pwd'
        )
    parser.add_argument('--name', '-n'
        , required = True
        , type = int
        , help = 'Mouse index/name. Type int.'
        )
    parser.add_argument('--session_type', '-st'
        , required = True
        , type = int
        , help = 'Session type. 0, 1 or 2'
        )
    parser.add_argument('--session_no', '-sn'
        , required = True
        , type = int
        , help = 'Session no.'
        )
    class Args: pass 
    args = Args()
    parser.parse_args(namespace=args)
    args_ = vars(args)
    main()

