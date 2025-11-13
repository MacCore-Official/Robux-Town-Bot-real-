#!/usr/bin/env python3
# Robux Town™ – FINAL STABLE VERSION
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

# --- Links ---
ENEBA_REWARBLE_LINK = "https://www.eneba.com/rewarble-rewarble-visa-10-usd-voucher-global"
G2A_REWARBLE_LINK = "https://www.g2a.com/rewarble-visa-gift-card-10-usd-by-rewarble-key-global-i10000502992001?suid=960beb55-4797-46d5-b14c-94995fd68f31"

# --- Assets ---
EMOJI_GIVEAWAY_REACT = "<:giveawaygift:1437688517089165442>"
GIVEAWAY_THUMBNAIL = "https://i.ibb.co/v4rqV5Pj/9c5fd434-f30f-4e24-8212-ea40fa098678.png"
GIVEAWAY_BANNER = "https://i.ibb.co/FbRfdH7D/Screenshot-2025-11-10-at-6-58-42-PM.png"

# -------------------------------------------------
# TOKEN FROM NORTHFLANK (NO HARDCODED TOKEN!)
# -------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("ERROR: BOT_TOKEN not found in Northflank Environment Variables!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents, help_command=None)

# -------------------------------------------------
# CHANNEL & ROLE IDs
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
EMOJI_WARNING = "<:warning:1435526954689495091>"
EMOJI_CRYPTO = "<:Crypto:1437309415551406222>"
EMOJI_CARD = "<:Card:1435526554783318047>"
EMOJI_PAYPAL = "<:PayPal:1435526543513354354>"
EMOJI_PAYMENT_SUPPORT = "<:PAYMENT_SUPPORT:1435526984011874434>"

# -------------------------------------------------
# PRICING
# -------------------------------------------------
ROBUX_RATE_PER_1000 = 1.00
def get_price(robux_amount: int) -> float:
    return (robux_amount / 1000) * ROBUX_RATE_PER_1000

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
CONFIG_FILE = "config.json"
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
    },
    "deals": {
        "WINTERDEAL": {"robux": 100000, "price": 60.00, "min_robux_required": 100000}
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
            pass
    return default_config.copy()

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

config = load_config()

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
        self.discount_code = None

    async def send_step(self, step):
        if step == 1:
            embed = discord.Embed(title="Start Purchase? (1/6)", color=0x00A3FF)
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_1"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_1"))
            await self.thread.send(embed=embed, view=view)

        elif step == 2:
            embed = discord.Embed(title="How much Robux? (2/6)", color=0x00A3FF)
            embed.description = "Enter amount (10,000 – 800,000)"
            await self.thread.send(embed=embed)

        elif step == 3:
            embed = discord.Embed(title="Discount Code? (3/6)", color=0x00A3FF)
            embed.description = "Type code or **SKIP**"
            await self.thread.send(embed=embed)

        elif step == 4:
            rate = get_price(1000)
            discount = f"**COUPON: {self.discount_code}**\n" if self.discount_code else ""
            embed = discord.Embed(title="Confirm (4/6)", color=0x00A3FF)
            embed.description = f"{discount}**{self.robux:,} {EMOJI_ROBUX}** → **${self.price:.2f}** (${rate:.2f}/1K)"
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_4"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_4"))
            await self.thread.send(embed=embed, view=view)

        elif step == 5:
            embed = discord.Embed(title="Payment Method (5/6)", color=0x00A3FF)
            select = discord.ui.Select(placeholder="Select", custom_id="payment_select")
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

    async def payment_callback(self, i):
        self.method = i.data["values"][0]
        await i.response.defer()
        if self.method == "crypto":
            embed = discord.Embed(title="Select Coin", color=0x00A3FF)
            select = discord.ui.Select(placeholder="Coin", custom_id="crypto_select")
            select.options = [
                discord.SelectOption(label="BTC", value="btc"),
                discord.SelectOption(label="LTC", value="ltc"),
                discord.SelectOption(label="ETH", value="eth"),
                discord.SelectOption(label="SOL", value="sol"),
            ]
            async def cb2(j): await self.crypto_callback(j)
            select.callback = cb2
            view = discord.ui.View(timeout=None)
            view.add_item(select)
            await i.followup.send(embed=embed, view=view)
        else:
            await self.send_payment_invoice(i)

    async def crypto_callback(self, i):
        self.crypto = i.data["values"][0]
        await i.response.defer()
        await self.send_crypto_invoice(i)

    async def send_crypto_invoice(self, i):
        price_usd = self.price
        coin_price = await get_crypto_price(self.crypto)
        amount = round(price_usd / coin_price, 8)
        address = config["wallets"].get(self.crypto, "Not Set")
        qr = config["qr_urls"].get(self.crypto, f"https://api.qrserver.com/v1/create-qr-code/?data={address}&size=200x200")
        expiry = int((datetime.now() + timedelta(minutes=20)).timestamp())
        embed = discord.Embed(title=f"{self.crypto.upper()} Invoice", color=0x00A3FF)
        embed.description = f"Send `{amount:.8f}` {self.crypto.upper()}\nExpires: <t:{expiry}:R>"
        embed.add_field(name="Address", value=f"```{address}```", inline=False)
        embed.set_image(url=qr)
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit TX", style=discord.ButtonStyle.blurple, custom_id="submit_tx"))
        await i.followup.send(embed=embed, view=view)

    async def send_payment_invoice(self, i):
        name = "Giftcard" if self.method == "gift" else self.method.capitalize()
        details = ""
        if self.method == "card":
            details = f"[Buy on G2A]({G2A_REWARBLE_LINK})"
        elif self.method == "paypal":
            details = f"[Buy on Eneba]({ENEBA_REWARBLE_LINK})"
        embed = discord.Embed(title=f"{name} Invoice", color=0x00A3FF)
        embed.description = f"Submit code.\n\n{details}"
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit", style=discord.ButtonStyle.blurple, custom_id="submit_details"))
        await i.followup.send(embed=embed, view=view)

