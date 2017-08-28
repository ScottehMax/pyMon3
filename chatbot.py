import asyncio
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

    async def _connect(self):
        session = aiohttp.ClientSession()
        ws_url = 'ws://{}/showdown/websocket'.format(self.server)
        self.ws = await session.ws_connect(ws_url)
        self.logintime = int(time.time())
        await self.get_message()

    async def get_message(self):
        while True:
            msg = await self.ws.receive()
            await handler.handle_msg(msg.data, self)

    async def send(self, room, msg):
        await self.ws.send_str("{}|{}".format(room, msg))

    async def send_pm(self, user, msg):
        await self.send('', '/pm {},{}'.format(user, msg))
