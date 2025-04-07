import discord
from discord import app_commands
from discord.ext import commands
from utils.colors import get_embed_color
from utils.invites import InvitesSystem
import asyncio
from datetime import datetime

def admin_or_owner():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator or interaction.user.id == interaction.guild.owner_id:
            return True
        await interaction.response.send_message(
            "❌ Cette commande est réservée aux administrateurs et au propriétaire du serveur.",
            ephemeral=True
        )
        return False
    return app_commands.check(predicate)

class InvitesConfigCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites = InvitesSystem(bot)

    @app_commands.command(name="invites", description="Configure le système d'invitations")
    @admin_or_owner()
    async def invites_config(self, interaction: discord.Interaction):
        
        guild_config = self.bot.invites.get_guild_config(interaction.guild_id)
        
        
        toggle_button = discord.ui.Button(
            label="ON" if not guild_config["enabled"] else "OFF",
            style=discord.ButtonStyle.green if not guild_config["enabled"] else discord.ButtonStyle.red,
            emoji="🔌",
            custom_id="toggle_invites"
        )
        
        joins_button = discord.ui.Button(
            label="Canal des joins",
            style=discord.ButtonStyle.primary,
            emoji="👋",
            custom_id="set_joins_channel"
        )
        
        leaves_button = discord.ui.Button(
            label="Canal des leaves",
            style=discord.ButtonStyle.primary,
            emoji="👋",
            custom_id="set_leaves_channel"
        )
        
        leaderboard_button = discord.ui.Button(
            label="Classement",
            style=discord.ButtonStyle.secondary,
            emoji="🏆",
            custom_id="show_leaderboard"
        )
        
        
        view = discord.ui.View()
        view.add_item(toggle_button)
        view.add_item(joins_button)
        view.add_item(leaves_button)
        view.add_item(leaderboard_button)
        
        
        embed = discord.Embed(
            title="⚙️ Configuration du système d'invitations",
            description="Configurez le système de suivi des invitations.\n\n"
                       "**💡 Guide d'utilisation:**\n"
                       "• Activez/désactivez le système avec le bouton ON/OFF\n"
                       "• Configurez les canaux pour les arrivées et départs\n"
                       "• Consultez le classement des invitations",
            color=get_embed_color("administration")
        )
        
        
        status = "✅ Activé" if guild_config["enabled"] else "❌ Désactivé"
        embed.add_field(
            name="🔌 État du système",
            value=f"**Statut:** {status}\n"
                  f"**ID du serveur:** `{interaction.guild_id}`",
            inline=False
        )
        
        
        joins_channel = interaction.guild.get_channel(guild_config["channels"]["joins"])
        leaves_channel = interaction.guild.get_channel(guild_config["channels"]["leaves"])
        
        channels_info = []
        if joins_channel:
            channels_info.append(f"**👋 Arrivées:** {joins_channel.mention}")
        else:
            channels_info.append("**👋 Arrivées:** Non configuré")
            
        if leaves_channel:
            channels_info.append(f"**👋 Départs:** {leaves_channel.mention}")
        else:
            channels_info.append("**👋 Départs:** Non configuré")
        
        embed.add_field(
            name="📺 Canaux de logs",
            value="\n".join(channels_info),
            inline=False
        )
        
        
        embed.add_field(
            name="⏰ Dernière modification",
            value=f"<t:{int(datetime.now().timestamp())}:F>",
            inline=True
        )
        
        
        embed.set_footer(
            text=f"ID du serveur: {interaction.guild_id}",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        await interaction.response.send_message(embed=embed, view=view)
        
        
        try:
            while True:
                interaction = await self.bot.wait_for(
                    "interaction",
                    check=lambda i: isinstance(i, discord.Interaction) and i.type == discord.InteractionType.component and i.data.get("custom_id") in ["toggle_invites", "set_joins_channel", "set_leaves_channel", "show_leaderboard"]
                )
                
                if not interaction.user.guild_permissions.administrator and interaction.user.id != interaction.guild.owner_id:
                    await interaction.response.send_message(
                        "❌ Cette commande est réservée aux administrateurs et au propriétaire du serveur.",
                        ephemeral=True
                    )
                    continue
                
                if interaction.data["custom_id"] == "toggle_invites":
                    
                    guild_config["enabled"] = not guild_config["enabled"]
                    self.bot.invites.update_guild_config(interaction.guild_id, guild_config)
                    
                    
                    toggle_button.label = "ON" if not guild_config["enabled"] else "OFF"
                    toggle_button.style = discord.ButtonStyle.green if not guild_config["enabled"] else discord.ButtonStyle.red
                    
                    
                    status = "🟢 Activé" if guild_config["enabled"] else "🔴 Désactivé"
                    embed.set_field_at(0, name="🔌 État du système", value=f"**Statut:** {status}\n**ID du serveur:** `{interaction.guild_id}`")
                    
                    await interaction.response.edit_message(embed=embed, view=view)
                    
                elif interaction.data["custom_id"] == "set_joins_channel":
                    await interaction.response.send_message(
                        "🔍 Mentionnez le salon pour les arrivées ou envoyez son ID",
                        ephemeral=True
                    )
                    
                    def check(m):
                        return m.author == interaction.user and m.channel == interaction.channel
                    
                    try:
                        msg = await self.bot.wait_for('message', check=check, timeout=60)
                        channel = None
                        
                        
                        if msg.channel_mentions:
                            channel = msg.channel_mentions[0]
                        else:
                            
                            try:
                                channel_id = int(msg.content)
                                channel = interaction.guild.get_channel(channel_id)
                            except ValueError:
                                await msg.reply("❌ Format invalide. Mentionnez un salon ou envoyez son ID.")
                                continue
                        
                        if channel:
                            guild_config["channels"]["joins"] = channel.id
                            self.bot.invites.update_guild_config(interaction.guild_id, guild_config)
                            
                            
                            channels_info = []
                            channels_info.append(f"**👋 Arrivées:** {channel.mention}")
                            leaves_channel = interaction.guild.get_channel(guild_config["channels"]["leaves"])
                            channels_info.append(f"**👋 Départs:** {leaves_channel.mention if leaves_channel else 'Non configuré'}")
                            embed.set_field_at(1, name="📺 Canaux de logs", value="\n".join(channels_info))
                            
                            await interaction.message.edit(embed=embed, view=view)
                            await msg.reply(f"✅ Salon {channel.mention} configuré pour les arrivées!")
                        else:
                            await msg.reply("❌ Salon non trouvé.")
                            
                    except asyncio.TimeoutError:
                        await interaction.followup.send("❌ Temps écoulé", ephemeral=True)
                        
                elif interaction.data["custom_id"] == "set_leaves_channel":
                    await interaction.response.send_message(
                        "🔍 Mentionnez le salon pour les départs ou envoyez son ID",
                        ephemeral=True
                    )
                    
                    def check(m):
                        return m.author == interaction.user and m.channel == interaction.channel
                    
                    try:
                        msg = await self.bot.wait_for('message', check=check, timeout=60)
                        channel = None
                        
                        
                        if msg.channel_mentions:
                            channel = msg.channel_mentions[0]
                        else:
                            
                            try:
                                channel_id = int(msg.content)
                                channel = interaction.guild.get_channel(channel_id)
                            except ValueError:
                                await msg.reply("❌ Format invalide. Mentionnez un salon ou envoyez son ID.")
                                continue
                        
                        if channel:
                            guild_config["channels"]["leaves"] = channel.id
                            self.bot.invites.update_guild_config(interaction.guild_id, guild_config)
                            
                            
                            channels_info = []
                            joins_channel = interaction.guild.get_channel(guild_config["channels"]["joins"])
                            channels_info.append(f"**👋 Arrivées:** {joins_channel.mention if joins_channel else 'Non configuré'}")
                            channels_info.append(f"**👋 Départs:** {channel.mention}")
                            embed.set_field_at(1, name="📺 Canaux de logs", value="\n".join(channels_info))
                            
                            await interaction.message.edit(embed=embed, view=view)
                            await msg.reply(f"✅ Salon {channel.mention} configuré pour les départs!")
                        else:
                            await msg.reply("❌ Salon non trouvé.")
                            
                    except asyncio.TimeoutError:
                        await interaction.followup.send("❌ Temps écoulé", ephemeral=True)
                        
                elif interaction.data["custom_id"] == "show_leaderboard":
                    await self.bot.invites.show_leaderboard(interaction.guild, interaction.channel)
                    await interaction.response.defer()
                    
        except asyncio.TimeoutError:
            
            for item in view.children:
                item.disabled = True
            await interaction.message.edit(view=view)

async def setup(bot):
    await bot.add_cog(InvitesConfigCommand(bot)) 
