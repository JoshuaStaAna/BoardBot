import random

from discord.ext import commands
import discord
from discord.ui import View, Button
from commands import get_member_ping, ping_string

from cogs.games import Game, games


class tictactoe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def ttt(self, ctx):
        pass

    @ttt.command()
    async def start(self, ctx, opponent):
        author = ctx.author
        guild = ctx.guild
        if guild is None:
            await ctx.send("Cannot start game in this chat")
            return
        opp = get_member_ping(guild, opponent)
        if opp is not None:
            if games.check_duplicate(Tictactoe, [opp, author]):
                await ctx.send("Existing game with at least one of the players")
                return
            game = Tictactoe(guild, ctx.channel, author, [author, opp])
            game.vs = f"⭕ {ping_string(game.players[0].id)} vs ❌ {ping_string(game.players[1].id)}"
            view = T_view(game)
            msg = await ctx.send(f"{game.status()}\n{game.vs}", view=view)
            game.msg = msg
            game.view = view
            view.msg = msg
        else:
            await ctx.send("Invalid opponent!")

    @ttt.command()
    async def exit(self, ctx):
        author = ctx.author
        current = games.get_current(Tictactoe, [author])
        if current is not None:
            current.view.disable()
            await current.msg.edit(content=f"EXITED!\n{current.vs}", view=current.view)
            current.destroy()
            await ctx.send("Exited game")
        else:
            await ctx.send("No existing game")


class T_button(Button):
    def __init__(self, ttt, row, col):
        self.ttt = ttt
        self.col = col
        super().__init__(style=discord.ButtonStyle.green, emoji="➖", row=row)

    async def callback(self, interaction):
        if self.ttt.board[self.row][self.col] is None:
            if interaction.user == self.ttt.turn[0]:
                self.ttt.board[self.row][self.col] = self.ttt.turn[1]
                if self.ttt.turn[1] == 0:
                    self.emoji = "⭕"
                    self.style = discord.ButtonStyle.gray
                else:
                    self.emoji = "❌"
                    self.style = discord.ButtonStyle.gray
                self.disabled = True
                self.ttt.switch()

                win = self.ttt.win()
                view = self.view
                if len(win) == 9:
                    for x in view.children:
                        x.style = discord.ButtonStyle.blurple
                        x.disabled = True
                    view.is_finished()
                    self.ttt.destroy()
                elif len(win) == 3:
                    for x in view.children:
                        for y in win:
                            if x.row == y[0] and x.col == y[1]:
                                x.style = discord.ButtonStyle.blurple
                        x.disabled = True
                    view.is_finished()
                    self.ttt.destroy()

                await interaction.response.edit_message(content=f"{self.ttt.status()}\n{self.ttt.vs}", view=self.view)
            else:
                interaction.response.is_done()
        else:
            interaction.response.is_done()


class T_view(View):
    def __init__(self, ttt):
        self.game = ttt
        self.msg = None
        super().__init__(timeout=600)
        for i in range(len(ttt.board)):
            for j in range(len(ttt.board[i])):
                self.add_item(T_button(ttt, i, j))

    async def on_timeout(self):
        self.disable()
        if self.msg is not None:
            await self.msg.edit(content=f"EXPIRED!\n{self.game.vs}", view=self)
        self.game.destroy()

    def disable(self):
        for x in self.children:
            x.disabled = True


class Tictactoe(Game):
    def __init__(self, guild, channel, author, players):
        self.board = games.board(3, 3)
        player = random.choice(players)
        self.turn = [player, players.index(player)]
        self.msg = None
        self.vs = ""
        self.view = None
        super().__init__(guild, channel, author, players)

    def __str__(self):
        return super().__str__("TicTacToe")

    def switch(self):
        for x in self.players:
            if self.turn[0] != x:
                self.turn[0] = x
                break
        if self.turn[1] == 1:
            self.turn[1] = 0
        else:
            self.turn[1] = 1

    def win(self):

        result = [[]]

        for i in range(len(self.board)):  # Rows
            if len(result) == 3:
                break
            result = [[]]
            for j in range(len(self.board[i])):
                check = True
                for k in range(len(result)):
                    if self.board[i][j] is not None:
                        if result != [[]]:
                            if self.board[i][j] != self.board[result[k][0]][result[k][1]] \
                                    and self.board[i][j] is not None:
                                check = False
                                break
                    else:
                        check = False
                        break
                if not check:
                    result = [[]]
                    break
                elif result != [[]]:
                    result.append([i, j])
                else:
                    result = [[i, j]]

        if len(result) != 3:  # Columns
            for j in range(len(self.board[0])):
                if len(result) == 3:
                    break
                result = [[]]
                for i in range(len(self.board)):
                    check = True
                    for k in range(len(result)):
                        if self.board[i][j] is not None:
                            if result != [[]]:
                                if self.board[i][j] != self.board[result[k][0]][result[k][1]] \
                                        and self.board[i][j] is not None:
                                    check = False
                                    break
                        else:
                            check = False
                            break
                    if not check:
                        result = [[]]
                        break
                    elif result != [[]]:
                        result.append([i, j])
                    else:
                        result = [[i, j]]

        if len(result) != 3:  # Diagonal \
            result = [[]]
            for i in range(len(self.board)):
                check = True
                for k in range(len(result)):
                    if self.board[i][i] is not None:
                        if result != [[]]:
                            if self.board[i][i] != self.board[result[k][0]][result[k][1]] \
                                    and self.board[i][i] is not None:
                                check = False
                                break
                    else:
                        check = False
                        break
                if not check:
                    result = [[]]
                    break
                elif result != [[]]:
                    result.append([i, i])
                else:
                    result = [[i, i]]

        if len(result) != 3:  # Diagonal /
            result = [[]]
            for i in range(len(self.board)):
                check = True
                for k in range(len(result)):
                    if self.board[i][len(self.board) - 1 - i] is not None:
                        if result != [[]]:
                            if self.board[i][len(self.board) - 1 - i] != self.board[result[k][0]][result[k][1]] \
                                    and self.board[i][len(self.board) - 1 - i] is not None:
                                check = False
                                break
                    else:
                        check = False
                        break
                if not check:
                    result = [[]]
                    break
                elif result != [[]]:
                    result.append([i, len(self.board) - 1 - i])
                else:
                    result = [[i, len(self.board) - 1 - i]]

        if len(result) != 3:
            for i in range(len(self.board)):  # Tie
                for j in range(len(self.board[i])):
                    if self.board[i][j] is not None:
                        if result == [[]]:
                            result = [[i, j]]
                        else:
                            result.append([i, j])
            if len(result) != 9:
                result = [[]]

        return result

    def status(self):

        result = ""
        win = self.win()

        if len(win) == 9:
            result = "TIED!"
        elif len(win) != 3:
            match self.turn[1]:
                case 0:
                    result += "⭕"
                case 1:
                    result += "❌"
            result += "'s Turn"
        else:
            match self.board[win[1][0]][win[1][1]]:
                case 0:
                    result += "⭕"
                case 1:
                    result += "❌"
            result += " WINS!"

        return result


async def setup(bot):
    await bot.add_cog(tictactoe(bot))
