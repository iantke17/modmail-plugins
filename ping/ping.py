import discord
from discord.ext import commands
from core import checks
from core.models import PermissionLevel


class Ping(commands.Cog):
    """Send pings in bulk or filtered by role name."""

    def __init__(self, bot):
        self.bot = bot

    # --------- Commands ----------

    @commands.group(name="ping", invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def ping(self, ctx):
        """Ping roles in bulk. Use subcommands `all` or `with`."""
        await ctx.send("Use `?ping all` or `?ping with <term>`")

    # --------- Ping All Roles ----------
    @ping.command(name="all")
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def ping_all(self, ctx):
        """Ping all roles (excluding @everyone and @here). Admin only."""
        roles = [r for r in ctx.guild.roles if r.name not in ("@everyone", "@here")]
        roles.sort(key=lambda r: r.position, reverse=True)

        if not roles:
            return await ctx.send("No roles found to ping!")

        mentions = " ".join(r.mention for r in roles)
        await ctx.send(mentions)

    # --------- Ping Roles With Term ----------
    @ping.command(name="with")
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def ping_with(self, ctx, *, term: str):
        """Ping roles containing a specific term. Everyone can use."""
        roles = [r for r in ctx.guild.roles if term.lower() in r.name.lower()]

        if not roles:
            return await ctx.send("No roles found with the term!")

        mentions = " ".join(r.mention for r in roles)
        await ctx.send(mentions)


async def setup(bot):
    await bot.add_cog(Ping(bot))
