import discord

from discord.ext import commands

import logging

import json

from datetime import datetime

from cogs.core.help import HelpCommand

from cogs.administration.autoclear import AutoClearSystem

from cogs.administration.logs_config import LogsConfigCommand

from cogs.administration.invites_config import InvitesConfigCommand

from cogs.administration.antispam_config import AntiSpamConfigCommand

from cogs.administration.antilinks_config import AntiLinksConfigCommand

from cogs.moderation.ban import BanCommand

from cogs.moderation.kick import KickCommand

from cogs.moderation.softban import SoftbanCommand

from cogs.moderation.clear import ClearCommand

from cogs.utilities.serverinfo import ServerInfoCommand

from cogs.utilities.userinfo import UserInfoCommand

from cogs.utilities.botinfo import BotInfoCommand

from utils.voice_manager import VoiceManager

from utils.welcome import send_welcome_message

from utils.status import setup_status

from utils.logs import LogsSystem

from utils.invites import InvitesSystem

from utils.antispam import AntiSpamSystem

from utils.antilinks import AntiLinksSystem





logging.basicConfig(

    level=logging.INFO,

    format='%(asctime)s %(levelname)-8s %(message)s',

    datefmt='%Y-%m-%d %H:%M:%S'

)





with open('config.json') as f:

    config = json.load(f)



intents = discord.Intents.all()  



bot = commands.Bot(command_prefix="!", intents=intents)

bot.start_time = datetime.now()




cogs = [
    "cogs.core.help",
    "cogs.utilities.serverinfo",
    "cogs.utilities.userinfo",
    "cogs.utilities.botinfo",
    "cogs.moderation.ban",
    "cogs.moderation.kick",
    "cogs.moderation.softban",
    "cogs.moderation.clear",
    
    "cogs.welcome.welcome_config",
    "cogs.welcome.welcome_events",
    "cogs.games.hangman",
    "cogs.games.tictactoe",
    "cogs.games.scores",
    "cogs.stats.graphs"
]





anti_links = None

anti_spam = None



@bot.event

async def on_ready():

    global anti_links, anti_spam

    

    

    try:

        anti_links = AntiLinksSystem(bot)

        logging.info("âœ… Système anti-liens initialisé")

    except Exception as e:

        logging.error(f"âŒ Erreur lors de l'initialisation du système anti-liens: {e}")

        

    try:

        anti_spam = AntiSpamSystem(bot)

        logging.info("âœ… Système anti-spam initialisé")

    except Exception as e:

        logging.error(f"âŒ Erreur lors de l'initialisation du système anti-spam: {e}")

    

    

    for cog in cogs:

        try:

            await bot.load_extension(cog)

            logging.info(f"âœ… Cog {cog} chargé")

        except Exception as e:

            logging.error(f"âŒ Erreur lors du chargement du cog {cog}: {e}")

    

    

    bot.logs = LogsSystem(bot)

    bot.invites = InvitesSystem(bot)

    

    

    for guild in bot.guilds:

        await bot.invites.cache_invites(guild)

    

    

    admin_cogs = [

        "cogs.administration.autoclear",

        "cogs.administration.logs_config",

        "cogs.administration.invites_config",

        "cogs.administration.antispam_config",

        "cogs.administration.antilinks_config"

    ]

    

    for cog in admin_cogs:

        try:

            await bot.load_extension(cog)

            logging.info(f"âœ… Cog {cog} chargé")

        except Exception as e:

            logging.error(f"âŒ Erreur lors du chargement du cog {cog}: {e}")

    

    

    await bot.add_cog(VoiceManager(bot))

    

    

    await setup_status(bot)

    

    

    try:

        synced = await bot.tree.sync()

        logging.info(f"Commandes slash synchronisées: {len(synced)}")

    except Exception as e:

        logging.error(f"âŒ Erreur lors de la synchronisation des commandes slash: {e}")

    

    logging.info(f"Bot connecté en tant que {bot.user}")





@bot.event

async def on_member_join(member):

    

    inviter = await bot.invites.find_inviter(member)

    await bot.invites.log_member_join(member, inviter)

    await bot.invites.update_invite_cache(member.guild)

    

    

    await send_welcome_message(member)



@bot.event

async def on_member_remove(member):

    

    try:

        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):

            moderator = entry.user

            reason = entry.reason

            if moderator and moderator.id != bot.user.id:

                now = datetime.utcnow()

                entry_time = entry.created_at.replace(tzinfo=None)

                time_diff = (now - entry_time).total_seconds()

                if time_diff < 2:

                    await bot.logs.log_member_kick(member.guild, member, moderator, reason)

    except Exception as e:

        print(f"Erreur lors de la vérification des logs d'audit: {e}")

    

    await bot.invites.log_member_leave(member)





@bot.event

async def on_message(message):

    if message.author == bot.user:

        return

        

    

    if anti_links and await anti_links.check_links(message):

        await message.delete()

        await message.channel.send(

            f"âŒ {message.author.mention}, les liens ne sont pas autorisés dans ce salon!",

            delete_after=5

        )

        return

        

    

    if anti_spam and await anti_spam.is_spam(message):

        await message.delete()

        await message.channel.send(

            f"âŒ {message.author.mention}, vous envoyez trop de messages!",

            delete_after=5

        )

        return

        

    await bot.process_commands(message)



@bot.event

async def on_message_delete(message):

    if message.guild:

        await bot.logs.log_message_delete(message)



@bot.event

async def on_message_edit(before, after):

    if before.guild and before.content != after.content:

        await bot.logs.log_message_edit(before, after)





@bot.event

async def on_member_ban(guild, user):

    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):

        moderator = entry.user

        reason = entry.reason

        if moderator and moderator.id != bot.user.id:

            await bot.logs.log_member_ban(guild, user, moderator, reason)

            break



@bot.event

async def on_member_unban(guild, user):

    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):

        moderator = entry.user

        if moderator and moderator.id != bot.user.id:

            await bot.logs.log_member_unban(guild, user, moderator)

            break





try:

    with open('config.json', 'r') as f:

        config = json.load(f)

        token = config.get('token')

        if not token:

            raise ValueError("Token non trouvé dans config.json")

except Exception as e:

    logging.error(f"âŒ Erreur lors du chargement du token: {e}")

    exit(1)





bot.run(token)
