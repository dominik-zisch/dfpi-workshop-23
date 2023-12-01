import yaml
import math
import numpy as np
import cv2
from scipy.optimize import curve_fit

# ===========================================================================//
# --------------------------------------------------------------// Config Files

# -----------------------------------------/
# ---/ Read config file
def read_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

# -----------------------------------------/
# ---/ Save fixed point to config file
def save_fixed_point_to_config(file_path, point):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    
    # Update the config with new fixed point
    config['fixed-point'] = list(point)

    # Write the updated config back to the file
    with open(file_path, 'w') as file:
        yaml.dump(config, file)

# -----------------------------------------/
# ---/ Save exclusion points to config file
def save_exclusion_points_to_config(file_path, points):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    
    # convert points to flat list
    points_flat = [item for sublist in points for item in sublist]

    # Update the config with new exclusion points
    config['exclusion-zone'] = points_flat

    # Write the updated config back to the file
    with open(file_path, 'w') as file:
        yaml.dump(config, file)



# ===========================================================================//
# -----------------------------------------------------------------// Recording

# -----------------------------------------/
# ---/ Get unique filename
def get_unique_filename(base_name, count):
    return f"{base_name}_{count}.csv"



# ===========================================================================//
# ----------------------------------------------------------------// Main Logic

# -----------------------------------------/
# ---/ Create exclusion mask
def create_exclusion_mask(frame, exclusion_points):
    mask = np.zeros(frame.shape[:2], dtype="uint8")
    if exclusion_points:
        pts = np.array(exclusion_points, dtype=np.int32)
        cv2.fillPoly(mask, [pts], (255, 255, 255))
    return mask


# -----------------------------------------/
# ---/ Calculate angle between two points
def calculate_angle(p1, p2):
    # Calculate the difference in coordinates
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    # Calculate the angle in radians and then convert to degrees
    radians = math.atan2(-dy, dx)  # Negate dy to adjust for screen coordinate system
    angle = math.degrees(radians)

    # Adjust angle to get the desired format]
    if angle < -90:
        angle = -90
    elif angle < 0:
        angle = 90
    else:
        angle = (-1) * (angle - 90)

    return angle



# ===========================================================================//
# ----------------------------------------------------------------// UI Helpers

# -----------------------------------------/
# ---/ Create shortcuts image
def create_shortcuts_image():
    # Create a blank image
    image = np.zeros((300, 600, 3), dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Define your shortcuts and their descriptions
    shortcuts = {
        "q": "Quit",
        "space": "Play/Pause Video (only for video playback)",
        "e": "Toggle Edit mode",
        "Esc": "Exit Edit mode and save changes",
        "Left mouse click": "Add a point",
        "Right mouse click": "Move a point",
        "del or backspace": "Delete a point",
        "p": "Set Base Position",
        "r": "Start/Stop Recording"
    }

    # Starting Y position
    startY = 30

    # Loop through each shortcut and put text on the image
    for key, description in shortcuts.items():
        cv2.putText(image, f"{key}: {description}", (10, startY), font, 0.5, (255, 255, 255), 1)
        startY += 30

    return image

# -----------------------------------------/
# ---/ Draw exclusion zone
def draw_exclusion_zone(frame, points):
    for i, point in enumerate(points):
        cv2.circle(frame, point, 5, (0, 0, 255), -1)
        if i > 0:
            cv2.line(frame, points[i - 1], point, (0, 0, 255), 2)
    if len(points) > 1:
        cv2.line(frame, points[-1], points[0], (0, 0, 255), 2)  # Close the zone



# ===========================================================================//
# ----------------------------------------------------------------// UI Helpers

# -----------------------------------------/
# ---/ 
def calculate_linear_params(input_range, output_range):
    # Linear function: y = mx + b
    def linear_func(x, m, b):
        return m * x + b
    params, _ = curve_fit(linear_func, input_range, output_range)
    return params  # Returns [m, b]

# -----------------------------------------/
# ---/ 
def calculate_log_params(input_range, output_range):
    # Logarithmic function: y = a * log(x) + b
    def log_func(x, a, b):
        return a * np.log(x) + b
    params, _ = curve_fit(log_func, input_range, output_range)
    return params  # Returns [a, b]

# -----------------------------------------/
# ---/ 
def calculate_exp_params(input_range, output_range):
    # Exponential function: y = a * exp(b * x)
    def exp_func(x, a, b):
        return a * np.exp(b * x)
    params, _ = curve_fit(exp_func, input_range, output_range)
    return params  # Returns [a, b]

# -----------------------------------------/
# ---/ 
def linear_interpolation(x, linear_params):
    m, b = linear_params
    return m * x + b

# -----------------------------------------/
# ---/ 
def logarithmic_interpolation(x, log_params):
    a, b = log_params
    return a * np.log(x) + b

# -----------------------------------------/
# ---/ 
def exponential_interpolation(x, exp_params):
    a, b = exp_params
    return a * np.exp(b * x)