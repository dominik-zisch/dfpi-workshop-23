#!/usr/bin/python

import sys
import signal
import os
import argparse
import cv2
import imutils
import time
import math
import csv
import yaml
from collections import deque
from imutils.video import VideoStream
import numpy as np
import paho.mqtt.client as mqtt
import uuid

from utils import *


# ===========================================================================//
# -----------------------------------------------------------// Argument Parser

def parse_arguments():
    parser = argparse.ArgumentParser(description='Object tracking with optional video input.')
    parser.add_argument('-v', '--video', help='Path to the video file (optional).', default=None)
    return parser.parse_args()

# ===========================================================================//
# -------------------------------------------------------------------// Globals

running = True
mouseX = 0
mouseY = 0
unique_id = str(uuid.uuid4())
is_setting_exclusion = False # Flag to check if we are setting exclusion zone
is_dragging = False
selected_point_index = -1
video_playing = True

config = read_config("config.yaml")
video_source = config['video-source']
lower_hsv = np.array(config['HSV-values']['lower-hsv'])
upper_hsv = np.array(config['HSV-values']['upper-hsv'])
show_mask = config['show-mask']
frame_width = config['frame-width']
diameter_bounds = tuple(config['diameter-bounds'])
moving_average_strength = config['moving-average-strength']
broker_address = config['broker-address']
username = config['username']
password = config['password']
topic_prefix = config['topic-prefix']

config_internal = read_config("config_internal.yaml")
fixed_point = tuple(config_internal['fixed-point'])
points_list = config_internal['exclusion-zone']
exclusion_points = [(points_list[i], points_list[i+1]) for i in range(0, len(points_list), 2)]



# ===========================================================================//
# ------------------------------------------------------------// 

# -----------------------------------------/
# ---/ 
def get_closest_point(points, x, y, threshold=10):
    for i, point in enumerate(points):
        if math.sqrt((point[0] - x) ** 2 + (point[1] - y) ** 2) < threshold:
            return i
    return -1

# -----------------------------------------/
# ---/ Mouse Callback
def mouse_callback(event, x, y, flags, param):
    global mouseX, mouseY, is_dragging, selected_point_index, exclusion_points

    mouseX,mouseY = x,y

    if is_setting_exclusion:

        if event == cv2.EVENT_LBUTTONDOWN:
            closest_point_index = get_closest_point(exclusion_points, x, y)
            if closest_point_index == -1:
                exclusion_points.append((x, y))
        
        if event == cv2.EVENT_RBUTTONDOWN:
            closest_point_index = get_closest_point(exclusion_points, x, y)
            if closest_point_index != -1:
                selected_point_index = closest_point_index
                is_dragging = True
        
        elif event == cv2.EVENT_RBUTTONUP:
            is_dragging = False
            selected_point_index = -1
        
        if event == cv2.EVENT_MOUSEMOVE:
            if is_dragging and selected_point_index != -1:
                exclusion_points[selected_point_index] = (x, y)
        


# ===========================================================================//
# ----------------------------------------------------------------------// MQTT

# -----------------------------------------/
# ---/ MQTT On Connect Callback
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with result code " + str(rc))
    client.subscribe(f"{topic_prefix}/record")

# -----------------------------------------/
# ---/ MQTT On Disconnect Callback
def on_disconnect(client, userdata, rc):
    print("Disconnected from MQTT Broker with result code " + str(rc))

# -----------------------------------------/
# ---/ MQTT On Message Callback
def on_message(client, userdata, msg):
    global is_recording
    message = msg.payload.decode()
    msg_id, command = message.split('|', 1)

    # Ignore if the message is from this script
    if msg_id == unique_id:
        return
    
    if command == "START_RECORDING" and not is_recording:
        start_recording()
    elif command == "STOP_RECORDING" and is_recording:
        stop_recording()



# ===========================================================================//
# -----------------------------------------------------------------// Recording

