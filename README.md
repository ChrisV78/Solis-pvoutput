# Solis-pvoutput
Solis modbus rs485 to pvoutput

Reading the inverter and uploading to pvoutput is based on https://github.com/bram2202/Ginlong-Solis-mqtt

Changes:
- Added logging that rotates logfiles for a week
- Moved secrets to .env file
- Run as cronjob and not with python scheduler

I run this script with the Solis S5-GR3P5K inverter.

## Requirements
- RS485 to USB converter.
- Linux - Can be on a Respberry pi on or a full server.
- Python 3
- PIP3

## Libraries
Use `pip3 install`
- minimalmodbus
- python-dotenv


## Cron

Add a line to your crontab to run the script every five minutes:

`*/5 6-22 * * * cd /path/to/directory && /usr/bin/python3 ./pvoutput.py`

## USB on PI
I use a fixed USB name in the script, find out your RS485-USB convertor idVendor & idProduct and add this line:

`SUBSYSTEM=="tty", ATTRS{idProduct}=="something", ATTRS{idVendor}=="something", SYMLINK+="ttyUSB_solis"`

to this file:

`/etc/udev/rules.d/10-usb-serial.rules`
