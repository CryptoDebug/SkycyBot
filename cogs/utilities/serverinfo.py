import discord
from discord import app_commands
from discord.ext import commands
from utils.colors import get_embed_color
from datetime import datetime

class ServerInfoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="serverinfo", description="Affiche les informations détaillées du serveur")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        
        total_members = guild.member_count
        human_members = len([m for m in guild.members if not m.bot])
        bot_members = len([m for m in guild.members if m.bot])
        online_members = len([m for m in guild.members if m.status != discord.Status.offline])
        text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
        categories = len([c for c in guild.channels if isinstance(c, discord.CategoryChannel)])
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count
        
        
        embed = discord.Embed(
            title=f"🏰 {guild.name}",
            description=f"```{guild.description if guild.description else 'Aucune description'}```\n"
                       f"ID: `{guild.id}`",
            color=guild.owner.color if guild.owner else get_embed_color("utilities")
        )
        
        
        embed.add_field(
            name="👥 Membres",
            value=f"👤 Total: **{total_members:,}**\n"
                  f"👨‍💻 Humains: **{human_members:,}**\n"
                  f"🤖 Bots: **{bot_members:,}**\n"
                  f"🟢 En ligne: **{online_members:,}**",
            inline=True
        )
        
        
        embed.add_field(
            name="📺 Salons",
            value=f"💬 Textuels: **{text_channels:,}**\n"
                  f"🔊 Vocaux: **{voice_channels:,}**\n"
                  f"📑 Catégories: **{categories:,}**\n"
                  f"📊 Total: **{len(guild.channels):,}**",
            inline=True
        )
        
        
        stats_info = f"👑 Rôles: **{len(guild.roles):,}**\n"
        stats_info += f"😀 Emojis: **{len(guild.emojis):,}**\n"
        if boost_level > 0:
            stats_info += f"⭐ Boost Niveau: **{boost_level}**\n"
            stats_info += f"🚀 Boosts: **{boost_count:,}**"
        embed.add_field(
            name="📈 Statistiques",
            value=stats_info,
            inline=True
        )
        
        
        owner_info = "Non disponible"
        if guild.owner:
            owner_info = f"{guild.owner.mention}\n{guild.owner.name}"
        embed.add_field(
            name="👑 Propriétaire", 
            value=owner_info,
            inline=True
        )
        
        embed.add_field(
            name="📅 Création",
            value=f"<t:{int(guild.created_at.timestamp())}:F>\n"
                  f"(<t:{int(guild.created_at.timestamp())}:R>)",
            inline=True
        )
        
        
        verification_level = {
            discord.VerificationLevel.none: "🔓 Aucune",
            discord.VerificationLevel.low: "🔒 Faible",
            discord.VerificationLevel.medium: "🔒 Moyenne",
            discord.VerificationLevel.high: "🔒 Haute",
            discord.VerificationLevel.highest: "🔒 Maximale"
        }
        
        embed.add_field(
            name="🔒 Vérification",
            value=verification_level.get(guild.verification_level, "❓ Inconnue"),
            inline=True
        )
        
        embed.add_field(
            name="🌍 Région",
            value=str(guild.preferred_locale).replace('_', '-').title(),
            inline=True
        )
        
        
        features = []
        if "COMMUNITY" in guild.features:
            features.append("👥 Communauté")
        if "PARTNERED" in guild.features:
            features.append("🤝 Partenaire")
        if "VERIFIED" in guild.features:
            features.append("✅ Vérifié")
        if "DISCOVERABLE" in guild.features:
            features.append("🔍 Découvrable")
        if "FEATURABLE" in guild.features:
            features.append("⭐ Mise en avant")
        
        if features:
            embed.add_field(
                name="✨ Fonctionnalités",
                value="\n".join(features),
                inline=True
            )
        
        
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        
        embed.set_footer(
            text=f"Demandé par {interaction.user.name} • {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
            
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerInfoCommand(bot)) 
