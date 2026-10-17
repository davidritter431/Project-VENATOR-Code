# David Ritter
# 10/12/2026

# SSD1306 OLED Display reference
# https://randomnerdtutorials.com/raspberry-pi-pico-ssd1306-oled-micropython/

# Raspberry Pi Pico reference
# https://pip-assets.raspberrypi.com/categories/610-raspberry-pi-pico/documents/RP-008276-DS-2-getting-started-with-pico.pdf

# LoRa communication code references
# https://shillehtek.com/blogs/news/raspberry-pi-pico-w-lora-sender-receiver-system
# https://reyax.com/upload/products_download/download_file/LoRa_AT_Command_RYLR998_RYLR498_EN.pdf

# main.py
# VENATOR Gateway

# Rotary Encoder References
# https://core-electronics.com.au/guides/getting-started-with-rotary-encoders-examples-with-raspberry-pi-pico/#setup

from machine import Pin, SoftI2C
from ssd1309 import SSD1309_I2C
from rotary_irq_rp2 import RotaryIRQ
from rotary import Rotary
import machine
import utime

# OLED setup code
# SCL is Pin 5 and SDA is pin 4
i2c = SoftI2C(scl=Pin(5), sda=Pin(4), freq=100000)

# Size of the OLED screen 128 x 64 pixles
oled_width = 128
oled_height = 64

# Create OLED boject
oled = SSD1309_I2C(oled_width, oled_height, i2c)

tasks = ["Takeoff", "Get Coords", "Go Home"]

# Printing display menu to the OLED display
def display_menu(selected):
    # Refresh OLED
    oled.framebuf.fill(0)
    
    # Header Text
    oled.framebuf.text('Drone Commands:', 0, 0)
    
    # Tasks
    oled.framebuf.text('Takeoff', 10, 12)
    oled.framebuf.text('Get Coords', 10, 22)
    oled.framebuf.text('Go Home', 10, 32)

    # Selector Arrow
    # The selected range is from 0 to 2 so we multiply it by 10 for position.
    oled.framebuf.text(">", 0, 12 + (selected * 10))

    # X, y, Z text and values
    oled.framebuf.text("X:10", 0, 52)
    oled.framebuf.text("Y:20", 42, 52)
    oled.framebuf.text("Z:30", 84, 52)

    # Display the text
    oled.show()
 
# Displaying the status message
def display_status(message):
    # Status message area of the display
    oled.framebuf.fill_rect(0, 42, 128, 10, 0)
    
    # Display status
    oled.framebuf.text(message, 0, 42)
   
    # Display the text
    oled.show()
        
# Setup UART, Baud rate, tx and rx pins for LoRa RYLR998 Module
uart = machine.UART(0, baudrate=115200, tx=machine.Pin(0), rx=machine.Pin(1))

def send_command(command):
    if isinstance(command, str):
        command = command.encode('ascii')
    uart.write(command + b"\r\n")
    utime.sleep(0.5)
    while uart.any():
        response = uart.read()
        if response:
            print("Response:", response.decode('utf-8', 'ignore'))

# This function sets up the address, network and band for our decive
def initialize_lora():
    send_command("AT")
    send_command("AT+ADDRESS=1")
    send_command("AT+NETWORKID=5")
    send_command("AT+BAND=915000000")

    # Configure RYLR998 radio parameters
    send_command("AT+PARAMETER=7,7,1,12")
    
def send_message(task):
    
    # different cases for task send different commands
    if task == 0:
        message = "Takeoff"
      
    elif task == 1:
        message = "Get Coords"
        
    elif task == 2:
        message = "Go Home"
    
    # Sending command to address 2 with message
    command = f"AT+SEND=2,{len(message)},{message}"
    
    # Send command
    send_command(command)
    
    # Print which command was sent
    print("Command Sent:", message)
    
# Rotary Encoder Code
# GPIO pins connected to data pins A and B
# Setting the range of the Rotary Encoder 
rotary = RotaryIRQ(6, 7, min_val=0, max_val=2,range_mode = Rotary.RANGE_BOUNDED, pull_up=True)

# Rotary Button
rbtn = Pin(8, Pin.IN, Pin.PULL_UP)

# Reset Button
btn = Pin(9, Pin.IN, Pin.PULL_UP)

# Track the last known value of the encoder
current_val = 0  

initialize_lora()

display_menu(0)

while True: 
    # What is the encoder value right now?
    new_val = rotary.value()  
    
    # Reset Button if statement
    # Has the button been pressed?
    if btn.value() == 0: 
        print("Reset encoder to:", 0)
        
        # Reset the rotary
        rotary.reset() 
        current_val = 0
        
        # Return arrow back to top
        display_menu(0)
        
        # Waiting for the button to stop being pressed
        utime.sleep_ms(250) 
        
        # Continue to next part of loop
        continue
    
    # Has the rotary button been pressed?
    if rbtn.value() == 0: 
        # Printing to shell
        print("Selected Task:", new_val)
        
        # Display the selected task number
        # The + 1 is because the value starts at 0
        display_status(tasks[new_val])
        
        # After the task has been selected, send LoRa message
        send_message(new_val)
        
        # Reset rotary back to zero
        rotary.reset() 
        current_val = 0
        
        # Waiting for the button to stop being pressed
        utime.sleep_ms(1000)
        
        # Redraw the display menu
        display_menu(0)
        
        display_status("Command Sent")
        
        # Waiting for the button to stop being pressed
        utime.sleep_ms(1000)
        
        # Redraw the display menu
        display_menu(0)
        
        continue
    
    # The encoder value has changed!
    if current_val != new_val:  
        # Do something with the new value
        print('Encoder value:', new_val)  
        
        # Display value from display_menu function
        display_menu(new_val)
        
        # Track this change as the last know value
        current_val = new_val  

    utime.sleep_ms(10)



