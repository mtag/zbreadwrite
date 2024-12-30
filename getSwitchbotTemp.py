#! /home/mtag/.pyenv/shims/python
# -*- coding: utf-8 -*-
import os
import time
import pathlib
import sys
import fcntl
import asyncio
from bleak import BleakClient

data_CharacteristicUUID    = "CBA20003-224D-11E6-9FB8-0002A5D5C51B";
command_CharacteristicUUID = "CBA20002-224D-11E6-9FB8-0002A5D5C51B";

async def get(address):
    async with BleakClient(address, timeout=60.0) as client:
        
        write_byte = bytearray(b'\x57\x0f\x31')
        await client.write_gatt_char(command_CharacteristicUUID, write_byte)
        data = await client.read_gatt_char(data_CharacteristicUUID)
        # print(data)
        Temperature_I = data[1]
        Temperature_D = data[2]  & 0b01111111
        
        Humidity = data[3]

        print('{{"temperature":{:2d}.{:1d}, "humidity":{:2d}}}'.format(int(Temperature_D), int(Temperature_I), int(Humidity)))
    
asyncio.run(get(sys.argv[1]))
