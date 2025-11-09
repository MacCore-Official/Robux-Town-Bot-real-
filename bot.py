#!/usr/bin/env python3
# Robux Town — Automatic Order Flow (Blue Border, Persistent Views, Northflank-Ready)
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

# Emojis
EMOJI_ROBUX = "<:Robux:1396166686356275200>"

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

# Load/Save Deals
def load_deals():
    if os.path.exists(DEALS_FILE):
        with open(DEALS_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_DEALS.copy()

def save_deals(data):
    with open(DEALS_FILE, "w") as f:
        json.dump(data, f, indent=2)

deals_data = load_deals()

# --- PERSISTENT VIEWS ---
class PurchaseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent

    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.blurple, emoji="hexagon", custom_id="purchase_robux_btn")
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        thread = await interaction.channel.create_thread(
            name=f"Purchase-{interaction.user.name}-{interaction.id[:6]}",
            auto_archive_duration=1440
        )
        await thread.add_user(interaction.user)
        flow = PurchaseFlow(interaction.user.id, thread)
        await flow.send_step(1)
        await interaction.followup.send("Purchase started! Check your thread.", ephemeral=True)

class PurchaseFlow(discord.ui.View):
    def __init__(self, user_id, thread):
        super().__init__(timeout=None)  # Persistent
        self.user_id = user_id
        self.thread = thread
        self.robux = 0
        self.price = 0.0
        self.method = ""

    async def send_step(self, step):
        if step == 1:
            embed = discord.Embed(title="Would you like to start buying Robux? (1/5)", color=0x00A3FF)
            embed.description = "Click **Yes** to begin."
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_1"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_1"))
            await self.thread.send(embed=embed, view=view)

        elif step == 2:
            embed = discord.Embed(title="How much Robux would you like to buy? (2/5)", color=0x00A3FF)
            embed.description = f"Type the amount below.\nExample: `100000`\nMinimum: **10,000** {EMOJI_ROBUX}"
            await self.thread.send(embed=embed)

        elif step == 3:
            base_rate = 10000 / 10.0
            self.price = self.robux / base_rate
            for deal in deals_data["deals"]:
                if self.robux == deal["amount"]:
                    self.price = deal["new"]
                    break
            embed = discord.Embed(title="Confirm Purchase (3/5)", color=0x00A3FF)
            embed.description = (
                f"**{self.robux:,}** {EMOJI_ROBUX}\n"
                f"**Price:** `${self.price:.2f}`"
            )
            if self.price < (self.robux / base_rate):
                embed.description += " **(Winter Deal!)**"
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_3"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_3"))
            await self.thread.send(embed=embed, view=view)

        elif step == 4:
            embed = discord.Embed(title="Select Payment Method (4/5)", color=0x00A3FF)
            embed.description = "Choose your payment option."
            select = discord.ui.Select(
                placeholder="Select method",
                custom_id="payment_select",
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
            view = discord.ui.View(timeout=None)
            view.add_item(select)
            await self.thread.send(embed=embed, view=view)

        elif step == 5:
            embed = discord.Embed(title="Payment Invoice (5/5)", color=0x00A3FF)
            if "visa" in self.method:
                embed.description = (
                    "Purchase a **Rewarble Visa Gift Card** for:\n"
                    f"**`${self.price:.2f}`**\n\n"
                    "Reply with the **gift card code**."
                )
            else:
                embed.description = f"Send **${self.price:.2f}** to the address provided by staff."
            await self.thread.send(embed=embed)

    async def select_callback(self, interaction: discord.Interaction):
        self.method = interaction.data["values"][0]
        await interaction.response.defer()
        await self.send_step(5)

# --- INTERACTION HANDLER ---
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data or "custom_id" not in interaction.data:
        return

    cid = interaction.data["custom_id"]

    if cid == "purchase_robux_btn":
        # Handled in PurchaseButton
        pass

    elif cid == "flow_yes_1":
        flow = PurchaseFlow(interaction.user.id, interaction.channel)
        await interaction.response.defer()
        await flow.send_step(2)

    elif cid == "flow_yes_3":
        flow = PurchaseFlow(interaction.user.id, interaction.channel)
        await interaction.response.defer()
        await flow.send_step(4)

    elif cid in ["flow_no_1", "flow_no_3"]:
        await interaction.response.send_message("Purchase cancelled.", ephemeral=True)

    elif cid == "payment_select":
        # Handled in PurchaseFlow
        pass

# --- MESSAGE INPUT: Robux Amount ---
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.channel.name.startswith("Purchase-"):
        return await bot.process_commands(message)

    if re.fullmatch(r"\d{5,}", message.content.strip()):
        try:
            amount = int(message.content.replace(",", "").strip())
            if amount < 10000:
                await message.reply("Minimum is **10,000** Robux.")
                return
            flow = PurchaseFlow(message.author.id, message.channel)
            flow.robux = amount
            await message.delete()
            await flow.send_step(3)
        except:
            pass
    await bot.process_commands(message)

# --- ADMIN PANEL: +panel ---
@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):
    modal = WinterDealsModal()
    await ctx.send("Click below to edit Winter Deals.", view=discord.ui.View().add_item(
        discord.ui.Button(label="Edit Deals", style=discord.ButtonStyle.blurple, custom_id="open_deals_modal")
    ))

