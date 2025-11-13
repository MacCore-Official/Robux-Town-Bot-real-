#!/usr/bin/env python3
# Robux Town™ – FINAL STABLE VERSION (ALL FEATURES + DISCOUNT VIA MESSAGE)
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

# --- Assets ---
EMOJI_GIVEAWAY_REACT = "<:giveawaygift:1437688517089165442>"
GIVEAWAY_THUMBNAIL = "https://i.ibb.co/v4rqV5Pj/9c5fd434-f30f-4e24-8212-ea40fa098678.png"
GIVEAWAY_BANNER = "https://i.ibb.co/FbRfdH7D/Screenshot-2025-11-10-at-6-58-42-PM.png"

# -------------------------------------------------
# TOKEN FROM NORTHFLANK
# -------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("ERROR: BOT_TOKEN not set in Northflank Environment Variables!")
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
EMOJI_LOADING = "<a:Loading:1435526855523434576>"
EMOJI_BITCOIN = "<:Bitcoin:1435526466527039579>"
EMOJI_LITECOIN = "<:Litecoin:1435526448684339321>"
EMOJI_ETHEREUM = "<:Ethereum:1435526479126597745>"
EMOJI_SOLANA = "<:Solana:1435526514115350549>"
EMOJI_COG = "Settings"
EMOJI_USER = "User"
EMOJI_USD = "USD"
EMOJI_RATING = "Rating"
EMOJI_ORDER_ID = "Order ID"
EMOJI_LOCK = "Lock"
EMOJI_MAX = "Max"

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
                loaded_data = json.load(f)
            config_data = default_config.copy()
            config_data.update(loaded_data)
            return config_data
        except json.JSONDecodeError:
            print("Error reading config.json. Using defaults.")
            return default_config.copy()
    return default_config.copy()

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

config = load_config()

# -------------------------------------------------
# CRYPTO PRICE
# -------------------------------------------------
CRYPTO_IDS = {"btc": "bitcoin", "ltc": "litecoin", "eth": "ethereum", "sol": "solana"}
async def get_crypto_price(crypto: str) -> float:
    try:
        r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={CRYPTO_IDS[crypto]}&vs_currencies=usd", timeout=5)
        r.raise_for_status()
        return r.json()[CRYPTO_IDS[crypto]]["usd"]
    except:
        return 60000.0 if crypto == "btc" else 80.0 if crypto == "ltc" else 3000.0 if crypto == "eth" else 100.0

# -------------------------------------------------
# SEND TO STAFF DMs + LOG CHANNEL
# -------------------------------------------------
async def send_to_staff(order_data: dict):
    embed = discord.Embed(title="New Payment Submission", color=0x00A3FF)
    for k, v in order_data.items():
        embed.add_field(name=k, value=v, inline=False)
    for user_id in STAFF_DM_IDS:
        try:
            user = await bot.fetch_user(user_id)
            await user.send(embed=embed)
        except:
            pass
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

# -------------------------------------------------
# ADMIN MODALS
# -------------------------------------------------
class DiscountModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Set New Discount Code", timeout=600)
        self.code = discord.ui.TextInput(label="Discount Code (e.g., WINTERDEAL)", placeholder="Must be uppercase, one word")
        self.amount = discord.ui.TextInput(label="Robux Amount Covered by Deal", placeholder="e.g., 100000")
        self.price = discord.ui.TextInput(label="Discounted Price in USD", placeholder="e.g., 60.00")
        self.add_item(self.code); self.add_item(self.amount); self.add_item(self.price)

    async def on_submit(self, interaction: discord.Interaction):
        code = self.code.value.upper()
        try:
            amount = int(self.amount.value.replace(",", ""))
            price = float(self.price.value)
        except ValueError:
            await interaction.response.send_message(f"{EMOJI_WARNING} Invalid number format.", ephemeral=True)
            return
        config["deals"][code] = {"robux": amount, "price": price, "min_robux_required": amount}
        save_config(config)
        await interaction.response.send_message(
            f"{EMOJI_VERIFIED} Discount code **{code}** set: {amount:,} R$ for **${price:.2f} USD**.",
            ephemeral=True
        )

