from discord.ext import commands
from discord import Interaction, Object, Color
from discord.app_commands import Group
import config
from utils import Game, Player
from components import NewGameView

class NewGame(commands.Cog):
    """
    The new game has 
    - Game ID in the footer
    - Two Fields for each player displaying their names
    - Two Fields for Scores
    - Two buttons: Join and Cancel (remove them after a player joins) and send a guide to use /action <text>
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    new = Group(name='new', description='Create a new game')

    @new.command(name='game', description='Create a new game')
    async def new_game(self, interaction: Interaction):
        if not await Game.preGameChecks(interaction):
            return
        await interaction.response.defer()
        new_game_view = NewGameView(interaction.user)
        new_game_embed = await Game.sendEmbed('New Game', 'Waiting for another player to join', Color.blue())
        await interaction.followup.send(view=new_game_view, embed=new_game_embed)
    
    @new_game.error
    async def new_game_error(self, interaction: Interaction, error):
        if isinstance(error, commands.errors.UserInputError):
            await interaction.followup.send('You can only create a game in the PVP channel', ephemeral=True)
        else:
            await interaction.followup.send('An error occurred while creating a new game', ephemeral=True)
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(NewGame(bot), guilds=[Object(id=config.GUILD_ID)])
