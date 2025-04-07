import discord
from discord import app_commands
from discord.ext import commands
from utils.colors import get_embed_color
from utils.logs import LogsSystem
from datetime import datetime

class BanCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logs = LogsSystem(bot)

    @app_commands.command(name="ban", description="Bannir un membre")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message(
                "❌ Permission manquante",
                ephemeral=True
            )

        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(
                "❌ Vous ne pouvez pas bannir ce membre",
                ephemeral=True
            )

        await member.ban(reason=reason)
        await self.logs.log_member_ban(interaction.guild, member, interaction.user, reason)

        embed = discord.Embed(
            title="🔨 Membre banni",
            description=f"ID: `{member.id}`",
            color=get_embed_color("moderation")
        )
        
        
        embed.add_field(
            name="👤 Membre",
            value=f"{member.mention}\n{member.name}
            inline=True
        )
        
        
        embed.add_field(
            name="🛡️ Modérateur",
            value=f"{interaction.user.mention}\n{interaction.user.name}
            inline=True
        )
        
        
        roles = [role.mention for role in member.roles[1:]]  
        roles.reverse()
        roles_text = " ".join(roles) if roles else "Aucun rôle"
        if len(roles_text) > 1024:  
            roles_text = " ".join(roles[:10]) + f"\n... et {len(roles) - 10} autres rôles"
        embed.add_field(
            name=f"👑 Rôles ({len(roles)})",
            value=roles_text,
            inline=False
        )
        
        
        if reason:
            embed.add_field(
                name="📝 Raison",
                value=reason,
                inline=False
            )
        
        
        embed.add_field(
            name="⏰ Date",
            value=f"<t:{int(datetime.now().timestamp())}:F>",
            inline=True
        )
        
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
            
        
        embed.set_footer(
            text=f"Modéré par {interaction.user.name}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(BanCommand(bot)) 