class PaymentModal(discord.ui.Modal):
    def __init__(self, method, amount, price, crypto=None, discount_code=None):
        super().__init__(title=f"Submit {method.upper()} Details", timeout=None)
        self.method = method; self.amount = amount; self.price = price; self.crypto = crypto; self.discount_code = discount_code
        self.details = discord.ui.TextInput(label="Payment ID / TX Hash / Code", placeholder="e.g., TXabc123", style=discord.TextStyle.paragraph)
        self.add_item(self.details)

    async def on_submit(self, interaction: discord.Interaction):
        method_name = self.crypto.upper() if self.crypto else self.method
        order_data = {
            "User": f"{interaction.user.mention} ({interaction.user})",
            "Robux": f"{self.amount:,}",
            "USD": f"${self.price:.2f}",
            "Method": method_name,
            "Details": self.details.value,
            "Discount": self.discount_code or "None",
            "Thread": interaction.channel.mention,
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        await interaction.response.send_message(f"{EMOJI_VERIFIED} **Payment Submitted!**", ephemeral=True)
        await send_to_staff(order_data)

class AddressModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Set Crypto Address", timeout=600)
        self.coin = discord.ui.TextInput(label="Coin (btc, ltc, eth, sol)", max_length=3)
        self.address = discord.ui.TextInput(label="New Address", style=discord.TextStyle.paragraph)
        self.add_item(self.coin); self.add_item(self.address)

    async def on_submit(self, interaction: discord.Interaction):
        coin = self.coin.value.lower()
        if coin in config["wallets"]:
            config["wallets"][coin] = self.address.value
            save_config(config)
            await interaction.response.send_message(f"{EMOJI_VERIFIED} {coin.upper()} address updated.", ephemeral=True)

class QRModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Set Crypto QR URL", timeout=600)
        self.coin = discord.ui.TextInput(label="Coin (btc, ltc, eth, sol)", max_length=3)
        self.url = discord.ui.TextInput(label="New QR Image URL", style=discord.TextStyle.paragraph)
        self.add_item(self.coin); self.add_item(self.url)

    async def on_submit(self, interaction: discord.Interaction):
        coin = self.coin.value.lower()
        if coin in config["qr_urls"]:
            config["qr_urls"][coin] = self.url.value
            save_config(config)
            await interaction.response.send_message(f"{EMOJI_VERIFIED} {coin.upper()} QR updated.", ephemeral=True)

# -------------------------------------------------
# CLOSE TICKET VIEW
# -------------------------------------------------
class CloseTicketView(discord.ui.View):
    def __init__(self, thread_id):
        super().__init__(timeout=None)
        self.thread_id = thread_id

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket_btn", emoji=EMOJI_LOCK)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        thread = bot.get_channel(self.thread_id)
        if thread:
            await interaction.response.send_message("Closing the ticket...", ephemeral=False)
            await thread.edit(archived=True, locked=True)
            active_flows.pop(interaction.user.id, None)

# -------------------------------------------------
# DISCLAIMER EMBED
# -------------------------------------------------
async def send_disclaimer_embed(thread: discord.Thread):
    embed = discord.Embed(
        title="Please Note",
        description=(
            "**Please make sure that all conversations related to the deal are done within this ticket.**\n"
            "Our staff will **never DM you** regarding any deals."
        ),
        color=0xFFA500
    )
    view = CloseTicketView(thread.id)
    await thread.send(embed=embed, view=view)

# -------------------------------------------------
# DISCOUNT VIA MESSAGE (NEW)
# -------------------------------------------------
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return await bot.process_commands(message)

    # === DISCOUNT CODE VIA MESSAGE (STAFF ONLY) ===
    if STAFF_ROLE_ID in [role.id for role in message.author.roles]:
        content = message.content.strip()
        if "," in content and len(content.split(",")) == 3:
            code, robux_str, price_str = [x.strip() for x in content.split(",", 2)]
            if code.isalnum() and len(code) >= 3:
                try:
                    robux = int(robux_str.replace(",", ""))
                    price = float(price_str)
                    if robux >= 10000 and price > 0:
                        config["deals"][code.upper()] = {
                            "robux": robux,
                            "price": price,
                            "min_robux_required": robux
                        }
                        save_config(config)
                        embed = discord.Embed(title="Discount Code Added", color=0x00FF00)
                        embed.add_field(name="Code", value=f"**{code.upper()}**", inline=True)
                        embed.add_field(name="Robux", value=f"{robux:,}", inline=True)
                        embed.add_field(name="Price", value=f"${price:.2f}", inline=True)
                        await message.reply(embed=embed, delete_after=30)
                        await message.delete(delay=30)
                        return await bot.process_commands(message)
                except:
                    pass
# === ADD THIS IN `on_message` (BEFORE PURCHASE FLOW) ===
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return await bot.process_commands(message)

    # === DISCOUNT VIA MESSAGE (STAFF) ===
    if STAFF_ROLE_ID in [r.id for r in message.author.roles]:
        content = message.content.strip()
        if "," in content and len(content.split(",")) == 3:
            code, robux_str, price_str = [x.strip() for x in content.split(",", 2)]
            if code.isalnum() and len(code) >= 3:
                try:
                    robux = int(robux_str.replace(",", ""))
                    price = float(price_str)
                    if robux >= 10000 and price > 0:
                        config["deals"][code.upper()] = {
                            "robux": robux,
                            "price": price,
                            "min_robux_required": robux
                        }
                        save_config(config)
                        embed = discord.Embed(title="Discount Code Added", color=0x00FF00)
                        embed.add_field(name="Code", value=f"**{code.upper()}**", inline=True)
                        embed.add_field(name="Robux", value=f"{robux:,}", inline=True)
                        embed.add_field(name="Price", value=f"${price:.2f}", inline=True)
                        await message.reply(embed=embed, delete_after=30)
                        await message.delete(delay=30)
                        return await bot.process_commands(message)
                except:
                    pass

    # === REST OF YOUR on_message (PURCHASE FLOW) ===
    # ... keep your existing code below ...
    # === PURCHASE FLOW MESSAGES ===
    if not message.channel.name.startswith("Purchase-"):
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
        if code.upper() != "SKIP" and code.upper():
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
# PURCHASE FLOW
# -------------------------------------------------
active_flows = {}

class PurchaseFlow(discord.ui.View):
    def __init__(self, user_id, thread):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.thread = thread
        self.robux = 0
        self.price = 0.0
        self.method = ""
        self.crypto = ""
        self.discount_code = None

    async def send_step(self, step: int):
        color = 0x00A3FF
        if step == 1:
            await send_disclaimer_embed(self.thread)
            embed = discord.Embed(title="Would you like to start buying robux? (1/6)", color=color)
            embed.description = "Please click \"Yes\" to begin."
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_1"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_1"))
            await self.thread.send(embed=embed, view=view)
        elif step == 2:
            embed = discord.Embed(title="How much robux would you like to buy? (2/6)", color=color)
            embed.description = "Please specify the amount of Robux you would like to purchase:\n**The minimum order amount is 10,000 Robux**"
            await self.thread.send(embed=embed)
        elif step == 3:
            embed = discord.Embed(title="Do you have a discount code? (3/6)", color=color)
            embed.description = "Enter your coupon code below, or type **'SKIP'** to continue to the standard pricing."
            await self.thread.send(embed=embed)
        elif step == 4:
            rate_per_1k = get_price(1000)
            discount_info = f"**COUPON APPLIED:** {self.discount_code}\n" if self.discount_code else ""
            embed = discord.Embed(title="Would you like to purchase this amount of Robux? (4/6)", color=color)
            embed.description = (
                f"Are you sure you want to purchase **{self.robux:,} {EMOJI_ROBUX}**?\n"
                f"{discount_info}"
                f"Standard Rate: **${rate_per_1k:.2f} per 1,000 {EMOJI_ROBUX}**\n"
                f"Total Price in USD: **${self.price:.2f}**"
            )
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_4"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_4"))
            await self.thread.send(embed=embed, view=view)
        elif step == 5:
            embed = discord.Embed(title="Please select your preferred payment method (5/6)", color=color)
            embed.description = "Choose your payment method below:"
            select = discord.ui.Select(
                placeholder="Select your payment method",
                custom_id="payment_select",
                options=[
                    discord.SelectOption(label="Cryptocurrency", value="crypto", emoji=EMOJI_CRYPTO),
                    discord.SelectOption(label="Card (G2A)", value="card", emoji=EMOJI_CARD),
                    discord.SelectOption(label="PayPal (Eneba)", value="paypal", emoji=EMOJI_PAYPAL),
                    discord.SelectOption(label="Giftcards", value="gift", emoji=EMOJI_PAYMENT_SUPPORT),
                ]
            )
            async def payment_callback_wrapper(interaction: discord.Interaction):
                await self.payment_callback(interaction)
            select.callback = payment_callback_wrapper
            view = discord.ui.View(timeout=None)
            view.add_item(select)
            await self.thread.send(embed=embed, view=view)

    async def payment_callback(self, interaction: discord.Interaction):
        self.method = interaction.data["values"][0]
        await interaction.response.defer()
        if self.method == "crypto":
            embed = discord.Embed(title="Select Cryptocurrency", color=0x00A3FF)
            embed.description = "Which coin will you be sending?"
            select = discord.ui.Select(
                placeholder="Select your crypto",
                custom_id="crypto_select",
                options=[
                    discord.SelectOption(label="BTC", value="btc", emoji=EMOJI_BITCOIN),
                    discord.SelectOption(label="LTC", value="ltc", emoji=EMOJI_LITECOIN),
                    discord.SelectOption(label="ETH", value="eth", emoji=EMOJI_ETHEREUM),
                    discord.SelectOption(label="SOL", value="sol", emoji=EMOJI_SOLANA),
                ]
            )
            async def crypto_callback_wrapper(interaction: discord.Interaction):
                await self.crypto_callback(interaction)
            select.callback = crypto_callback_wrapper
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
        amount_coin = round(price_usd / coin_price, 8) if coin_price else 0.0
        address = config["wallets"].get(self.crypto, "Address Not Set")
        qr_url = config["qr_urls"].get(self.crypto)
        if not qr_url or not qr_url.startswith("http"):
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={address}&size=200x200"
        expiry_time = datetime.now() + timedelta(minutes=20)
        expiry_timestamp = int(expiry_time.timestamp())
        embed = discord.Embed(title=f"{self.crypto.upper()} Payment Invoice (6/6)", color=0x00A3FF)
        embed.description = (
            f"This transaction is **${price_usd:.2f} USD**.\n"
            f"Please send the **exact** amount of `{amount_coin:.8f}` {self.crypto.upper()} to the address below.\n\n"
            f"**Invoice Expires:** <t:{expiry_timestamp}:R> (<t:{expiry_timestamp}:T>)"
        )
        embed.add_field(name="Payment Address", value=f"```\n{address}\n```", inline=False)
        embed.add_field(name=f"Amount ({self.crypto.upper()})", value=f"`{amount_coin:.8f}`", inline=False)
        embed.add_field(name="Amount USD", value=f"**${price_usd:.2f}**", inline=False)
        embed.set_image(url=qr_url)
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit TX Hash", style=discord.ButtonStyle.blurple, custom_id="submit_tx"))
        await interaction.followup.send(embed=embed, view=view)

    async def send_payment_invoice(self, interaction: discord.Interaction):
        name = "Giftcard" if self.method == "gift" else self.method
        details = ""
        if self.method == "card":
            details = f"**You must purchase a Rewarble Card from G2A** for the amount and submit the code.\n**G2A Link:** [Buy Rewarble Card Here]({G2A_REWARBLE_LINK})"
        elif self.method == "paypal":
            details = f"**You must purchase a Rewarble Card from Eneba** using PayPal/Card and submit the code.\n**Eneba Link:** [Buy Rewarble Card Here]({ENEBA_REWARBLE_LINK})"
        else:
            details = "Please purchase the necessary giftcard and prepare to submit the code/details."
        embed = discord.Embed(title=f"{name.upper()} Payment Invoice (6/6)", color=0x00A3FF)
        embed.description = f"Send **${self.price:.2f} USD** via **{name}**.\n\n{details}"
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit Details", style=discord.ButtonStyle.blurple, custom_id="submit_details"))
        await interaction.followup.send(embed=embed, view=view)

