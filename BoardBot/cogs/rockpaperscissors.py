import random

from discord.ext import commands
import discord
from discord.ui import View, Select
from commands import get_member_ping, ping_string, pref_name, is_creator

from cogs.games import Game, games


class Rockpaperscissors(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def rps(self, ctx):
        pass

    @rps.command()
    async def start(self, ctx, opponent):
        author = ctx.author
        guild = ctx.guild
        if guild is None:
            await ctx.send("Cannot start game in this chat")
            return
        opp = get_member_ping(guild, opponent)
        if opp is not None:
            if games.check_duplicate(RockPaperScissors, [opp, author]):
                await ctx.send("Existing game with at least one of the players")
                return
            game = RockPaperScissors(guild, ctx.channel, author, [author, opp])
            view = RPS_view(game)
            content = f"1 - {ping_string(game.players[0].id)} vs 2 - {ping_string(game.players[1].id)}"
            msg = await ctx.send(content, view=view)
            game.content = content
            game.msg = msg
            game.view = view
            view.msg = msg
        else:
            await ctx.send("Invalid opponent!")

    @rps.command()
    async def gun(self, ctx):
        author = ctx.author
        game = games.get_current(RockPaperScissors, [author])
        if is_creator(author):
            if game is not None:
                cnt = 0
                for x in game.players:
                    if x == author:
                        game.select[cnt] = "Gun"
                        break
                    cnt += 1
                if game.select[0] is not None and game.select[1] is not None:
                    winner = game.winner()
                    result = game.progress()
                    game.view.game.content += result
                    if winner is not None:
                        game.view.disable()
                        game.view.is_finished()
                        game.destroy()
                    await game.msg.edit(content=game.content, view=game.view)
                else:
                    result = f"{pref_name(author)} READY"
                    await game.msg.edit(content=f"{game.content}\n{result}",
                                        view=game.view)

    @rps.command()
    async def exit(self, ctx):
        author = ctx.author
        current = games.get_current(RockPaperScissors, [author])
        if current is not None:
            current.view.disable()
            await current.msg.edit(content=f"{current.content}\nEXITED!", view=current.view)
            current.destroy()
            await ctx.send("Exited game")
        else:
            await ctx.send("No existing game")


class RPS_select(Select):
    def __init__(self, player, num):
        self.num = num
        self.player = player
        options = [discord.SelectOption(label="Rock", emoji="🪨"),
                   discord.SelectOption(label="Paper", emoji="📃"),
                   discord.SelectOption(label="Scissors", emoji="✂️")]
        super().__init__(options=options, placeholder=f"{num + 1} - {pref_name(player)}")

    async def callback(self, interaction):
        if interaction.user == self.player:
            game = self.view.game
            game.select[self.num] = self.values[0]
            if game.select[0] is not None and game.select[1] is not None:
                winner = game.winner()
                result = game.progress()
                self.view.game.content += result
                if winner is not None:
                    self.view.disable()
                    self.view.is_finished()
                    game.destroy()
                await interaction.response.edit_message(content=self.view.game.content, view=self.view)
            else:
                result = f"{pref_name(self.player)} READY"
                await interaction.response.edit_message(content=f"{self.view.game.content}\n{result}", view=self.view)


class RPS_view(View):
    def __init__(self, rps):
        self.game = rps
        self.msg = None
        super().__init__(timeout=600)
        cnt = 0
        for x in self.game.players:
            self.add_item(RPS_select(x, cnt))
            cnt += 1

    async def on_timeout(self):
        self.disable()
        if self.msg is not None:
            await self.msg.edit(content=f"{self.content}\nEXPIRED!", view=self)
        self.game.destroy()

    def disable(self):
        for x in self.children:
            x.disabled = True


class RockPaperScissors(Game):
    def __init__(self, guild, channel, author, players):
        self.select = [None, None]
        self.content = ""
        self.msg = None
        self.view = None
        self.round = 1
        super().__init__(guild, channel, author, players)

    def __str__(self):
        return super().__str__("RockPaperScissors")

    def round_end(self, zero, one, win):
        result = f"\nRound {self.round}: "
        self.round += 1
        match zero:
            case "Rock":
                result += "🪨"
            case "Paper":
                result += "📃"
            case "Scissors":
                result += "✂️"
            case "Gun":
                result += "🔫"
        result += " **"
        match win:
            case None:
                result += "="
            case 0:
                result += "<"
            case 1:
                result += ">"
        result += "** "
        match one:
            case "Rock":
                result += "🪨"
            case "Paper":
                result += "📃"
            case "Scissors":
                result += "✂️"
            case "Gun":
                result += "🔫"
        if win is not None:
            result += f"\n{pref_name(self.players[win])} WINS!"
        return result

    def winner(self):
        win = None
        if self.select[0] is not None and self.select[1] is not None:
            zero = str(self.select[0])
            one = str(self.select[1])

            if zero == one:  # Tie
                win = None
            else:
                if zero == "Gun":
                    win = 0
                elif one == "Gun":
                    win = 1
                elif zero == "Rock":
                    if one == "Scissors":
                        win = 0
                    else:
                        win = 1
                elif zero == "Paper":
                    if one == "Rock":
                        win = 0
                    else:
                        win = 1
                elif zero == "Scissors":
                    if one == "Paper":
                        win = 0
                    else:
                        win = 1
        return win

    def progress(self):
        result = ""
        if self.select[0] is not None and self.select[1] is not None:
            win = None
            zero = str(self.select[0])
            self.select[0] = None
            one = str(self.select[1])
            self.select[1] = None

            if zero == one:  # Tie
                print("check")
                win = None
            else:
                if zero == "Gun":
                    win = 0
                elif one == "Gun":
                    win = 1
                elif zero == "Rock":
                    if one == "Scissors":
                        win = 0
                    else:
                        win = 1
                elif zero == "Paper":
                    if one == "Rock":
                        win = 0
                    else:
                        win = 1
                elif zero == "Scissors":
                    if one == "Paper":
                        win = 0
                    else:
                        win = 1
            result = self.round_end(zero, one, win)
        return result


async def setup(bot):
    await bot.add_cog(Rockpaperscissors(bot))
