#!/usr/bin/env python3

from pathlib import Path
import sys
import cv2
import depthai as dai
import numpy as np
import time
import serial
import math
import random

import pygame
from pygame.locals import *



# pyserial connect to arduino
#serial_port = 'COM4'
serial_port = "/dev/ttyUSB0"
ser = serial.Serial(serial_port, 115200, timeout=0.05, xonxoff = 1, write_timeout = 0.05) # port config  # rtscts= 0






'''
Spatial Tiny-yolo example
  Performs inference on RGB camera and retrieves spatial location coordinates: x,y,z relative to the center of depth map.
  Can be used for tiny-yolo-v3 or tiny-yolo-v4 networks
'''

# Tiny yolo v3/4 label texts
labelMap = [
    "person",         "bicycle",    "car",           "motorbike",     "aeroplane",   "bus",           "train",
    "truck",          "boat",       "traffic light", "fire hydrant",  "stop sign",   "parking meter", "bench",
    "bird",           "cat",        "dog",           "horse",         "sheep",       "cow",           "elephant",
    "bear",           "zebra",      "giraffe",       "backpack",      "umbrella",    "handbag",       "tie",
    "suitcase",       "frisbee",    "skis",          "snowboard",     "sports ball", "kite",          "baseball bat",
    "baseball glove", "skateboard", "surfboard",     "tennis racket", "bottle",      "wine glass",    "cup",
    "fork",           "knife",      "spoon",         "bowl",          "banana",      "apple",         "sandwich",
    "orange",         "broccoli",   "carrot",        "hot dog",       "pizza",       "donut",         "cake",
    "chair",          "sofa",       "pottedplant",   "bed",           "diningtable", "toilet",        "tvmonitor",
    "laptop",         "mouse",      "remote",        "keyboard",      "cell phone",  "microwave",     "oven",
    "toaster",        "sink",       "refrigerator",  "book",          "clock",       "vase",          "scissors",
    "teddy bear",     "hair drier", "toothbrush"

]

syncNN = True

# Get argument first
nnBlobPath = 'tiny-yolo-v4_openvino_2021.2_6shave.blob'


if not Path(nnBlobPath).exists():
    import sys
    raise FileNotFoundError(f'Required file/s not found, please run "{sys.executable} install_requirements.py"')

# Start defining a pipeline
pipeline = dai.Pipeline()

# Define a source - color camera
colorCam = pipeline.createColorCamera()
spatialDetectionNetwork = pipeline.createYoloSpatialDetectionNetwork()
monoLeft = pipeline.createMonoCamera()
monoRight = pipeline.createMonoCamera()
stereo = pipeline.createStereoDepth()

xoutRgb = pipeline.createXLinkOut()
xoutNN = pipeline.createXLinkOut()
xoutBoundingBoxDepthMapping = pipeline.createXLinkOut()
xoutDepth = pipeline.createXLinkOut()

xoutRgb.setStreamName("rgb")
xoutNN.setStreamName("detections")
xoutBoundingBoxDepthMapping.setStreamName("boundingBoxDepthMapping")
xoutDepth.setStreamName("depth")


colorCam.setPreviewSize(416, 416)
colorCam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
colorCam.setInterleaved(False)
colorCam.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)

monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)

# setting node configs
stereo.setOutputDepth(True)
stereo.setConfidenceThreshold(255)

spatialDetectionNetwork.setBlobPath(nnBlobPath)
spatialDetectionNetwork.setConfidenceThreshold(0.5)
spatialDetectionNetwork.input.setBlocking(False)
spatialDetectionNetwork.setBoundingBoxScaleFactor(0.5)
spatialDetectionNetwork.setDepthLowerThreshold(100)
spatialDetectionNetwork.setDepthUpperThreshold(5000)
# Yolo specific parameters
spatialDetectionNetwork.setNumClasses(80)
spatialDetectionNetwork.setCoordinateSize(4)
spatialDetectionNetwork.setAnchors(np.array([10,14, 23,27, 37,58, 81,82, 135,169, 344,319]))
spatialDetectionNetwork.setAnchorMasks({ "side26": np.array([1,2,3]), "side13": np.array([3,4,5]) })
spatialDetectionNetwork.setIouThreshold(0.5)

# Create outputs

monoLeft.out.link(stereo.left)
monoRight.out.link(stereo.right)

colorCam.preview.link(spatialDetectionNetwork.input)
if syncNN:
    spatialDetectionNetwork.passthrough.link(xoutRgb.input)
