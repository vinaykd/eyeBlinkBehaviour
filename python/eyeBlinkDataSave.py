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
import datetime
import argparse
import re

# Global argument.
args_ = {}

class ExpState():

    def __init__(self):
        self.states = {}
        self.params = {}
        self.state = 1

    def get_state(self):
        if self.state >= 0 and self.state < 10:
            return "WAITING_FOR_MOUSE_INFO"
        elif self.state >= 10 and self.state < 20:
            return "WAITING_FOR_SESSION_INFO"
        elif self.state >= 20 and self.state < 30:
            return "WAITING_FOR_TRIAL_START"
        elif self.state >= 30 and self.state < 40:
            return "WAITING_FOR_TRIAL_END"
        elif self.state >= 40 and self.state < 50:
            return "START_WRITE_TRIAL_FILE"
        else:
            return "UNKNOWN_STATE"

    def __str__(self):
        return "%s" % self.get_state()

    def update_state(self, line):
        global args_
        if self.get_state() == "WAITING_FOR_MOUSE_INFO":
            mousePat = re.compile(r'Mouse(?P<name>\w\d)')
            m = mousePat.search(line)
            if m:
                self.params['mouse_name'] = m.group('name')
                print("")
                inform_user("Got mouse : %s" % self.params['mouse_name'])
                self.state = 10
                return None
            else:
                print('.', end='')
                sys.stdout.flush()

        if self.get_state() == "WAITING_FOR_SESSION_INFO":
            sesPat = re.compile(
                    r'Session(?P<sno>\d+)\:\s*(?P<stype>(Cntrl|Delay|Trace))'
                    )
            m = sesPat.search(line)
            if m:
                self.params['session'] = [m.group('sno'), m.group('stype')]
                inform_user("Session: %s" % self.params['session'])
                self.state = 20
                return None

        if self.get_state() == "WAITING_FOR_TRIAL_START":
            dataPat = re.compile(
                    r'^\@Trial\s*No\.\s*(?P<tn>\d+)\s*\:\s*(?P<tt>(CS+|CS-))'
                    )
            m = dataPat.search(line)
            if m:
                inform_user("Trial: %s starts .." % m.group(0))
                self.params['trial'] = [ m.group('tn'), m.group('tt') ]
                self.params['trial_file'] = os.path.join(
                        args_['data_dir']
                        , "Trial" + "_".join(self.params['trial']) + ".csv"
                        )
                self.write_to_trial_file("timestamp,data")
                self.state = 30
            return None

        if self.get_state() == "WAITING_FOR_TRIAL_END":
            endPat = re.compile(r'Blink\s*Count\s*=\s*(?P<num>\d+)')
            m = endPat.search(line)
            if m:
                inform_user("Trial Ends. Total blinks: %s" % m.group('num'))
                inform_user("Wrote trial file: %s" % self.params['trial_file'])
                self.state = 20
            else:
                # In lieu of current line, add a header to csv file. We need
                # to write all data starting next line on. We achieve this
                # by setting the sate value after writing this line.
                self.write_to_trial_file(line)
        return None

    def write_to_trial_file(self, line):
        global args_
        if not line.strip():
            return
        with open(self.params['trial_file'], "a") as f:
            f.write("%s\n" % line)
            print('+', end='')
            sys.stdout.flush()

    def insert_line(self, line):
        self.update_state(line)

exp_ = ExpState()

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

def get_serial_port(portPath, baudRate = 9600, timeout = 1):
    """If portPath is given, connet to it. Else try few default ports"""

    import serial.tools.list_ports as lp
    if not portPath:
        ports = sorted([ x for x, y, z in lp.comports() ])
    else:
        ports = [ portPath ]

    serialPort = None
    for i, p in enumerate(ports):
        print("[INFO] Trying to connect to %s" % ports[i])
        try:
            serialPort = serial.Serial(ports[i], baudRate, timeout=1)
            break
        except Exception as e:
            if "resource busy" in e.message:
                inform_user(["Port %s is read by some other process" % ports[i]
                    , "Close it and try again."])
            else:
                pass

    if serialPort is None:
        print("[ERROR] I could not connect. Tried: %s" % ports)
        quit()

    print("[INFO] Connected to %s" % serialPort)
    return serialPort

def process_data(port, **kwargs):
    global args_, exp_
    while True:
        line = port.readline().strip()
        write_raw_data(line)
        exp_.insert_line(line)

def write_data( serial_port):
    """Main function responsible for writing data.
    """
    global args__
    userInformed = False
    while True:
        line = serial_port.readline()
        write_raw_data(line)
        if not line.strip():
            if not userInformed:
                userInformed = True
                msg = ["Waiting for trial to start.", "Press SELECT on board" ]
                inform_user(msg)
                break
            else:
                print(".", end='')
                sys.stdout.flush()
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
        inform_user("Creating directory %s" % dataDir)
        os.makedirs(dataDir)
    else:
        inform_user("Directory %s already exists. Using it" % dataDir)
    args_['data_dir'] = dataDir
    # Create a file with stamp.
    args_['raw_data_file'] = os.path.join(dataDir, 'raw_data.txt')
    with open(args_['raw_data_file'], "w") as f:
        f.write("# raw_data: %s\n" % datetime.datetime.now().isoformat())

def write_raw_data(line):
    global args_
    with open(args_['raw_data_file'], "a") as f:
        f.write("%s\n" % line)

def main():
    global args_
    init_storage()
    serialPort = get_serial_port( args_['port'] )
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

