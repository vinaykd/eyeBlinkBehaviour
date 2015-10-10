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
import time

def get_ellipse(cnts):
    ellipses = []
    for cnt in cnts[0]:
        try:
            e = cv2.fitEllipse(cnt)
            ellipses.append(e)
        except: pass
    return ellipses

def merge_contours(cnts, img):
    """Merge these contours together. And create an image"""
    for c in cnts:
        hull = cv2.convexHull(c)
        cv2.fillConvexPoly(img, hull, 0)
    return img

def process_frame(frame):
    # Find edge in frame
    edges = cv2.Canny(frame, 50, 250)
    cnts = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cntImg = np.ones(frame.shape)
    merge_contours(cnts[0], cntImg)

    # cool, find the contour again and convert again. Sum up their area.
    im = np.array((1-cntImg) * 255, dtype = np.uint8)
    cnts = cv2.findContours(im, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    hullImg = np.ones(frame.shape)
    for c in cnts[0]:
        c = cv2.convexHull(c)
        cv2.fillConvexPoly(hullImg, c, 0, 8)

    hullImg = np.array((1-hullImg) * 255, dtype = np.uint8)
    return frame, hullImg


def process_video(video_file_name, outFile = None,  args = {}):
    cap = cv2.VideoCapture(video_file_name)
    out = None
    if outFile:
        print("Trying to write %s" % outFile)
        out = cv2.VideoWriter(outFile, -1, 15, (640,480))
    while(cap.isOpened()):
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        nRows, nCols = gray.shape
        if args.get('bbox'):
            x0, y0, w, h = args['bbox']
            gray = gray[y0:y0+h,x0:x0+w]
        infile, outfile = process_frame(gray)
        result = np.concatenate((infile, outfile), axis=1)
        cv2.imshow('Eye-Blink', result)
        if out: 
            out.write(result)

        # This continue till one presses q.
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        #k = cv2.waitKey(0)
        #if k==27:    # Esc key to stop
        #    break
        #elif k==-1:  # normally -1 returned,so don't print it
        #    continue
        #else:
        #    print k # else print its value

    if outFile:
        out.release()
    cap.release()
    cv2.destroyAllWindows()

def main(args):
    fileName = args['video_file']
    out = '%s_output.avi' % fileName
    process_video(fileName, outFile = out, args = args)

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

