import RPi.GPIO as GPIO
import time

# Set up GPIO pins
GPIO.setmode(GPIO.BCM)

GPIO.setup(26, GPIO.OUT)
GPIO.setup(19, GPIO.OUT)

# Define arrow key functions
def right():
    GPIO.output(26, GPIO.HIGH)
    print("Turning right")
    time.sleep(1)
    GPIO.output(26, GPIO.LOW)
    print("off")
    time.sleep(1)
def left():
    GPIO.output(19, GPIO.HIGH)
    print("Turning left")
    time.sleep(1)
    GPIO.output(19, GPIO.LOW)
    print("off")
    time.sleep(1)



while True:
    right()
    left()
    
