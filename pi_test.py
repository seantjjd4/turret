import time
import board
import busio
import numpy as np
import adafruit_mlx90640

import time
import board
import busio
import adafruit_mlx90640
import numpy as np
import cv2

def init_mlx_sensor():
    i2c = busio.I2C(board.SCL, board.SDA, frequency=10000)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
    print("MLX addr detected on I2C", [hex(i) for i in mlx.serial_number])
    return mlx

def process_frame(frame):
    thermal_matrix = np.array(frame).reshape(24, 32)
    
    # Reduce noise with Gaussian blur
    blurred_matrix = cv2.GaussianBlur(thermal_matrix, (5, 5), 0)
    
    # Extract temperatures within the desired range
    _, thresholded_matrix = cv2.threshold(blurred_matrix, TEMP_RANGE[0], TEMP_RANGE[1], cv2.THRESH_BINARY)
    thresholded_matrix = thresholded_matrix.astype(np.uint8) * 255
    
    # Remove small areas from the matrix and keep only the largest one if there are multiple
    contours, _ = cv2.findContours(thresholded_matrix, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return np.zeros_like(thresholded_matrix), 0

    # Sort contours by area in descending order
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    # Create an empty matrix to store the largest region
    largest_region = np.zeros_like(thresholded_matrix)
    
    # Draw the largest contour
    cv2.drawContours(largest_region, [contours[0]], 0, 255, thickness=cv2.FILLED)

    return largest_region, thermal_matrix.max()

def print_results(thresholded_matrix, highest_temp):
    location = np.where(thresholded_matrix == 255)
    print(f"highest temp: {highest_temp} at location {location}")
    
    for row in thresholded_matrix:
        print(", ".join(["%d" % (value//255) for value in row]))
    print("_______")

if __name__ == "__main__":
    TEMP_RANGE = (30, 40)
    mlx = init_mlx_sensor()
    frame = [0] * 768
    program_time = time.time()
    count = 0
    try:
        while True:
            start_time = time.time()
            try:
                mlx.getFrame(frame)
            except ValueError:
                print('Error reading frame')
                continue
            
            thresholded_matrix, highest_temp = process_frame(frame)
            print_results(thresholded_matrix, highest_temp)

            print("--- %s seconds ---" % (time.time() - start_time))
            count+=1
    except RuntimeError:
        print("tooooooooooooooooo  many  retries")
        print("program time : %s" % (time.time() - program_time))
        print('Total frames count: '+str(count))
    except KeyboardInterrupt:
        print("tooooooooooooooooo  many  retries")
        print("program time : %s" % (time.time() - program_time))
        print('Total frames count: '+str(count))