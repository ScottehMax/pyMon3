from plugins.plugin import Plugin
import utils


class Eval(Plugin):
    async def match(self, info):
        return (utils.condense(info.get('who')) == self.cb.master and
                info.get('what').startswith('.eval'))

    async def response(self, info):
        command = info.get('what')[6:]
        try:
            if command.startswith('await '):
                command = command[6:]
                result = await eval(command)
                print(result)
            else:
                result = eval(command)
            return result
        except Exception as e:
            await self.cb.send_pm(self.cb.master, str(e) + ': ' + e.__doc__)


class Exec(Plugin):
    async def match(self, info):
        return (utils.condense(info.get('who')) == self.cb.master and
                info.get('what').startswith('.exec'))

    async def response(self, info):
        command = info.get('what')[6:]
        try:
            if command.startswith('await '):
                command = command[6:]
                result = await exec(command)
            else:
                exec(command)
            await self.cb.send_pm(self.cb.master, 'Success!')
        except Exception as e:
            await self.cb.send_pm(self.cb.master, str(e) + ': ' + e.__doc__)


def setup(cb):
    return [Eval(cb), Exec(cb)]