# -------------------------------------------------
# INTERACTION HANDLER
# -------------------------------------------------
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data or "custom_id" not in interaction.data:
        return
    cid = interaction.data["custom_id"]
    user_id = interaction.user.id
    flow = active_flows.get(user_id)

    if cid == "flow_yes_1" and flow:
        await interaction.response.defer()
        await flow.send_step(2)
    elif cid == "flow_no_1" and flow:
        await interaction.response.defer()
        await flow.thread.send("Purchase flow cancelled.")
        await flow.thread.edit(archived=True, locked=True)
        active_flows.pop(user_id, None)
    elif cid == "flow_yes_4" and flow:
        await interaction.response.defer()
        await flow.send_step(5)
    elif cid == "flow_no_4" and flow:
        await interaction.response.defer()
        await flow.thread.send("Cancelled. Restarting...")
        await flow.thread.edit(archived=True, locked=True)
        active_flows.pop(user_id, None)
        info_channel = bot.get_channel(INFO_CHANNEL_ID)
        thread = await info_channel.create_thread(
            name=f"Purchase-{interaction.user.name}-{random.randint(1000,9999)}",
            auto_archive_duration=1440,
            type=discord.ChannelType.private_thread
        )
        await thread.add_user(interaction.user)
        new_flow = PurchaseFlow(interaction.user.id, thread)
        active_flows[interaction.user.id] = new_flow
        await new_flow.send_step(1)
    elif cid == "submit_tx" and flow:
        modal = PaymentModal("Cryptocurrency", flow.robux, flow.price, flow.crypto, flow.discount_code)
        await interaction.response.send_modal(modal)
    elif cid == "submit_details" and flow:
        modal = PaymentModal(flow.method, flow.robux, flow.price, discount_code=flow.discount_code)
        await interaction.response.send_modal(modal)

