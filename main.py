import time
import machine
from machine import Pin, ADC
import uasyncio as asyncio
from BLE_CEEO import Yell
from mqtt import MQTTClient

# MIDI Message Constants
NoteOn = 0x90
NoteOff = 0x80
StopNotes = 123

# Volume settings and levels
velocity_levels = [8, 20, 31, 42, 53, 64, 80, 96, 112, 127]
velocity_index = 5  # Start at mid-level volume (64)

# Tempo settings
tempo_delay = 0.5  # Default delay between notes, in seconds

# Initialize photoresistor
photoresistor = ADC(Pin(27))
threshold_value = 1400  # Set threshold for photoresistor coverage

# MQTT setup
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "/djohnsen"

# Function to check if the photoresistor is covered
def is_covered():
    light_value = photoresistor.read_u16()
    print("Light sensor value:", light_value)
    return light_value < threshold_value

# Function to stop all notes immediately
def stop_all_notes(p, scale, channel):
    timestamp_ms = time.ticks_ms()
    tsM = (timestamp_ms >> 7 & 0b111111) | 0x80
    tsL = 0x80 | (timestamp_ms & 0b1111111)
    for note in scale:
        payload_off = bytes([tsM, tsL, NoteOff | channel, note, 0])
        p.send(payload_off)

# Function to adjust volume
def adjust_volume(change):
    global velocity_index
    if change == "increase" and velocity_index < len(velocity_levels) - 1:
        velocity_index += 1
    elif change == "decrease" and velocity_index > 0:
        velocity_index -= 1
    print(f"Volume adjusted to: {velocity_levels[velocity_index]}")

# Function to adjust tempo
def adjust_tempo(change):
    global tempo_delay
    if change == "increase":
        tempo_delay = max(0.1, tempo_delay - 0.05)  # Increase speed, lower delay
    elif change == "decrease":
        tempo_delay += 0.05  # Decrease speed, increase delay
    print(f"Tempo delay set to: {tempo_delay}")

# Function to handle MQTT commands
def mqtt_callback(topic, msg):
    command = msg.decode('utf-8')
    print(f"Received MQTT command: {command}")
    if command == "loud":
        adjust_volume("increase")
    elif command == "quiet":
        adjust_volume("decrease")
    elif command == "fast":
        adjust_tempo("increase")
    elif command == "slow":
        adjust_tempo("decrease")

# MQTT setup
def setup_mqtt():
    client = MQTTClient("pico_client", MQTT_BROKER, port=MQTT_PORT)
    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed to MQTT topic: {MQTT_TOPIC}")
    return client

# Function to play the scale based on the photoresistor status
async def play_scale():
    p = Yell('pico_instrument', verbose=True, type='midi')
    p.connect_up()
    scale = [55, 57, 59, 60, 62, 64, 66, 67]
    channel = 0x0F & 0
    cmd_on = NoteOn
    cmd_off = NoteOff

    while True:
        if not is_covered():
            print("Playing music - photoresistor uncovered")
            for note in scale:
                if is_covered():
                    print("Music paused mid-scale - photoresistor covered")
                    stop_all_notes(p, scale, channel)
                    break

                timestamp_ms = time.ticks_ms()
                tsM = (timestamp_ms >> 7 & 0b111111) | 0x80
                tsL = 0x80 | (timestamp_ms & 0b1111111)

                # Play the note (NoteOn) with the current volume
                payload_on = bytes([tsM, tsL, cmd_on | channel, note, velocity_levels[velocity_index]])
                p.send(payload_on)
                await asyncio.sleep(tempo_delay)

                # Stop the note (NoteOff)
                payload_off = bytes([tsM, tsL, cmd_off | channel, note, 0])
                p.send(payload_off)
                await asyncio.sleep(0.1)
        else:
            print("Music paused - photoresistor covered")
            stop_all_notes(p, scale, channel)
            await asyncio.sleep(0.1)

    p.disconnect()

# Main async function
async def main():
    mqtt_client = setup_mqtt()
    play_scale_task = asyncio.create_task(play_scale())
    
    # Continuously check for new MQTT messages
    while True:
        mqtt_client.check_msg()  # Check for incoming MQTT messages
        await asyncio.sleep(0.1)  # Short delay between checks

# Run the main function
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Program interrupted.")
