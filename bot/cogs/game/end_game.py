from discord.ext import commands
from discord import Interaction, Object, Color
from discord.app_commands import Group
import config
from utils import Game, Player

class EndGame(commands.Cog):
    """The description for EndGame goes here."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    end = Group(name='end', description='End the game')

    @end.command(name='game', description='End the game')
    async def end_game(self, interaction: Interaction):
        if not await Game.preGameChecks(interaction):
            return
        await interaction.response.defer()
        await Game.endGame(interaction)

    @end_game.error
    async def end_game_error(self, interaction: Interaction, error):
        if isinstance(error, commands.errors.UserInputError):
            await interaction.followup.send('You can only end a game in the PVP channel', ephemeral=True)
        else:
            await interaction.followup.send('An error occurred while ending the game', ephemeral=True)
            raise error

async def setup(bot: commands.Bot):
    await bot.add_cog(EndGame(bot), guilds=[Object(id=config.GUILD_ID)])
