from discord.ext import commands
import discord
import config

class Bot(commands.Bot):
    def __init__(self, intents: discord.Intents, **kwargs):
        super().__init__(command_prefix=commands.when_mentioned_or('!'), intents=intents, **kwargs)

    async def setup_hook(self):
        for cog in config.cogs:
            try:
                await self.load_extension("cogs."+cog)
            except Exception as exc:
                print(f'Could not load extension {cog} due to {exc.__class__.__name__}: {exc}')
        # sync commands
        await self.tree.sync(guild=discord.Object(id=config.GUILD_ID))

    async def on_ready(self):
        print(f'Logged on as {self.user} (ID: {self.user.id})')


intents = discord.Intents.all()
intents.message_content = True
bot = Bot(intents=intents)

# write general commands here

bot.run(config.token)
