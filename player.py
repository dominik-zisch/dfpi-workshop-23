import csv
import time
import serial

from utils import *

config = read_config("player_config.yaml")
serial_port = config['serial-port']
baud_rate = config['baud-rate']
csv_files = config['csv-files']
x_values = config['x-values']
y_values = config['y-values']
max_step = config['max-step']
step = config['step']

# if x_values is not 2 values, error
if len(x_values) != 2:
    raise ValueError("x-values must be 2 values")
    sys.exit(1)

# if y_values is not 2 values, error
if len(y_values) != 2:
    raise ValueError("y-values must be 2 values")
    sys.exit(1)

min_x = x_values[0]
max_x = x_values[1]
min_y = y_values[0]
max_y = y_values[1]

min_input = -90
max_input = 90



def playback_csv(csv_file, serial_connection):
    last_output_x = min_x + (max_x - min_x) / 2
    last_output_y = min_y + (max_y - min_y) / 2
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header

        previous_time = 0
        for row in reader:
            current_time, angle_x, angle_y = float(row[0]), float(row[4]), float(row[5])
            
            # Calculate the sleep time
            sleep_time = current_time - previous_time
            if sleep_time > 0:
                time.sleep(sleep_time)

            # Prepare the data string
            data_string = f"{angle_x},{angle_y}\n"
            serial_connection.write(data_string.encode())

            # remap
            output_x = min_x + (angle_x - min_input) * (max_x - min_x) / (max_input - min_input)
            output_y = min_y + (angle_y - min_input) * (max_y - min_y) / (max_input - min_input)

            # diff_x = abs(output_x - last_output_x)
            # diff_y = abs(output_y - last_output_y)

            # if diff_x > max_step or diff_y > max_step:
            #     interpolating = True
            #     curr_x = last_output_x
            #     curr_y = last_output_y

            #     while interpolating:
            #         diff_x = output_x - last_output_x
            #         if diff_x > 0:
            #             curr_x += step
            #             if curr_x > output_x:
            #                 curr_x = output_x
            #         else:
            #             curr_x -= step
            #             if curr_x < output_x:
            #                 curr_x = output_x

            #         diff_y = output_y - last_output_y
            #         if diff_y > 0:
            #             curr_y += step
            #             if curr_y > output_y:
            #                 curr_y = output_y
            #         else:
            #             curr_y -= step
            #             if curr_y < output_y:
            #                 curr_y = output_y
                    
            #         data_string = f"{curr_x},{curr_y}\n"
            #         serial_connection.write(data_string.encode())

            #         print(f"interpolating : {round(angle_x, 2)} - {round(curr_x, 2)}, {round(angle_y, 2)} - {round(curr_y, 2)}")
            #         time.sleep(0.01)

            #         if curr_x == output_x and curr_y == output_y:
            #             interpolating = False

            print(f"{current_time} : {round(angle_x, 2)} - {round(output_x, 2)}, {round(angle_y, 2)} - {round(output_y, 2)}")
            
            last_output_x = output_x
            last_output_y = output_y
            previous_time = current_time

def read_and_playback(csv_files, port, baud_rate):
    with serial.Serial(port, baud_rate) as serial_connection:
        for file in csv_files:
            playback_csv(file, serial_connection)
            print(f"Completed playback for {file}")

read_and_playback(csv_files, serial_port, baud_rate)
