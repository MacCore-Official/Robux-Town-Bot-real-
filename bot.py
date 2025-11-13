#!/usr/bin/env python3
# Robux Town™ – FINALIZED UI + DISCOUNTS + ADMIN PANEL + PRICE LIST
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
except json.JSONDecodeError as e:
print(f"Config JSON error: {e}. Using defaults.")
except Exception as e:
print(f"Config load error: {e}")
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
embed = discord.Embed(title="Start Purchase? (1/6)", color=color)
view = discord.ui.View(timeout=None)
view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_1"))
view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_1"))
await self.thread.send(embed=embed, view=view)

elif step == 2:
embed = discord.Embed(title="How much Robux? (2/6)", color=color)
embed.description = "Enter amount (10,000 – 800,000)"
await self.thread.send(embed=embed)

elif step == 3:
embed = discord.Embed(title="Discount Code? (3/6)", color=color)
embed.description = "Type code or **SKIP**"
await self.thread.send(embed=embed)

elif step == 4:
rate = get_price(1000)
discount = f"**COUPON: {self.discount_code}**\n" if self.discount_code else ""
embed = discord.Embed(title="Confirm (4/6)", color=color)
embed.description = f"{discount}**{self.robux:,} {EMOJI_ROBUX}** → **${self.price:.2f}** (${rate:.2f}/1K)"
view = discord.ui.View(timeout=None)
view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_4"))
view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_4"))
await self.thread.send(embed=embed, view=view)

elif step == 5:
embed = discord.Embed(title="Payment Method (5/6)", color=color)
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
discord.SelectOption(label="BTC", value="btc", emoji=EMOJI_BITCOIN),
discord.SelectOption(label="LTC", value="ltc", emoji=EMOJI_LITECOIN),
discord.SelectOption(label="ETH", value="eth", emoji=EMOJI_ETHEREUM),
discord.SelectOption(label="SOL", value="sol", emoji=EMOJI_SOLANA),
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
# MESSAGE HANDLER (INCLUDES DISCOUNT VIA TEXT)
# -------------------------------------------------
@bot.event
async def on_message(message):
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
def __init__(self):
super().__init__(timeout=None)

@discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.blurple, custom_id="persistent_buy_robux")
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
# ADMIN PANEL
# ADMIN PANEL (PERSISTENT)
# -------------------------------------------------
class AdminPanel(discord.ui.View):
def __init__(self):
        super().__init__(timeout=300)
        super().__init__(timeout=None)  # REQUIRED

@discord.ui.button(label="Set Crypto Address", style=discord.ButtonStyle.blurple, custom_id="admin_set_address", emoji=EMOJI_CRYPTO)
async def set_address_button(self, interaction: discord.Interaction, button: discord.ui.Button):
await interaction.response.send_modal(AddressModal())

@discord.ui.button(label="Set Crypto QR URL", style=discord.ButtonStyle.blurple, custom_id="admin_set_qr", emoji="image")
async def set_qr_button(self, interaction: discord.Interaction, button: discord.ui.Button):
await interaction.response.send_modal(QRModal())

@discord.ui.button(label="Add Discount Code", style=discord.ButtonStyle.green, custom_id="admin_add_discount_msg", emoji="label")
async def add_discount_button(self, interaction: discord.Interaction, button: discord.ui.Button):
embed = discord.Embed(title="How to Add Discount Code", color=0x00FF00)
embed.description = (
            "Type in **any channel** ( with Staff role):\n\n"
            "Type in **any channel** (with Staff role):\n\n"
"```WINTERDEAL, 100000, 60.00```\n\n"
"**Format:** `CODE, ROBUX_AMOUNT, PRICE_USD`"
)
await interaction.response.send_message(embed=embed, ephemeral=True)

@discord.ui.button(label="Trigger Fake Order", style=discord.ButtonStyle.green, custom_id="admin_fake_order", emoji="robot")
async def fake_order_button(self, interaction: discord.Interaction, button: discord.ui.Button):
await trigger_fake_order_now()
await interaction.response.send_message(f"{EMOJI_VERIFIED} Fake order sent!", ephemeral=True)

# -------------------------------------------------
# MODALS (Address, QR)
# -------------------------------------------------
class AddressModal(discord.ui.Modal):
def __init__(self):
super().__init__(title="Set Crypto Address", timeout=600)
self.coin = discord.ui.TextInput(label="Coin (btc/ltc/eth/sol)", max_length=3)
self.address = discord.ui.TextInput(label="Address", style=discord.TextStyle.paragraph)
self.add_item(self.coin); self.add_item(self.address)
async def on_submit(self, i):
coin = self.coin.value.lower()
if coin in config["wallets"]:
config["wallets"][coin] = self.address.value
save_config(config)
await i.response.send_message(f"{EMOJI_VERIFIED} {coin.upper()} address updated.", ephemeral=True)

class QRModal(discord.ui.Modal):
def __init__(self):
super().__init__(title="Set Crypto QR URL", timeout=600)
self.coin = discord.ui.TextInput(label="Coin (btc/ltc/eth/sol)", max_length=3)
self.url = discord.ui.TextInput(label="QR Image URL", style=discord.TextStyle.paragraph)
self.add_item(self.coin); self.add_item(self.url)
async def on_submit(self, i):
coin = self.coin.value.lower()
if coin in config["qr_urls"]:
config["qr_urls"][coin] = self.url.value
save_config(config)
await i.response.send_message(f"{EMOJI_VERIFIED} {coin.upper()} QR updated.", ephemeral=True)

# -------------------------------------------------
# FAKE ORDER
# -------------------------------------------------
async def trigger_fake_order_now():
channel = bot.get_channel(COMPLETED_CHANNEL_ID)
if not channel: return
amount = random.choice([10000, 25000, 50000, 100000])
embed = discord.Embed(title="New Order Completed", color=0x38B750)
embed.add_field(name="Robux", value=f"**{amount:,}**", inline=True)
embed.add_field(name="USD", value=f"**${get_price(amount):.2f}**", inline=True)
await channel.send(embed=embed)

@tasks.loop(hours=random.uniform(4, 8))
async def fake_loop():
await trigger_fake_order_now()

# -------------------------------------------------
# ON READY
# -------------------------------------------------
@bot.event
async def on_ready():
print(f"Bot ready: {bot.user}")
    bot.add_view(BuyView())
    bot.add_view(AdminPanel())
    bot.add_view(BuyView())          # Persistent
    bot.add_view(AdminPanel())       # Now persistent
if not fake_loop.is_running():
fake_loop.start()

# -------------------------------------------------
# ADMIN COMMAND
# -------------------------------------------------
@bot.command()
async def admin(ctx):
if STAFF_ROLE_ID not in [r.id for r in ctx.author.roles]:
return
await ctx.send("Admin Panel", view=AdminPanel(), ephemeral=True)

# -------------------------------------------------
# RUN
# -------------------------------------------------
bot.run(BOT_TOKEN)
