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
        self.rooms = {}

    async def _connect(self):
        session = aiohttp.ClientSession()
        ws_url = 'ws://{}/showdown/websocket'.format(self.server)
        self.ws = await session.ws_connect(ws_url)
        self.logintime = int(time.time())
        await self.get_message()

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
            await handler.handle_msg(msg.data, self)

    async def send(self, room, msg):
        await self.ws.send_str("{}|{}".format(room, msg))

    async def send_pm(self, user, msg):
        await self.send('', '/pm {},{}'.format(user, msg))