# -------------------------------------------------
# CRYPTO PRICE
# -------------------------------------------------
async def get_crypto_price(crypto: str) -> float:
    try:
        r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies=usd", timeout=5)
        r.raise_for_status()
        return r.json()[crypto]["usd"]
    except:
        return 60000.0 if crypto == "bitcoin" else 80.0 if crypto == "litecoin" else 3000.0 if crypto == "ethereum" else 100.0

# -------------------------------------------------
# INTERACTIONS
# -------------------------------------------------
@bot.event
async def on_interaction(interaction):
    if not interaction.data or "custom_id" not in interaction.data:
        return
    cid = interaction.data["custom_id"]
    flow = active_flows.get(interaction.user.id)

    if cid == "flow_yes_1" and flow:
        await interaction.response.defer()
        await flow.send_step(2)
    elif cid in ["flow_no_1", "flow_no_4"] and flow:
        await interaction.response.defer()
        await flow.thread.edit(archived=True, locked=True)
        active_flows.pop(interaction.user.id, None)
    elif cid == "flow_yes_4" and flow:
        await interaction.response.defer()
        await flow.send_step(5)
    elif cid == "submit_tx" and flow:
        modal = PaymentModal("Crypto", flow.robux, flow.price, flow.crypto, flow.discount_code)
        await interaction.response.send_modal(modal)
    elif cid == "submit_details" and flow:
        modal = PaymentModal(flow.method, flow.robux, flow.price, discount_code=flow.discount_code)
        await interaction.response.send_modal(modal)

