from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time
import machine
import random


class TIG00:
    def __init__(self):
        """Inizializza l'hardware e le configurazioni del gioco"""
        # Hardware setup
        self.buzzer = machine.PWM(machine.Pin(9))
        self.button_blue = Pin(4, Pin.IN, Pin.PULL_UP)
        self.button_yellow = Pin(5, Pin.IN, Pin.PULL_UP)
        self.button_green = Pin(6, Pin.IN, Pin.PULL_UP)
        self.button_red = Pin(7, Pin.IN, Pin.PULL_UP)
        self.internal_led = Pin(25, Pin.OUT)
        self.led_blue = Pin(11, Pin.OUT)
        self.led_yellow = Pin(10, Pin.OUT)
        self.led_green = Pin(2, Pin.OUT)
        self.led_red = Pin(3, Pin.OUT)

        # Mappa dei colori: ID -> (LED, pulsante, testo, tono)
        self.COLORS = {
            0: (self.led_blue, self.button_blue, "BLUE", 300),
            1: (self.led_yellow, self.button_yellow, "YELLOW", 600),
            2: (self.led_green, self.button_green, "GREEN", 900),
            3: (self.led_red, self.button_red, "RED", 1200)
        }

        # Configurazione I2C e display
        i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
        print("Dispositivi I2C connessi:", [hex(addr) for addr in i2c.scan()])
        self.display = SSD1306_I2C(128, 64, i2c)

        # Stato del gioco
        self.sequence = []
        self.level = 0

    def play_tone(self, frequency, duration):
        """Suona una nota per la durata specificata"""
        self.buzzer.freq(frequency)
        self.buzzer.duty_u16(32768)  # 50% duty cycle
        time.sleep(duration)
        self.buzzer.duty_u16(0)  # Silenzio

    def clear_display(self):
        """Cancella il display"""
        self.display.fill(0)  # 0 = nero (pixel spento)
        self.display.show()

    def show_text(self, message):
        """Mostra testo centrato sul display"""
        self.clear_display()
        # Centra il testo (ogni carattere è 8 pixel di larghezza)
        x = (128 - len(message) * 8) // 2
        y = 28  # Centrato verticalmente
        self.display.text(message, x, y, 1)  # 1 = bianco (pixel acceso)
        self.display.show()

    def flash_color(self, color_id, duration=0.5):
        """Accende LED, suona tono e mostra testo per un colore"""
        led, _, text, tone = self.COLORS[color_id]
        led.on()
        self.show_text(text)
        self.play_tone(tone, duration)
        time.sleep(duration)
        led.off()
        self.clear_display()
        time.sleep(0.1)

    def show_sequence(self, sequence, level):
        """Mostra la sequenza di colori con velocità crescente per livello"""
        self.clear_display()
        self.display.text("WATCH!", 35, 28, 1)
        self.display.show()
        time.sleep(1)

        # Velocità aumenta con il livello: da 0.6s a 0.2s minimo
        duration = max(0.2, 0.6 - (level * 0.05))

        for color_id in sequence:
            self.flash_color(color_id, duration)

    def wait_for_start(self):
        """Attende silenziosamente che un pulsante venga premuto per iniziare"""
        # Aspetta che tutti i pulsanti siano rilasciati
        while not all(self.COLORS[i][1].value() for i in range(4)):
            time.sleep(0.01)

        # Aspetta che un pulsante venga premuto (senza feedback)
        while True:
            for color_id in range(4):
                _, button, _, _ = self.COLORS[color_id]
                if button.value() == 0:  # Pulsante premuto (PULL_UP)
                    # Aspetta rilascio
                    while button.value() == 0:
                        time.sleep(0.01)
                    return
            time.sleep(0.01)

    def wait_for_button(self, timeout=None):
        """Attende che un pulsante venga premuto e rilasciato

        Args:
            timeout: Tempo massimo di attesa in secondi. None = nessun timeout

        Returns:
            color_id se premuto, None se timeout scaduto
        """
        # Aspetta che tutti i pulsanti siano rilasciati
        while not all(self.COLORS[i][1].value() for i in range(4)):
            time.sleep(0.01)

        start_time = time.time() if timeout else None

        # Aspetta che un pulsante venga premuto
        while True:
            # Controlla timeout
            if timeout and (time.time() - start_time) > timeout:
                return None

            for color_id in range(4):
                led, button, text, tone = self.COLORS[color_id]
                if button.value() == 0:  # Pulsante premuto (PULL_UP)
                    # Feedback visivo e sonoro
                    led.on()
                    self.show_text(text)
                    self.play_tone(tone, 0.3)
                    led.off()
                    self.clear_display()

                    # Aspetta rilascio
                    while button.value() == 0:
                        time.sleep(0.01)

                    return color_id
            time.sleep(0.01)

    def check_player_input(self, sequence):
        """Verifica l'input del giocatore con timeout di 2 secondi per iniziare

        Returns:
            True se corretto, False se sbagliato, "timeout" se timeout
        """
        self.clear_display()
        self.display.text("YOUR TURN!", 25, 28, 1)
        self.display.show()
        time.sleep(1)

        for i, expected_color in enumerate(sequence):
            # Timeout di 2 secondi solo per il primo pulsante
            timeout = 2.0 if i == 0 else None
            player_color = self.wait_for_button(timeout)

            # Timeout scaduto
            if player_color is None:
                return "timeout"

            # Colore sbagliato
            if player_color != expected_color:
                return False

        return True

    def game_over(self, level):
        """Mostra schermata game over"""
        self.clear_display()
        self.display.text("GAME OVER!", 20, 20, 1)
        self.display.text("Level: " + str(level), 35, 35, 1)
        self.display.show()

        # Suono game over
        for i in range(3):
            self.play_tone(200, 0.2)
            time.sleep(0.1)

        time.sleep(3)

    def game_win(self):
        """Messaggio vittoria"""
        self.clear_display()
        self.display.text("CORRECT", 35, 28, 1)
        self.display.show()
        time.sleep(1)

    def start(self):
        """Avvia il gioco principale"""
        # Game loop
        while True:
            # Schermata iniziale
            self.clear_display()
            self.display.text("SIMON SAYS", 20, 20, 1)
            self.display.text("Press button", 15, 35, 1)
            self.display.text("to start", 30, 45, 1)
            self.display.show()

            # Aspetta un pulsante qualsiasi (senza feedback)
            self.wait_for_start()

            # Inizia il gioco
            self.sequence = []
            self.level = 0

            while True:
                # Aggiungi un colore casuale alla sequenza
                self.sequence.append(random.randint(0, 3))
                self.level += 1

                # Mostra il livello
                self.clear_display()
                self.display.text("LEVEL " + str(self.level), 35, 28, 1)
                self.display.show()
                time.sleep(1.5)

                # Mostra la sequenza con velocità crescente
                self.show_sequence(self.sequence, self.level)

                # Verifica input del giocatore
                result = self.check_player_input(self.sequence)

                if result == "timeout":
                    # Mostra messaggio timeout
                    self.clear_display()
                    self.display.text("TIMEOUT", 35, 28, 1)
                    self.display.show()
                    time.sleep(1.5)
                    self.game_over(self.level)
                    break
                elif not result:
                    # Errore normale
                    self.game_over(self.level)
                    break

                # Vittoria per questo livello
                self.game_win()
                time.sleep(0.5)


def start():
    game = TIG00()
    game.start()
