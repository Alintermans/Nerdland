import RPi.GPIO as GPIO
import time
import curses

# Set up GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(6, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(19, GPIO.OUT)
GPIO.setup(26, GPIO.OUT)

# Set up curses
screen = curses.initscr()
curses.noecho()
curses.cbreak()
screen.keypad(True)

# Define arrow key functions
def up():
    GPIO.output(6, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(6, GPIO.LOW)

def down():
    GPIO.output(13, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(13, GPIO.LOW)

def left():
    GPIO.output(19, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(19, GPIO.LOW)

def right():
    GPIO.output(26, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(26, GPIO.LOW)

# Map arrow keys to functions
actions = {
    curses.KEY_UP: up,
    curses.KEY_DOWN: down,
    curses.KEY_LEFT: left,
    curses.KEY_RIGHT: right
}

# Main loop
try:
    while True:
        char = screen.getch()
        if char == ord('q'):
            break
        elif char in actions:
            actions[char]()

finally:
    # Clean up
    curses.nocbreak()
    screen.keypad(0)
    curses.echo()
    curses.endwin()
    GPIO.cleanup()
