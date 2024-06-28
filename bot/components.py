import discord
from discord import ui
from utils import Players, Player, Game
import asyncio

"""
The new game has 
    - Game ID in the footer
    - Two Fields for each player displaying their names
    - Two Fields for Scores
    - Two buttons: Join and Cancel (remove them after a player joins) and send a guide to use /action <text>
"""

class NewGameView(discord.ui.View):
    def __init__(self, player1: discord.User):
        super().__init__()
        self.player1 = player1
        self.player2 = None
    
    
    @discord.ui.button(label='Join', style=discord.ButtonStyle.primary, custom_id='join')
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if interaction.user == self.player1:
            await interaction.followup.send('You cannot join your own game', ephemeral=True)
            return
        if await Player.getNumberOfActiveGames(interaction.user) >= 1:
            await interaction.followup.send('You can only join one game at a time', ephemeral=True)
            return
        if self.player2 is None:
            self.player2 = interaction.user
            button.disabled = True
            await Players.addPlayersToDB(self.player1, self.player2)
            game_embed = await Game.createNewGame(self.player1, self.player2)
            join_embed = await Game.sendEmbed('Game Joined', f'{self.player2.mention} has joined the game', discord.Color.green())
            await interaction.followup.send(embed=join_embed)
            await asyncio.sleep(1)
            await interaction.followup.edit_message(interaction.message.id, embed=game_embed, view=None)
    
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.danger, custom_id='cancel')
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not await Game.checkPermissions(interaction, self.player1):
            return
        self.clear_items()
        cancelled_embed = discord.Embed(title='Game Cancelled', description='The game has been cancelled', color=discord.Color.red())
        await interaction.followup.send(embed=cancelled_embed, ephemeral=True)
        # Delete the game embed message
        await interaction.followup.delete_message(interaction.message.id)

    async def on_error(self, interaction: discord.Interaction, error, item):
        await Game.sendEmbed('Error', f'An error occurred: {error}', discord.Color.red(), interaction.channel)

    
    