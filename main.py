from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time
import machine

def play_tone(frequency, duration):
    """Suona una nota per la durata specificata"""
    buzzer.freq(frequency)
    buzzer.duty_u16(32768)  # 50% duty cycle
    time.sleep(duration)
    buzzer.duty_u16(0)  # Silenzio

buzzer = machine.PWM(machine.Pin(9))
button_blue = Pin(4, Pin.IN, Pin.PULL_UP)
button_yellow = Pin(5, Pin.IN, Pin.PULL_UP)
button_green = Pin(6, Pin.IN, Pin.PULL_UP)
button_red = Pin(7, Pin.IN, Pin.PULL_UP)
internal_led = Pin(25, Pin.OUT)
led_blue = Pin(11, Pin.OUT)
led_yellow = Pin(10, Pin.OUT)
led_green = Pin(2, Pin.OUT)
led_red = Pin(3, Pin.OUT)


button_blue_pressed = False
button_yellow_pressed = False
button_green_pressed = False
button_red_pressed = False

def button_handler(pin):
    global button_blue_pressed
    global button_yellow_pressed
    global button_green_pressed
    global button_red_pressed

    if pin == button_blue:
        button_blue_pressed = True
    elif pin == button_yellow:
        button_yellow_pressed = True
    elif pin == button_green:
        button_green_pressed = True
    elif pin == button_red:
        button_red_pressed = True


# Configura interrupt sul fronte di discesa (quando il pulsante viene premuto)
button_blue.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
button_yellow.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
button_green.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
button_red.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)

# Configurazione I2C
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)  # I2C0, pins GP0 (SDA) e GP1 (SCL)

# Verifica dei dispositivi I2C connessi
print("Dispositivi I2C connessi:", [hex(addr) for addr in i2c.scan()])

# Inizializzazione del display (128x64 pixel)
display = SSD1306_I2C(128, 64, i2c)

# Funzione per cancellare il display
def clear_display():
    display.fill(0)  # 0 = nero (pixel spento)
    display.show()

# Esempi di visualizzazione

# 1. Testo semplice
def show_text(message):
    clear_display()
    display.text(message, 0, 0, 1)  # 1 = bianco (pixel acceso)
    display.show()


while True:
    if button_blue_pressed:
        led_blue.on()
        show_text("blue")
        play_tone(300, 0.5)
        button_blue_pressed = False
        time.sleep(0.5)
        clear_display()
        led_blue.off()
        
    if button_yellow_pressed:
        led_yellow.on()
        show_text("yellow")
        play_tone(600, 0.5)
        button_yellow_pressed = False
        time.sleep(0.5)
        clear_display()
        led_yellow.off()
    
    if button_green_pressed:
        led_green.on()
        show_text("green")
        play_tone(900, 0.5)
        button_green_pressed = False
        time.sleep(0.5)
        clear_display()
        led_green.off()
    
    if button_red_pressed:
        led_red.on()
        show_text("red")
        play_tone(1200, 0.5)
        button_red_pressed = False
        time.sleep(0.5)
        clear_display()
        led_red.off()
        
    
    time.sleep(0.1)