class WinterDealsModal(discord.ui.Modal, title="Edit Winter Deals"):
    title_input = discord.ui.Text include = discord.ui.TextInput(label="Title", default=deals_data.get("title", "WINTER DEALS"))
    emoji_input = discord.ui.TextInput(label="Emoji", default=deals_data.get("emoji", "snowflake"))
    deal1 = discord.ui.TextInput(label="50k: Old/New", placeholder="49.99 / 25.00", default="49.99 / 25.00")
    deal2 = discord.ui.TextInput(label="75k: Old/New", placeholder="74.99 / 35.00", default="74.99 / 35.00")
    deal3 = discord.ui.TextInput(label="100k: Old/New", placeholder="99.99 / 40.00", default="99.99 / 40.00")
    deal4 = discord.ui.TextInput(label="150k: Old/New", placeholder="149.99 / 55.00", default="149.99 / 55.00")
    deal5 = discord.ui.TextInput(label="250k: Old/New", placeholder="249.99 / 75.00", default="249.99 / 75.00")

    async def on_submit(self, interaction: discord.Interaction):
        global deals_data
        deals_data["title"] = self.title_input.value
        deals_data["emoji"] = self.emoji_input.value

        new_deals = []
        inputs = [self.deal1, self.deal2, self.deal3, self.deal4, self.deal5]
        amounts = [50000, 75000, 100000, 150000, 250000]
        for inp, amt in zip(inputs, amounts):
            try:
                old, new = map(float, [x.strip() for x in inp.value.split("/")])
                new_deals.append({"amount": amt, "old": old, "new": new})
            except:
                pass
        deals_data["deals"] = new_deals
        save_deals(deals_data)

        channel = bot.get_channel(DEALS_CHANNEL_ID)
        if channel:
            emoji = deals_data["emoji"]
            if emoji.isdigit():
                emoji = f"<:e:{emoji}>"
            embed = discord.Embed(title=f"{emoji} {deals_data['title']} {emoji}", color=0x00A3FF)
            embed.description = f"{deals_data.get('mention', '@everyone')}\nGet your {EMOJI_ROBUX} stacked!\n\n"
            for d in deals_data["deals"]:
                embed.description += f"{emoji} **{d['amount']:,}** {EMOJI_ROBUX} → ~~${d['old']:.2f}~~ **${d['new']:.2f}**\n"
            embed.description += f"{emoji} Don’t miss out!\nBuy at <#{INFO_CHANNEL_ID}>"
            await channel.send(embed=embed)

        await interaction.response.send_message("Deals updated!", ephemeral=True)

# --- INFO EMBED ---
async def send_info_embed():
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if not channel:
        print("Info channel not found!")
        return

    embed = discord.Embed(color=0x00A3FF)
    embed.set_author(name="Robux Town™", icon_url="https://i.imgur.com/ROBUXTOWN.png")
    embed.description = (
        "lock **Automated Purchase**\n"
        "Secure, instant Robux delivery via Discord.\n\n"
        "zap **Under 60 Seconds**\n"
        "Robux delivered instantly after payment.\n\n"
        "credit_card **Smart Payments**\n"
        "Fully automated — no delays.\n\n"
        "shield **Bank-Level Security**\n"
        "Encrypted & verified transactions.\n\n"
        "globe_with_meridians **Payment Options**\n"
        "• **Visa Gift Card (G2A)**\n"
        "• **PayPal (Eneba)**\n"
        "• **BTC • LTC • SOL • ETH**"
    )
    embed.set_image(url="https://i.imgur.com/ROBUXTOWNBANNER.png")

    view = PurchaseButton()
    await channel.send(embed=embed, view=view)
    print("Info embed sent (BLUE BORDER)")

# --- STARTUP ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.add_view(PurchaseButton())
    bot.add_view(PurchaseFlow(0, None))  # dummy for persistence
    await send_info_embed()

# --- RUN ---
bot.run(BOT_TOKEN)