# -----------------------------------------/
# ---/ Start recording function
def start_recording():
    global is_recording, csv_file, csv_writer, recording_start_time, recording_count
    if not is_recording:
        is_recording = True
        while os.path.exists(get_unique_filename('angles', recording_count)):
            recording_count += 1
        csv_file = open(get_unique_filename('angles', recording_count), 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Time', 'Pos X', 'Pos Y', 'Diameter', 'Angle_X', 'Angle_Y'])
        recording_start_time = time.time()
        
# -----------------------------------------/
# ---/ Stop recording function
def stop_recording():
    global is_recording, csv_file, csv_writer
    if is_recording:
        is_recording = False
        if csv_file:
            csv_file.close()
            csv_file = None
            csv_writer = None







# ===========================================================================//
# --------------------------------------------------------// Main program logic

if __name__ == '__main__':

    args = parse_arguments()
    video_path = args.video

    # Initialize MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(username, password)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message
    mqtt_client.connect(broker_address, 1883, 60)
    mqtt_client.loop_start()

    # Initialize VideoStream or VideoCapture
    # if video_path is not None:
    #     vs = cv2.VideoCapture(video_path)
    # else:
    #     vs = VideoStream(src=video_source).start()
    if video_path is not None:
        vs = cv2.VideoCapture(video_path)
        fps = vs.get(cv2.CAP_PROP_FPS)
    else:
        vs = VideoStream(src=video_source).start()
        fps = 30  # Assume a standard FPS for a webcam if not using a video file

    frame_delay = int(1000 / fps)

    # Set the mouse callback function for the window
    cv2.namedWindow("Frame")
    cv2.setMouseCallback("Frame", mouse_callback)

    # allow the camera or video file to warm up
    time.sleep(2.0)

    # Initialise the output variables
    pos_x = 0
    pos_y = 0
    diameter = 0
    angle_x = 0
    angle_y = 0

    # Initialise the average variables
    pos_x_avg = 0
    pos_y_avg = 0
    diameter_avg = 0
    angle_x_avg = 0
    angle_y_avg = 0

    last_recorded_time = time.time()

    # Initialize recording variables
    is_recording = False
    recording_start_time = None
    csv_file = None
    csv_writer = None
    recording_count = 0

    # Create the shortcuts image
    shortcuts_image = create_shortcuts_image()
    cv2.namedWindow("Shortcuts")

    # Main loop
    while (running):
        
        # Record the current time
        current_time = time.time()

        # grab the current frame
        if video_path is not None:
            if video_playing:
                ret, new_frame = vs.read()
                if not ret:
                    break  # End of video file
        else:
            new_frame = vs.read()
        
        frame = new_frame.copy()
        frame = imutils.resize(frame, width=frame_width)

        # if we are viewing a video and we did not grab a frame,
        # then we have reached the end of the video
        if frame is None:
            break

        if video_playing:

            # resize the frame, blur it, and convert it to the HSV
            # color space
            blurred = cv2.GaussianBlur(frame, (11, 11), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            # construct a mask for the color "green", then perform
            # a series of dilations and erosions to remove any small
            # blobs left in the mask
            mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)

            # Create and apply the exclusion mask
            exclusion_mask = create_exclusion_mask(mask, exclusion_points)
            mask = cv2.bitwise_and(mask, mask, mask=cv2.bitwise_not(exclusion_mask))

            # find contours in the mask and initialize the current
            # (x, y) center of the ball
            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            center = None

            # only proceed if at least one contour was found
            if len(cnts) > 0:
                # find the largest contour in the mask, then use
                # it to compute the minimum enclosing circle and
                # centroid
                c = max(cnts, key=cv2.contourArea)
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            # Draw a line from the fixed point to the center of the ball
            if center is not None:

                pos_x = center[0]
                pos_y = center[1]

                # Calculate the angle
                angle_x = calculate_angle(fixed_point, center)
                diameter = radius * 2
                # normalise diameter to be between -90 and +90
                angle_y = (diameter - diameter_bounds[0]) / (diameter_bounds[1] - diameter_bounds[0]) * 180 - 90

                pos_x_avg = pos_x_avg * (moving_average_strength - 1) / moving_average_strength + pos_x / moving_average_strength
                pos_y_avg = pos_y_avg * (moving_average_strength - 1) / moving_average_strength + pos_y / moving_average_strength
                diameter_avg = diameter_avg * (moving_average_strength - 1) / moving_average_strength + diameter / moving_average_strength
                angle_x_avg = angle_x_avg * (moving_average_strength - 1) / moving_average_strength + angle_x / moving_average_strength
                angle_y_avg = angle_y_avg * (moving_average_strength - 1) / moving_average_strength + angle_y / moving_average_strength

        # cv2.imshow("Mask", mask)
        # key = cv2.waitKey(1) & 0xFF
        key = cv2.waitKey(frame_delay) & 0xFF

        # Handle space to pause video
        if key == ord(" "):
            if not is_recording:
                video_playing = not video_playing

        # Handle 'e' key for starting to set exclusion zone
        if key == ord("e"):
            is_setting_exclusion = True
            exclusion_points = []  # Reset exclusion points
            print("Setting exclusion zone...")

        # Handle delete key and backspace key for deleting last exclusion point
        if key == 127 or key == 40:
            if is_setting_exclusion:
                if len(exclusion_points) > 0:
                    closest_point_index = get_closest_point(exclusion_points, mouseX, mouseY)
                    if closest_point_index != -1:
                        del exclusion_points[closest_point_index]

        # Handle 'ESC' key for exiting exclusion zone setting
        if key == 27:  # ESC key
            if is_setting_exclusion:
                is_setting_exclusion = False
                print("Exclusion zone set: " + str(exclusion_points))
                save_exclusion_points_to_config("config_internal.yaml", exclusion_points)

        # record new fixed_point position when pressing 'p'
        if key == ord("p"):
            fixed_point = (mouseX, mouseY)
            save_fixed_point_to_config("config_internal.yaml", fixed_point)

        # Toggle recording with 'r' key
        if key == ord("r"):
            if video_playing:
                if is_recording:
                    mqtt_client.publish(f"{topic_prefix}/record", unique_id + "|STOP_RECORDING")
                    print(f"publishing {unique_id}|STOP_RECORDING to {topic_prefix}/record")
                    stop_recording()
                else:
                    mqtt_client.publish(f"{topic_prefix}/record", unique_id + "|START_RECORDING")
                    print(f"publishing {unique_id}|START_RECORDING to {topic_prefix}/record")
                    start_recording()

        # Record data if recording is active
        if is_recording and csv_writer and current_time - last_recorded_time >= 0.1:
            elapsed_time = current_time - recording_start_time
            csv_writer.writerow([elapsed_time, pos_x, pos_y, diameter, angle_x, angle_y])
            last_recorded_time = current_time

        if is_recording and csv_writer:
            # Draw recording indicator
            cv2.circle(frame, (500, 20), 10, (0, 0, 255), -1)
            cv2.putText(frame, f"{elapsed_time:.2f}s", (520, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # draw circle
        circle_pos = (int(pos_x_avg), int(pos_y_avg))
        cv2.line(frame, fixed_point, circle_pos, (0, 255, 0), 2)
        cv2.circle(frame, circle_pos, int(diameter_avg/2), (0, 255, 255), 2)
        cv2.circle(frame, circle_pos, 5, (0, 0, 255), -1)

        # Display the X, Y coordinates and the diameter
        cv2.putText(frame, f"Angle: {angle_x:.2f} degrees", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Diameter: {diameter:.2f} degrees", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Angle: {angle_y:.2f} degrees", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Draw exclusion zone if points are available
        if exclusion_points:
            draw_exclusion_zone(frame, exclusion_points)

        # show the frame to our screen
        cv2.imshow("Frame", frame)
        if show_mask:
            cv2.imshow("Mask", mask)
        cv2.imshow("Shortcuts", shortcuts_image)

        # if the 'q' key is pressed, stop the loop
        if key == ord("q"):
            if is_recording and csv_file:
                # Close the CSV file if recording
                stop_recording()
            break

    # if we are not using a video file, stop the camera video stream
    if video_path is not None:
        vs.release()
    else:
        vs.stream.release()

    # close all windows
    cv2.destroyAllWindows()

    # Disconnect MQTT client before closing
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

    print('Closing program!')
    sys.exit(0)
