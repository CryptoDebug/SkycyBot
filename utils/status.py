import discord
from discord.ext import tasks

class StatusManager:
    def __init__(self, bot):
        self.bot = bot
        self.statuses = [
            "📊 Prédictions Crypto & Trading",
            "🔍 Analyse de Marché",
            "🔮 Prédictions Crypto 24/7"
        ]
        self.current_index = 0
        self.rotate_status.start()

    def cog_unload(self):
        self.rotate_status.cancel()

    @tasks.loop(seconds=10)
    async def rotate_status(self):
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name=self.statuses[self.current_index]
            )
        )
        self.current_index = (self.current_index + 1) % len(self.statuses)

async def setup_status(bot):
    status_manager = StatusManager(bot)
    bot.status_manager = status_manager
