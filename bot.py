#!/usr/bin/env python3
# Robux Town — Automatic Order Flow (Blue Border, Persistent, Restart-Safe)
import os
import asyncio
import json
import re
from datetime import datetime
import discord
from discord.ext import commands

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN not set!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="+", intents=intents, help_command=None)

# Channels & Roles
INFO_CHANNEL_ID = 1435516058105675818
DEALS_CHANNEL_ID = 1435516058105675817
STAFF_ROLE_ID = 1435516057526734991

# Emojis (replace IDs if needed)
EMOJI_ROBUX = "<:Robux:1396166686356275200>"
EMOJI_SNOW = "snowflake"  # default, can be changed via +panel

# Persistent storage
DEALS_FILE = "deals.json"

# Default Winter Deals
DEFAULT_DEALS = {
    "title": "WINTER SPECIAL DEALS",
    "emoji": "snowflake",
    "mention": "@everyone",
    "deals": [
        {"amount": 50000, "old": 49.99, "new": 25.00},
        {"amount": 75000, "old": 74.99, "new": 35.00},
        {"amount": 100000, "old": 99.99, "new": 40.00},
        {"amount": 150000, "old": 149.99, "new": 55.00},
        {"amount": 250000, "old": 249.99, "new": 75.00}
    ]
}

# Load or create deals
def load_deals():
    if os.path.exists(DEALS_FILE):
        with open(DEALS_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_DEALS.copy()

def save_deals(data):
    with open(DEALS_FILE, "w") as f:
        json.dump(data, f, indent=2)

deals_data = load_deals()

# --- EMBED: Info Channel (Blue Border) ---
async def send_info_embed():
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if not channel:
        print("Info channel not found!")
        return

    embed = discord.Embed(
        color=0x00A3FF  # BLUE BORDER
    )
    embed.set_author(name="Robux Town™", icon_url="https://i.imgur.com/ROBUXTOWN.png")

    embed.description = (
        "lock **Automated Purchase**\n"
        "A secure, instant Discord bot for buying **Robux** with zero hassle.\n\n"
        "zap **Instant Delivery**\n"
        "Robux hits your account in **under 60 seconds**.\n\n"
        "credit_card **Smart Payments**\n"
        "Fully automated — no middlemen, no delays.\n\n"
        "shield **Bank-Level Security**\n"
        "Every transaction is encrypted and verified.\n\n"
        "globe_with_meridians **Payment Options**\n"
        "• **Visa Gift Card (G2A)**\n"
        "• **PayPal (Eneba)**\n"
        "• **BTC • LTC • SOL • ETH**"
    )

    embed.set_image(url="https://i.imgur.com/ROBUXTOWNBANNER.png")

    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(
        label="Purchase Robux", style=discord.ButtonStyle.blurple, emoji="hexagon",
        custom_id="purchase_robux"
    ))

    await channel.send(embed=embed, view=view)
    print("Info embed sent with BLUE border!")

# --- PURCHASE FLOW: Step-by-Step ---
class PurchaseFlow(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=600)
        self.user_id = user_id
        self.step = 1
        self.robux = 0
        self.price = 0.0
        self.method = ""

    async def start(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        thread = await interaction.channel.create_thread(
            name=f"Purchase-{interaction.user.name}",
            auto_archive_duration=1440,
            reason="Robux Purchase"
        )
        self.thread = thread
        await thread.add_user(interaction.user)
        await self.send_step()

    async def send_step(self):
        if self.step == 1:
            embed = discord.Embed(title="Would you like to start buying Robux? (1/5)", color=0x00A3FF)
            embed.description = "Click **Yes** to begin your purchase."
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="yes1"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="no1"))
            await self.thread.send(embed=embed, view=view)

        elif self.step == 2:
            embed = discord.Embed(title="How much Robux would you like to buy? (2/5)", color=0x00A3FF)
            embed.description = (
                "Please type the amount below.\n"
                f"Example: `100000`\n"
                "Minimum: **10,000** {EMOJI_ROBUX}"
            )
            await self.thread.send(embed=embed)

        elif self.step == 3:
            # Calculate price
            base_rate = 10000 / 10.0  # $10 per 10k
            self.price = (self.robux / base_rate)
            for deal in deals_data["deals"]:
                if self.robux == deal["amount"]:
                    self.price = deal["new"]
                    break

            embed = discord.Embed(title="Confirm Your Purchase (3/5)", color=0x00A3FF)
            embed.description = (
                f"Are you sure you want to buy **{self.robux:,}** {EMOJI_ROBUX}?\n\n"
                f"**Price:** `${self.price:.2f}`"
            )
            if self.price < (self.robux / base_rate):
                embed.description += " (Special Deal!)"
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="yes3"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="no3"))
            await self.thread.send(embed=embed, view=view)

        elif self.step == 4:
            embed = discord.Embed(title="Select Payment Method (4/5)", color=0x00A3FF)
            embed.description = "Choose your preferred payment option."
            select = discord.ui.Select(
                placeholder="Select payment method",
                options=[
                    discord.SelectOption(label="Visa Gift Card (G2A)", value="visa", emoji="credit_card"),
                    discord.SelectOption(label="PayPal (Eneba)", value="paypal", emoji="money_with_wings"),
                    discord.SelectOption(label="BTC", value="btc", emoji="coin"),
                    discord.SelectOption(label="LTC", value="ltc", emoji="coin"),
                    discord.SelectOption(label="SOL", value="sol", emoji="gem"),
                    discord.SelectOption(label="ETH", value="eth", emoji="gem"),
                ]
            )
            select.callback = self.select_callback
            view = discord.ui.View()
            view.add_item(select)
            await self.thread.send(embed=embed, view=view)

        elif self.step == 5:
            embed = discord.Embed(title="Payment Invoice (5/5)", color=0x00A3FF)
            if "visa" in self.method:
                embed.description = (
                    "Please purchase a **Rewarble Visa Gift Card** for the exact amount.\n"
                    f"**Amount:** `${self.price:.2f}`\n\n"
                    "After purchase, reply with the **gift card code**."
                )
            else:
                embed.description = f"Send **${self.price:.2f}** to the address provided by staff."
            await self.thread.send(embed=embed)

    async def select_callback(self, interaction: discord.Interaction):
        self.method = interaction.data["values"][0]
        await interaction.response.defer()
        self.step = 5
        await self.send_step()

