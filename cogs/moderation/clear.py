import discord
from discord import app_commands
from discord.ext import commands
from utils.colors import get_embed_color
from datetime import datetime

class ClearCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clear", description="Supprimer un nombre de messages")
    async def clear(self, interaction: discord.Interaction, amount: int):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message(
                "❌ Permission manquante",
                ephemeral=True
            )

        if amount < 1 or amount > 100:
            return await interaction.response.send_message(
                "❌ Le nombre doit être entre 1 et 100",
                ephemeral=True
            )

        
        await interaction.response.defer(ephemeral=True)
        
        
        deleted = await interaction.channel.purge(limit=amount)
        
        embed = discord.Embed(
            title="🧹 Messages supprimés",
            description=f"ID du salon: `{interaction.channel.id}`",
            color=get_embed_color("moderation")
        )
        
        
        embed.add_field(
            name="📊 Statistiques",
            value=f"📝 Messages supprimés: **{len(deleted):,}**\n"
                  f"📅 Demandés: **{amount:,}**",
            inline=True
        )
        
        
        embed.add_field(
            name="🛡️ Modérateur",
            value=f"{interaction.user.mention}\n{interaction.user.name}
            inline=True
        )
        
        
        embed.add_field(
            name="📺 Salon",
            value=f"{interaction.channel.mention}\n{interaction.channel.name}",
            inline=True
        )
        
        
        embed.add_field(
            name="⏰ Date",
            value=f"<t:{int(datetime.now().timestamp())}:F>",
            inline=True
        )
        
        
        embed.set_footer(
            text=f"Modéré par {interaction.user.name}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )

        
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ClearCommand(bot)) 
