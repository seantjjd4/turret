import cv2
import sys
import time
import board
import busio
import atexit
import threading
import logging
import pigpio
import numpy as np
import adafruit_mlx90640

'''
Raspberry Pi 4 Model B
Pins with hardware PWM:
channel 0:
    GPIO 12
    GPIO 18
channel 1:
    GPIO 13
    GPIO 19
'''
GPIO_MOTOR1 = 12
GPIO_MOTOR2 = 13

'''
K-Power Hb200t 12V 200kg Torque Steel Gear Digital Industrial Servo

Voltage Range	        DC 10-14.8V
Rated Voltage	        12V
Stall Torque	        20.1N.M(205kg.cm)
No load Speed	        55.5rpm(0.18s/60°)
Motor Type	            Brushless
Resolution	            0.23°
Running Degree	        0-180°
Communication Method	PWM(deadband 1-2μs)
NO.of Wire	5Pin
Position Sensor	        Potentiometer
'''

# using pulsewidth to control motor spin to a specific angle
# using set_servo_pulsewidth to move to certain angle,
# and get_servo_pulsewidth to get the signal pulsewidth passing to motor.

MOTOR_PULSEWIDTH_MIN = 1000
MOTOR_PULSEWIDTH_MID = 1500
MOTOR_PULSEWIDTH_MAX = 2000

# not using pi.hardware_PWM() to control the motor, using pi.set_servo_pulsewidth() instead.
# 
# MOTOR_PWM_FREQUENCY = 50
# MOTOR_PWM_DUTY_CYCLE_180 = 120000
# MOTOR_PWM_DUTY_CYCLE_90 = 60000
# MOTOR_PWM_DUTY_CYCLE_0 = 20000
# MOTOR_PWM_RANGE = 400

'''
MLX90640-BAA IR Thermal Camera

I2C compatible digital interface
Programmable refresh rate 0.5Hz…64Hz (0.25 ~ 32 FPS)
3.3V-5V supply voltage, regulated to 3.3V on breakout
Current consumption less than 23mA
Field of view: 110°x75°
Operating temperature -40°C ~ 85°C
Target temperature -40°C ~ 300°C
Product Dimensions: 25.8mm x 17.8mm x 10.5mm / 1.0" x 0.7" x 0.4"
Product Weight: 3.0g / 0.1oz 
'''
IMAGE_CENTER_POINT_X = 15
IMAGE_CENTER_POINT_Y = 11


