import argparse
import cv2
import numpy as np
from imutils.video import VideoStream

def parse_arguments():
    parser = argparse.ArgumentParser(description='Object tracking with optional video input.')
    parser.add_argument('-v', '--video', help='Path to the video file (optional).', default=None)
    return parser.parse_args()

def nothing(x):
    pass

def read_hsv_values(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        lower_hsv = np.array([int(val) for val in lines[0].strip().split(',')])
        upper_hsv = np.array([int(val) for val in lines[1].strip().split(',')])
        return lower_hsv, upper_hsv


def save_hsv_values(lower_hsv, upper_hsv, file_path="color.txt"):
    with open(file_path, 'w') as file:
        file.write(','.join(map(str, lower_hsv)) + '\n')
        file.write(','.join(map(str, upper_hsv)) + '\n')

# Read HSV values from the file
lower_hsv, upper_hsv = read_hsv_values("color.txt")

args = parse_arguments()
video_path = args.video
video_playing = True

# Initialize the webcam
# cap = cv2.VideoCapture(1)
if video_path is not None:
    vs = cv2.VideoCapture(video_path)
    fps = vs.get(cv2.CAP_PROP_FPS)
else:
    vs = VideoStream(src=1).start()
    fps = 30  # Assume a standard FPS for a webcam if not using a video file

frame_delay = int(1000 / fps)

# Create a window
cv2.namedWindow("HSV Adjustments")

# Create trackbars for color change
cv2.createTrackbar('H L', 'HSV Adjustments', lower_hsv[0], 179, nothing)
cv2.createTrackbar('H U', 'HSV Adjustments', upper_hsv[0], 179, nothing)
cv2.createTrackbar('S L', 'HSV Adjustments', lower_hsv[1], 255, nothing)
cv2.createTrackbar('S U', 'HSV Adjustments', upper_hsv[1], 255, nothing)
cv2.createTrackbar('V L', 'HSV Adjustments', lower_hsv[2], 255, nothing)
cv2.createTrackbar('V U', 'HSV Adjustments', upper_hsv[2], 255, nothing)



while True:
    # Read from the webcam
    if video_path is not None:
        if video_playing:
            ret, frame = vs.read()
            if not ret:
                break  # End of video file
    else:
        frame = vs.read()

    if frame is None:
        break

    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Get values from the trackbars
    h_lower = cv2.getTrackbarPos('H L', 'HSV Adjustments')
    h_upper = cv2.getTrackbarPos('H U', 'HSV Adjustments')
    s_lower = cv2.getTrackbarPos('S L', 'HSV Adjustments')
    s_upper = cv2.getTrackbarPos('S U', 'HSV Adjustments')
    v_lower = cv2.getTrackbarPos('V L', 'HSV Adjustments')
    v_upper = cv2.getTrackbarPos('V U', 'HSV Adjustments')

    # Define range for HSV mask
    lower_hsv = np.array([h_lower, s_lower, v_lower])
    upper_hsv = np.array([h_upper, s_upper, v_upper])

    # Save these values to colour.txt
    save_hsv_values(lower_hsv, upper_hsv)

    # Create the mask
    mask = cv2.inRange(hsv, lower_hsv, upper_hsv)

    # Display the original frame and the mask
    cv2.imshow('Original', frame)
    cv2.imshow('Mask', mask)

    # Break the loop when 'q' is pressed
    key = cv2.waitKey(frame_delay) & 0xFF

    if key == ord("q"):
        break

    if key == ord(" "):
        video_playing = not video_playing

# Release the webcam and destroy all windows
if video_path is not None:
    vs.release()
else:
    vs.stream.release()
cv2.destroyAllWindows()
