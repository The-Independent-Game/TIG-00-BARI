from machine import Pin
import time

button = Pin(1, Pin.IN, Pin.PULL_UP)
led = Pin(0, Pin.OUT)

last_state = 1
button_pressed = False

while True:
    current_state = button.value()
    if current_state != last_state:
        time.sleep(0.02)  # Debounce delay
        current_state = button.value()  # Rileggi dopo il delay
        if current_state == 0 and last_state == 1:  # Pressione
            button_pressed = not button_pressed  # Toggle
            led.value(button_pressed)
        last_state = current_state
    time.sleep(0.01)