# -------------------------------------------------
# MESSAGE HANDLER
# -------------------------------------------------
@bot.event
async def on_message(message):
    if message.author.bot or not message.channel.name.startswith("Purchase-"):
        return await bot.process_commands(message)

    flow = active_flows.get(message.author.id)
    if not flow or flow.thread.id != message.channel.id:
        return await bot.process_commands(message)

    if flow.robux == 0 and re.fullmatch(r"[\d,]+", message.content.strip()):
        try:
            amount = int(message.content.replace(",", ""))
            if amount < 10000 or amount > 800000:
                await message.reply(f"{EMOJI_WARNING} 10K–800K only.", delete_after=5)
                return
            flow.robux = amount
            await message.delete()
            await flow.send_step(3)
        except: pass
    elif flow.robux > 0 and flow.price == 0.0:
        code = message.content.strip()
        await message.delete()
        flow.price = get_price(flow.robux)
        if code.upper() != "SKIP":
            deal = config["deals"].get(code.upper())
            if deal and flow.robux >= deal.get("min_robux_required", 0):
                flow.price = deal["price"]
                flow.discount_code = code.upper()
                await flow.thread.send(f"{EMOJI_VERIFIED} Coupon **{code.upper()}** applied!")
            else:
                await flow.thread.send(f"{EMOJI_WARNING} Invalid coupon.")
        await flow.send_step(4)
    await bot.process_commands(message)

# -------------------------------------------------
# MODAL
# -------------------------------------------------
class PaymentModal(discord.ui.Modal):
    def __init__(self, method, amount, price, crypto=None, discount_code=None):
        super().__init__(title="Submit Details", timeout=None)
        self.method = method; self.amount = amount; self.price = price; self.crypto = crypto; self.discount_code = discount_code
        self.details = discord.ui.TextInput(label="TX / Code", style=discord.TextStyle.paragraph)
        self.add_item(self.details)

    async def on_submit(self, i):
        data = {
            "User": i.user.mention,
            "Robux": f"{self.amount:,}",
            "USD": f"${self.price:.2f}",
            "Method": self.crypto.upper() if self.crypto else self.method.capitalize(),
            "Details": self.details.value,
            "Discount": self.discount_code or "None"
        }
        await i.response.send_message(f"{EMOJI_VERIFIED} Submitted!", ephemeral=True)
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            embed = discord.Embed(title="New Payment", color=0x00A3FF)
            for k, v in data.items():
                embed.add_field(name=k, value=v, inline=False)
            await channel.send(embed=embed)

# -------------------------------------------------
# PERSISTENT BUY BUTTON
# -------------------------------------------------
class BuyView(discord.ui.View):
    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.blurple, custom_id="buy_robux")
    async def buy(self, i, b):
        if i.user.id in active_flows:
            await i.response.send_message(f"{EMOJI_WARNING} One at a time!", ephemeral=True)
            return
        info = bot.get_channel(INFO_CHANNEL_ID)
        thread = await info.create_thread(name=f"buy-{i.user.name}-{random.randint(1000,9999)}", type=discord.ChannelType.private_thread)
        await thread.add_user(i.user)
        flow = PurchaseFlow(i.user.id, thread)
        active_flows[i.user.id] = flow
        await i.response.send_message(f"Started! → {thread.mention}", ephemeral=True)
        await flow.send_step(1)

# -------------------------------------------------
# SETUP COMMAND
# -------------------------------------------------
@bot.command()
async def setup(ctx):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    embed = discord.Embed(title="Robux Town™", description="Click below to buy!", color=0x00A3FF)
    await channel.send(embed=embed, view=BuyView())

# -------------------------------------------------
# FAKE ORDERS
# -------------------------------------------------
async def send_fake_order():
    channel = bot.get_channel(COMPLETED_CHANNEL_ID)
    if not channel: return
    amount = random.choice([10000, 25000, 50000, 100000])
    embed = discord.Embed(title="New Order Completed", color=0x38B750)
    embed.add_field(name="Robux", value=f"**{amount:,}**", inline=True)
    embed.add_field(name="USD", value=f"**${get_price(amount):.2f}**", inline=True)
    await channel.send(embed=embed)

@tasks.loop(hours=random.uniform(4, 8))
async def fake_loop():
    await send_fake_order()

# -------------------------------------------------
# ON READY
# -------------------------------------------------
@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")
    bot.add_view(BuyView())
    if not fake_loop.is_running():
        fake_loop.start()

# -------------------------------------------------
# RUN
# -------------------------------------------------
bot.run(BOT_TOKEN)
