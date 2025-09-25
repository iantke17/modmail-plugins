import random
import json
import discord
from discord.ext import commands
from core import checks
from core.models import PermissionLevel

FACTS_FILE = "facts.json"


class Fact(commands.Cog):
    """Send and manage facts."""

    def __init__(self, bot):
        self.bot = bot
        self.facts = self.load_facts()

    # --------- Utility functions ----------
    def load_facts(self):
        try:
            with open(FACTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return [
                "The honeybee is the only insect that produces food eaten by humans.",
                "A group of flamingos is called a 'flamboyance'.",
                "The Eiffel Tower can be 15 cm taller during hot days."
            ]

    def save_facts(self):
        with open(FACTS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.facts, f, indent=2, ensure_ascii=False)

    # --------- Commands ----------
    @commands.group(name="fact", invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def fact(self, ctx):
        """Show a random fact."""
        if not self.facts:
            return await ctx.send("No facts available. Use `?fact add <fact>` to add a fact.")

        fact = random.choice(self.facts)
        index = self.facts.index(fact) + 1

        embed = discord.Embed(
            title=f"Fact #{index}",
            description=f"**Did You Know?**\n{fact}",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @fact.command(name="add")
    @checks.has_permissions(PermissionLevel.MOD)
    async def fact_add(self, ctx, *, fact: str):
        """Add a new fact."""
        self.facts.append(fact)
        self.save_facts()
        await ctx.send(f"Fact added #{len(self.facts)}.")

    @fact.command(name="remove")
    @checks.has_permissions(PermissionLevel.MOD)
    async def fact_remove(self, ctx, *, arg: str):
        """Remove a fact by number or exact text."""
        # Remove by number
        if arg.isdigit():
            index = int(arg) - 1
            if 0 <= index < len(self.facts):
                removed = self.facts.pop(index)
                self.save_facts()
                return await ctx.send(f"Fact removed #{index+1}: {removed}")
            else:
                return await ctx.send("Invalid fact number.")

        # Remove by exact text
        if arg in self.facts:
            self.facts.remove(arg)
            self.save_facts()
            return await ctx.send(f"Fact removed: {arg}")

        await ctx.send("Fact not found.")

    @fact.command(name="list")
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def fact_list(self, ctx):
        """List all facts with pagination."""
        if not self.facts:
            return await ctx.send("No facts available.")

        per_page = 5
        pages = (len(self.facts) + per_page - 1) // per_page

        def make_embed(page: int):
            start = page * per_page
            end = start + per_page
            description = "\n".join(
                [f"**#{i+1}**: {fact}" for i, fact in enumerate(self.facts[start:end], start=start)]
            )
            embed = discord.Embed(
                title=f"All Facts (Page {page+1}/{pages})",
                description=description or "No facts on this page.",
                color=discord.Color.blurple()
            )
            return embed

        class FactListView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.page = 0

            async def update(self, interaction: discord.Interaction):
                await interaction.response.edit_message(embed=make_embed(self.page), view=self)

            @discord.ui.button(label="<<", style=discord.ButtonStyle.secondary)
            async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.page = 0
                await self.update(interaction)

            @discord.ui.button(label="<", style=discord.ButtonStyle.secondary)
            async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.page > 0:
                    self.page -= 1
                await self.update(interaction)

            @discord.ui.button(label=">", style=discord.ButtonStyle.secondary)
            async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.page < pages - 1:
                    self.page += 1
                await self.update(interaction)

            @discord.ui.button(label=">>", style=discord.ButtonStyle.secondary)
            async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.page = pages - 1
                await self.update(interaction)

            @discord.ui.button(label="stop", style=discord.ButtonStyle.danger)
            async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                for child in self.children:
                    child.disabled = True
                await interaction.response.edit_message(view=self)

        view = FactListView()
        await ctx.send(embed=make_embed(0), view=view)


async def setup(bot):
    await bot.add_cog(Fact(bot))
