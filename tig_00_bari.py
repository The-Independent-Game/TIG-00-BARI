from machine import Pin, I2C, PWM
import time
import urandom
import json
import gc
import urequests
from lovable import SUPABASE_URL, SUPABASE_ANON_KEY

class TIG00:
    
    # Pin definitions
    PIN_BUTTON_BLUE = 4
    PIN_BUTTON_YELLOW = 5
    PIN_BUTTON_GREEN = 6
    PIN_BUTTON_RED = 7
    PIN_LED_BLUE = 11
    PIN_LED_YELLOW = 10
    PIN_LED_GREEN = 2
    PIN_LED_RED = 3
    PIN_BUZZER = 9
    PIN_SDA = 0
    PIN_SCL = 1
    PIN_INTERNAL_LED = 25

    # I2C addresses
    I2C_DISPLAY_ADDR = 0x3C

    # Constants
    NO_BUTTON = 255
    MAX_SEQUENCE_LENGTH = 25
    RECORD_FILE = "record.json"

    # Game states
    class GameStates:
        LOBBY = 0
        SEQUENCE_CREATE_UPDATE = 1
        SEQUENCE_PRESENTING = 2
        PLAYER_WAITING = 3
        GAME_OVER = 4
        OPTIONS = 5
        OPTIONS_ASK_RESET = 6
        OPTIONS_ASK_SOUND = 7
        INSERT_NAME = 8

    class Button:
        """Rappresenta un pulsante con il suo pin, tono e LED associato"""
        def __init__(self, pin, tone, led_pin):
            self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
            self.tone = tone
            self.led = Pin(led_pin, Pin.OUT)
            self.is_ready = True
            self.is_pressed = False

    def __init__(self):
        # Inizializza I2C
        self.i2c = I2C(0, scl=Pin(self.PIN_SCL), sda=Pin(self.PIN_SDA), freq=400000)

        # Definizione dei pulsanti con LED diretti
        # Toni: 300, 600, 900, 1200
        self.buttons = [
            self.Button(self.PIN_BUTTON_BLUE, 300, self.PIN_LED_BLUE),      # Blue
            self.Button(self.PIN_BUTTON_YELLOW, 600, self.PIN_LED_YELLOW),  # Yellow
            self.Button(self.PIN_BUTTON_GREEN, 900, self.PIN_LED_GREEN),    # Green
            self.Button(self.PIN_BUTTON_RED, 1200, self.PIN_LED_RED)        # Red
        ]

        # Nomi dei colori per il display
        self.color_names = ["Blue", "Yellow", "Green", "Red"]

        # LED interno
        self.internal_led = Pin(self.PIN_INTERNAL_LED, Pin.OUT)

        # Toni per melodie
        self.tones = [261, 277, 294, 311, 330, 349, 370, 392, 415, 440]

        # Buzzer PWM
        self.buzzer = PWM(Pin(self.PIN_BUZZER))
        self.buzzer_active = False

        # Display SSD1306 (semplificato - richiede libreria ssd1306)
        self.display = None
        self._init_display()

        # Variabili di gioco
        self.level = 1
        self.game_sequence = [self.NO_BUTTON] * self.MAX_SEQUENCE_LENGTH
        self.game_state = self.GameStates.LOBBY
        self.animation_sequence = [2, 3, 1, 0]  # Green, Red, Yellow, Blue
        self.animation_sequence_index = -1  # Start at -1 so first increment gives 0
        self.animation_button = self.animation_sequence[0]  # Initialize to first in sequence (Green)
        self.presenting_index = 0
        self.player_playing_index = 0
        self.need_wait = False
        self.sequence_ended = False

        # Timer
        self.timer_playing = 0
        self.timer_pause = 0
        self.timer_player_waiting = 0
        self.timer_sequence_end = 0

        # Record e settings
        self.record = 0
        self.record_name = ""
        self.sound = True
        self.name_index = 0
        self.name_letter = 'A'

        # Game session e record tracking
        self.game_session = None
        self.is_top_record = False
        self.online = False  # Will be set by caller

    def _init_display(self):
        """Inizializza il display SSD1306"""
        try:
            # Verifica presenza display
            devices = self.i2c.scan()
            if self.I2C_DISPLAY_ADDR in devices:
                # Importa libreria ssd1306 se disponibile
                try:
                    import ssd1306
                    self.display = ssd1306.SSD1306_I2C(128, 64, self.i2c)
                    self.display.poweron()
                    print("Display SSD1306 initialized")
                except ImportError:
                    print("Warning: ssd1306 library not found")
                    self.display = None
            else:
                print("Warning: Display not found at 0x3C")
        except Exception as e:
            print(f"Display init error: {e}")
            self.display = None


    def display_text(self, lines):
        """Mostra testo sul display (array di stringhe)"""
        if self.display:
            self.display.fill(0)
            for i, line in enumerate(lines):
                self.display.text(line, 0, i * 10, 1)
            self.display.show()

    def display_clear(self):
        """Pulisce il display"""
        if self.display:
            self.display.fill(0)
            self.display.show()

    def tone(self, frequency, duration_ms=None):
        """Genera un tono con il buzzer"""
        if self.sound:
            self.buzzer.freq(frequency)
            self.buzzer.duty_u16(32768)  # 50% duty cycle
            self.buzzer_active = True
            if duration_ms:
                time.sleep_ms(duration_ms)
                self.no_tone()
        else:
            if duration_ms:
                time.sleep_ms(duration_ms)

    def no_tone(self):
        """Ferma il tono del buzzer"""
        if self.buzzer_active:
            self.buzzer.duty_u16(0)
            self.buzzer_active = False

    def led_on(self, led_index, execute_sound):
        """Accende un LED specifico"""
        #try:
        button = self.buttons[led_index]
        button.led.on()

        # Mostra il colore sul display SOLO durante la presentazione della sequenza
        if self.display and self.game_state == self.GameStates.SEQUENCE_PRESENTING:
            color_name = self.color_names[led_index]
            # Centra il nome del colore (circa 16 caratteri per riga)
            centered_color = color_name.center(16)
            if self.online:
                self.display_text([
                    f"Level  {self.level}",
                    "",
                    f"Record {self.record}",
                    f"By {self.record_name}",
                    "",
                    centered_color
                ])
            else:
                self.display_text([
                    f"Level  {self.level}",
                    "",
                    "OFFLINE MODE",
                    "",
                    centered_color
                ])

        if execute_sound:
            self.tone(button.tone)
        self.playing_start()
        #except Exception as e:
        #    print(f"LED error: {e}")

    def all_leds_on(self):
        """Accende tutti i LED"""
        for button in self.buttons:
            button.led.on()

    def stop_leds(self):
        """Spegne tutti i LED"""
        for button in self.buttons:
            button.led.off()
        self.no_tone()

    def read_buttons(self):
        """Legge lo stato dei pulsanti con debouncing (PULL_UP: 0=premuto, 1=rilasciato)"""
        for button in self.buttons:
            if button.pin.value() == 0:  # Pulsante premuto (PULL_UP)
                if button.is_ready:
                    button.is_ready = False
                    button.is_pressed = True
                else:
                    button.is_pressed = False
            else:  # Pulsante rilasciato
                button.is_ready = True
                button.is_pressed = False

    def is_button_pressed(self, index):
        """Verifica se un pulsante specifico � premuto"""
        return self.buttons[index].is_pressed

    def are_all_buttons_pressed(self):
        """Verifica se tutti i pulsanti sono premuti contemporaneamente (PULL_UP: 0=premuto)"""
        count = sum(1 for btn in self.buttons if btn.pin.value() == 0)
        return count == len(self.buttons)

    def reset_button_states(self):
        """Reset dello stato di tutti i pulsanti"""
        for button in self.buttons:
            button.is_ready = True
            button.is_pressed = False

    def any_button_pressed(self):
        """Verifica se almeno un pulsante � premuto"""
        return any(btn.is_pressed for btn in self.buttons)

    def random_button(self):
        """Genera un indice casuale di pulsante"""
        return urandom.randint(0, 3)

    def penalty(self, base):
        """Calcola la penalit� temporale basata sul livello"""
        difficulty = -1.0 / (self.level * self.level) + 0.5
        if difficulty > 0:
            return int(difficulty * base)
        return 0

    def millis(self):
        """Restituisce il tempo in millisecondi"""
        return time.ticks_ms()

    def playing_passed(self):
        """Verifica se � passato il tempo di presentazione"""
        return time.ticks_diff(self.millis(), self.timer_playing) >= (500 - self.penalty(400))

    def pause_passed(self):
        """Verifica se � passata la pausa tra presentazioni"""
        return time.ticks_diff(self.millis(), self.timer_pause) >= (300 - self.penalty(200))

    def player_waiting_timeout(self):
        """Verifica se il giocatore ha esaurito il tempo"""
        return time.ticks_diff(self.millis(), self.timer_player_waiting) >= 5000

    def playing_start(self):
        """Avvia il timer di presentazione"""
        self.timer_playing = self.millis()

    def pause_start(self):
        """Avvia il timer di pausa"""
        self.timer_pause = self.millis()

    def player_waiting_start(self):
        """Avvia il timer di attesa del giocatore"""
        self.timer_player_waiting = self.millis()

    def sequence_end_start(self):
        """Avvia il timer per la fine della sequenza"""
        self.timer_sequence_end = self.millis()

    def sequence_end_delay_passed(self):
        """Verifica se è passato 1 secondo dalla fine della sequenza"""
        return time.ticks_diff(self.millis(), self.timer_sequence_end) >= 1000

    def rotate_animation(self):
        """Animazione rotante nella lobby"""
        # Spegne tutti i LED prima di accendere il successivo
        self.stop_leds()
        # Avanza all'animazione successiva usando la sequenza personalizzata
        self.animation_sequence_index = (self.animation_sequence_index + 1) % len(self.animation_sequence)
        self.animation_button = self.animation_sequence[self.animation_sequence_index]
        # Accende solo il LED corrente
        self.led_on(self.animation_button, False)

    def end_game_melody(self):
        """Melodia di fine partita"""
        melody = [250, 196, 196, 220, 196, 0, 247, 250]
        note_durations = [4, 8, 8, 4, 4, 4, 4, 4]

        for i, note in enumerate(melody):
            duration = 1000 // note_durations[i]
            if note > 0:
                self.tone(note, duration)
                self.rotate_animation()
            else:
                time.sleep_ms(duration)
            pause = int(duration * 1.3)
            time.sleep_ms(pause - duration)
            self.no_tone()
            if note > 0:
                self.stop_leds()

    def update_top_1(self):
        self.display_text([
            "TIG-00",
            "",
            "Press a button",
            "",
            f"Record {self.record}",
            f"By {self.record_name}"
        ])

    def change_game_state(self, new_state):
        """Cambia lo stato del gioco"""
        #print(f"State change: {self.game_state} -> {new_state}")
        self.game_state = new_state

        if new_state == self.GameStates.LOBBY:
            self.level = 1
            if self.online:
                self.update_top_1()
            else:
                self.display_text([
                    "TIG-00",
                    "",
                    "Press a button",
                    "",
                    "OFFLINE MODE"
                ])

        elif new_state == self.GameStates.OPTIONS:
            self.no_tone()
            self.stop_leds()
            self.display_text([
                "OPTIONS",
                "B-RESET RECORD",
                "Y-SOUND",
                "R-EXIT"
            ])
            time.sleep(2)

        elif new_state == self.GameStates.OPTIONS_ASK_RESET:
            self.display_text([
                "RESET RECORD ?",
                "B-YES R-NO"
            ])

        elif new_state == self.GameStates.OPTIONS_ASK_SOUND:
            self.display_text([
                "SOUND ?",
                "B-YES R-NO"
            ])

        elif new_state == self.GameStates.SEQUENCE_CREATE_UPDATE:
            if self.online:
                self.display_text([
                    f"Level  {self.level}",
                    "",
                    f"Record {self.record}",
                    f"By {self.record_name}"
                ])
            else:
                self.display_text([
                    f"Level  {self.level}",
                    "",
                    "OFFLINE MODE"
                ])

        elif new_state == self.GameStates.SEQUENCE_PRESENTING:
            self.presenting_index = -1
            self.need_wait = False
            self.sequence_ended = False

        elif new_state == self.GameStates.PLAYER_WAITING:
            self.player_playing_index = 0

        elif new_state == self.GameStates.GAME_OVER:
            self.display_text([
                "GAME OVER !"
            ])

        elif new_state == self.GameStates.INSERT_NAME:
            self.name_letter = 'A'
            self.record_name = ""
            self.display_text([
                "!! NEW RECORD !!",
                "INSERT NAME",
                "R:< Y:> B:OK G:DEL"
            ])

    def rewrite_name(self):
        """Aggiorna la visualizzazione del nome durante l'inserimento"""
        self.display_text([
            "INSERT NAME",
            self.record_name,
            self.name_letter,
            "",
            "R:< Y:> B:OK G:DEL"
        ])

    def handle_lobby(self):
        """Gestisce lo stato LOBBY"""
        # Animazione casuale
        if urandom.randint(0, 400000) == 0:
            self.all_leds_on()
            if self.sound:
                self.tone(self.tones[urandom.randint(0, len(self.tones) - 1)])
            time.sleep_ms(500)
            self.no_tone()
            self.stop_leds()
        else:
            if self.playing_passed():
                self.rotate_animation()

        # Avvia partita se premuto un pulsante
        if self.any_button_pressed():
            self.all_leds_on()
            time.sleep_ms(1500)
            self.stop_leds()
            time.sleep_ms(500)
            self.game_session = self.game_started()
            self.change_game_state(self.GameStates.SEQUENCE_CREATE_UPDATE)

    def handle_sequence_create_update(self):
        """Crea/aggiorna la sequenza di gioco"""
        for n in range(self.level - 1, self.MAX_SEQUENCE_LENGTH):
            if n < self.level:
                self.game_sequence[n] = self.random_button()
            else:
                self.game_sequence[n] = self.NO_BUTTON
        self.change_game_state(self.GameStates.SEQUENCE_PRESENTING)

    def handle_sequence_presenting(self):
        """Presenta la sequenza al giocatore"""
        if self.playing_passed() and not self.need_wait:
            if self.pause_passed():
                self.presenting_index += 1
                current_button = self.game_sequence[self.presenting_index]
                if current_button != self.NO_BUTTON:
                    self.led_on(current_button, True)
                    self.need_wait = True
                else:
                    # Sequenza finita - passa subito a PLAYER_WAITING
                    # Il timer per pulire il display partirà in PLAYER_WAITING
                    self.sequence_ended = True
                    self.sequence_end_start()
                    self.change_game_state(self.GameStates.PLAYER_WAITING)
                    self.player_waiting_start()
        elif self.need_wait and self.playing_passed():
            self.pause_start()
            self.stop_leds()
            self.need_wait = False

    def stop_button_label_on_show_sequence(self):
        if self.online:
            self.display_text([
                f"Level  {self.level}",
                "",
                f"Record {self.record}",
                f"By {self.record_name}"
            ])
        else:
            self.display_text([
                f"Level  {self.level}",
                "",
                "OFFLINE MODE"
            ])
        self.sequence_ended = False

    def handle_player_waiting(self):
        # Pulisci display dopo 1 secondo dalla fine della sequenza
        if self.sequence_ended and self.sequence_end_delay_passed():
            self.stop_button_label_on_show_sequence()

        if self.player_waiting_timeout():
            print("Player TIMEOUT")
            self.all_leds_on()
            if self.sound:
                self.tone(self.tones[4])
            time.sleep(1)

            # Gestione record solo in modalità online
            if self.online:
                self.is_top_record = self.game_ended(self.game_session, self.level)
                if self.is_top_record:
                    self.record = self.level
                    self.name_letter = 'A'
                    self.record_name = ""
                    self.end_game_melody()
                    self.change_game_state(self.GameStates.INSERT_NAME)
                    self.rewrite_name()
                else:
                    self.change_game_state(self.GameStates.GAME_OVER)
            else:
                # Modalità offline - vai direttamente a GAME_OVER
                self.change_game_state(self.GameStates.GAME_OVER)
        else:
            if self.playing_passed() or self.any_button_pressed():
                self.stop_button_label_on_show_sequence()
                self.stop_leds()

                if self.game_sequence[self.player_playing_index] == self.NO_BUTTON:
                    time.sleep_ms(500)
                    self.level += 1
                    self.change_game_state(self.GameStates.SEQUENCE_CREATE_UPDATE)
                else:
                    button_pressed_found = False
                    for i, button in enumerate(self.buttons):
                        if button.is_pressed:
                            if self.game_sequence[self.player_playing_index] == i:
                                self.player_waiting_start()
                                self.led_on(i, True)
                                self.player_playing_index += 1
                                button_pressed_found = True
                                break
                            else:
                                # Errore - gestione record solo in modalità online
                                if self.online:
                                    self.is_top_record = self.game_ended(self.game_session, self.level)

                                    if self.is_top_record:
                                        self.record = self.level
                                        self.name_letter = 'A'
                                        self.record_name = ""
                                        self.end_game_melody()
                                        self.change_game_state(self.GameStates.INSERT_NAME)
                                        self.rewrite_name()
                                    else:
                                        self.change_game_state(self.GameStates.GAME_OVER)
                                else:
                                    # Modalità offline - vai direttamente a GAME_OVER
                                    self.change_game_state(self.GameStates.GAME_OVER)
                                break

    def handle_options(self):
        """Gestisce il menu opzioni"""
        if self.is_button_pressed(3):  # R - Exit
            self.change_game_state(self.GameStates.LOBBY)
        elif self.is_button_pressed(2):  # B - Reset
            self.change_game_state(self.GameStates.OPTIONS_ASK_RESET)
        elif self.is_button_pressed(0):  # Y - Sound
            self.change_game_state(self.GameStates.OPTIONS_ASK_SOUND)

    def handle_options_ask_reset(self):
        """Conferma reset record"""
        if self.is_button_pressed(2):  # B - Yes
            self.record = 0
            self.record_name = ""
            self.change_game_state(self.GameStates.OPTIONS)
        elif self.is_button_pressed(3):  # R - No
            self.change_game_state(self.GameStates.OPTIONS)

    def handle_options_ask_sound(self):
        """Conferma impostazione suono"""
        if self.is_button_pressed(2):  # B - Yes
            self.sound = True
            self.change_game_state(self.GameStates.OPTIONS)
        elif self.is_button_pressed(3):  # R - No
            self.sound = False
            self.change_game_state(self.GameStates.OPTIONS)

    def handle_insert_name(self):
        """Gestisce l'inserimento del nome per il record"""
        if self.is_button_pressed(3):  # Red - Prev letter
            if self.name_letter > 'A':
                self.name_letter = chr(ord(self.name_letter) - 1)
            self.rewrite_name()
        elif self.is_button_pressed(1):  # Yellow - Next letter
            if self.name_letter < 'Z':
                self.name_letter = chr(ord(self.name_letter) + 1)
            self.rewrite_name()
        elif self.is_button_pressed(0):  # Blue - Confirm
            if len(self.record_name) < 3:
                self.record_name += self.name_letter
                self.rewrite_name()
            else:
                if self.is_top_record:
                    self.submit_name(self.game_session,self.record_name)
                    # Ricarica il top score dal server per mostrare il primo classificato
                    self.record_name, self.record = self.get_top_score()
                self.change_game_state(self.GameStates.LOBBY)
        elif self.is_button_pressed(2):  # Green - Delete
            if len(self.record_name) > 0:
                self.record_name = self.record_name[:-1]
            self.rewrite_name()

    def handle_game_over(self):
        """Gestisce lo stato GAME OVER"""
        self.end_game_melody()
        self.change_game_state(self.GameStates.LOBBY)

    def loop(self):
        self.read_buttons()

        # Menu opzioni (tutti i pulsanti premuti)
        if self.are_all_buttons_pressed() and self.game_state != self.GameStates.OPTIONS:
            self.reset_button_states()
            self.change_game_state(self.GameStates.OPTIONS)

        # State machine
        if self.game_state == self.GameStates.LOBBY:
            self.handle_lobby()
        elif self.game_state == self.GameStates.SEQUENCE_CREATE_UPDATE:
            self.handle_sequence_create_update()
        elif self.game_state == self.GameStates.SEQUENCE_PRESENTING:
            self.handle_sequence_presenting()
        elif self.game_state == self.GameStates.PLAYER_WAITING:
            self.handle_player_waiting()
        elif self.game_state == self.GameStates.GAME_OVER:
            self.handle_game_over()
        elif self.game_state == self.GameStates.OPTIONS:
            self.handle_options()
        elif self.game_state == self.GameStates.OPTIONS_ASK_RESET:
            self.handle_options_ask_reset()
        elif self.game_state == self.GameStates.OPTIONS_ASK_SOUND:
            self.handle_options_ask_sound()
        elif self.game_state == self.GameStates.INSERT_NAME:
            self.handle_insert_name()

    def submit_name(self, game_id, nome):
        """Chiama submit-name per registrare il nome (max 5 lettere)"""
        if not self.online:
            # Modalità offline - salva nome nel record locale
            print(f"Modalità offline - salvo nome '{nome}' nel record locale")
            self.record_name = nome
            self._save_record()
            return True

        url = f"{SUPABASE_URL}/functions/v1/submit-name"

        headers = {
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json"
        }

        body = json.dumps({
            "game_id": game_id,
            "player_name": nome.upper()[:5]  # Max 5 lettere maiuscole
        })

        try:
            response = urequests.post(url, headers=headers, data=body)

            if response.status_code == 200:
                print(f"Nome '{nome}' registrato nella classifica!")
                response.close()
                return True
            else:
                print(f"Errore: {response.status_code}")
                response.close()
                return False

        except Exception as e:
            print(f"Errore: {e}")
            return False

    def get_top_score(self):
        """Ottiene il primo classificato"""
        if not self.online:
            # Modalità offline - usa record locale
            print("Modalità offline - uso record locale")
            return self.record_name, self.record

        url = f"{SUPABASE_URL}/functions/v1/get-top-score"

        headers = {
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json"
        }

        response = None
        try:
            print("get-top-score")
            response = urequests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                top_score = data.get("topScore")

                if top_score:
                    player = top_score.get("player_name")
                    score = top_score.get("score")
                    print(f"Top player: {player} - Score: {score}")
                    return player, score
                else:
                    print("Nessun record trovato")
                    return None, None
            else:
                print(f"Errore: {response.status_code}")
                print(response.text)
                return None, None

        except Exception as e:
            print(f"Errore durante la chiamata: {e}")
            return None, None
        finally:
            if response:
                response.close()

    def game_started(self):
        """Chiama start-game per ottenere un game_id"""
        if not self.online:
            # Modalità offline - nessuna sessione online
            print("Modalità offline - nessuna sessione online")
            return None

        url = f"{SUPABASE_URL}/functions/v1/start-game"

        headers = {
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json"
        }

        try:
            print("Inizio nuovo gioco...")
            response = urequests.post(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                game_id = data["game_id"]
                print(f"Gioco iniziato! Game ID: {game_id}")
                response.close()
                return game_id
            else:
                print(f"Errore: {response.status_code}")
                print(response.text)
                response.close()
                return None

        except Exception as e:
            print(f"Errore nella richiesta: {e}")
            return None
        
    def game_ended(self, game_id, punteggio):
        """end-game per salvare il punteggio"""
        if self.online:
            
            url = f"{SUPABASE_URL}/functions/v1/end-game"

            headers = {
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json"
            }

            body = json.dumps({
                "game_id": game_id,
                "score": punteggio
            })

            try:
                print(f"Salvataggio punteggio: {punteggio}")
                response = urequests.post(url, headers=headers, data=body)

                if response.status_code == 200:
                    data = response.json()
                    response.close()
                    return data.get("is_top_record")
                else:
                    print(f"Errore: {response.status_code}")
                    response.close()
                    return False

            except Exception as e:
                print(f"Errore: {e}")
                return False
        else:

            return False


    def start(self, online):
        """Main game entry point"""
        print("Game Starting...")

        self.online = online

        #Press GREEN to switch SOUND mode 
        if not self.buttons[2].pin.value(): # and self.is_button_pressed(1):
            print("sound ON")
            self.sound = not self.sound
            self.tone(200, 200)
            time.sleep(2);

        loop_counter = 0
        scoreboard_counter = 0
        try:
            # Carica record solo se online
            if self.online:
                self.record_name, self.record = self.get_top_score()
            self.change_game_state(self.GameStates.LOBBY)

            while True:
                self.loop()
                time.sleep_ms(5)  # Small delay for stability

                # Periodic garbage collection every ~10 seconds
                loop_counter += 1
                if loop_counter >= 2000:  # ~10s at 5ms per loop
                    gc.collect()
                    loop_counter = 0

                # Periodic leaderboard loading (solo in modalità online)
                if self.online:
                    scoreboard_counter += 1
                    if scoreboard_counter >= 5000:
                        if self.game_state == self.GameStates.LOBBY:
                            self.record_name, self.record = self.get_top_score()
                            self.update_top_1()
                        scoreboard_counter = 0
        except KeyboardInterrupt:
            print("\nGame stopped")


def start(online):
    try:
        game = TIG00()
        game.start(online)
    except Exception as e:
        print(f"ERRORE: {type(e).__name__}: {e}")
        import sys
        sys.print_exception(e)

