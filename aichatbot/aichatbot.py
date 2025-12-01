import discord
from discord.ext import commands
import aiohttp
import json

from core import checks
from core.models import PermissionLevel


class AIChatbot(commands.Cog):
    """AI Chatbot with optional memory."""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.plugin_db.get_partition(self)
        self.bot_prefix = "?"   # Your required prefix

    async def get_key(self):
        return await self.config.find_one({"_id": "api_key"})

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

    def cog_check(self, ctx):
        return ctx.prefix == self.bot_prefix

    #
    #  COMMAND: aisetkey
    #
    @commands.command(name="aisetkey")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def aisetkey(self, ctx, *, key: str):
        """Set the API key."""
        await self.config.update_one(
            {"_id": "api_key"},
            {"$set": {"value": key}},
            upsert=True
        )
        await ctx.reply("API key saved.", mention_author=False)

    #
    #  COMMAND: airemember
    #
    @commands.command(name="airemember")
    async def airemember(self, ctx):
        """Toggle AI memory ON/OFF."""
        enabled = await self.get_memory_state()
        new_state = not enabled
        await self.update_memory_state(new_state)

        msg = "enabled" if new_state else "disabled"
        await ctx.reply(f"AI memory {msg}.", mention_author=False)

    #
    #  Internal AI generator
    #
    async def generate_ai(self, prompt: str, key: str, memory_enabled: bool):
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        messages = []

        if memory_enabled:
            mem = await self.config.find_one({"_id": "memory_blob"})
            if mem:
                messages.append({"role": "system", "content": mem["value"]})

        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "temperature": 0.7
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    return f"API error {resp.status}: {await resp.text()}"

                data = await resp.json()
                reply = data["choices"][0]["message"]["content"]

                if memory_enabled:
                    await self.config.update_one(
                        {"_id": "memory_blob"},
                        {"$set": {"value": reply}},
                        upsert=True
                    )

                return reply


async def setup(bot):
    await bot.add_cog(AIChatbot(bot))
