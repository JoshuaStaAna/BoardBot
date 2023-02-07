import random

from discord.ext import commands
import discord
from discord.ui import View, Select, Button
from commands import get_member_ping, ping_string, pref_name, is_creator

from cogs.games import Game, games


class battleship(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def bts(self, ctx):
        pass

    @bts.command()
    async def start(self, ctx, opponent):
        author = ctx.author
        guild = ctx.guild
        if guild is None:
            await ctx.send("Cannot start game in this chat")
            return
        opp = get_member_ping(guild, opponent)
        if opp is not None:
            if games.check_duplicate(Battleship, [opp, author]):
                await ctx.send("Existing game with at least one of the players")
                return
            game = Battleship(guild, ctx.channel, author, [author, opp])
            game.vs = f"1 - {ping_string(author.id)} vs 2 - {ping_string(opp.id)}"
            view = BTS_view_main(game)
            msg = await ctx.send(game.get_message_main(), view=view)
            game.msg_main = msg
            game.view_main = view
            view.msg = msg
            cnt = 0
            for x in game.players:
                index = cnt
                view_player = BTS_view_players(game, index)
                num_opp = view_player.num_opp
                msg_player = await x.send(f"Player {index + 1}\n{game.status()}\n\nOpponent Board"
                                          f"\n{game.show(num_opp, False, [-1, -1])}\n\nYour Board"
                                          f"\n{game.show(index, False, [-1, -1])}", view=view_player)
                view_player.msg = msg_player
                game.view_players[index] = view_player
                game.msg_players[index] = msg_player
                cnt += 1
        else:
            await ctx.send("Invalid opponent!")

    @bts.command()
    async def exit(self, ctx):
        author = ctx.author
        current = games.get_current(Battleship, [author])
        if current is not None:
            current.view_main.disable()
            for x in current.view_players:
                x.disable()
            await current.msg_main.edit(content=f"EXITED!\n\n{current.get_message_main()}", view=current.view_main)
            for x in range(0, 2):
                await current.msg_players[x].edit(content=f"EXITED!\n\n{current.get_message_player(x)}", view=current.view_players[x])
            current.destroy()
            await ctx.send("Exited game")
        else:
            await ctx.send("No existing game")


class BTS_button_place(Button):
    def __init__(self, player):
        self.player = player
        super().__init__(custom_id="button_place", style=discord.ButtonStyle.green, label="Place", disabled=True)

    async def callback(self, interaction):
        cnt = 0
        game = self.view.game
        num = self.view.num
        board = game.board[num]
        pos = self.view.select
        if game.check_game() is False:
            for i in range(len(board)):
                for j in range(len(board[i])):
                    if pos[0] != -1 and pos[1] != -1:
                        if self.view.horizontal and pos[0] == i and get_size(game.turn[num]) > j - pos[1] >= 0 and \
                                board[i][j] is None:
                            cnt += 1
                        elif self.view.horizontal is False and pos[1] == j and get_size(game.turn[num]) > i - pos[
                            0] >= 0 and board[i][j] is None:
                            cnt += 1
            if cnt == get_size(game.turn[num]):
                for i in range(len(board)):
                    for j in range(len(board[i])):
                        if pos[0] != -1 and pos[1] != -1:
                            check = False
                            if self.view.horizontal and pos[0] == i and get_size(game.turn[num]) > j - pos[1] >= 0:
                                check = True
                            elif self.view.horizontal is False and pos[1] == j and get_size(game.turn[num]) > i - pos[
                                0] >= 0:
                                check = True
                            if check:
                                game.board[num][i][j] = game.turn[num]
                game.turn[num] -= 1
                self.view.select[0] = -1
                self.view.select[1] = -1
                self.label = "Place"
                if game.turn[0] == 0 and game.turn[1] == 0:
                    game.turn[0] = random.choice(game.players)
                    for x in range(0, 2):
                        if game.players[x] == game.turn[0]:
                            game.turn[1] = x
                            break
            else:
                self.label = "Invalid Place!"
            await game.update_message_all()
        else:
            await game.update_message_all()
        await interaction.response.defer()


class BTS_button_rotate(Button):
    def __init__(self, player):
        self.player = player
        self.hit = 0
        super().__init__(custom_id="button_rotate", style=discord.ButtonStyle.red, label="Horizontal", disabled=True)

    async def callback(self, interaction):
        game = self.view.game
        num = self.view.num
        num_opp = self.view.num_opp
        board = game.board
        pos = self.view.select
        if game.check_game() is False:
            self.view.horizontal = not self.view.horizontal
            match self.view.horizontal:
                case True:
                    self.label = "Horizontal"
                case False:
                    self.label = "Vertical"
            await game.update_message_all()
        else:
            if board[num_opp][pos[0]][pos[1]] is None:
                board[num_opp][pos[0]][pos[1]] = 0
                self.hit = -1
                self.label = "Miss!"
            else:
                ship = board[num_opp][pos[0]][pos[1]]
                board[num_opp][pos[0]][pos[1]] = -1
                self.hit = -1
                if game.check_ship(num_opp, ship) is False:
                    match ship:
                        case 5:
                            self.label = "Carrier sunk!"
                        case 4:
                            self.label = "Battleship sunk!"
                        case 3:
                            self.label = "Destroyer sunk!"
                        case 2:
                            self.label = "Submarine sunk!"
                        case 1:
                            self.label = "Patrol Boat sunk!"
                else:
                    self.label = "Hit!"

            self.view.select[0] = -1
            self.view.select[1] = -1
            game.switch()
            await game.update_message_all()
        await interaction.response.defer()


class BTS_select(Select):
    def __init__(self, player, num):
        self.num = num
        self.player = player
        if num == 1:
            options = [discord.SelectOption(label="1"),
                       discord.SelectOption(label="2"),
                       discord.SelectOption(label="3"),
                       discord.SelectOption(label="4"),
                       discord.SelectOption(label="5"),
                       discord.SelectOption(label="6"),
                       discord.SelectOption(label="7"),
                       discord.SelectOption(label="8"),
                       discord.SelectOption(label="9"),
                       discord.SelectOption(label="10")]
            placeholder = "1-10"
        else:
            options = [discord.SelectOption(label="A"),
                       discord.SelectOption(label="B"),
                       discord.SelectOption(label="C"),
                       discord.SelectOption(label="D"),
                       discord.SelectOption(label="E"),
                       discord.SelectOption(label="F"),
                       discord.SelectOption(label="G"),
                       discord.SelectOption(label="H"),
                       discord.SelectOption(label="I"),
                       discord.SelectOption(label="J")]
            placeholder = "A-J"

        super().__init__(options=options, placeholder=placeholder)

    async def callback(self, interaction):
        game = self.view.game
        num = self.view.num
        val = self.values[0]
        if game.check_game() is False:
            if game.turn[num] != 0:
                match val:
                    case "A":
                        self.view.select[self.num] = 0
                    case "B":
                        self.view.select[self.num] = 1
                    case "C":
                        self.view.select[self.num] = 2
                    case "D":
                        self.view.select[self.num] = 3
                    case "E":
                        self.view.select[self.num] = 4
                    case "F":
                        self.view.select[self.num] = 5
                    case "G":
                        self.view.select[self.num] = 6
                    case "H":
                        self.view.select[self.num] = 7
                    case "I":
                        self.view.select[self.num] = 8
                    case "J":
                        self.view.select[self.num] = 9
                    case _:
                        self.view.select[self.num] = int(val) - 1
                await game.update_message_all()
        elif game.is_turn(num):
            match val:
                case "A":
                    self.view.select[self.num] = 0
                case "B":
                    self.view.select[self.num] = 1
                case "C":
                    self.view.select[self.num] = 2
                case "D":
                    self.view.select[self.num] = 3
                case "E":
                    self.view.select[self.num] = 4
                case "F":
                    self.view.select[self.num] = 5
                case "G":
                    self.view.select[self.num] = 6
                case "H":
                    self.view.select[self.num] = 7
                case "I":
                    self.view.select[self.num] = 8
                case "J":
                    self.view.select[self.num] = 9
                case _:
                    self.view.select[self.num] = int(val) - 1
            await game.update_message_all()
        await interaction.response.defer()


class BTS_view_main(View):
    def __init__(self, bts):
        self.game = bts
        self.msg = None
        super().__init__(timeout=600)
        pass

    async def on_timeout(self):
        self.disable()
        for x in self.game.view_players:
            if x.timeout >= 0:
                x.timeout = 0
        if self.game.view_main.timeout >= 0:
            self.game.view_main.timeout = 0
        if self.msg is not None:
            await self.msg.edit(content=f"EXPIRED!\n\n{self.game.get_message_main()}", view=self)
        self.game.destroy()

    def disable(self):
        for x in self.children:
            x.disabled = True


class BTS_view_players(View):
    def __init__(self, bts, num):
        self.game = bts
        self.num = num
        self.num_opp = 0
        if num == 0:
            self.num_opp = 1
        self.msg = None
        self.select = [-1, -1]
        self.horizontal = True
        super().__init__(timeout=600)
        for x in range(0, 2):
            self.add_item(BTS_select(self.game.players, 1 - x))
        self.add_item(BTS_button_place(self.game.players))
        self.add_item(BTS_button_rotate(self.game.players))

    async def on_timeout(self):
        self.disable()
        for x in self.game.view_players:
            if x.timeout >= 0:
                x.timeout = 0
        if self.game.view_main.timeout >= 0:
            self.game.view_main.timeout = 0
        if self.msg is not None:
            await self.msg.edit(content=f"EXPIRED!\n\n{self.game.get_message_player(self.num)}", view=self)

    def disable(self):
        for x in self.children:
            x.disabled = True


class Battleship(Game):
    def __init__(self, guild, channel, author, players):
        self.board = [games.board(10, 10), games.board(10, 10)]
        """
        for num in range(0, 2):
            for x in range(2, 6):
                for y in range(0, x + 1):
                    self.board[num][x][y] = x
        self.turn = [1, 1]
        """
        self.turn = [5, 5]
        self.msg_main = None
        self.msg_players = [None, None]
        self.vs = ""
        self.view_main = None
        self.view_players = [None, None]
        super().__init__(guild, channel, author, players)

    def __str__(self):
        return super().__str__("Battleship")

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

    def check_game(self):
        if isinstance(self.turn[0], discord.Member):
            return True
        else:
            return False

    async def update_message_all(self):
        for x in range(0, 2):
            await self.msg_players[x].edit(content=self.get_message_player(x), view=self.view_players[x])
        await self.msg_main.edit(content=self.get_message_main(), view=self.view_main)

    def get_message_main(self):
        game = self
        result = f"{game.status()}\n{game.vs}\n\n1 - {ping_string(game.players[0].id)}" \
                 f"\n{game.show(0, False, [-1, -1])}\n\n2 - {ping_string(game.players[1].id)}" \
                 f"\n{game.show(1, False, [-1, -1])}"
        return result

    def get_message_player(self, num):
        result = ""
        x = self.view_players[num]
        num_opp = x.num_opp
        cnt = 0
        for y in x.select:
            if y != -1:
                cnt += 1
        if self.check_game() is False:
            if self.turn[num] != 0:
                if cnt == 2:
                    button = [y for y in x.children if y.custom_id == "button_place"][0]
                    button.disabled = False
                    button = [y for y in x.children if y.custom_id == "button_rotate"][0]
                    button.disabled = False
                else:
                    button = [y for y in x.children if y.custom_id == "button_place"][0]
                    button.disabled = True
                    button = [y for y in x.children if y.custom_id == "button_rotate"][0]
                    button.disabled = True
            else:
                button = [y for y in x.children if y.custom_id == "button_place"][0]
                button.disabled = True
                button = [y for y in x.children if y.custom_id == "button_rotate"][0]
                button.disabled = True
            index = x.num
            num_opp = x.num_opp
            result = f"Player {index + 1}\n{self.status()}\n\nOpponent Board" \
                     f"\n{self.show(num_opp, True, [-1, -1])}\n\nYour Board" \
                     f"\n{self.show(index, False, x.select)}"
        else:
            if cnt != 2:
                button = [y for y in x.children if y.custom_id == "button_place"][0]
                button.disabled = True
                button.label = "Confirm"
                button = [y for y in x.children if y.custom_id == "button_rotate"][0]
                button.disabled = True
                if button.hit == 0:
                    button.label = "Fire"
            elif self.check_valid(num_opp, x.select) is False:
                button = [y for y in x.children if y.custom_id == "button_place"][0]
                button.disabled = True
                button.label = "Invalid Place"
                button = [y for y in x.children if y.custom_id == "button_rotate"][0]
                button.disabled = True
                if button.hit == 0:
                    button.label = "Fire"
            else:
                button = [y for y in x.children if y.custom_id == "button_place"][0]
                if button.disabled:
                    button.disabled = False
                    button.label = "Confirm"
                else:
                    button.disabled = True
                    button.label = "Confirmed"
                    button = [y for y in x.children if y.custom_id == "button_rotate"][0]
                    button.disabled = False
                    if button.hit == 0:
                        button.label = "Fire"
            button = [y for y in x.children if y.custom_id == "button_rotate"][0]
            if button.hit != 0:
                button.hit = 0
            index = x.num
            num_opp = x.num_opp
            result = f"Player {index + 1}\n{self.status()}\n\nOpponent Board" \
                     f"\n{self.show(num_opp, True, x.select)}\n\nYour Board" \
                     f"\n{self.show(index, False, [-1, -1])}"
        return result

    def check_valid(self, num, pos):
        board = self.board[num]
        if board[pos[0]][pos[1]] != -1 and board[pos[0]][pos[1]] != 0:
            return True
        else:
            return False

    def show(self, num, hidden, pos):
        num_opp = 0
        if num == 0:
            num_opp = 1
        result = ""
        result += "     1    2    3   4    5   6    7   8   9   10\n"
        for i in range(len(self.board[num])):
            match i:
                case 0:
                    result += "A"
                case 1:
                    result += "B "
                case 2:
                    result += "C"
                case 3:
                    result += "D"
                case 4:
                    result += "E "
                case 5:
                    result += "F "
                case 6:
                    result += "G"
                case 7:
                    result += "H"
                case 8:
                    result += "I  "
                case 9:
                    result += "J  "
            result += " "
            for j in range(len(self.board[num][i])):
                bold = False
                if (pos[0] == -1 and pos[1] != -1) or (pos[0] != -1 and pos[1] == -1):
                    if pos[0] == i or pos[1] == j:
                        bold = True
                elif pos[0] != -1 and pos[1] != -1:
                    if self.check_game() is False:
                        if self.view_players[num].horizontal and pos[0] == i and get_size(self.turn[num]) > j - pos[
                            1] >= 0:
                            bold = True
                        elif self.view_players[num].horizontal is False and pos[1] == j and get_size(
                                self.turn[num]) > i - \
                                pos[0] >= 0:
                            bold = True
                    elif pos[0] == i and pos[1] == j:
                        bold = True
                if bold:
                    result += "**"
                if self.board[num][i][j] is not None:
                    if hidden is False:
                        match self.board[num][i][j]:
                            case -1:
                                result += "▣"
                            case 0:
                                result += "▤"
                            case 1:
                                result += "▩"
                            case 2:
                                result += "▦"
                            case 3:
                                result += "◧"
                            case 4:
                                result += "◩"
                            case 5:
                                result += "◰"
                    else:
                        if self.board[num][i][j] == -1:
                            result += "▣"
                        elif self.board[num][i][j] == 0:
                            result += "▤"
                        else:
                            result += "◫"
                else:
                    result += "◫"
                if bold:
                    result += "**"
                result += "  "
            result += "\n"
        return result

    def check_loss(self, num):
        cnt = 0
        for x in range(1, 6):
            if self.check_ship(num, x) is False:
                cnt += 1
        if cnt == 5:
            return True
        return False

    def check_ship(self, num, ship):
        board = self.board[num]
        if self.check_game() is True:
            for i in range(len(board)):
                for j in range(len(board[i])):
                    if board[i][j] == ship:
                        return True
            return False
        return False

    def status(self):

        result = ""

        if self.check_game() is False:
            for x in range(0, 2):
                result += f"{pref_name(self.players[x])}"
                match self.turn[x]:
                    case 5:
                        result += " placing Carrier (Size 5)"
                    case 4:
                        result += " placing Battleship (Size 4)"
                    case 3:
                        result += " placing Destroyer (Size 3)"
                    case 2:
                        result += " placing Submarine (Size 3)"
                    case 1:
                        result += " placing Patrol Boat (Size 2)"
                    case _:
                        result += " READY"
                if x == 0:
                    result += "\n"
        elif self.check_game() and (self.check_loss(0) or self.check_loss(1)):
            if self.check_loss(1):
                result += "1 - "
                num = 0
            else:
                result += "2 - "
                num = 1
            result += f"{pref_name(self.players[num])} WINS!"
            for x in self.view_players:
                x.disable()
                x.is_finished()
            self.view_main.disable()
            self.view_main.is_finished()
        elif self.check_game():
            match self.turn[1]:
                case 0:
                    result += "1 - "
                case 1:
                    result += "2 - "
            result += f"{pref_name(self.turn[0])}'s Turn\n\n"
            for x in range(0, 2):
                result += f"{pref_name(self.players[x])} Ships:\n"
                for y in range(1, 6):
                    match y:
                        case 5:
                            result += "Carrier (Size 5) "
                        case 4:
                            result += "Battleship (Size 4) "
                        case 3:
                            result += "Destroyer (Size 3) "
                        case 2:
                            result += "Submarine (Size 3) "
                        case 1:
                            result += "Patrol Boat (Size 2) "
                    if self.check_ship(x, y):
                        result += "intact"
                    else:
                        result += "sunk"
                    if y != 5:
                        result += "\n"
                if x != 1:
                    result += "\n\n"
                else:
                    result += "\n"
        return result


def get_size(num):
    match num:
        case 5:
            return 5
        case 4:
            return 4
        case 3:
            return 3
        case 2:
            return 3
        case 1:
            return 2


async def setup(bot):
    await bot.add_cog(battleship(bot))
