# Codice per controllare un display OLED SSD1306 con Raspberry Pi Pico W
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time

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
def show_text():
    clear_display()
    display.text("Ciao Mondo!", 0, 0, 1)  # 1 = bianco (pixel acceso)
    display.text("Display SSD1306", 0, 16, 1)
    display.text("con Pico W", 0, 32, 1)
    display.show()

# 2. Rettangolo
def show_rectangle():
    clear_display()
    display.rect(10, 10, 108, 44, 1)  # x, y, larghezza, altezza, colore
    display.text("Rettangolo", 30, 25, 1)
    display.show()

# 3. Rettangolo pieno
def show_filled_rectangle():
    clear_display()
    display.fill_rect(20, 15, 88, 34, 1)  # x, y, larghezza, altezza, colore
    display.text("Pieno", 50, 25, 0)  # 0 = nero (testo invertito)
    display.show()

# 4. Linee
def show_lines():
    clear_display()
    for i in range(0, 128, 8):
        display.line(0, 0, i, 63, 1)
    for i in range(0, 64, 8):
        display.line(0, 0, 127, i, 1)
    display.show()

# 5. Contatore semplice
def counter_demo(count=10):
    for i in range(count):
        clear_display()
        display.text("Contatore:", 0, 0, 1)
        display.text(str(i), 64, 32, 1)
        display.show()
        time.sleep(1)

# Esecuzione degli esempi
try:
    # Verifico se il display è stato rilevato
    if len(i2c.scan()) > 0:
        print("Display rilevato!")
        
        # Eseguo gli esempi
        show_text()
        time.sleep(2)
        
        show_rectangle()
        time.sleep(2)
        
        show_filled_rectangle()
        time.sleep(2)
        
        show_lines()
        time.sleep(2)
        
        counter_demo(5)  # Conta fino a 5
        
        # Messaggio finale
        clear_display()
        display.text("Fine Demo", 25, 25, 1)
        display.show()
    else:
        print("Nessun dispositivo I2C rilevato!")

except Exception as e:
    print("Errore:", e)