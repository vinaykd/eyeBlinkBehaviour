"""thresholding_eyeblink_data.py: 

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import sys
import numpy as np
import pylab
import os
from collections import defaultdict

result_ = defaultdict(list)
pretoneN_ = 500
blinkResponseInterval_ = pretoneN_ + 60


def get_status(i, filename, dirname):
    statusFile = os.path.join(dirname, "Trial%s.csv" % (i+1))
    status = None
    with open(statusFile, "r") as f:
        thirdLine = f.read().split("\n")[2]
        status = int(thirdLine.split(",")[1].strip())
    return status


def process(filename, dirname):
    data = np.loadtxt(filename, delimiter=',')
    global result_
    for i, d in enumerate(data[:,:]):
        status = get_status(i, filename, dirname)
        if status == 1:
            result_['session_type'].append("CS_PLUS")
        else:
            result_['session_type'].append("CS_MINUS")

        pretoneData = d[:pretoneN_]
        mean, std = np.mean(pretoneData), np.std(pretoneData)
        threshold = mean + 2*std
        crData = d[pretoneN_:blinkResponseInterval_]
        if crData.max() >= threshold:
            result_['blink'].append(1)
        else:
            result_['blink'].append(0)
    print result_['blink']
    pylab.plot(result_['blink'], 'o')
    pylab.ylim(-0.1, 1.1)
    pylab.title("Blink in Blink Response Interval. 1 : Present, 0 : Absent")
    pylab.show()

def main():
    filename = sys.argv[1]
    dirpath = sys.argv[2]
    process(filename, dirpath)

if __name__ == '__main__':
    main()
