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
    frame_interval = 1.0 / 4
    program_time = time.time()
    count = 0
    try:
        while True:
            start_time = time.time()  # 记录开始时间

            mlx.getFrame(frame)  # 获取温度数据帧
            for row in frame:
                print("get")

            elapsed_time = time.time() - start_time  # 计算已经花费的时间
            print("total time : %s" % elapsed_time)
            # 如果已经花费的时间小于时间间隔，等待剩余时间
            if elapsed_time < frame_interval:
                print("Sleeping for : %s" % (frame_interval - elapsed_time))
                time.sleep(frame_interval - elapsed_time)
    except KeyboardInterrupt:
        pass
    # try:
    #     while True:
    #         try:
    #             start_time = time.time()
    #             print("start next frame")
    #             mlx.getFrame(frame)
    #             print("frame get")
    #             read_end_time = time.time()
    #             image_time = time.time()
    #             thresholded_matrix, highest_temp = process_frame(frame)
    #             print_results(thresholded_matrix, highest_temp)
    #             elapsed_time = time.time() - start_time
            
    #             print("--- total %s seconds ---" % (time.time() - start_time))
    #             print("--- read image time %s seconds ---" % (read_end_time - start_time))
    #             print("--- image process %s seconds ---" % (time.time() - image_time))
    #             count+=1
    #             if elapsed_time < interval:
    #                 print("Sleeping for : %s" % (interval - elapsed_time))
    #                 time.sleep(interval - elapsed_time)
    #         except ValueError:
    #             print('Error reading frame')
    #             continue
            
                
    # except RuntimeError:
    #     print("tooooooooooooooooo  many  retries")
    #     print("program time : %s" % (time.time() - program_time))
    #     print('Total frames count: '+str(count))
    # except KeyboardInterrupt:
    #     print("Key Board Interrupt")
    #     print("program time : %s" % (time.time() - program_time))
    #     print('Total frames count: '+str(count))