#! /home/mtag/.pyenv/shims/python
# -*- coding: utf-8 -*-
import asyncio
import sys
from ZabbixCache import Cache
from bleak import BleakClient
from typing import NoReturn

class SwitchBotTemperature(Cache):
    def __init__(self, cache_dir:str, address:str, timeout:int=30, cache_limit:int = 60, reuse_limit:int=20):
        cache_path = cache_dir + address.replace(':', '-')
        super().__init__(cache_path, timeout=timeout, cache_limit=cache_limit, reuse_limit=reuse_limit)
        self.address = address
        self.data_CharacteristicUUID    = "CBA20003-224D-11E6-9FB8-0002A5D5C51B";
        self.command_CharacteristicUUID = "CBA20002-224D-11E6-9FB8-0002A5D5C51B";

    async def set_json(self) -> NoReturn:
        address:str = self.address
        async with BleakClient(address) as client:
            write_byte = bytearray(b'\x57\x0f\x31')
            await client.write_gatt_char(self.command_CharacteristicUUID, write_byte)
            data = await client.read_gatt_char(self.data_CharacteristicUUID)
            # print(data)
            Temperature_I = data[1]
            Temperature_D = data[2]  & 0b01111111
        
            Humidity = data[3]
            self.json = '{{"temperature":{:2d}.{:1d}, "humidity":{:2d}}}'.format(int(Temperature_D), int(Temperature_I), int(Humidity))

async def main() -> NoReturn:
    switchBot = SwitchBotTemperature("/home/mtag/.switchbot", sys.argv[1])
    await asyncio.wait_for(switchBot.body(), timeout=30)
    
asyncio.run(main())
