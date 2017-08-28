from plugins.plugin import Plugin
from utils import condense


class Eval(Plugin):
    async def match(self, info):
        return (condense(info.get('who')) == self.cb.master and
                info.get('what').startswith('.eval'))

    async def response(self, info):
        command = info.get('what')[6:]
        try:
            result = eval(command)
            return result
        except Exception as e:
            await self.cb.send_pm(self.cb.master, str(e) + ': ' + e.__doc__)


def setup(cb):
    return Eval(cb)
