import aiosqlite
import discord
import random
import config
from datetime import datetime


class Player:
    @staticmethod
    async def isMod(user: discord.Member):
        # Check if the user has the mod role
        return any(role.id == config.MOD_ROLE_ID for role in user.roles)
    
    @staticmethod
    async def playerExists(player: discord.User):
        async with aiosqlite.connect('database.db') as db:
            async with db.execute('SELECT player_id FROM players WHERE player_id = ?', (player.id,)) as cursor:
                return await cursor.fetchone()
    
    @staticmethod
    async def addPlayerToDB(player: discord.User):
        async with aiosqlite.connect('database.db') as db:
            await db.execute('INSERT INTO players (player_id, player_name, wins, losses, elo) VALUES (?, ?, ?, ?, ?)', (player.id, player.name, 0, 0, 0))
            await db.commit()

    @staticmethod
    async def getNumberOfActiveGames(player: discord.User):
        await Players.createTableIfNotExists()
        async with aiosqlite.connect('database.db') as db:
            async with db.execute('SELECT game_id FROM games WHERE player1_id = ? OR player2_id = ?', (player.id, player.id)) as cursor:
                return len(await cursor.fetchall())

class Players:
    @staticmethod
    async def createTableIfNotExists():
        async with aiosqlite.connect('database.db') as db:
            await db.execute('CREATE TABLE IF NOT EXISTS players (player_id INTEGER PRIMARY KEY, player_name TEXT, wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0, elo INTEGER DEFAULT 0)')
            await db.commit()

    @staticmethod
    async def addPlayersToDB(player1: discord.User, player2: discord.User):
        await Players.createTableIfNotExists()
        async with aiosqlite.connect('database.db') as db:
            if player1.id == player2.id:
                return
            if not await Player.playerExists(player1):
                await Player.addPlayerToDB(player1)
            if not await Player.playerExists(player2):
                await Player.addPlayerToDB(player2)

