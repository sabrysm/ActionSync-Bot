from discord.ext import commands, tasks
import discord
import aiosqlite
from utils import Game
from datetime import datetime
import config

class Tasks(commands.Cog):
    """
    Check each game every 5 minutes and if 10 minutes have passed since the last move, end the game
    """
    def __init__(self, bot):
        self.bot = bot
        self.check_inactive_games.start()
        self.reveal_actions.start()

    @tasks.loop(seconds=config.INACTIVE_TIME)
    async def check_inactive_games(self):
        await Game.checkInactiveGames(self.bot)
    
    @tasks.loop(seconds=config.WAIT_TIME_FOR_REVEAL_ACTIONS)
    async def reveal_actions(self):
        await Game.revealActions(self.bot)

async def setup(bot: commands.Bot):
    await bot.add_cog(Tasks(bot), guilds=[discord.Object(id=config.GUILD_ID)])
