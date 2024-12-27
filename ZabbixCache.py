#! /home/mtag/.pyenv/shims/python
# -*- coding: utf-8 -*-
import os
import time
import pathlib
import fcntl
import asyncio
from typing import NoReturn

class Cache:
    """ Fetch external value with cache for zabbix agent
    """

    def __init__(self, cache_path:str, timeout:int=3, cache_limit:int = 1, reuse_limit:int=3):
        """constructor

        Parameters
        ----------
        cache_path : string
            cache file name
        timeout : int
            timeout for get value
        cache_limit : int
            reuse limit on timedout to get value
        reuse_limit : int
            reuse values if cache file are newer than reuse_limit
        """
        self.cache_path:str = cache_path
        self.timeout:int = timeout
        self.cache_limit:int = cache_limit
        self.reuse_limit:int = reuse_limit
        self.json:str = ""

    async def over_write(self) -> NoReturn:
        """ over writer cache file with getting value
        """
        timeout:int = int(self.timeout)
        with open(str(self.cache_path), 'r+') as self.f:
            try:
                # 排他ロックを取得
                fcntl.flock(self.f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                await asyncio.wait_for(self.write(), timeout=timeout)
            except IOError:
                # 排他されていたので、解除を待ってから
                fcntl.flock(self.f.fileno(), fcntl.LOCK_EX)  # ここだけ変更
                await asyncio.wait_for(self.write(), timeout=timeout)
            finally:
                fcntl.flock(self.f.fileno(), fcntl.LOCK_UN)

    async def set_json(self) -> NoReturn:
        """ set value to self.json : abstract method
        """

    async def write(self) -> NoReturn:
        """ get value and write cache
        """
        await asyncio.wait_for(self.set_json(), timeout=self.timeout)
        self.f.write(self.json)
        print(self.json)

    def dumpCache(self) -> NoReturn:
        """ output from cache value
        """
        path:str = str(self.cache_path)        
        with open(path, 'r') as f:
            print(f.read())
    
    async def body(self) -> NoReturn:
        """ main process for get value
        """
        path:str = str(self.cache_path)
        timeout:int = int(self.timeout)
        if not(os.path.isfile(path)):
            # キャッシュがないので値を取得しキャッシュファイルを作成
            with open(path, 'w') as self.f:
                try:
                    fcntl.flock(self.f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    # timeout してもキャッシュがないのでそのままraise
                    await asyncio.wait_for(self.write(), timeout=timeout)
                finally:
                    fcntl.flock(self.f.fileno(), fcntl.LOCK_UN)
        else:
            mtime = int(os.stat(path).st_mtime)
            if int(time.time()) - mtime <= self.reuse_limit:
                # 現在 - 更新時刻 = 更新されてからの時間のほうがreuse_limit以下であれば
                # キャッシュファイルから出力する
                self.dumpCache()
            else:
                # それ以外は取得する
                try:
                    await asyncio.wait_for(self.over_write(), timeout=timeout)
                except asyncio.TimeoutError:
                    # timeoutしたら、キャッシュが利用可能であれば利用する
                    if int(time.time()) - mtime <= self.cache_limit:
                        self.dumpCache()
                    else:
                        raise
