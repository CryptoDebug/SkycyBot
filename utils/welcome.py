import discord

async def send_welcome_message(member):
    welcome_embed = discord.Embed(
        title="Bienvenue sur **Skycy** ! :coin:",
        description=(
            "**Skycy** est un outil de prédiction crypto qui analyse les tendances pour t'aider à anticiper le marché.\n\n"
            ":small_blue_diamond: **Accède au site** : [Lien vers Skycy.com](https://...)\n"
            ":small_blue_diamond: **Rejoins la discussion** : <
            ":small_blue_diamond: **Besoin d’aide ?** : <
            ":tada: **Participe**, partage ton avis, mais reste respectueux !"
        ),
        color=0x00ff00
    )
    try:
        await member.send(embed=welcome_embed)
    except discord.Forbidden:
        print(f"Impossible d'envoyer un MP à {member.name}")
