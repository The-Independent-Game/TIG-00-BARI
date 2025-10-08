from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time
import machine
import random

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


# Mappa dei colori: ID -> (LED, pulsante, testo, tono)
COLORS = {
    0: (led_blue, button_blue, "BLUE", 300),
    1: (led_yellow, button_yellow, "YELLOW", 600),
    2: (led_green, button_green, "GREEN", 900),
    3: (led_red, button_red, "RED", 1200)
}

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


def flash_color(color_id, duration=0.5):
    """Accende LED, suona tono e mostra testo per un colore"""
    led, button, text, tone = COLORS[color_id]
    led.on()
    show_text(text)
    play_tone(tone, duration)
    time.sleep(duration)
    led.off()
    clear_display()
    time.sleep(0.2)

def show_sequence(sequence):
    """Mostra la sequenza di colori"""
    clear_display()
    display.text("WATCH!", 35, 28, 1)
    display.show()
    time.sleep(1)

    for color_id in sequence:
        flash_color(color_id)

def wait_for_button():
    """Attende che un pulsante venga premuto e rilasciato"""
    # Aspetta che tutti i pulsanti siano rilasciati
    while not all(COLORS[i][1].value() for i in range(4)):
        time.sleep(0.01)

    # Aspetta che un pulsante venga premuto
    while True:
        for color_id in range(4):
            led, button, text, tone = COLORS[color_id]
            if button.value() == 0:  # Pulsante premuto (PULL_UP)
                # Feedback visivo e sonoro
                led.on()
                show_text(text)
                play_tone(tone, 0.3)
                led.off()
                clear_display()

                # Aspetta rilascio
                while button.value() == 0:
                    time.sleep(0.01)

                return color_id
        time.sleep(0.01)

def check_player_input(sequence):
    """Verifica l'input del giocatore"""
    clear_display()
    display.text("YOUR TURN!", 25, 28, 1)
    display.show()
    time.sleep(1)

    for i, expected_color in enumerate(sequence):
        player_color = wait_for_button()
        if player_color != expected_color:
            return False
    return True

def game_over(level):
    """Mostra schermata game over"""
    clear_display()
    display.text("GAME OVER!", 20, 20, 1)
    display.text("Level: " + str(level), 35, 35, 1)
    display.show()

    # Suono game over
    for i in range(3):
        play_tone(200, 0.2)
        time.sleep(0.1)

    time.sleep(3)

def game_win():
    """Animazione vittoria"""
    # Accende tutti i LED
    for color_id in range(4):
        COLORS[color_id][0].on()

    # Suono vittoria
    for freq in [400, 500, 600, 800]:
        play_tone(freq, 0.2)

    # Spegne tutti i LED
    for color_id in range(4):
        COLORS[color_id][0].off()

    time.sleep(0.3)

# Game loop
while True:
    # Schermata iniziale
    clear_display()
    display.text("SIMON SAYS", 20, 20, 1)
    display.text("Press button", 15, 35, 1)
    display.text("to start", 30, 45, 1)
    display.show()

    # Aspetta un pulsante qualsiasi
    wait_for_button()

    # Inizia il gioco
    sequence = []
    level = 0

    while True:
        # Aggiungi un colore casuale alla sequenza
        sequence.append(random.randint(0, 3))
        level += 1

        # Mostra il livello
        clear_display()
        display.text("LEVEL " + str(level), 35, 28, 1)
        display.show()
        time.sleep(1.5)

        # Mostra la sequenza
        show_sequence(sequence)

        # Verifica input del giocatore
        if not check_player_input(sequence):
            game_over(level)
            break

        # Vittoria per questo livello
        game_win()
        time.sleep(0.5)

