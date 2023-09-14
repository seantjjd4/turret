import pigpio
import time

GPIO_MOTOR1 = 12
GPIO_MOTOR2 = 13

MOTOR_PWM_FREQUENCY = 50
MOTOR_PWM_DUTY_CYCLE_180 = 120000
MOTOR_PWM_DUTY_CYCLE_90 = 60000
MOTOR_PWM_DUTY_CYCLE_0 = 20000

print("start")
pi = pigpio.pi()
pi.set_mode(GPIO_MOTOR1, pigpio.OUTPUT)
pi.set_mode(GPIO_MOTOR2, pigpio.OUTPUT)

print("start moving")

pi.hardware_PWM(GPIO_MOTOR1, MOTOR_PWM_FREQUENCY, MOTOR_PWM_DUTY_CYCLE_90)
pi.hardware_PWM(GPIO_MOTOR2, MOTOR_PWM_FREQUENCY, MOTOR_PWM_DUTY_CYCLE_90)
time.sleep(2)
pi.write(GPIO_MOTOR1, 0)
pi.write(GPIO_MOTOR2, 0)

for i in range(5):
    print("frequency : %s" % (MOTOR_PWM_DUTY_CYCLE_90 + i*10000))
    pi.hardware_PWM(GPIO_MOTOR1, MOTOR_PWM_FREQUENCY, MOTOR_PWM_DUTY_CYCLE_90)
    time.sleep(2)
    pi.write(GPIO_MOTOR1, 0)
    pi.write(GPIO_MOTOR2, 0)
    time.sleep(2)

pi.write(GPIO_MOTOR1, 0)
pi.write(GPIO_MOTOR2, 0)
pi.stop()

print("-------end------")