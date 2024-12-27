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

cache_dir = "/home/mtag/.switchbot/"
cache_limit = 60 # timeout発生時にcache_limit内のファイルがあればその値を返す
reuse_limit = 20 # この秒数内なら再利用する

async def get(address, f):
    async with BleakClient(address) as client:
        
        write_byte = bytearray(b'\x57\x0f\x31')
        await client.write_gatt_char(command_CharacteristicUUID, write_byte)
        data = await client.read_gatt_char(data_CharacteristicUUID)
        # print(data)
        Temperature_I = data[1]
        Temperature_D = data[2]  & 0b01111111
        
        Humidity = data[3]

        json = '{{"temperature":{:2d}.{:1d}, "humidity":{:2d}}}'.format(int(Temperature_D), int(Temperature_I), int(Humidity))
        f.write(json)
        print(json)

def outputCache(f):
    print(f.read())

    
async def body(address, cache_path, f):
    mtime = int(os.stat(cache_path).st_mtime)
    if int(time.time()) - mtime > reuse_limit:
        # 現在 - 更新時刻 = 更新されてからの時間のほうがreuse_limitより長い
        # 場合には取得する
        try:
            await asyncio.wait_for(get(address, f), timeout=30)
        except asyncio.TimeoutError:
            if int(time.time()) - mtime <= cache_limit:
                outputCache(f)
            else:
                raise
    else:
        # それ以外はキャッシュファイルから出力する
        outputCache(f)
        
async def main(address):
    cache_path = cache_dir + address.replace(':', '-')
    if not(os.path.isfile(cache_path)):
        # ファイルを作成
        with open(cache_path, 'w') as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                await asyncio.wait_for(get(address, f), timeout=30)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    else:
        with open(cache_path, 'r+') as f:
            try:
                # 排他ロックを取得
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                await asyncio.wait_for(body(address, cache_path, f), timeout=30)
            except IOError:
                # 排他されていたので、解除を待ってから
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # ここだけ変更
                await asyncio.wait_for(body(address, cache_path, f), timeout=30)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

asyncio.run(main(sys.argv[1]))
