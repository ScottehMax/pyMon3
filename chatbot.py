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
        self.master = self.config['DEFAULT']['master']
        self.plugins = []

    async def _connect(self):
        session = aiohttp.ClientSession()
        ws_url = 'ws://{}/showdown/websocket'.format(self.server)
        self.ws = await session.ws_connect(ws_url)
        self.logintime = int(time.time())
        await self.get_message()

    async def _init_plugins(self):
        plugin_list = self.config[self.id]['plugins'].split(',')
        for plugin_fn in plugin_list:
            mod_name, ext = os.path.splitext(plugin_fn)
            mod = importlib.import_module('plugins.{}'.format(mod_name))
            self.plugins.append(mod.setup(self))

    async def get_message(self):
        while True:
            msg = await self.ws.receive()
            await handler.handle_msg(msg.data, self)

    async def send(self, room, msg):
        await self.ws.send_str("{}|{}".format(room, msg))

    async def send_pm(self, user, msg):
        await self.send('', '/pm {},{}'.format(user, msg))
