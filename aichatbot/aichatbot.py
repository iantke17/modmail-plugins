import discord
from discord.ext import commands
import aiohttp

from core import checks
from core.models import PermissionLevel

class AIChatbot(commands.Cog):
    """AI Chatbot using Pollinations.AI with optional memory."""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.plugin_db.get_partition(self)
        self.bot_prefix = "?"  # Your required prefix

    # --------------------
    # Helpers
    # --------------------
    async def get_key(self):
        key_data = await self.config.find_one({"_id": "api_key"})
        if key_data:
            return key_data.get("value")
        return None

    async def get_memory_state(self):
        mem = await self.config.find_one({"_id": "memory"})
        if mem is None:
            await self.config.update_one(
                {"_id": "memory"},
                {"$set": {"enabled": True}},
                upsert=True
            )
            return True
        return mem.get("enabled", True)

    async def update_memory_state(self, value: bool):
        await self.config.update_one(
            {"_id": "memory"},
            {"$set": {"enabled": value}},
            upsert=True
        )

    async def clear_memory(self):
        await self.config.delete_one({"_id": "memory_blob"})

    def cog_check(self, ctx):
        return ctx.prefix == self.bot_prefix

    # --------------------
    # COMMAND: aisetkey
    # --------------------
    @commands.command(name="aisetkey")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def aisetkey(self, ctx, *, key: str):
        """Set the Pollinations API key."""
        await self.config.update_one(
            {"_id": "api_key"},
            {"$set": {"value": key}},
            upsert=True
        )
        await ctx.reply("Pollinations API key saved.", mention_author=False)

    # --------------------
    # COMMAND: airemember
    # --------------------
    @commands.command(name="airemember")
    async def airemember(self, ctx, *, prompt: str = None):
        """Toggle AI memory ON/OFF and optionally respond to a prompt."""
        enabled = await self.get_memory_state()
        new_state = not enabled
        await self.update_memory_state(new_state)
        msg = "enabled" if new_state else "disabled"

        if prompt:
            key = await self.get_key()
            if not key:
                await ctx.reply("API key not set. Use ?aisetkey first.", mention_author=False)
                return
            reply = await self.generate_ai(prompt, key, memory_enabled=new_state)
            await ctx.reply(f"AI memory {msg}.\n\nResponse: {reply}", mention_author=False)
        else:
            await ctx.reply(f"AI memory {msg}.", mention_author=False)

    # --------------------
    # COMMAND: aiforget
    # --------------------
    @commands.command(name="aiforget")
    async def aiforget(self, ctx, *, prompt: str = None):
        """Clear AI memory and optionally respond to a prompt."""
        await self.clear_memory()

        if prompt:
            key = await self.get_key()
            if not key:
                await ctx.reply("API key not set. Use ?aisetkey first.", mention_author=False)
                return
            reply = await self.generate_ai(prompt, key, memory_enabled=False)
            await ctx.reply(f"AI memory cleared.\n\nResponse: {reply}", mention_author=False)
        else:
            await ctx.reply("AI memory cleared.", mention_author=False)

    # --------------------
    # COMMAND: ai
    # --------------------
    @commands.command(name="ai")
    async def ai(self, ctx, *, prompt: str):
        """Generate AI response using current memory state."""
        key = await self.get_key()
        if not key:
            await ctx.reply("API key not set. Use ?aisetkey first.", mention_author=False)
            return

        memory_enabled = await self.get_memory_state()
        reply = await self.generate_ai(prompt, key, memory_enabled)
        await ctx.reply(reply, mention_author=False)

    # --------------------
    # Internal AI generator using Pollinations with API key
    # --------------------
    async def generate_ai(self, prompt: str, key: str, memory_enabled: bool):
        """
        Calls Pollinations API for text generation using API key.
        """
        url = "https://api.pollinations.ai/v1/generate-text"  # example endpoint

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        payload = {"prompt": prompt}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    return f"API error {resp.status}: {await resp.text()}"

                data = await resp.json()
                reply = data.get("text", "No response from Pollinations.")

                if memory_enabled:
                    await self.config.update_one(
                        {"_id": "memory_blob"},
                        {"$set": {"value": reply}},
                        upsert=True
                    )

                return reply


async def setup(bot):
    await bot.add_cog(AIChatbot(bot))
