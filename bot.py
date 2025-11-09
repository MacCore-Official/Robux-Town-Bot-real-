#!/usr/bin/env python3
# Robux Town™ — BLUE THEME + PRO AUTOMATED ORDERS + ALL YOUR EMOJIS
import os
import asyncio
import json
import re
import random
from datetime import datetime
import discord
from discord.ext import commands, tasks

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
ORDER_LOG_CHANNEL_ID = 1435516058105675819
COMPLETED_CHANNEL_ID = 1435516058286035015

# === YOUR CUSTOM EMOJIS ===
EMOJI_LITECOIN = "<:Litecoin:1435526448684339321>"
EMOJI_BITCOIN = "<:Bitcoin:1435526466527039579>"
EMOJI_ETHEREUM = "<:Ethereum:1435526479126597745>"
EMOJI_SOLANA = "<:Solana:1435526514115350549>"
EMOJI_PAYPAL = "<:PayPal:1435526543513354354>"
EMOJI_CARD = "<:Card:1435526554783318047>"
EMOJI_REWARBLE = "<:Rewarble:1435526590472650763>"
EMOJI_ROBUX = "<:Robux:1435526693472178176>"
EMOJI_LOADING = "<:Loading:1435526855523434576>"
EMOJI_VERIFIED = "<:Verified:1435526918891110551>"
EMOJI_WARNING = "<:warning:1435526954689495091>"
EMOJI_PAYMENT_SUPPORT = "<:PAYMENT_SUPPORT:1435526984011874434>"

# === TIERED RATES (Like Screenshot) ===
ROBUX_TIERS = [
    {"min": 10000, "max": 24999, "rate": 1.00},
    {"min": 25000, "max": 49999, "rate": 0.90},
    {"min": 50000, "max": 99999, "rate": 0.80},
    {"min": 100000, "max": 249999, "rate": 0.70},
    {"min": 250000, "max": 499999, "rate": 0.60},
    {"min": 500000, "max": 10000000, "rate": 0.50}
]

# --- LOAD DEALS ---
DEALS_FILE = "deals.json"
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

def load_deals():
    if os.path.exists(DEALS_FILE):
        with open(DEALS_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_DEALS.copy()

def save_deals(data):
    with open(DEALS_FILE, "w") as f:
        json.dump(data, f, indent=2)

deals_data = load_deals()

def get_price(amount):
    for deal in deals_data["deals"]:
        if amount == deal["amount"]:
            return deal["new"]
    for tier in ROBUX_TIERS:
        if tier["min"] <= amount <= tier["max"]:
            return (amount / 1000) * tier["rate"]
    return (amount / 1000) * 1.00

# === AUTOMATED ORDERS — 3-STEP LIKE YOUR EXAMPLE ===
@tasks.loop(minutes=random.uniform(5, 15))
async def fake_order_loop():
    channel = bot.get_channel(ORDER_LOG_CHANNEL_ID)
    if not channel:
        return

    name = random.choice(["Alex", "Luna", "Kai", "Zoe", "Max", "Nia", "Leo", "Ava", "Jax", "Milo"])
    amount = random.choice([10000, 25000, 50000, 75000, 100000, 150000, 180000, 250000])
    method = random.choice([
        f"{EMOJI_BITCOIN} Cryptocurrency (BTC / LTC / ETH / SOL)",
        f"{EMOJI_CARD} Card (Powered by G2A)",
        f"{EMOJI_PAYPAL} PayPal (Powered by Eneba)",
        f"{EMOJI_PAYMENT_SUPPORT} Giftcards (Steam / Binance / PaySafe)"
    ])
    price = get_price(amount)

    # Step 1: Order Placed
    embed1 = discord.Embed(title=f"{EMOJI_VERIFIED} New Order Placed", color=0x00A3FF)
    embed1.description = (
        f"{EMOJI_WARNING} **Disclaimer**\n"
        f"{EMOJI_VERIFIED} Minimum purchase amount is 10,000 {EMOJI_ROBUX}.\n"
        f"{EMOJI_VERIFIED} {EMOJI_ROBUX} are delivered via Gamepass.\n"
        f"{EMOJI_VERIFIED} Buying {EMOJI_ROBUX} through us is safe and secure. You will NOT get banned.\n"
        f"{EMOJI_VERIFIED} Enjoy instant {EMOJI_ROBUX} delivery with fully automated payments.\n\n"
        f"**Payment Method:** {method}"
    )
    embed1.add_field(name="Robux Rates", value=(
        "• 10K-24K → $1.00 per 1K\n"
        "• 25K-49K → $0.90 per 1K\n"
        "• 50K-99K → $0.80 per 1K\n"
        "• 100K-249K → $0.70 per 1K\n"
        "• 250K-499K → $0.60 per 1K\n"
        "• 500K-10M → $0.50 per 1K"
    ), inline=False)
    await channel.send(embed=embed1)

    # Step 2: Processing
    await asyncio.sleep(30)
    embed2 = discord.Embed(title=f"{EMOJI_LOADING} Processing Order...", color=0x00A3FF)
    embed2.add_field(name="User", value=f"`{name}#{random.randint(1000,9999)}`", inline=True)
    embed2.add_field(name="Amount", value=f"{amount:,} {EMOJI_ROBUX}", inline=True)
    embed2.add_field(name="Price", value=f"${price:.2f}", inline=True)
    embed2.add_field(name="Method", value=method, inline=False)
    await channel.send(embed=embed2)

    # Step 3: Completed (70% chance)
    if random.random() < 0.7:
        await asyncio.sleep(10)
        await send_completed_order(amount, price, method)

# === COMPLETED ORDER (Blue) ===
async def send_completed_order(amount, price, method):
    channel = bot.get_channel(COMPLETED_CHANNEL_ID)
    if not channel:
        return

    order_id = ''.join(random.choices('0123456789', k=15))
    embed = discord.Embed(title=f"{EMOJI_VERIFIED} New Completed Order", color=0x00A3FF, timestamp=datetime.now())
    embed.add_field(name="User", value="Hidden", inline=True)
    embed.add_field(name="Payment Method", value=method, inline=True)
    embed.add_field(name="Robux Purchased", value=f"{amount:,} {EMOJI_ROBUX} (via Gamepass)", inline=False)
    embed.add_field(name="USD Spent", value=f"${price:.2f}", inline=True)
    embed.add_field(name="Rating", value="Rating (5/5)", inline=True)
    embed.add_field(name="Order ID", value=order_id, inline=False)
    embed.set_footer(text="Powered by Robux Town™ • discord.gg/robuxworld")
    await channel.send(embed=embed)

# === PURCHASE BUTTON ===
class PurchaseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.blurple, emoji=EMOJI_ROBUX, custom_id="purchase_robux_btn")
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        thread = await interaction.channel.create_thread(
            name=f"Purchase-{interaction.user.name}-{random.randint(1000, 9999)}",
            auto_archive_duration=1440
        )
        await thread.add_user(interaction.user)
        flow = PurchaseFlow(interaction.user.id, thread)
        await flow.send_step(1)
        await interaction.followup.send("Purchase started! Check your thread.", ephemeral=True)