class Game:
    @staticmethod
    async def createTableIfNotExists():
        async with aiosqlite.connect('database.db') as db:
            await db.execute('CREATE TABLE IF NOT EXISTS games (game_id INTEGER, player1_id INTEGER, player2_id INTEGER, action1 TEXT, action2 TEXT, status TEXT, last_action_at TEXT, round INTEGER DEFAULT 1)')
            await db.commit()

    @staticmethod
    def generateGameID():
        # Generate a random ID of length 6 including numbers and alphabets
        return ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=6))
    
    
    @staticmethod
    async def createNewGame(player1: discord.User, player2: discord.User):
        game_id = Game.generateGameID()
        await Game.addGameToDB(player1, player2, game_id)
        game_embed = await Game.createGameEmbed(player1, player2, game_id)
        return game_embed

    @staticmethod
    async def addGameToDB(player1: discord.User, player2: discord.User, game_id: str):
        async with aiosqlite.connect('database.db') as db:
            await db.execute('INSERT INTO games (game_id, player1_id, player2_id, action1, action2, status, last_action_at, round) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (game_id, player1.id, player2.id, 'Waiting', 'Waiting', 'active', discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 1))
            await db.commit()

    @staticmethod
    async def createGameEmbed(player1: discord.User, player2: discord.User, game_id: str):
        round_number = await Game.getRoundNumber(game_id)
        description = f'Use `/action <text>` to make a move'
        game_embed = discord.Embed(title=f'{player1.name} vs {player2.name} - Round {round_number[0]}', description=description, color=discord.Color.blue())
        game_embed.add_field(name='Player 1', value=player1.mention, inline=True)
        game_embed.add_field(name='** **', value='** **', inline=True)
        game_embed.add_field(name='Player 2', value=player2.mention, inline=True)
        game_embed.add_field(name='Action 1', value='Waiting', inline=True)
        game_embed.add_field(name='** **', value='** **', inline=True)
        game_embed.add_field(name='Action 2', value='Waiting', inline=True)
        game_embed.set_footer(text=f'Game ID: {game_id}')
        return game_embed
    
    @staticmethod
    async def getRoundNumber(game_id: str):
        async with aiosqlite.connect('database.db') as db:
            async with db.execute('SELECT round FROM games WHERE game_id = ?', (game_id,)) as cursor:
                return await cursor.fetchone()
    
    @staticmethod
    def isPvpChannel(interaction: discord.Interaction):
        return interaction.channel.id == config.PVP_CHANNEL_ID

    @staticmethod
    async def sendEmbed(title: str, description: str, color: discord.Color, channel: discord.TextChannel=None):
        error_embed = discord.Embed(title=title, description=description, color=color)
        if channel:
            return await channel.send(embed=error_embed)
        return error_embed
    
    @staticmethod
    async def checkInactiveGames(bot: discord.Client):
        active_games = await Game.getActiveGames()
        await Game.endInactiveGames(active_games, bot)

    @staticmethod
    async def getActiveGames() -> list:
        await Game.createTableIfNotExists()
        async with aiosqlite.connect('database.db') as db:
            async with db.execute('SELECT game_id, last_action_at FROM games WHERE status = ?', ('active',)) as cursor:
                return await cursor.fetchall()
    
    @staticmethod
    async def endInactiveGames(active_games: list, bot: discord.Client):
        for game in active_games:
            game_id, last_action_at = game
            last_action_at, time_now = Game.getTimestamps(last_action_at)
            time_diff = time_now - last_action_at
            if time_diff.total_seconds() > 600:
                await Game.finishGame(game_id)
                channel = bot.get_channel(config.PVP_CHANNEL_ID)
                await Game.sendEmbed('Game Ended', f'The game with ID {game_id} has ended due to inactivity', discord.Color.red(), channel)
    
    @staticmethod
    def getTimestamps(last_action_at: str):
        # print(f"Last action at: {last_action_at[:-7]}")
        last_action_at = datetime.strptime(last_action_at, '%Y-%m-%d %H:%M:%S')
        time_now = datetime.strptime(discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
        return last_action_at, time_now
    
    @staticmethod
    async def finishGame(game_id: str):
        async with aiosqlite.connect('database.db') as db:
            await db.execute('UPDATE games SET status = ? WHERE game_id = ?', ('finished', game_id))
            await db.commit()

    @staticmethod
    async def checkPermissions(interaction: discord.Interaction, player1: discord.Member):
        # Only the player who created the game and mods can cancel it
        if interaction.user != player1 or not await Player.isMod(interaction.user):
            await interaction.followup.send('You cannot cancel the game', ephemeral=True)
            return False
        return True
    
    @staticmethod
    async def takeAction(interaction: discord.Interaction, text: str):
        await interaction.response.defer(ephemeral=True)
        if not text:
            return await Game.notValidAction(interaction)
        await interaction.followup.send(f'You made a move: {text}')
        await Game.updateGameBoard(interaction, text)
    
    @staticmethod
    async def notValidAction(interaction: discord.Interaction):
        not_valid = discord.Embed(title='Error', description='Please provide a valid action', color=discord.Color.red())
        return await interaction.followup.send(embed=not_valid, ephemeral=True)
    
    @staticmethod
    async def updateGameBoard(interaction: discord.Interaction, text: str):
        game_id, round = await Game.getGameIDandRound(interaction)
        await Game.updateGameInDB(interaction, game_id, round, text)
        game_embed = await Game.getGameBoardFromChannel(interaction, game_id)
        if not game_embed:
            return await Game.gameNotFound(interaction)
        player_number = 1 if await Game.isPlayer1(interaction.user.id, game_id) else 2
        game_embed.set_field_at(player_number * 2 + 1, name=f'Action {player_number}', value='Ready!', inline=True)
        await interaction.followup.send(embed=game_embed)

    @staticmethod
    async def updateGameInDB(interaction: discord.Interaction, game_id: str, round: str, text: str):
        async with aiosqlite.connect('database.db') as db:
            player_number = 1 if await Game.isPlayer1(interaction.user.id, game_id) else 2
            await db.execute(f'UPDATE games SET action{player_number} = ?, last_action_at = ? WHERE game_id = ? and round = ?', (text, discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S'), game_id, round))
            await db.commit()

    @staticmethod
    async def getGameBoardFromChannel(interaction: discord.Interaction, game_id: str):
        pvp_channel = interaction.guild.get_channel(config.PVP_CHANNEL_ID)
        async for message in pvp_channel.history(limit=config.SEARCH_LIMIT):
            if message.embeds and message.embeds[0].footer.text == f'Game ID: {game_id}':
                return message.embeds[0]
            
    @staticmethod
    async def getGameIDandRound(interaction: discord.Interaction):
        async with aiosqlite.connect('database.db') as db:
            async with db.execute('SELECT game_id, round FROM games WHERE player1_id = ? OR player2_id = ?', (interaction.user.id, interaction.user.id)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return await Game.gameNotFound(interaction)
                return row

    @staticmethod
    async def gameNotFound(interaction: discord.Interaction):
        not_found = discord.Embed(title='Game Not Found', description='The game was not found or has ended', color=discord.Color.red())
        return await interaction.followup.send(embed=not_found, ephemeral=True)
    
    @staticmethod
    async def isPlayer1(player_id: int, game_id: str):
        async with aiosqlite.connect('database.db') as db:
            async with db.execute('SELECT player1_id FROM games WHERE game_id = ?', (game_id,)) as cursor:
                player1_id = await cursor.fetchone()
                return player1_id[0] and player1_id[0] == player_id
    
    @staticmethod
    async def preGameChecks(interaction: discord.Interaction):
        if not Game.isPvpChannel(interaction):
            error_embed = discord.Embed(title='Error', description=f'You can only create a game in the PVP channel: <#{config.PVP_CHANNEL_ID}>', color=discord.Color.red())
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return False
        player_active_games = await Player.getNumberOfActiveGames(interaction.user)
        if player_active_games >= 1:
            error_embed = discord.Embed(title='Error', description='You can only play one game at a time', color=discord.Color.red())
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return False
        
        return True
    
    @staticmethod
    async def revealActions(bot: discord.Client):
        ready_games = await Game.getReadyGames()
        for game in ready_games:
            game_id, player1_action, player2_action = game[0], game[3], game[4]
            if player1_action != 'Waiting' and player2_action != 'Waiting':
                await Game.revealActionsInChannel(bot, game_id, player1_action, player2_action)

    @staticmethod
    async def getReadyGames():
        await Game.createTableIfNotExists()
        async with aiosqlite.connect('database.db') as db:
            async with db.execute('SELECT * FROM games WHERE status = ? AND action1 != ? AND action2 != ?', ('active', 'Waiting', 'Waiting')) as cursor:
                return await cursor.fetchall()
            
    @staticmethod
    async def revealActionsInChannel(bot: discord.Client, game_id: str, player1_action: str, player2_action: str):
        pvp_channel = bot.get_guild(config.GUILD_ID).get_channel(config.PVP_CHANNEL_ID)
        messages = [msg async for msg in pvp_channel.history(limit=config.SEARCH_LIMIT)]
        for message in messages:
            if message.embeds and message.embeds[0].footer.text == f'Game ID: {game_id}' and message.embeds[0].fields[3].value == 'Ready!' and message.embeds[0].fields[5].value == 'Ready!':
                game_embed = message.embeds[0]
                game_embed.set_field_at(3, name='Action 1', value=player1_action, inline=True)
                game_embed.set_field_at(5, name='Action 2', value=player2_action, inline=True)
                game_embed.set_footer(text=f'Game ID: {game_id} - Use `/next round` to continue')
                await message.edit(embed=game_embed)
                break
    
    @staticmethod
    async def createNewRound(interaction: discord.Interaction):
        game_id, _ = await Game.getGameIDandRound(interaction)
        ready_games = await Game.getReadyGames()
        for game in ready_games:
            _game_id, player1_id, player2_id, round = game[0], game[1], game[2], game[7]
            if game_id == _game_id:
                await Game.resetRound(game_id, round)
                await Game.startRound(interaction, game_id, player1_id, player2_id)
    
    @staticmethod
    async def startRound(interaction: discord.Interaction, game_id: str, player1_id: int, player2_id: int):
        player1 = interaction.guild.get_member(player1_id)
        player2 = interaction.guild.get_member(player2_id)
        game_embed = await Game.createGameEmbed(player1, player2, game_id)
        pvp_channel = interaction.guild.get_channel(config.PVP_CHANNEL_ID)
        await pvp_channel.send(embed=game_embed)

    
    @staticmethod
    async def resetRound(game_id: str, round: int):
        async with aiosqlite.connect('database.db') as db:
            await db.execute('UPDATE games SET round = round + 1, action1 = ?, action2 = ?, last_action_at = ? WHERE game_id = ? and round = ?', ('Waiting', 'Waiting', discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S'), game_id, round))
            await db.commit()
    
    @staticmethod
    async def endGame(interaction: discord.Interaction):
        game_id, _ = await Game.getGameIDandRound(interaction)
        await Game.finishGame(game_id)
        await interaction.followup.send('The game has ended', ephemeral=True)