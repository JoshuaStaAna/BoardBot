from discord.ext import commands
import discord


class games(commands.Cog):
    list = []

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, pass_context=True)
    @commands.has_permissions(administrator=True)
    async def games(self, ctx):
        pass

    @games.command()
    async def show(self, ctx):
        result = ""
        cnt = 0
        for x in games.list:
            cnt += 1
            result += f"{cnt}: {x}\n"
        await ctx.send(result)

    @games.command()
    async def reset(self, ctx):
        games.list.clear()

    @classmethod
    def board(cls, w, h):
        matrix = [[None for x in range(w)] for y in range(h)]
        return matrix

    @classmethod
    def check_duplicate(cls, game, players):
        for x in games.list:
            if str(game) == str(type(x)):
                for y in x.players:
                    for z in players:
                        if y == z:
                            return True
        return False

    @classmethod
    def get_current(cls, game, players):
        for x in games.list:
            if str(game) == str(type(x)):
                for y in x.players:
                    for z in players:
                        if y == z:
                            return x
        return None


class Game:
    def __init__(self, guild, channel, author, players):
        self.guild = guild
        self.channel = channel
        self.players = players
        games.list.append(self)

    def __str__(self, string):
        result = ""
        result += string
        if result.endswith("\n") is False:
            result += "\n"
        result += "Players: "
        cnt = 0
        for x in self.players:
            cnt += 1
            if cnt > 1:
                result += ", "
            result += f"{x}"
        return result

    def destroy(self):
        games.list.remove(self)


async def setup(bot):
    await bot.add_cog(games(bot))