class VideoUtils(object):
    '''
    Class used for video processing
    '''
    @staticmethod
    def init_mlx90640():
        i2c = busio.I2C(board.SCL, board.SDA, frequency=1000000)
        mlx = adafruit_mlx90640.MLX90640(i2c)
        mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_16_HZ
        logging.debug("MLX addr detected on I2C", [hex(i) for i in mlx.serial_number])
        return mlx
    
    @staticmethod
    def process_frame(frame):
        thermal_matrix = np.array(frame).reshape(24, 32)
        blurred_matrix = cv2.GaussianBlur(thermal_matrix, (5, 5), 0)
        _, thresholded_matrix = cv2.threshold(blurred_matrix, TEMP_RANGE[0], TEMP_RANGE[1], cv2.THRESH_BINARY)
        thresholded_matrix = thresholded_matrix.astype(np.uint8) * 255
        contours, _ = cv2.findContours(thresholded_matrix, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) == 0:
            return np.zeros_like(thresholded_matrix), 0
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        largest_region = np.zeros_like(thresholded_matrix)
        cv2.drawContours(largest_region, [contours[0]], 0, 255, thickness=cv2.FILLED)
        return largest_region, thermal_matrix.max()

    @staticmethod
    def print_results(thresholded_matrix, highest_temp):
        for row in thresholded_matrix:
            print(", ".join(["%d" % (value//255) for value in row]))
        print("_______")

    @staticmethod
    def find_centroid_difference(thresholded_matrix):
        
        y_positions, x_positions = np.where(thresholded_matrix == 255)
        if len(x_positions) == 0 or len(y_positions) == 0:
            return None, (0, 0)
        centroid_x = int(np.mean(x_positions))
        centroid_y = int(np.mean(y_positions))
        difference_x = centroid_x - IMAGE_CENTER_POINT_X
        difference_y = centroid_y - IMAGE_CENTER_POINT_Y
        return (centroid_x, centroid_y), (difference_x, difference_y)

    @staticmethod
    def thermal_detection(callback):
        mlx = VideoUtils.init_mlx90640()
        frame = [0] * 768
        frame_interval = 1.0 / 16
        program_time = time.time()
        frame_count = 0
        restart_count = 0
        try:
            while True:
                try:
                    logging.debug("start new frame")
                    start_time = time.time()
                    mlx.getFrame(frame)
                    image_time = time.time()

                    thresholded_matrix, highest_temp = VideoUtils.process_frame(frame)
                    centroid, difference_to_center = VideoUtils.find_centroid_difference(thresholded_matrix)


                    if centroid:
                        logging.debug(f'Difference from the most central point: {difference_to_center}')
                        callback(centroid, difference_to_center)

                    elapsed_time = time.time() - start_time
                    logging.debug("--- total %s seconds ---" % (time.time() - start_time))
                    logging.debug("--- read image time %s seconds ---" % (image_time - start_time))
                    logging.debug("--- image process %s seconds ---" % (time.time() - image_time))
                    frame_count += 1

                    if elapsed_time < frame_interval:
                        logging.info("Sleeping for : %s" % (frame_interval - elapsed_time))
                        time.sleep(frame_interval - elapsed_time)
                except:
                    logging.warning('Error reading frame')
                    restart_count += 1
                    continue
        except RuntimeError:
            logging.warning("tooooooooooooooooo  many  retries")
            logging.info("detection time : %s" % (time.time() - program_time))
            logging.info('Total frames count: '+str(frame_count))
            logging.info("Restart Count : %s" % restart_count)
        except KeyboardInterrupt:
            logging.debug("Key Board Interrupt")
            logging.info("detection time : %s" % (time.time() - program_time))
            logging.info('Total frames count: '+str(frame_count))
            logging.info("Restart Count : %s" % restart_count)
            raise KeyboardInterrupt




class Turret(object):
    '''
    Class used for turret control
    control a turret with two servo motor
    '''
    def __init__(self, temp_range = (30, 40)):
        logging.getLogger().setLevel(logging.DEBUG)
        logging.info('Turret Start initialize')

        self.temp_range = temp_range

        # initialize raspberry pi connection
        self.pi = pigpio.pi()
        self.pi.set_mode(GPIO_MOTOR1, pigpio.OUTPUT)
        self.pi.set_mode(GPIO_MOTOR2, pigpio.OUTPUT)
        # self.pi.set_PWM_frequency(GPIO_MOTOR1, MOTOR_PWM_FREQUENCY)
        # self.pi.set_PWM_range(GPIO_MOTOR1, MOTOR_PWM_RANGE)
        # self.pi.set_PWM_frequency(GPIO_MOTOR2, MOTOR_PWM_FREQUENCY)
        # self.pi.set_PWM_range(GPIO_MOTOR2, MOTOR_PWM_RANGE)


        # set to relocate and release the motors
        atexit.register(self.__turn_of_motors)
        logging.info('Turret Initialize sucess')

    # calibrate two servo motors to central position
    def calibrate(self):
        logging.debug('Start calibrate')
        self.pi.set_servo_pulsewidth(GPIO_MOTOR1, MOTOR_PULSEWIDTH_MID)
        self.pi.set_servo_pulsewidth(GPIO_MOTOR2, MOTOR_PULSEWIDTH_MID)
        self.m1_pulsewidth = MOTOR_PULSEWIDTH_MID
        self.m2_pulsewidth = MOTOR_PULSEWIDTH_MID
        logging.debug('Calibrate success')

    def track(self, x, y):
        
        t_m1 = threading.Thread()
        t_m2 = threading.Thread()

        
        if x > 0:
            if self.m1_pulsewidth < MOTOR_PULSEWIDTH_MAX:
                self.m1_pulsewidth = self.m1_pulsewidth + 25
                t_m1 = threading.Thread(target=self.__move, args=(GPIO_MOTOR1, self.m1_pulsewidth))
        elif x < 0:
            if self.m1_pulsewidth > MOTOR_PULSEWIDTH_MID:
                self.m1_pulsewidth = self.m1_pulsewidth - 25
                t_m1 = threading.Thread(target=self.__move, args=(GPIO_MOTOR1, self.m1_pulsewidth))
        
        if y > 0:
            if self.m2_pulsewidth < MOTOR_PULSEWIDTH_MAX:
                self.m2_pulsewidth = self.m2_pulsewidth + 25
                t_m2 = threading.Thread(target=self.__move, args=(GPIO_MOTOR2, self.m2_pulsewidth))
        elif y < 0:
            if self.m2_pulsewidth > MOTOR_PULSEWIDTH_MID:
                self.m2_pulsewidth = self.m2_pulsewidth - 25
                t_m2 = threading.Thread(target=self.__move, args=(GPIO_MOTOR2, self.m2_pulsewidth))

        # starting thread (controlling motor)
        t_m1.start()
        t_m2.start()

        # wait until thread end
        t_m1.join()
        t_m2.join()
    
    def __move(self, motor, puslewidth):
        self.pi.set_servo_pulsewidth(motor, puslewidth)


    # start thermal detection
    def thermal_tracking(self):
        VideoUtils.thermal_detection(self.track)
    

    def __turn_of_motors(self):
        self.calibrate()
        self.pi.write(GPIO_MOTOR1, 0)
        self.pi.write(GPIO_MOTOR2, 0)
        self.pi.stop()

if __name__ == '__main__':

    user_input = input("Choose an mode: (1) Thermal Tracking (2) Customize Setting \n")
    if str(user_input) == "1":
        t = Turret()
        t.calibrate()
        t.thermal_tracking()
    elif str(user_input) == "2":
        low_temp = input("Setting: detect temp range from ? (Type the lowest temperture be detected)\n")
        try:
            low = int(low_temp)
        except:
            print("Invalid input. Please enter a valid integer.")
            exit(1)
        high_temp = input(f"Setting: detect temp range from {low} to ? (Type the highest temperture be detected)\n")
        try:
            high = int(high_temp)
        except:
            print("Invalid input. Please enter a valid integer.")
            exit(1)
        if low > high:
            print("Invalid input. From 'low' to 'high'.")
    else:
        print("Unknown input mode. Please choose a number (1) or (2)")

