import RPi.GPIO as GPIO
import pn532.pn532 as nfc
from pn532 import *

print("=====    NFC URI Writer  =====")

pn532 = PN532_SPI(debug=False, reset=20, cs=4)
ic, ver, rev, support = pn532.get_firmware_version()
print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))
# Configure PN532 to communicate with NTAG215 cards
pn532.SAM_configuration()

def write(block, block_number):
    data = bytes(block)
    try:
        pn532.ntag2xx_write_block(block_number, data)
        if pn532.ntag2xx_read_block(block_number) == data:
            print('write block %d successfully' % block_number)
    except nfc.PN532Error as e:
        print(e.errmsg)

def splitter(uri_bytes):
    # Write starting at block #6
    block_number = 6
    count = 1
    block = []
    for byte in uri_bytes:
        block.append(byte)
        if count == 4:
            write(block, block_number)
            block_number += 1
            block = []
            count = 1
        else:
            count += 1
    block.append(0x00)
    block.append(0x00)
    write(block, block_number)

while True:
    URI = input("Input album URI here: ")
    uri_bytes = [int(hex(ord(elem)), 16) for elem in URI]
    print("converted to bytes: {}".format(uri_bytes))


    print('Waiting for RFID/NFC card to write to!')
    while True:
        # Check if a card is available to read
        uid = pn532.read_passive_target(timeout=0.5)
        # Try again if no card is available.
        if uid is not None:
            print('Found card with UID:', [hex(i) for i in uid])
            splitter(uri_bytes)
            break
    cont = input("Would you like to continue? (y/n)")
    if cont.lower() == 'y':
        continue
    else:
        break




GPIO.cleanup()