# === PURCHASE FLOW ===
class PurchaseFlow(discord.ui.View):
    def __init__(self, user_id, thread):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.thread = thread
        self.robux = 0
        self.price = 0.0
        self.method = ""

    async def send_step(self, step):
        color = 0x00A3FF
        if step == 1:
            embed = discord.Embed(title=f"Would you like to start buying {EMOJI_ROBUX}? (1/5)", color=color)
            embed.description = "Click **Yes** to begin."
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_1"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_1"))
            await self.thread.send(embed=embed, view=view)

        elif step == 2:
            embed = discord.Embed(title=f"How much {EMOJI_ROBUX} would you like to buy? (2/5)", color=color)
            embed.description = f"Type the amount below.\nExample: `100000`\nMinimum: **10,000** {EMOJI_ROBUX}"
            await self.thread.send(embed=embed)

        elif step == 3:
            self.price = get_price(self.robux)
            embed = discord.Embed(title=f"{EMOJI_VERIFIED} Confirm Purchase (3/5)", color=color)
            embed.description = f"**{self.robux:,}** {EMOJI_ROBUX}\n**Price:** `${self.price:.2f}`"
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_3"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_3"))
            await self.thread.send(embed=embed, view=view)

        elif step == 4:
            embed = discord.Embed(title=f"{EMOJI_PAYMENT_SUPPORT} Select Payment Method (4/5)", color=color)
            embed.description = "Choose your payment option."
            select = discord.ui.Select(
                placeholder="Select method",
                custom_id="payment_select",
                options=[
                    discord.SelectOption(label="Cryptocurrency (BTC/LTC/ETH/SOL)", value="crypto", emoji=EMOJI_BITCOIN),
                    discord.SelectOption(label="Card (G2A)", value="card", emoji=EMOJI_CARD),
                    discord.SelectOption(label="PayPal (Eneba)", value="paypal", emoji=EMOJI_PAYPAL),
                    discord.SelectOption(label="Giftcards (Steam/Binance/PaySafe)", value="gift", emoji=EMOJI_PAYMENT_SUPPORT),
                ]
            )
            select.callback = self.select_callback
            view = discord.ui.View(timeout=None)
            view.add_item(select)
            await self.thread.send(embed=embed, view=view)

        elif step == 5:
            embed = discord.Embed(title=f"{EMOJI_REWARBLE} Payment Invoice (5/5)", color=color)
            if "crypto" in self.method:
                embed.description = f"Send **${self.price:.2f}** in BTC/LTC/ETH/SOL to staff."
            elif "card" in self.method:
                embed.description = f"Purchase via G2A for **${self.price:.2f}**.\nReply with details."
            elif "paypal" in self.method:
                embed.description = f"Send **${self.price:.2f}** via Eneba PayPal.\nReply with ID."
            else:
                embed.description = f"Purchase Giftcard for **${self.price:.2f}**.\nReply with code."
            await self.thread.send(embed=embed)

    async def select_callback(self, interaction: discord.Interaction):
        self.method = interaction.data["values"][0]
        await interaction.response.defer()
        await self.send_step(5)

