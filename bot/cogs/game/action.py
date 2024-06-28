from discord.ext import commands
import discord
from discord import app_commands
from utils import Game
import config

class Action(commands.Cog):
    """The description for Action goes here."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name='action', description='Make a move in the game')
    async def action(self, interaction: discord.Interaction, text: str):
        if not Game.isPvpChannel(interaction):
            not_allowed_embed = discord.Embed(title='Not Allowed', description=f'You can only play in the PVP channel: <#{config.PVP_CHANNEL_ID}>', color=discord.Color.red())
            return await interaction.response.send_message(embed=not_allowed_embed, ephemeral=True)
        await Game.takeAction(interaction, text)

async def setup(bot: commands.Bot):
    await bot.add_cog(Action(bot), guilds=[discord.Object(id=config.GUILD_ID)])
