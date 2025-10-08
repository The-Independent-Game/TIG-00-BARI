# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a MicroPython project for Raspberry Pi Pico2W implementing a Simon Says game with hardware components:
- 4 colored buttons (blue, yellow, green, red) on GPIO pins 4-7
- 4 corresponding LEDs on GPIO pins 11, 10, 2, 3
- Buzzer on GPIO pin 9 (PWM)
- SSD1306 OLED display (128x64) via I2C (SDA: GP0, SCL: GP1)
- Internal LED on GPIO pin 25

## Hardware Pin Configuration

All pins are hardcoded in main.py:
- **Buttons**: GP4 (blue), GP5 (yellow), GP6 (green), GP7 (red) - configured with PULL_UP
- **LEDs**: GP11 (blue), GP10 (yellow), GP2 (green), GP3 (red)
- **Buzzer**: GP9 (PWM)
- **Display I2C**: GP0 (SDA), GP1 (SCL)

Button logic: `value() == 0` means pressed (pull-up resistor configuration)

## Code Architecture

**main.py** - Main game logic:
- `COLORS` dictionary maps color IDs (0-3) to tuples of (LED, button, text, tone)
- Game functions:
  - `flash_color()` - Shows a color with LED, sound, and display
  - `show_sequence()` - Plays the sequence for the player to memorize
  - `wait_for_button()` - Blocking function that waits for player input
  - `check_player_input()` - Validates player's sequence against expected
  - `game_over()` / `game_win()` - Feedback screens
- Main loop handles game flow: start screen → level display → sequence → player input → feedback

**ssd1306.py** - MicroPython OLED driver library (do not modify)
- SSD1306_I2C class for I2C interface
- Provides framebuf-based graphics primitives

**test-scripts/** - Contains simple test scripts for hardware validation

## Deployment

This code runs on a Raspberry Pi Pico with MicroPython firmware. To deploy:
1. Copy main.py and ssd1306.py to the Pico's filesystem
2. The main.py will auto-run on boot if named main.py

No build or test commands - this is embedded hardware code tested directly on device.

## Code Style Notes

- Pylance warnings about unused variables (like loop counters) can be ignored for MicroPython
- Timing delays are critical for debouncing and game flow - modify carefully
- All frequencies (Hz) and durations (seconds) are tuned for game experience
