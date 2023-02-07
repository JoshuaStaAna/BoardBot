import random

from discord.ext import commands
import discord
from discord.ui import View, Select
from commands import get_member_ping, ping_string, pref_name, is_creator

from cogs.games import Game, games


class connect4(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def con(self, ctx):
        pass

    @con.command()
    async def start(self, ctx, opponent):
        author = ctx.author
        guild = ctx.guild
        if guild is None:
            await ctx.send("Cannot start game in this chat")
            return
        opp = get_member_ping(guild, opponent)
        if opp is not None:
            if games.check_duplicate(Connect4, [opp, author]):
                await ctx.send("Existing game with at least one of the players")
                return
            game = Connect4(guild, ctx.channel, author, [author, opp])
            view = CON_view(game)
            for x in view.children:
                x.placeholder = f"{pref_name(game.turn[0])}"
            game.vs = f"🟡 - {ping_string(game.players[0].id)} vs 🔴 - {ping_string(game.players[1].id)}"
            content = f"{game.status()}\n{game.vs}\n\n{game.show()}"
            msg = await ctx.send(content, view=view)
            game.content = content
            game.msg = msg
            game.view = view
            view.msg = msg
        else:
            await ctx.send("Invalid opponent!")

    @con.command()
    async def exit(self, ctx):
        author = ctx.author
        current = games.get_current(Connect4, [author])
        if current is not None:
            current.view.disable()
            await current.msg.edit(content=f"EXITED!\n{current.vs}\n\n{current.show()}", view=current.view)
            current.destroy()
            await ctx.send("Exited game")
        else:
            await ctx.send("No existing game")


class CON_select(Select):
    def __init__(self):
        options = []
        for x in range(1, 8):
            options.append(discord.SelectOption(label=f"{x}"))
        super().__init__(options=options, placeholder=f"Position")

    async def callback(self, interaction):
        if interaction.user == self.view.game.turn[0]:
            game = self.view.game
            col = int(self.values[0]) - 1
            pos = game.drop(col)
            options = []
            for i in range(len(game.board[0])):  # Columns
                for j in range(len(game.board)):  # Rows
                    if game.board[j][i] is None:
                        options.append(discord.SelectOption(label=f"{i + 1}"))
                        break
            self.options = options
            if options == []:
                game.win = -1
            else:
                game.win = game.win_check(game.turn[1], pos[0], pos[1])
                if game.win is not None:
                    self.disabled = True
                    self.view.is_finished()
                    game.destroy()
            game.switch()
            self.placeholder = f"{pref_name(game.turn[0])}"
            await interaction.response.edit_message(content=f"{game.status()}\n{game.vs}\n\n{game.show()}", view=self.view)


class CON_view(View):
    def __init__(self, con):
        self.game = con
        self.msg = None
        super().__init__(timeout=600)
        self.add_item(CON_select())

    async def on_timeout(self):
        self.disable()
        if self.msg is not None:
            await self.msg.edit(content=f"EXITED!\n{self.game.vs}\n\n{self.game.show()}", view=self.view)
        self.game.destroy()

    def disable(self):
        for x in self.children:
            x.disabled = True


class Connect4(Game):
    def __init__(self, guild, channel, author, players):
        self.board = games.board(7, 6)
        self.select = [None, None]
        self.win = None
        player = random.choice(players)
        self.turn = [player, players.index(player)]
        self.msg = None
        self.vs = ""
        self.view = None
        super().__init__(guild, channel, author, players)

    def __str__(self):
        return super().__str__("Connect4")

    def show(self):
        result = ""
        for i in range(len(self.board)):  # Rows
            for j in range(len(self.board[i])):  # Columns
                match self.board[i][j]:
                    case 0:
                        result += "🟡"
                    case 1:
                        result += "🔴"
                    case _:
                        result += "🟦"
            result += "\n"
        result += "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣"
        return result

    def drop(self, num):
        for x in reversed(range(0, 6)):
            if self.board[x][num] is None:
                self.board[x][num] = self.turn[1]
                return [x, num]
        return [-1, -1]

    def is_turn(self, num):
        if num == self.turn[1]:
            return True
        else:
            return False

    def switch(self):
        for x in self.players:
            if self.turn[0] != x:
                self.turn[0] = x
                break
        if self.turn[1] == 1:
            self.turn[1] = 0
        else:
            self.turn[1] = 1

    def win_check(self, num, i, j):
        #   Horizontal
        row = 0

        #   Right
        for x in reversed(range(0, j)):
            if self.board[i][x] == num:
                row += 1
            else:
                break
        #   Left
        for x in range(j, len(self.board[i])):
            if self.board[i][x] == num:
                row += 1
            else:
                break
        if row > 3:
            return num

        #   Vertical
        row = 0

        #   Down
        for x in reversed(range(0, i)):
            if self.board[x][j] == num:
                row += 1
            else:
                break
        #   Up
        for x in range(i, len(self.board)):
            if self.board[x][j] == num:
                row += 1
            else:
                break
        if row > 3:
            return num

        #   \
        row = 0

        #   Down
        x = 0
        while (i - x) >= 0 and (j - x) >= 0:
            if self.board[i - x][j - x] == num:
                row += 1
            else:
                break
            x += 1
        x = 1
        while (i + x) < len(self.board) and (j + x) < len(self.board[0]):
            if self.board[i + x][j + x] == num:
                row += 1
            else:
                break
            x += 1
        if row > 3:
            return num

        #   /
        row = 0

        #   Down
        x = 0
        while (i + x) < len(self.board) and (j - x) >= 0:
            if self.board[i + x][j - x] == num:
                row += 1
            else:
                break
            x += 1
        x = 1
        while (i - x) >= 0 and (j + x) < len(self.board[0]):
            if self.board[i - x][j + x] == num:
                row += 1
            else:
                break
            x += 1
        if row > 3:
            return num

        return None

    def status(self):

        result = ""

        if self.win is None:
            match self.turn[1]:
                case 0:
                    result += "🟡"
                case 1:
                    result += "🔴"
            result += "'s Turn"
        elif self.win == -1:
            result = "TIED!"
        else:
            match self.win:
                case 0:
                    result += "🟡"
                case 1:
                    result += "🔴"
            result += " WINS!"

        return result


async def setup(bot):
    await bot.add_cog(connect4(bot))