else:
    colorCam.preview.link(xoutRgb.input)

spatialDetectionNetwork.out.link(xoutNN.input)
spatialDetectionNetwork.boundingBoxMapping.link(xoutBoundingBoxDepthMapping.input)

stereo.depth.link(spatialDetectionNetwork.inputDepth)
spatialDetectionNetwork.passthroughDepth.link(xoutDepth.input)

# Pipeline is defined, now we can connect to the device
with dai.Device(pipeline) as device:
    # Start pipeline
    device.startPipeline()

    # Output queues will be used to get the rgb frames and nn data from the outputs defined above
    previewQueue = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
    detectionNNQueue = device.getOutputQueue(name="detections", maxSize=4, blocking=False)
    xoutBoundingBoxDepthMapping = device.getOutputQueue(name="boundingBoxDepthMapping", maxSize=4, blocking=False)
    depthQueue = device.getOutputQueue(name="depth", maxSize=4, blocking=False)

    frame = None
    detections = []

    startTime = time.monotonic()
    counter = 0
    fps = 0
    color = (255, 255, 255)


    while True:
        inPreview = previewQueue.get()
        inNN = detectionNNQueue.get()
        depth = depthQueue.get()

        counter+=1
        current_time = time.monotonic()
        if (current_time - startTime) > 1 :
            fps = counter / (current_time - startTime)
            counter = 0
            startTime = current_time

        frame = inPreview.getCvFrame()
        depthFrame = depth.getFrame()
        objects = list()


        depthFrameColor = cv2.normalize(depthFrame, None, 255, 0, cv2.NORM_INF, cv2.CV_8UC1)
        depthFrameColor = cv2.equalizeHist(depthFrameColor)
        depthFrameColor = cv2.applyColorMap(depthFrameColor, cv2.COLORMAP_HOT)
        detections = inNN.detections



        h, w = frame.shape[1],frame.shape[0]    
        width_cutoff = w // 2    
        right = frame[:,:width_cutoff]
        left = frame[:,width_cutoff:]
        # h, w = depthFrameColor.shape[1],depthFrameColor.shape[0]        
        # width_cutoff = w // 2    
        # right = depthFrameColor[:,:width_cutoff]
        # left = depthFrameColor[:,width_cutoff:]



        if len(detections) != 0:
            boundingBoxMapping = xoutBoundingBoxDepthMapping.get()
            roiDatas = boundingBoxMapping.getConfigData()

            for roiData in roiDatas:
                roi = roiData.roi
                roi = roi.denormalize(depthFrameColor.shape[1], depthFrameColor.shape[0])
                topLeft = roi.topLeft()
                bottomRight = roi.bottomRight()
                xmin = int(topLeft.x)
                ymin = int(topLeft.y)
                xmax = int(bottomRight.x)
                ymax = int(bottomRight.y)

                cv2.rectangle(depthFrameColor, (xmin, ymin), (xmax, ymax), color, cv2.FONT_HERSHEY_SCRIPT_SIMPLEX)


        # If the frame is available, draw bounding boxes on it and show the frame
        img_h = frame.shape[0]
        img_w  = frame.shape[1]
        for detection in detections:
            # Denormalize bounding box
            x1 = int(detection.xmin * img_w)
            x2 = int(detection.xmax * img_w)
            y1 = int(detection.ymin * img_h)
            y2 = int(detection.ymax * img_h)
            try:
                label = labelMap[detection.label]
            except:
                label = detection.label
            #     cv2.putText(frame, str(label), (x1 + 10, y1 + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            #     cv2.putText(frame, "{:.2f}".format(detection.confidence*100), (x1 + 10, y1 + 35), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            #     cv2.putText(frame, f"X: {int(detection.spatialCoordinates.x)} mm", (x1 + 10, y1 + 50), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            #     cv2.putText(frame, f"Y: {int(detection.spatialCoordinates.y)} mm", (x1 + 10, y1 + 65), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            #     cv2.putText(frame, f"Z: {int(detection.spatialCoordinates.z)} mm", (x1 + 10, y1 + 80), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)

            #     cv2.rectangle(frame, (x1, y1), (x2, y2), color, cv2.FONT_HERSHEY_SIMPLEX)


            # for detection in detections:
            pt1 = int(detection.xmin * img_w), int(detection.ymin * img_h)
            pt2 = int(detection.xmax * img_w), int(detection.ymax * img_h)





            scaled_object = dict(xmin=x1, xmax=x2, ymin=y1, ymax=y2, class_id=label, confidence=detection.confidence, 
                depth_x=detection.spatialCoordinates.x, depth_y=detection.spatialCoordinates.y, depth_z=detection.spatialCoordinates.z)
            objects.append(scaled_object)
            # print(objects) ## can dump to json if


            # distance =  math.trunc(detection.spatialCoordinates.z/10)
            # distance = str(distance)
            # print(distance)


            cv2.rectangle(frame, pt1, pt2, (0, 0, 255), 1)      
            cv2.putText(frame, label,(pt1[0] + 2, pt1[1] + 15),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)     

            x1, y1 = pt1
            x2, y2 = pt2

            pt_t2 = x1, y1 + 40
            cv2.putText(frame, '{:.2f}'.format(detection.confidence*100) + ' %', pt_t2, cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            pt_t5 = x1, y1 + 60
            # cv2.putText(frame, f"object distance : {int(detection.spatialCoordinates.z)} mm ", pt_t5, cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            cv2.putText(frame, f"Z : {int(detection.spatialCoordinates.z/100)} cm ", pt_t5, cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)


            # Distance config
            # print(f"obstacles detected at : { int(detection.spatialCoordinates.z) }" + ' meters ahead')
            # if float(detection.spatialCoordinates.z)  < float(1000):
                # print(f"obstacles detected at : { int(detection.spatialCoordinates.z) }" + ' milimeters ahead')


            #distance normalize
            object_distance = float(detection.spatialCoordinates.z/100)
            # print(int(detection.spatialCoordinates.z/100))


        ser.flush()
        print (ser.readline())

        def forward(ms):
            ser.write(b'1')
            print ('forward')
            time.sleep(ms / 1000.)

        def reverse(ms):
            ser.write(b'2')
            print ('reverse')
            time.sleep(ms / 1000.)


        def right(ms):
            ser.write(b'3')
            print ('right')
            time.sleep(ms / 1000.)


        def left(ms):
            ser.write(b'4')
            print ('left')
            time.sleep(ms / 1000.)


        def forward_right(ms):
            ser.write(b'5')
            print ('forward_right')
            time.sleep(ms / 1000.)

        def forward_left(ms):
            ser.write(b'6')
            print ('forward_left')
            time.sleep(ms / 1000.)

        def reverse_right(ms):
            ser.write(b'7')
            print ('reverse_right')
            time.sleep(ms / 1000.)

        def reverse_left(ms):
            ser.write(b'8')
            print ('reverse_left')
            time.sleep(ms / 1000.)

        def stop():
            ser.write(b'0')

        def pause(ms):
            # print 'pausing...'
            time.sleep(ms / 1000.)



        # Get input from human driver
        send_inst = True
        pygame.init()
        pygame.display.set_mode((200, 100))
        for event in pygame.event.get():
            if event.type == KEYDOWN:                            
                key_input = pygame.key.get_pressed()


                
                # FORWARD
                if key_input[pygame.K_UP]:
                    forward(100)
                elif key_input[pygame.K_RIGHT]:
                    right(50)
                elif key_input[pygame.K_LEFT]:                       
                    left(50)
                # REVERSE; not saving images for this
                elif key_input[pygame.K_DOWN]:
                    reverse(20)

                elif key_input[pygame.K_UP] and key_input[pygame.K_RIGHT]:
                    forward_right(200)

                elif key_input[pygame.K_UP] and key_input[pygame.K_LEFT]:
                    forward_left(200)

                elif key_input[pygame.K_DOWN] and key_input[pygame.K_RIGHT]:
                    reverse_right(200)

                elif key_input[pygame.K_DOWN] and key_input[pygame.K_LEFT]:
                    reverse_left(200)


                elif key_input[pygame.K_x] or key_input[pygame.K_q]:
                    # pause(10)
                    stop()
                    send_inst = False
                    break

            elif event.type == pygame.KEYUP:                           
                stop()

            elif event.type == pygame.QUIT:
                break




        # mutex.release()
        cv2.putText(frame, "NN fps: {:.2f}".format(fps), (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4, color)
        # cv2.imshow("SPY-D depth", depthFrameColor)
        cv2.imshow("SPY-D", frame)


        if cv2.waitKey(1) == ord('q'):
            ser.write(b'0')
            ser.close()
            print("\n\n\n\nE X I T\n\n\n\n")
            break


cv2.destroyAllWindows()            
