# Codice per controllare un display OLED SSD1306 con Raspberry Pi Pico W
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
internal_led = Pin(25, Pin.OUT)
led_blue = Pin(11, Pin.OUT)

button_blue_pressed = False

def button_blue_handler(pin):
    """Funzione chiamata quando il pulsante viene premuto"""
    global button_blue_pressed
    button_blue_pressed = True

# Configura interrupt sul fronte di discesa (quando il pulsante viene premuto)
button_blue.irq(trigger=Pin.IRQ_FALLING, handler=button_blue_handler)

# Configurazione I2C
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)  # I2C0, pins GP0 (SDA) e GP1 (SCL)
# Nota: potrebbe essere necessario adattare i pin in base alla tua configurazione

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
        play_tone(1000, 0.5)
        button_blue_pressed = False
        time.sleep(0.5)
        clear_display()
        led_blue.off()
        
    
    time.sleep(0.1)
1