# -------------------------------------------------
# ADMIN PANEL (FULLY FIXED + SETTINGS BUTTON + ALL EMOJIS)
# -------------------------------------------------
class AdminPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Set Crypto Address", style=discord.ButtonStyle.blurple, custom_id="admin_set_address", emoji=EMOJI_CRYPTO)
    async def set_address_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_set_address")

    @discord.ui.button(label="Set Crypto QR URL", style=discord.ButtonStyle.blurple, custom_id="admin_set_qr", emoji="image")
    async def set_qr_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_set_qr")

    @discord.ui.button(label="Add Discount Code", style=discord.ButtonStyle.green, custom_id="admin_add_discount_msg", emoji="label")
    async def add_discount_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="How to Add Discount Code", color=0x00FF00)
        embed.description = (
            "Type in **any channel** (with Staff role):\n\n"
            "```WINTERDEAL, 100000, 60.00```\n\n"
            "**Format:** `CODE, ROBUX_AMOUNT, PRICE_USD`"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Trigger Fake Order", style=discord.ButtonStyle.green, custom_id="admin_fake_order", emoji="robot")
    async def fake_order_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_fake_order")

    @discord.ui.button(label="Update Price List", style=discord.ButtonStyle.green, custom_id="admin_set_prices", emoji=EMOJI_ROBUX)
    async def set_prices_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_set_prices")

    @discord.ui.button(label="Update Payments", style=discord.ButtonStyle.secondary, custom_id="admin_set_payments", emoji="credit_card")
    async def set_payments_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_set_payments")

    @discord.ui.button(label="Update ToS", style=discord.ButtonStyle.secondary, custom_id="admin_set_tos", emoji="scroll")
    async def set_tos_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_set_tos")

    @discord.ui.button(label="Reset Info Embed", style=discord.ButtonStyle.red, custom_id="admin_reset_embed", emoji="repeat")
    async def reset_embed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_reset_embed")

    @discord.ui.button(label="Settings", style=discord.ButtonStyle.gray, custom_id="admin_settings", emoji=EMOJI_COG)
    async def settings_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Bot Settings", color=0x2F3136)
        embed.add_field(name="Rate", value=f"${ROBUX_RATE_PER_1000:.2f}/1K", inline=True)
        embed.add_field(name="Max Robux", value="800,000", inline=True)
        embed.add_field(name="Min Robux", value="10,000", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
# -------------------------------------------------
# COMPLETION LOGIC
# -------------------------------------------------
async def send_completed_order(amount, price, method):
    channel = bot.get_channel(COMPLETED_CHANNEL_ID)
    if not channel: return
    order_id = str(int(time.time() * 1000))[4:] + str(random.randint(100, 999))
    embed = discord.Embed(title="New Completed Order", color=0x38B750)
    embed.set_thumbnail(url="https://i.ibb.co/whbgBHWz/9c5fd434-f30f-4e24-8212-ea40fa098678.png")
    embed.add_field(name=f"{EMOJI_USER} User", value="**Hidden**", inline=True)
    embed.add_field(name="Payment Method", value=f"**{method}**", inline=True)
    embed.add_field(name=f"{EMOJI_ROBUX} Robux Purchased", value=f"**{amount:,} Robux**", inline=False)
    embed.add_field(name=f"{EMOJI_USD} USD Spent", value=f"**${price:.2f}**", inline=True)
    embed.add_field(name=f"{EMOJI_RATING} Rating", value="4/5", inline=True)
    embed.add_field(name=f"{EMOJI_ORDER_ID} Order ID", value=f"`{order_id}`", inline=False)
    embed.set_footer(text=f"Powered by Robux Town • discord.gg/robuxtown • {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}")
    await channel.send(embed=embed)

async def trigger_fake_order_now():
    amount = random.choice([10000, 25000, 50000, 100000, 250000])
    price = get_price(amount)
    method = random.choice(["Crypto", "Card", "PayPal", "Giftcard"])
    await send_completed_order(amount, price, method)

# -------------------------------------------------
# PRICE LIST EMBED
# -------------------------------------------------
async def send_price_embed(force_new: bool = False):
    channel = bot.get_channel(PRICE_CHANNEL_ID)
    if not channel: return
    try:
        if not force_new:
            messages = [m async for m in channel.history(limit=5)]
            for msg in messages:
                if msg.author == bot.user and msg.embeds and "Robux Town | Information:" in msg.embeds[0].title:
                    return
    except: pass
    embed = discord.Embed(
        title="Robux Town | Information:",
        description=(
            "**Welcome to Robux Town!** We pride ourselves on fast, reliable delivery and industry-low prices.\n\n"
            "• You will not get **Banned** for buying robux from us.\n"
            "• Robux is delivered via **Gamepass**.\n"
            "• Max Purchase Limit: **800,000** {EMOJI_ROBUX} {EMOJI_MAX}\n"
        ),
        color=0x2E639A
    )
    embed.set_thumbnail(url="https://i.ibb.co/v4rqV5Pj/9c5fd434-f30f-4e24-8212-ea40fa098678.png")
    embed.add_field(name=f"{EMOJI_ROBUX} **Available Packages**:", value=(
        "**Most Popular** fire\n"
        "• {EMOJI_ROBUX} **10,000 Robux** | **$9.99**\n"
        "• {EMOJI_ROBUX} **25,000 Robux** | **$24.99**\n"
        "• {EMOJI_ROBUX} **50,000 Robux** | **$49.99**\n"
        "\n**Best Deal** money\n"
        "• {EMOJI_ROBUX} **100,000 Robux** | **$99.99**\n"
        "• {EMOJI_ROBUX} **250,000 Robux** | **$249.99**\n"
        "\n**Other Packages**\n"
        "• {EMOJI_ROBUX} **500,000 Robux** | **$499.99**"
    ), inline=False)
    embed.set_image(url="https://i.ibb.co/FbRfdH7D/Screenshot-2025-11-10-at-6-58-42-PM.png")
    await channel.send(embed=embed)

# -------------------------------------------------
# PERSISTENT PURCHASE BUTTON
# -------------------------------------------------
class PersistentPurchaseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.blurple, custom_id="purchase_robux_btn")
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in active_flows:
            flow = active_flows[user_id]
            if not flow.thread.archived:
                await interaction.response.send_message(f"{EMOJI_WARNING} You already have an active flow in {flow.thread.mention}!", ephemeral=True)
                return
        await interaction.response.defer(ephemeral=True)
        thread_name = f"Purchase-{interaction.user.name}-{random.randint(1000,9999)}"
        info_channel = bot.get_channel(INFO_CHANNEL_ID)
        thread = await info_channel.create_thread(
            name=thread_name,
            auto_archive_duration=1440,
            type=discord.ChannelType.private_thread
        )
        await thread.add_user(interaction.user)
        flow = PurchaseFlow(interaction.user.id, thread)
        active_flows[interaction.user.id] = flow
        await interaction.followup.send(f"{EMOJI_VERIFIED} Purchase started! Check {thread.mention}", ephemeral=True)
        await flow.send_step(1)

# -------------------------------------------------
# INFO EMBED
# -------------------------------------------------
async def send_info_embed(force_new: bool = False):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if not channel: return
    try:
        messages = [m async for m in channel.history(limit=5)]
        for msg in messages:
            if msg.author == bot.user and msg.components and not force_new:
                return
    except: pass
    embed = discord.Embed(color=0x00A3FF)
    embed.set_author(name="Robux Town™", icon_url="https://i.ibb.co/v4rqV5Pj/9c5fd434-f30f-4e24-8212-ea40fa098678.png")
    embed.description = (
        "**Automated Purchase**\nSecure, instant Robux delivery.\n\n"
        "**Under 10 Minutes**\nRobux delivered via Gamepass.\n\n"
        "**Smart Payments**\nFully automated.\n\n"
        "**Bank-Level Security**\nYou will NOT get banned.\n\n"
        "**Payment Options**\n"
        f"• {EMOJI_CRYPTO} Crypto (BTC/LTC/ETH/SOL)\n"
        f"• {EMOJI_CARD} Card (G2A)\n"
        f"• {EMOJI_PAYPAL} PayPal (Eneba)\n"
        f"• {EMOJI_PAYMENT_SUPPORT} Giftcards\n\n"
        f"{EMOJI_ROBUX} **Rate:** **${ROBUX_RATE_PER_1000:.2f}** per 1,000 Robux"
    )
    embed.set_image(url="https://i.ibb.co/FbRfdH7D/Screenshot-2025-11-10-at-6-58-42-PM.png")
    view = PersistentPurchaseButton()
    await channel.send(embed=embed, view=view)

# -------------------------------------------------
# TERMS OF SERVICE EMBED

# -------------------------------------------------
async def send_tos_embed(force_new: bool = False):
    channel = bot.get_channel(TOS_CHANNEL_ID)
    if not channel: return
    if not force_new:
        try:
            if [m async for m in channel.history(limit=1)]: return
        except: pass
    embed = discord.Embed(
        title="Robux Town Terms of Service",
        description="By using our services, you agree to the following terms:",
        color=0x404040
    )
    embed.add_field(name="1. Delivery and Tax", value="All Robux is delivered via Gamepass. Roblox takes a 30% tax.", inline=False)
    embed.add_field(name="2. Refunds", value="Refunds are **not guaranteed** after payment.", inline=False)
    embed.add_field(name="3. Safety", value="We guarantee **zero bans**.", inline=False)
    embed.set_footer(text="Last Updated: November 2025")
    await channel.send(embed=embed)

# -------------------------------------------------
# PAYMENT METHODS EMBED
# -------------------------------------------------
async def send_payment_methods_embed(force_new: bool = False):
    channel = bot.get_channel(PAYMENT_METHOD_CHANNEL_ID)
    if not channel: return
    if not force_new:
        try:
            if [m async for m in channel.history(limit=1)]: return
        except: pass
    embed = discord.Embed(title="Accepted Payment Methods", description="Fully automated.", color=0x00A3FF)
    embed.add_field(name=f"1. {EMOJI_CRYPTO} Cryptocurrency", value="BTC, LTC, ETH, SOL.", inline=False)
    embed.add_field(name=f"2. {EMOJI_CARD} Card (via G2A Rewarble)", value=f"[G2A Link]({G2A_REWARBLE_LINK})", inline=False)
    embed.add_field(name=f"3. {EMOJI_PAYPAL} PayPal (via Eneba Rewarble)", value=f"[Eneba Link]({ENEBA_REWARBLE_LINK})", inline=False)
    embed.add_field(name=f"4. {EMOJI_PAYMENT_SUPPORT} Giftcards", value="Accepted on request.", inline=False)
    await channel.send(embed=embed)

# -------------------------------------------------
# AUTOMATED FAKE ORDER TASK
# -------------------------------------------------
@tasks.loop(hours=random.uniform(5, 10))
async def automated_fake_completion_loop():
    amount = random.choice([10000, 25000, 50000, 100000, 250000])
    price = get_price(amount)
    method = random.choice(["Crypto", "Card", "PayPal", "Giftcard"])
    await send_completed_order(amount, price, method)

# -------------------------------------------------
# ON READY
# -------------------------------------------------
@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")
    bot.add_view(PersistentPurchaseButton())
    await send_info_embed()
    await send_price_embed()
    await send_payment_methods_embed()
    await send_tos_embed()
    if not automated_fake_completion_loop.is_running():
        automated_fake_completion_loop.start()

# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("Please replace 'YOUR_DISCORD_BOT_TOKEN_HERE' with your actual token.")
    try:
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        print("Invalid BOT_TOKEN.")
    except Exception as e:
        print(f"Startup error: {e}")
