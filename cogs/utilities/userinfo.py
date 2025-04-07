import discord
from discord import app_commands
from discord.ext import commands
from utils.colors import get_embed_color
from datetime import datetime

class UserInfoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="Affiche les informations détaillées d'un utilisateur")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        
        
        try:
            member = await interaction.guild.fetch_member(member.id)
        except:
            pass
        
        embed = discord.Embed(
            title=f"👤 {member.name}",
            description=f"ID: `{member.id}`",
            color=member.color or get_embed_color("utilities")
        )
        
        
        embed.add_field(
            name="🎮 Compte Discord",
            value=f"📅 Créé le: <t:{int(member.created_at.timestamp())}:F>\n"
                f"(<t:{int(member.created_at.timestamp())}:R>)",
            inline=True
        )
        embed.add_field(
            name="📥 A rejoint",
            value=f"📅 Le: <t:{int(member.joined_at.timestamp())}:F>\n"
                f"(<t:{int(member.joined_at.timestamp())}:R>)",
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
        
        
        if member.guild_permissions.administrator:
            embed.add_field(
                name="🔑 Permissions",
                value="👑 Administrateur",
                inline=True
            )
        else:
            important_perms = []
            if member.guild_permissions.manage_guild:
                important_perms.append("⚙️ Gestionnaire du serveur")
            if member.guild_permissions.manage_messages:
                important_perms.append("📝 Gestionnaire des messages")
            if member.guild_permissions.manage_roles:
                important_perms.append("🎭 Gestionnaire des rôles")
            if member.guild_permissions.ban_members:
                important_perms.append("🔨 Peut bannir")
            if member.guild_permissions.kick_members:
                important_perms.append("👢 Peut expulser")
            if member.guild_permissions.manage_channels:
                important_perms.append("📺 Gestionnaire des salons")
            if member.guild_permissions.manage_emojis:
                important_perms.append("😀 Gestionnaire des emojis")
            if member.guild_permissions.manage_webhooks:
                important_perms.append("🔗 Gestionnaire des webhooks")
            
            if important_perms:
                embed.add_field(
                    name="🔑 Permissions importantes",
                    value="\n".join(important_perms),
                    inline=True
                )
        
        
        badges = []
        if member.premium_since:
            badges.append("⭐ Nitro")
        if member.bot:
            badges.append("🤖 Bot")
        if member.system:
            badges.append("⚙️ Système")
        if member.discriminator == "0000":
            badges.append("🎮 Nouveau nom d'utilisateur")
        
        
        if member.guild_permissions.administrator:
            badges.append("👑 Admin")
        else:
            
            if (member.guild_permissions.manage_messages or 
                member.guild_permissions.ban_members or 
                member.guild_permissions.kick_members):
                badges.append("📝 Modo")
            
            
            if (member.guild_permissions.manage_roles or 
                member.guild_permissions.manage_guild):
                badges.append("⚙️ Manager")
        
        if badges:
            embed.add_field(
                name="🏆 Badges",
                value="\n".join(badges),
                inline=True
            )
        
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        if member.banner:
            embed.set_image(url=member.banner.url)
            
        
        embed.set_footer(
            text=f"Demandé par {interaction.user.name} • {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
            
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(UserInfoCommand(bot))
