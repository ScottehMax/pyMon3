import asyncio
import importlib
import os
import time

import aiohttp

import handler


class Chatbot:
    def __init__(self, **kwargs):
        for arg in kwargs:
            setattr(self, arg, kwargs[arg])
        print("({}) Instance created".format(self.id))
        self.username = self.config[self.id]['username']
        self.server = self.config['DEFAULT']['server']
        self.master = self.config[self.id]['master']
        self.queue = asyncio.Queue(loop=self.loop)
        self.rooms = {}

    async def _connect(self):
        session = aiohttp.ClientSession()
        ws_url = 'ws://{}/showdown/websocket'.format(self.server)
        self.connected = False
        timeout = 1
        while not self.connected:
            try:
                await asyncio.sleep(timeout)
                self.ws = await session.ws_connect(ws_url)
                self.connected = True
                timeout = 1
                self.logintime = int(time.time())
                asyncio.run_coroutine_threadsafe(self.run_message_queue(), loop=self.loop)
                await self.get_message()
            except aiohttp.ClientConnectorError as e:
                timeout += 1
                print(e)

    async def reload_plugins(self):
        self.plugins = []
        self.config.read('config.ini')
        plugin_list = self.config[self.id]['plugins'].split(',')
        for plugin_fn in plugin_list:
            mod_name, ext = os.path.splitext(plugin_fn)
            mod = importlib.import_module('plugins.{}'.format(mod_name))
            mod = importlib.reload(mod)
            plugin = mod.setup(self)
            if type(plugin) != list:
                self.plugins.append(plugin)
            else:
                self.plugins += plugin

    async def _init_plugins(self):
        self.plugins = []
        plugin_list = self.config[self.id]['plugins'].split(',')
        for plugin_fn in plugin_list:
            mod_name, ext = os.path.splitext(plugin_fn)
            mod = importlib.import_module('plugins.{}'.format(mod_name))
            plugin = mod.setup(self)
            if type(plugin) != list:
                self.plugins.append(plugin)
            else:
                self.plugins += plugin

    async def get_message(self):
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                await handler.handle_msg(msg.data, self)
        self.connected = False

    async def run_message_queue(self):
        while True:
            msg = await self.queue.get()
            await self.ws.send_str(msg)
            await asyncio.sleep(0.3)

    async def send(self, room, msg):
        await self.queue.put("{}|{}".format(room, msg))

    async def send_pm(self, user, msg):
        await self.send('', '/pm {},{}'.format(user, msg))
