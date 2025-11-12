from modmail.plugins import Plugin, Command
from discord import PermissionOverwrite
from discord.ext import commands

class PingPlugin(Plugin):
    name = "Ping"
    description = "Send pings in bulk or with specific filters."

    def setup(self):
        # Register commands
        self.add_command(Command(
            name="pingall",
            func=self.ping_all,
            description="Ping all roles except @everyone and @here.",
            perms=["owner", "administrator"]
        ))

        self.add_command(Command(
            name="pingwith",
            func=self.ping_with,
            description="Ping roles containing a specific term.",
            perms=None  # Everyone can use
        ))

    async def ping_all(self, ctx):
        # Permission check
        if not (ctx.author.guild_permissions.administrator or ctx.author.id == ctx.guild.owner_id):
            await ctx.send("Only Owner or Administrator can use this command!")
            return

        roles = [r for r in ctx.guild.roles if r.name not in ("@everyone", "@here")]
        # Sort from highest to lowest
        roles.sort(key=lambda r: r.position, reverse=True)

        if not roles:
            await ctx.send("No roles found to ping!")
            return

        # Send ping in batches if necessary
        mentions = " ".join(r.mention for r in roles)
        await ctx.send(mentions)

    async def ping_with(self, ctx, *, term: str):
        roles = [r for r in ctx.guild.roles if term.lower() in r.name.lower()]

        if not roles:
            await ctx.send("No roles found with the term!")
            return

        mentions = " ".join(r.mention for r in roles)
        await ctx.send(mentions)
