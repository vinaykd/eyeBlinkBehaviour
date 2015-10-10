"""process_video_for_eye_blink.py: 

    Detects eye blink in video

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import cv2
import numpy as np
import sys

def process_frame(frame):
    print frame.shape
    return frame.shape, frame


def process_video(video_file_name, args):
    cap = cv2.VideoCapture(video_file_name)
    while(cap.isOpened()):
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        nRows, nCols = gray.shape
        if args.get('bbox'):
            x0, y0, w, h = args['bbox']
            gray = gray[y0:y0+h,x0:x0+w]
        res, retFrame = process_frame(gray)
        cv2.imshow('frame', retFrame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

def main(args):
    fileName = args['video_file']
    process_video(fileName, args)

if __name__ == '__main__':
    import argparse
    # Argument parser.
    description = '''description'''
    parser = argparse.ArgumentParser(description=description)
    class Args: pass 
    args = Args()
    parser.add_argument('--video-file', '-f'
        , required = True
        , help = 'Path of the video file'
        )
    parser.add_argument('--bbox', '-b'
        , required = False
        , nargs = '+'
        , type = int
        , help = 'Bounding box : topx topy width height'
        )
    parser.parse_args(namespace=args)
    main(vars(args))