# --- BUTTON CALLBACKS ---
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data or "custom_id" not in interaction.data:
        return

    cid = interaction.data["custom_id"]

    if cid == "purchase_robux":
        flow = PurchaseFlow(interaction.user.id)
        await flow.start(interaction)

    elif cid.startswith("yes1"):
        flow = PurchaseFlow(interaction.user.id)
        await interaction.response.defer()
        flow.step = 2
        flow.thread = interaction.channel
        await flow.send_step()

    elif cid.startswith("yes3"):
        flow = PurchaseFlow(interaction.user.id)
        await interaction.response.defer()
        flow.step = 4
        flow.thread = interaction.channel
        await flow.send_step()

    elif cid.startswith("no"):
        await interaction.response.send_message("Purchase cancelled.", ephemeral=True)

# --- MESSAGE HANDLER: Step 2 Input ---
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.channel.name.startswith("Purchase-"):
        return await bot.process_commands(message)

    # Step 2: Robux amount
    if re.fullmatch(r"\d{5,}", message.content):
        try:
            amount = int(message.content.replace(",", ""))
            if amount < 10000:
                await message.reply("Minimum order is **10,000** Robux.")
                return
            flow = PurchaseFlow(message.author.id)
            flow.robux = amount
            flow.step = 3
            flow.thread = message.channel
            await flow.send_step()
            await message.delete()
        except:
            pass
    await bot.process_commands(message)

# --- ADMIN PANEL: +panel ---
@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):
    embed = discord.Embed(title="Winter Deals Panel", color=0x00A3FF)
    embed.description = (
        "Edit your **Winter Specials** below.\n"
        "Use the fields to update title, emoji, and prices."
    )
    modal = WinterDealsModal()
    await ctx.send(embed=embed, view=discord.ui.View().add_item(discord.ui.Button(label="Edit Deals", style=discord.ButtonStyle.blurple, custom_id="open_modal")))
    # Modal handled below

class WinterDealsModal(discord.ui.Modal, title="Edit Winter Deals"):
    title_input = discord.ui.TextInput(label="Deal Title", default=deals_data["title"])
    emoji_input = discord.ui.TextInput(label="Emoji (name or ID)", default=deals_data["emoji"])
    deal1 = discord.ui.TextInput(label="50k: Old $ / New $", placeholder="49.99 / 25.00")
    deal2 = discord.ui.TextInput(label="75k: Old $ / New $", placeholder="74.99 / 35.00")
    deal3 = discord.ui.TextInput(label="100k: Old $ / New $", placeholder="99.99 / 40.00")
    deal4 = discord.ui.TextInput(label="150k: Old $ / New $", placeholder="149.99 / 55.00")
    deal5 = discord.ui.TextInput(label="250k: Old $ / New $", placeholder="249.99 / 75.00")

    async def on_submit(self, interaction: discord.Interaction):
        global deals_data
        deals_data["title"] = self.title_input.value
        deals_data["emoji"] = self.emoji_input.value
        deals = [self.deal1.value, self.deal2.value, self.deal3.value, self.deal4.value, self.deal5.value]
        new_deals = []
        for i, d in enumerate(deals):
            try:
                old, new = map(float, d.split("/"))
                amount = [50000,75000,100000,150000,250000][i]
                new_deals.append({"amount": amount, "old": old, "new": new})
            except:
                pass
        deals_data["deals"] = new_deals
        save_deals(deals_data)

        # Post updated deals
        channel = bot.get_channel(DEALS_CHANNEL_ID)
        if channel:
            emoji = deals_data["emoji"]
            if emoji.isdigit():
                emoji = f"<:emoji:{emoji}>"
            embed = discord.Embed(title=f"{emoji} {deals_data['title']} {emoji}", color=0x00A3FF)
            embed.description = f"{deals_data['mention']}\nGet your {EMOJI_ROBUX} stacked this season!\n\n"
            for d in deals_data["deals"]:
                embed.description += f"{emoji} **{d['amount']:,}** {EMOJI_ROBUX} → ~~${d['old']:.2f}~~ **${d['new']:.2f}**\n"
            embed.description += f"{emoji} Don’t miss out — #WinterDeals won’t last forever!\n➡️ Buy now at <#{INFO_CHANNEL_ID}> ⬅️"
            await channel.send(embed=embed)

        await interaction.response.send_message("Winter Deals updated!", ephemeral=True)

# --- STARTUP ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.add_view(PurchaseFlow(0))  # persistent view
    await send_info_embed()

# --- RUN ---
bot.run(BOT_TOKEN)