# === INTERACTION HANDLER ===
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data or "custom_id" not in interaction.data:
        return

    cid = interaction.data["custom_id"]
    if cid == "flow_yes_1":
        flow = PurchaseFlow(interaction.user.id, interaction.channel)
        await interaction.response.defer()
        await flow.send_step(2)
    elif cid == "flow_yes_3":
        flow = PurchaseFlow(interaction.user.id, interaction.channel)
        await interaction.response.defer()
        await flow.send_step(4)
    elif cid in ["flow_no_1", "flow_no_3"]:
        await interaction.response.send_message("Purchase cancelled.", ephemeral=True)

# === MESSAGE INPUT ===
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.channel.name.startswith("Purchase-"):
        return await bot.process_commands(message)

    content = message.content.strip()

    if re.fullmatch(r"\d{5,}", content):
        try:
            amount = int(content.replace(",", ""))
            if amount < 10000:
                await message.reply(f"Minimum is **10,000** {EMOJI_ROBUX}.")
                return
            flow = PurchaseFlow(message.author.id, message.channel)
            flow.robux = amount
            await message.delete()
            await flow.send_step(3)
        except:
            pass

    elif len(content) >= 10:
        await message.delete()
        await message.channel.send(f"{EMOJI_LOADING} Payment submitted! Verifying...")
        await message.channel.send(f"<@&{STAFF_ROLE_ID}> Please verify.")
        await asyncio.sleep(10)
        await send_completed_order(100000, get_price(100000), "Card (G2A)")
        await message.channel.send(f"{EMOJI_VERIFIED} Order completed! {EMOJI_ROBUX} delivered via Gamepass.")

    await bot.process_commands(message)

# === +emojis COMMAND ===
@bot.command()
async def emojis(ctx):
    guild = ctx.guild
    if not guild:
        await ctx.send("No guild found.")
        return
    
    emojis_list = [f"{e} - {e.name} (ID: {e.id})" for e in guild.emojis]
    for i in range(0, len(emojis_list), 25):
        chunk = emojis_list[i:i+25]
        embed = discord.Embed(title=f"{EMOJI_ROBUX} Server Emojis ({i+1}-{min(i+25, len(emojis_list))} of {len(emojis_list)})", description="\n".join(chunk), color=0x00A3FF)
        await ctx.send(embed=embed)

# === INFO EMBED (BLUE) ===
async def send_info_embed():
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if not channel:
        print("Info channel not found!")
        return

    embed = discord.Embed(color=0x00A3FF)
    embed.set_author(name="Robux Town™", icon_url="https://i.imgur.com/ROBUXTOWN.png")
    embed.description = (
        "lock **Automated Purchase**\nSecure, instant Robux delivery.\n\n"
        "zap **Under 60 Seconds**\nRobux delivered via Gamepass.\n\n"
        "credit_card **Smart Payments**\nFully automated.\n\n"
        "shield **Bank-Level Security**\nYou will NOT get banned.\n\n"
        "globe_with_meridians **Payment Options**\n"
        f"• {EMOJI_BITCOIN} Crypto (BTC/LTC/ETH/SOL)\n"
        f"• {EMOJI_CARD} Card (G2A)\n"
        f"• {EMOJI_PAYPAL} PayPal (Eneba)\n"
        f"• {EMOJI_PAYMENT_SUPPORT} Giftcards (Steam/Binance/PaySafe)"
    )
    embed.set_image(url="https://i.imgur.com/ROBUXTOWNBANNER.png")
    view = PurchaseButton()
    await channel.send(embed=embed, view=view)
    print("Info embed sent (BLUE)")

# === STARTUP ===
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.add_view(PurchaseButton())
    bot.add_view(PurchaseFlow(0, None))
    await send_info_embed()
    if not fake_order_loop.is_running():
        fake_order_loop.start()
        print("Pro automated orders started!")

# === RUN ===
bot.run(BOT_TOKEN)
