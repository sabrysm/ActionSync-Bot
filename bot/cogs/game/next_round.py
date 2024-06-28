from discord.ext import commands
from discord import Interaction, Object, Embed, Color
from discord.app_commands import Group
import config
from utils import Game

class NextRound(commands.Cog):
    """The description for NextRound goes here."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    next = Group(name='next', description='Move to next round')

    @next.command(name='round', description='Move to next round')
    async def next_round(self, interaction: Interaction):
        await interaction.response.defer()
        await Game.createNewRound(interaction)
        await interaction.followup.send('Next round started!', ephemeral=True)
    

async def setup(bot: commands.Bot):
    await bot.add_cog(NextRound(bot), guilds=[Object(id=config.GUILD_ID)])
