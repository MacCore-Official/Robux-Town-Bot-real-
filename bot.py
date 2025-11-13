import json
import re
import random
import time 
import time
from datetime import datetime, timedelta
import requests
import discord
from discord.ext import commands, tasks
#bot setupp
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    # 4 spaces required here for the lines inside the 'if' block
    BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE" # This line should be removed as it sets a placeholder
    raise SystemExit("ERROR: BOT_TOKEN not set in Northflank! Add it under Environment Variables.")

# --- Rewarble Links (Defined at the top for global access) ---
# --- Rewarble Links ---
ENEBA_REWARBLE_LINK = "https://www.eneba.com/rewarble-rewarble-visa-10-usd-voucher-global"
G2A_REWARBLE_LINK = "https://www.g2a.com/rewarble-visa-gift-card-10-usd-by-rewarble-key-global-i10000502992001?suid=960beb55-4797-46d5-b14c-94995fd68f31"

# --- Giveaway Branding Assets (Ensure these are here for global access) ---
# --- Giveaway Assets ---
EMOJI_GIVEAWAY_REACT = "<:giveawaygift:1437688517089165442>"
EMOJI_CROWN_WINNER   = "👑" 
GIVEAWAY_THUMBNAIL   = "https://i.ibb.co/v4rqV5Pj/9c5fd434-f30f-4e24-8212-ea40fa098678.png" 
GIVEAWAY_BANNER      = "https://i.ibb.co/FbRfdH7D/Screenshot-2025-11-10-at-6-58-42-PM.png"
# --------------------------------------------------------

GIVEAWAY_THUMBNAIL = "https://i.ibb.co/v4rqV5Pj/9c5fd434-f30f-4e24-8212-ea40fa098678.png"
GIVEAWAY_BANNER = "https://i.ibb.co/FbRfdH7D/Screenshot-2025-11-10-at-6-58-42-PM.png"

# -------------------------------------------------
# CONFIG
# TOKEN FROM NORTHFLANK
# -------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE" 
    raise SystemExit("ERROR: BOT_TOKEN not set in Northflank! Add it under Environment Variables.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="+", intents=intents, help_command=None)

# Channels (PLACEHOLDER IDs - REPLACE WITH YOUR REAL IDs)
INFO_CHANNEL_ID           = 1435516058105675818 
PRICE_CHANNEL_ID          = 1435516058105675817 
ORDER_LOG_CHANNEL_ID      = 1435516057845497981 
COMPLETED_CHANNEL_ID      = 1435516058286035015 
LOG_CHANNEL_ID            = 1435516058286035020 
STAFF_ROLE_ID             = 1435516057526734991 
STAFF_DM_IDS              = [1422665161466187976,1269145029943758899] 
PAYMENT_METHOD_CHANNEL_ID = 1435516058105675820 
TOS_CHANNEL_ID            = 1435516058286035016 
VOUCH_CHANNEL_ID          = 1435516058286035025 
MANUAL_ORDER_CHANNEL_ID   = 1437288464759652513


# EMOJIS (ALL EMOJIS DEFINED HERE FOR GLOBAL ACCESS)
EMOJI_ROBUX          = "<:Robux:1435526693472178176>"
EMOJI_VERIFIED       = "<:Verified:1435526918891110551>"
EMOJI_LOADING        = "<a:Loading:1435526855523434576>" 
EMOJI_WARNING        = "<:warning:1435526954689495091>"
EMOJI_BITCOIN        = "<:Bitcoin:1435526466527039579>"
EMOJI_LITECOIN       = "<:Litecoin:1435526448684339321>"
EMOJI_ETHEREUM       = "<:Ethereum:1435526479126597745>"
EMOJI_SOLANA         = "<:Solana:1435526514115350549>"
EMOJI_CARD           = "<:Card:1435526554783318047>"
EMOJI_PAYPAL         = "<:PayPal:1435526543513354354>"
EMOJI_PAYMENT_SUPPORT= "<:PAYMENT_SUPPORT:1435526984011874434>"
EMOJI_COG            = "⚙️" 
EMOJI_CRYPTO         = "<:Crypto:1437309415551406222>" 
EMOJI_USER           = "👤" 
EMOJI_USD            = "💶" 
EMOJI_RATING         = "⭐" 
EMOJI_ORDER_ID       = "📄" 
EMOJI_LOCK           = "🔒" 
EMOJI_MAX            = "🛑" 

# -------------------------------------------------
# PRICE CALCULATION 
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
VOUCH_CHANNEL_ID = 1435516058286035025
MANUAL_ORDER_CHANNEL_ID = 1437288464759652513

# -------------------------------------------------
# EMOJIS
# -------------------------------------------------
EMOJI_ROBUX = "<:Robux:1435526693472178176>"
EMOJI_VERIFIED = "<:Verified:1435526918891110551>"
EMOJI_LOADING = "<a:Loading:1435526855523434576>"
EMOJI_WARNING = "<:warning:1435526954689495091>"
EMOJI_BITCOIN = "<:Bitcoin:1435526466527039579>"
EMOJI_LITECOIN = "<:Litecoin:1435526448684339321>"
EMOJI_ETHEREUM = "<:Ethereum:1435526479126597745>"
EMOJI_SOLANA = "<:Solana:1435526514115350549>"
EMOJI_CARD = "<:Card:1435526554783318047>"
EMOJI_PAYPAL = "<:PayPal:1435526543513354354>"
EMOJI_PAYMENT_SUPPORT = "<:PAYMENT_SUPPORT:1435526984011874434>"
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
"""Calculates the standard total USD price based on the Robux amount."""
return (robux_amount / 1000) * ROBUX_RATE_PER_1000
    return (robux_amount / 1000) * ROBUX_RATE_PER_1000

# -------------------------------------------------
# PRICE LIST DATA (For the new embed)
# -------------------------------------------------
ROBUX_PRODUCTS = {
10000: {"label": "10,000 Robux", "price": 9.99, "tag": "🔥 Most Popular", "style": "fire"},
25000: {"label": "25,000 Robux", "price": 24.99, "tag": "", "style": "default"},
50000: {"label": "50,000 Robux", "price": 49.99, "tag": "", "style": "default"},
100000: {"label": "100,000 Robux", "price": 99.99, "tag": "", "style": "default"},
250000: {"label": "250,000 Robux", "price": 249.99, "tag": "💰 Best Deal", "style": "deal"},
    10000: {"label": "10,000 Robux", "price": 9.99, "tag": "Most Popular", "style": "fire"},
    25000: {"label": "25,000 Robux", "price": 24.99, "tag": "", "style": "default"},
    50000: {"label": "50,000 Robux", "price": 49.99, "tag": "", "style": "default"},
    100000: {"label": "100,000 Robux", "price": 99.99, "tag": "", "style": "default"},
    250000: {"label": "250,000 Robux", "price": 249.99, "tag": "Best Deal", "style": "deal"},
}

# -------------------------------------------------
# CRYPTO (LIVE PRICES + CUSTOM ADDRESS/QR)
# CONFIG & CRYPTO
# -------------------------------------------------
CONFIG_FILE = "config.json"
CRYPTO_IDS = {"btc": "bitcoin", "ltc": "litecoin", "eth": "ethereum", "sol": "solana"}

# Persistent storage for addresses / QR / DISCOUNTS
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
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                loaded = json.load(f)
            config = default_config.copy()
            config.update(loaded)
            return config
        except json.JSONDecodeError:
            print("Config error. Using defaults.")
    return default_config.copy()

def save_config(data):
with open(CONFIG_FILE, "w") as f:
json.dump(data, f, indent=2)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

config = load_config()

async def get_crypto_price(crypto: str) -> float:
try:
r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={CRYPTO_IDS[crypto]}&vs_currencies=usd")
r.raise_for_status()
return r.json()[CRYPTO_IDS[crypto]]["usd"]
except:
return 60000.0 if crypto == "btc" else 80.0 if crypto == "ltc" else 3000.0 if crypto == "eth" else 100.0
    try:
        r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={CRYPTO_IDS[crypto]}&vs_currencies=usd", timeout=5)
        r.raise_for_status()
        return r.json()[CRYPTO_IDS[crypto]]["usd"]
    except:
        return 60000.0 if crypto == "btc" else 80.0 if crypto == "ltc" else 3000.0 if crypto == "eth" else 100.0

# -------------------------------------------------
# SEND TO STAFF DMs + LOG CHANNEL (Remains the same)
# STAFF NOTIFY
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
# GIVEAWAY LOGIC
# -------------------------------------------------
async def start_new_giveaway(target_channel_id: int, prize: str, duration_minutes: int, rigged_id: int):
target_channel = bot.get_channel(target_channel_id)
if not target_channel or not isinstance(target_channel, discord.TextChannel):
print(f"ERROR: Giveaway target channel ID {target_channel_id} is invalid.")
return

end_time = datetime.now() + timedelta(minutes=duration_minutes)
end_timestamp = int(end_time.timestamp())

embed = discord.Embed(
title=f"🎉 G I V E A W A Y 🎉",
description=f"One lucky participant will receive **{prize}**!\n\n"
f"**How to Enter:** React with the emoji below {EMOJI_GIVEAWAY_REACT}\n"
f"**Ends:** <t:{end_timestamp}:R> (<t:{end_timestamp}:T>)",
color=0xFFD700 # Gold
)
embed.set_author(name=f"{prize}", icon_url=GIVEAWAY_THUMBNAIL)
embed.set_thumbnail(url=GIVEAWAY_THUMBNAIL)
embed.set_image(url=GIVEAWAY_BANNER)

giveaway_message = await target_channel.send(content=f"**{EMOJI_ROBUX} NEW EVENT! {EMOJI_ROBUX}**", embed=embed)
await giveaway_message.add_reaction(EMOJI_GIVEAWAY_REACT)

await asyncio.sleep(duration_minutes * 60)

try:
final_message = await target_channel.fetch_message(giveaway_message.id)
except:
return

reaction = discord.utils.get(final_message.reactions, emoji=EMOJI_GIVEAWAY_REACT)
users = []

if reaction:
async for user in reaction.users():
if user.bot:
continue
users.append(user)

winner = None

if users:
winner_id_log = str(rigged_id)
if rigged_id != 0:
try:
rigged_user = await bot.fetch_user(rigged_id)
if rigged_user and rigged_user in users:
winner = rigged_user
else:
winner = random.choice(users)
except discord.NotFound:
winner = random.choice(users)
else:
winner = random.choice(users)
winner_id_log = "Random"

await target_channel.send(
f"🎉 **GIVEAWAY ENDED!** 🎉\n"
f"The winner of the **{prize}** is: {winner.mention} {EMOJI_CROWN_WINNER}"
)

embed.description = f"**WINNER:** {winner.mention} {EMOJI_CROWN_WINNER}\n\n**ENDED:** <t:{end_timestamp}:T>"
embed.set_footer(text=f"Giveaway concluded | Rigged ID Log: {winner_id_log}")
await final_message.edit(embed=embed)

else:
await target_channel.send(f"❌ Giveaway for **{prize}** ended. No entries recorded.")

# -------------------------------------------------
# ADMIN MODALS AND VIEWS
# -------------------------------------------------
class DiscountModal(discord.ui.Modal):
def __init__(self):
super().__init__(title="Set New Discount Code", timeout=600)
self.code = discord.ui.TextInput(label="Discount Code (e.g., WINTERDEAL)", placeholder="Must be uppercase, one word")
self.amount = discord.ui.TextInput(label="Robux Amount Covered by Deal", placeholder="e.g., 100000 (R$ amount user must buy)")
self.price = discord.ui.TextInput(label="Discounted Price in USD", placeholder="e.g., 60.00 (the discounted price)")
self.add_item(self.code)
self.add_item(self.amount)
self.add_item(self.price)

async def on_submit(self, interaction: discord.Interaction):
code = self.code.value.upper()

try:
amount = int(self.amount.value.replace(",", ""))
price = float(self.price.value)
except ValueError:
await interaction.response.send_message(f"{EMOJI_WARNING} Invalid number format for amount or price.", ephemeral=True)
return

config["deals"][code] = {"robux": amount, "price": price, "min_robux_required": amount}
save_config(config)
await interaction.response.send_message(
f"{EMOJI_VERIFIED} Discount code **{code}** set: {amount:,} R$ for **${price:.2f} USD**.",
ephemeral=True
)

class GiveawayModal(discord.ui.Modal):
def __init__(self):
super().__init__(title="Start New Rigged Giveaway", timeout=600)

self.channel_id = discord.ui.TextInput(label="Target Channel ID", placeholder="e.g., 1437675911079002173 (Where the announcement goes)", required=True)
self.prize = discord.ui.TextInput(label="Prize Description", placeholder=f"e.g., 50,000 {EMOJI_ROBUX} or Nitro", max_length=100)
self.winner_id = discord.ui.TextInput(label="Rigged Winner ID (User ID)", placeholder="Enter the User ID or 0 for random winner", required=True)
self.duration = discord.ui.TextInput(label="Duration (in Minutes)", placeholder="e.g., 60 (for 1 hour)", required=True)

self.add_item(self.channel_id)
self.add_item(self.prize)
self.add_item(self.winner_id)
self.add_item(self.duration)

async def on_submit(self, interaction: discord.Interaction):
await interaction.response.defer(ephemeral=True)

try:
target_id = int(self.channel_id.value)
duration_minutes = int(self.duration.value)
winner_id = int(self.winner_id.value)
except ValueError:
await interaction.followup.send(f"{EMOJI_WARNING} Channel ID, Duration, or Winner ID must be a valid number.", ephemeral=True)
return

target_channel = bot.get_channel(target_id)
if not target_channel:
await interaction.followup.send(f"{EMOJI_WARNING} Target Channel ID `{target_id}` not found or is invalid.", ephemeral=True)
return

await start_new_giveaway(target_id, self.prize.value, duration_minutes, winner_id)
await interaction.followup.send(f"{EMOJI_GIVEAWAY_REACT} Giveaway for '{self.prize.value}' initiated in {target_channel.mention}.", ephemeral=True)


class DeleteDiscountView(discord.ui.Select):
def __init__(self, discounts):
options = [
discord.SelectOption(label=f"{code} ({details['robux']:,} R$ for ${details['price']:.2f})", value=code) 
for code, details in discounts.items()
]
super().__init__(placeholder="Select code to DELETE permanently", options=options, min_values=1, max_values=1)

async def callback(self, interaction: discord.Interaction):
code_to_delete = self.values[0]
if code_to_delete in config['deals']:
del config['deals'][code_to_delete]
save_config(config)
await interaction.response.send_message(f"🗑️ Discount code **{code_to_delete}** has been successfully deleted.", ephemeral=True)
else:
await interaction.response.send_message(f"{EMOJI_WARNING} Code not found.", ephemeral=True)


class DiscountListModal(discord.ui.Modal):
def __init__(self):
super().__init__(title="Active Discounts", timeout=None)
active_deals = config.get("deals", {})
if not active_deals:
self.add_item(discord.ui.TextInput(label="No Active Discounts Found.", default="Please use 'Set Discount Code' first.", style=discord.TextStyle.paragraph, required=False))
return
self.add_item(discord.ui.TextInput(
label=f"Listing {len(active_deals)} Active Discounts:",
default="\n".join([f"  - {code}: {details['robux']:,} R$ for ${details['price']:.2f}" for code, details in active_deals.items()]),
style=discord.TextStyle.paragraph, required=False
))
self.active_deals = active_deals

async def on_submit(self, interaction: discord.Interaction):
if not self.active_deals:
await interaction.response.send_message("No discounts to delete.", ephemeral=True)
return

await interaction.response.send_message(
"Select the code you wish to delete permanently:",
view=discord.ui.View().add_item(DeleteDiscountView(self.active_deals)),
ephemeral=True
)

class ManualOrderModal(discord.ui.Modal):
def __init__(self):
super().__init__(title="Manual Order Submission", timeout=600)

self.roblox_user = discord.ui.TextInput(
label="Roblox Username/ID",
placeholder="e.g., Builderman or 100021",
required=True
)
self.robux_amount = discord.ui.TextInput(
label="Robux Amount",
placeholder="e.g., 50000",
required=True
)
self.payment_method = discord.ui.TextInput(
label="Payment Method & Details",
placeholder="e.g., PayPal, Giftcard, etc.",
required=True,
style=discord.TextStyle.paragraph
)

self.add_item(self.roblox_user)
self.add_item(self.robux_amount)
self.add_item(self.payment_method)

async def on_submit(self, interaction: discord.Interaction):
await interaction.response.send_message(
f"**Thank you!** Your manual order for {self.robux_amount.value} Robux has been submitted.\n"
f"Please wait for a staff member ({interaction.user.mention}) to verify and complete the order.",
ephemeral=True
)

staff_log_channel = bot.get_channel(LOG_CHANNEL_ID)

embed = discord.Embed(
title="🚨 New MANUAL Order Submitted 🚨",
description=f"Staff attention required for a non-automated order from {interaction.user.mention}.",
color=0xFF0000
)
embed.add_field(name="User", value=f"{interaction.user.mention}", inline=False)
embed.add_field(name="Roblox User", value=self.roblox_user.value, inline=True)
try:
robux_amount_formatted = f"{int(self.robux_amount.value.replace(',', '')):,}"
except ValueError:
robux_amount_formatted = self.robux_amount.value

embed.add_field(name="Robux Amount", value=robux_amount_formatted, inline=True)
embed.add_field(name="Payment Details", value=self.payment_method.value, inline=False)
embed.set_footer(text="Staff must manually verify payment and deliver Robux.")

if staff_log_channel:
staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
role_mention = staff_role.mention if staff_role else "@Staff"

await staff_log_channel.send(content=f"{role_mention} **NEW MANUAL ORDER PENDING:**", embed=embed)


class PaymentModal(discord.ui.Modal):
def __init__(self, method, amount, price, crypto=None, discount_code=None): 
super().__init__(title=f"Submit {method.upper()} Details", timeout=None)
self.method = method
self.amount = amount
self.price = price
self.crypto = crypto
self.discount_code = discount_code

self.details = discord.ui.TextInput(
label="Payment ID / TX Hash / Code",
placeholder="e.g., TXabc123 or Giftcard Code",
style=discord.TextStyle.paragraph
)
self.add_item(self.details)

async def on_submit(self, interaction: discord.Interaction):
method_name = self.method
if self.crypto:
method_name = f"{self.crypto.upper()}"

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

await interaction.response.send_message(f"{EMOJI_VERIFIED} **Payment Submitted!** Your details have been sent to staff for manual verification. Please wait.", ephemeral=True)
await send_to_staff(order_data)

class AddressModal(discord.ui.Modal):
def __init__(self):
super().__init__(title="Set Crypto Address", timeout=600)
self.coin = discord.ui.TextInput(label="Coin (btc, ltc, eth, sol)", placeholder="e.g., btc", max_length=3)
self.address = discord.ui.TextInput(label="New Address", placeholder="Paste the full wallet address here", style=discord.TextStyle.paragraph)
self.add_item(self.coin)
self.add_item(self.address)

async def on_submit(self, interaction: discord.Interaction):
coin = self.coin.value.lower()
addr = self.address.value

if coin in config["wallets"]:
config["wallets"][coin] = addr
save_config(config)
await interaction.response.send_message(f"{EMOJI_VERIFIED} Updated **{coin.upper()}** address to:\n`{addr}`", ephemeral=True)
else:
await interaction.response.send_message(f"{EMOJI_WARNING} Invalid coin specified. Must be one of: `btc`, `ltc`, `eth`, `sol`.", ephemeral=True)

class QRModal(discord.ui.Modal):
def __init__(self):
super().__init__(title="Set Crypto QR URL", timeout=600)
self.coin = discord.ui.TextInput(label="Coin (btc, ltc, eth, sol)", placeholder="e.g., btc", max_length=3)
self.url = discord.ui.TextInput(label="New QR Image URL", placeholder="Must be a direct link to an image (http://...)", style=discord.TextStyle.paragraph)
self.add_item(self.coin)
self.add_item(self.url)

async def on_submit(self, interaction: discord.Interaction):
coin = self.coin.value.lower()
url = self.url.value

if coin in config["qr_urls"]:
config["qr_urls"][coin] = url
save_config(config)
await interaction.response.send_message(f"{EMOJI_VERIFIED} Updated **{coin.upper()}** QR URL.", ephemeral=True)
else:
await interaction.response.send_message(f"{EMOJI_WARNING} Invalid coin specified. Must be one of: `btc`, `ltc`, `eth`, `sol`.", ephemeral=True)

class CloseTicketView(discord.ui.View):
def __init__(self, thread_id):
super().__init__(timeout=None)
self.thread_id = thread_id

@discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket_btn", emoji="🔒")
async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
thread = bot.get_channel(self.thread_id)
if thread:
try:
await interaction.response.send_message("Closing the ticket...", ephemeral=False)
await thread.edit(archived=True, locked=True)
active_flows.pop(interaction.user.id, None)
except discord.Forbidden:
await interaction.response.send_message(f"{EMOJI_WARNING} I do not have permission to close this ticket.", ephemeral=True)
except Exception as e:
await interaction.response.send_message(f"{EMOJI_WARNING} An error occurred while closing the ticket: {e}", ephemeral=True)
else:
await interaction.response.send_message(f"{EMOJI_WARNING} Could not find the thread.", ephemeral=True)

class PersistentPurchaseButton(discord.ui.View):
def __init__(self):
super().__init__(timeout=None) 

@discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.blurple, custom_id="purchase_robux_btn")
async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
user_id = interaction.user.id

if user_id in active_flows:
existing_flow = active_flows[user_id]
if not existing_flow.thread.archived:
await interaction.response.send_message(
f"{EMOJI_WARNING} You already have an active purchase flow in {existing_flow.thread.mention}!", 
ephemeral=True
)
return

await interaction.response.defer(ephemeral=True)
thread_name = f"Purchase-{interaction.user.name}-{random.randint(1000,9999)}"
info_channel = bot.get_channel(INFO_CHANNEL_ID) or interaction.channel

thread = await info_channel.create_thread(
name=thread_name,
auto_archive_duration=1440,
type=discord.ChannelType.private_thread
)
await thread.add_user(interaction.user)

flow = PurchaseFlow(user_id, thread)
active_flows[user_id] = flow
await flow.send_step(1)
await interaction.followup.send(f"Purchase started! Check your new private thread: {thread.mention}", ephemeral=True)

@discord.ui.button(label="Start Manual Order", style=discord.ButtonStyle.secondary, custom_id="start_manual_btn", emoji="✍")
async def manual_order_button(self, interaction: discord.Interaction, button: discord.ui.Button):
await interaction.response.send_modal(ManualOrderModal())


# -------------------------------------------------
# DISCLAIMER EMBED
# -------------------------------------------------
async def send_disclaimer_embed(thread: discord.Thread):
embed = discord.Embed(
title="⚠️ Please Note",
description=(
"**Please make sure that all conversations related to the deal are done within this ticket.** Failing to do so may put you at risk of being scammed.\n\n"
"Our staff will **never DM you** regarding any deals that are active or have already been completed."
),
color=0xFFA500 # Orange color for warning
)
view = CloseTicketView(thread.id)
await thread.send(embed=embed, view=view)

# -------------------------------------------------
# PURCHASE FLOW HELPER
# -------------------------------------------------
async def apply_discount(flow, code):
"""Applies discount to flow.price and flow.discount_code if code is valid."""
flow.discount_code = None
flow.price = get_price(flow.robux) 

if code.upper() == "SKIP" or not code:
return

deal = config["deals"].get(code.upper())

if deal:
min_r = deal.get("min_robux_required", 0)

if flow.robux >= min_r:
flow.price = deal["price"]
flow.discount_code = code.upper()
await flow.thread.send(f"{EMOJI_VERIFIED} Coupon **{code.upper()}** accepted! Your new total price is **${flow.price:.2f} USD**.", delete_after=10)
else:
await flow.thread.send(f"{EMOJI_WARNING} Coupon invalid. Minimum purchase for this deal is {min_r:,} R$. Using standard pricing.", delete_after=10)
else:
await flow.thread.send(f"{EMOJI_WARNING} Coupon code `{code}` is invalid. Using standard pricing.", delete_after=10)

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
embed = discord.Embed(title="Would you like to purchase this amount of Robux? (4/6)", color=color)

discount_info = ""
if self.discount_code:
discount_info = f"**COUPON APPLIED:** {self.discount_code}\n"

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
discord.SelectOption(label="Cryptocurrency", value="crypto", emoji='🪙'),
discord.SelectOption(label="Card (G2A)", value="card", emoji='💳'),
discord.SelectOption(label="PayPal (Eneba)", value="paypal", emoji='💵'),
discord.SelectOption(label="Giftcards", value="gift", emoji='🎁'),
]
)
async def payment_callback_wrapper(interaction: discord.Interaction):
await self.payment_callback(interaction)

select.callback = payment_callback_wrapper
view = discord.ui.View(timeout=None)
view.add_item(select)
await interaction.followup.send(embed=embed, view=view)

elif step == 6: 
pass


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
discord.SelectOption(label="BTC", value="btc", emoji='₿'),
discord.SelectOption(label="LTC", value="ltc", emoji='Ł'),
discord.SelectOption(label="ETH", value="eth", emoji='Ξ'),
discord.SelectOption(label="SOL", value="sol", emoji='◎'),
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

check_embed = discord.Embed(title="Checking For Transactions", color=0x00A3FF)
check_embed.description = (
f"{EMOJI_LOADING} We are actively monitoring transactions. Please proceed with your payment to complete the transaction process.\n"
f"This invoice will expire <t:{expiry_timestamp}:R>."
)
await interaction.followup.send(embed=check_embed)

async def send_payment_invoice(self, interaction: discord.Interaction):
name = "Giftcard" if self.method == "gift" else self.method
embed = discord.Embed(title=f"{name.upper()} Payment Invoice (6/6)", color=0x00A3FF) 

details = ""
if self.method == "card":
details = (
"**You must purchase a Rewarble Card from G2A** for the amount and submit the code.\n"
f"**G2A Link:** [Buy Rewarble Card Here]({G2A_REWARBLE_LINK})" 
)
elif self.method == "paypal":
details = (
"**You must purchase a Rewarble Card from Eneba** for the amount and submit the code.\n"
f"**Eneba Link:** [Buy Rewarble Card Here]({ENEBA_REWARBLE_LINK})" 
)
else: # Giftcard
details = "Please purchase the necessary giftcard and prepare to submit the code/details."

embed.description = f"Send **${self.price:.2f} USD** via **{name}**.\n\n{details}"

view = discord.ui.View(timeout=None)
view.add_item(discord.ui.Button(label="Submit Details", style=discord.ButtonStyle.blurple, custom_id="submit_details"))
await interaction.followup.send(embed=embed, view=view)

# -------------------------------------------------
# INTERACTION HANDLER (Remains the same)
class PurchaseFlow:
    def __init__(self, user_id, thread):
        self.user_id = user_id
        self.thread = thread
        self.robux = 0
        self.price = 0.0
        self.method = ""
        self.crypto = ""
        self.discount_code = None

    async def send_step(self, step: int):
        if step == 1:
            await send_disclaimer_embed(self.thread)
            embed = discord.Embed(title="Start Buying? (1/6)", color=0x00A3FF)
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_1"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_1"))
            await self.thread.send(embed=embed, view=view)

        elif step == 2:
            embed = discord.Embed(title="How much Robux? (2/6)", color=0x00A3FF)
            embed.description = "Enter amount (min 10K, max 800K):"
            await self.thread.send(embed=embed)

        elif step == 3:
            embed = discord.Embed(title="Discount Code? (3/6)", color=0x00A3FF)
            embed.description = "Enter code or type **SKIP**"
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
        embed = discord.Embed(title=f"{self.crypto.upper()} Invoice (6/6)", color=0x00A3FF)
        embed.description = f"Send `{amount:.8f}` {self.crypto.upper()}\nExpires: <t:{expiry}:R>"
        embed.add_field(name="Address", value=f"```{address}```", inline=False)
        embed.add_field(name="Amount", value=f"`{amount:.8f}`", inline=False)
        embed.set_image(url=qr)
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit TX", style=discord.ButtonStyle.blurple, custom_id="submit_tx"))
        await i.followup.send(embed=embed, view=view)

    async def send_payment_invoice(self, i):
        name = "Giftcard" if self.method == "gift" else self.method.capitalize()
        details = ""
        if self.method == "card":
            details = f"Buy Rewarble Card from G2A: [Link]({G2A_REWARBLE_LINK})"
        elif self.method == "paypal":
            details = f"Buy Rewarble Card from Eneba: [Link]({ENEBA_REWARBLE_LINK})"
        embed = discord.Embed(title=f"{name} Invoice (6/6)", color=0x00A3FF)
        embed.description = f"Submit code below.\n\n{details}"
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit", style=discord.ButtonStyle.blurple, custom_id="submit_details"))
        await i.followup.send(embed=embed, view=view)

# -------------------------------------------------
# INTERACTIONS
# -------------------------------------------------
@bot.event
async def on_interaction(interaction: discord.Interaction):
if not interaction.data or "custom_id" not in interaction.data:
return await bot.process_commands(interaction.message)

cid = interaction.data["custom_id"]
user_id = interaction.user.id
flow = active_flows.get(user_id)

if cid.startswith("flow_") and flow:
if cid == "flow_yes_1":
await interaction.response.defer()
await flow.send_step(2)

elif cid == "flow_no_1":
await interaction.response.defer()
await flow.thread.send("Purchase flow cancelled.")
await flow.thread.edit(archived=True, locked=True)
active_flows.pop(user_id, None)

elif cid == "flow_yes_4" and flow: # Step 4 CONFIRMATION
await interaction.response.defer()
await flow.send_step(5) # Move to payment method

elif cid == "flow_no_4" and flow: # Step 4 RESTART
await interaction.response.defer()
await flow.thread.send("Cancelled. Restarting...")
await flow.thread.edit(archived=True, locked=True)
active_flows.pop(user_id, None)

# Start a new thread for restart
info_channel = bot.get_channel(INFO_CHANNEL_ID)
thread = await info_channel.create_thread(
name=f"Purchase-{interaction.user.name}-{random.randint(1000,9999)}",
auto_archive_duration=1440,
type=discord.ChannelType.private_thread
)
await thread.add_user(interaction.user)
new_flow = PurchaseFlow(interaction.user.id, thread)
active_flows[user_id] = new_flow
await new_flow.send_step(1)

elif cid == "submit_tx" and flow:
modal = PaymentModal("Cryptocurrency", flow.robux, flow.price, flow.crypto, flow.discount_code)
await interaction.response.send_modal(modal)

elif cid == "submit_details" and flow:
modal = PaymentModal(flow.method, flow.robux, flow.price, discount_code=flow.discount_code)
await interaction.response.send_modal(modal)

await bot.process_commands(interaction.message)

# -------------------------------------------------
# MESSAGE: AMOUNT (Step 2 input) & DISCOUNT CODE (Step 3 input) (Remains the same)
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
async def on_message(message: discord.Message):
# FIX: Always process commands first if not from a bot
if not message.author.bot:
await bot.process_commands(message) 

if message.author.bot or not message.channel.name.startswith("Purchase-"):
return 

flow = active_flows.get(message.author.id)

if flow and flow.thread.id == message.channel.id:

# Check 1: Waiting for Robux Amount (Step 2)
if flow.robux == 0 and re.fullmatch(r"[\d,]+", message.content.strip()):
try:
amount = int(message.content.replace(",", "").strip())
if amount < 10000:
await message.reply(f"{EMOJI_WARNING} The **minimum order** is 10,000 {EMOJI_ROBUX}.", delete_after=5)
return
if amount > 800000:
await message.reply(f"{EMOJI_MAX} The **maximum order** is 800,000 {EMOJI_ROBUX}.", delete_after=5)
return

flow.robux = amount
await message.delete()
await flow.send_step(3)
return
except ValueError:
pass 

# Check 2: Waiting for Discount Code (Step 3)
if flow.robux > 0 and flow.price == 0.0:
code = message.content.strip()
await message.delete()

await apply_discount(flow, code)

await flow.send_step(4)
return

async def on_message(message):
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
    elif flow.robux > 0 and flow.price == 0.0:
        code = message.content.strip()
        await message.delete()
        flow.price = get_price(flow.robux)
        if code.upper() != "SKIP":
            deal = config["deals"].get(code.upper())
            if deal and flow.robux >= deal.get("min_robux_required", 0):
                flow.price = deal["price"]
                flow.discount_code = code.upper()
                await flow.thread.send(f"{EMOJI_VERIFIED} Coupon **{code.upper()}** applied! Price: **${flow.price:.2f}**")
            else:
                await flow.thread.send(f"{EMOJI_WARNING} Invalid or not applicable coupon. Using standard price.")
        await flow.send_step(4)
    await bot.process_commands(message)

# -------------------------------------------------
# MODALS
# -------------------------------------------------
# STAFF ADMIN PANEL COMMANDS 
# -------------------------------------------------
def is_staff():
async def predicate(ctx):
if STAFF_ROLE_ID:
return STAFF_ROLE_ID in [role.id for role in ctx.author.roles]
return ctx.author.guild_permissions.administrator
return commands.check(predicate)

@bot.command(name="admin")
@is_staff()
async def admin_panel(ctx):
"""Opens the interactive staff administration panel."""
embed = discord.Embed(
title=f"{EMOJI_COG} Staff Administration Panel",
description="Select an action to manage bot settings or trigger automated events.",
color=discord.Color.blue()
)
await ctx.send(embed=embed, view=AdminPanel(), ephemeral=True)


@bot.command(name="vouchprompt")
@is_staff()
async def vouch_prompt_command(ctx):
"""Sends the server-wide vouch request announcement."""
await send_vouch_prompt(ctx)


# -------------------------------------------------
# MANUAL FAKE ORDER TRIGGER LOGIC 
# -------------------------------------------------
async def trigger_fake_order_now():
"""Generates and sends a single fake completion embed immediately."""
amount = random.choice([10000, 25000, 50000, 100000, 250000])
price = get_price(amount)
method = random.choice(["Crypto", "Card", "PayPal", "Giftcard"])

await send_completed_order(amount, price, method)

# --- CENTRALIZED HANDLER FOR ADMIN BUTTONS ---
async def handle_admin_panel_interaction(interaction: discord.Interaction, cid: str):
if cid == "admin_set_address":
await interaction.response.send_modal(AddressModal())
elif cid == "admin_set_qr":
await interaction.response.send_modal(QRModal())
elif cid == "admin_fake_order":
await interaction.response.defer(ephemeral=True)
await trigger_fake_order_now()
await interaction.followup.send(f"{EMOJI_VERIFIED} Fake order triggered to the completion channel.", ephemeral=True)
elif cid == "admin_set_discount":
await interaction.response.send_modal(DiscountModal())
elif cid == "admin_list_discounts":
await interaction.response.send_modal(DiscountListModal())
elif cid == "admin_start_giveaway":
if not isinstance(interaction.channel, discord.TextChannel):
await interaction.response.send_message(f"{EMOJI_WARNING} Please run this in a regular text channel.", ephemeral=True)
return

modal = GiveawayModal()
await interaction.response.send_modal(modal)
elif cid == "admin_set_prices":
await interaction.response.defer(ephemeral=True)
await send_price_embed(force_new=True)
await interaction.followup.send(f"{EMOJI_VERIFIED} New Price List embed sent to the price channel.", ephemeral=True)
elif cid == "admin_reset_embed":
await interaction.response.defer(ephemeral=True)
await send_info_embed(force_new=True)
await interaction.followup.send(f"{EMOJI_VERIFIED} New Info Embed sent to the main channel.", ephemeral=True)
elif cid == "admin_set_payments":
await interaction.response.defer(ephemeral=True)
await send_payment_methods_embed(force_new=True)
await interaction.followup.send(f"{EMOJI_VERIFIED} Payment Methods embed sent to the payment channel.", ephemeral=True)
elif cid == "admin_set_tos":
await interaction.response.defer(ephemeral=True)
await send_tos_embed(force_new=True)
await interaction.followup.send(f"{EMOJI_VERIFIED} ToS embed sent to the ToS channel.", ephemeral=True)
# -------------------------------------------------


# -------------------------------------------------
# ADMIN PANEL VIEW (The Interactive Menu)
class PaymentModal(discord.ui.Modal):
    def __init__(self, method, amount, price, crypto=None, discount_code=None):
        super().__init__(title=f"Submit {method.upper()} Details", timeout=None)
        self.method = method; self.amount = amount; self.price = price; self.crypto = crypto; self.discount_code = discount_code
        self.details = discord.ui.TextInput(label="TX Hash / Code", style=discord.TextStyle.paragraph)
        self.add_item(self.details)

    async def on_submit(self, i):
        method_name = self.crypto.upper() if self.crypto else self.method.capitalize()
        data = {
            "User": f"{i.user.mention}",
            "Robux": f"{self.amount:,} {EMOJI_ROBUX}",
            "USD": f"${self.price:.2f}",
            "Method": method_name,
            "Details": self.details.value,
            "Discount": self.discount_code or "None",
            "Thread": i.channel.mention,
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        await i.response.send_message(f"{EMOJI_VERIFIED} Submitted!", ephemeral=True)
        await send_to_staff(data)

# -------------------------------------------------
# ADMIN PANEL
# -------------------------------------------------
class AdminPanel(discord.ui.View):
def __init__(self):
super().__init__(timeout=300) 

@discord.ui.button(label="Set Crypto Address", style=discord.ButtonStyle.blurple, custom_id="admin_set_address", emoji='🪙')
async def set_address_button(self, interaction: discord.Interaction, button: discord.ui.Button):
await handle_admin_panel_interaction(interaction, "admin_set_address")

@discord.ui.button(label="Set Crypto QR URL", style=discord.ButtonStyle.blurple, custom_id="admin_set_qr", emoji="🖼️")
async def set_qr_button(self, interaction: discord.Interaction, button: discord.ui.Button):
await handle_admin_panel_interaction(interaction, "admin_set_qr")

@discord.ui.button(label="Set Discount Code", style=discord.ButtonStyle.blurple, custom_id="admin_set_discount", emoji="🏷️")
async def set_discount_button(self, interaction: discord.Interaction, button: discord.ui.Button):
await handle_admin_panel_interaction(interaction, "admin_set_discount")

@discord.ui.button(label="List/Delete Discounts", style=discord.ButtonStyle.secondary, custom_id="admin_list_discounts", emoji="🗑️")
async def list_discounts_button(self, interaction: discord.Interaction, button: discord.ui.Button):
await handle_admin_panel_interaction(interaction, "admin_list_discounts")

@discord.ui.button(label="Trigger Fake Order", style=discord.ButtonStyle.green, custom_id="admin_fake_order", emoji="🤖")
async def fake_order_button(self, interaction: discord.Interaction, button: discord.ui.Button):
await handle_admin_panel_interaction(interaction, "admin_fake_order")

@discord.ui.button(label="Start Giveaway", style=discord.ButtonStyle.green, custom_id="admin_start_giveaway", emoji=EMOJI_GIVEAWAY_REACT)
async def start_giveaway_button(self, interaction: discord.Interaction, button: discord.ui.Button):
await handle_admin_panel_interaction(interaction, "admin_start_giveaway")

@discord.ui.button(label="Update Price List", style=discord.ButtonStyle.green, custom_id="admin_set_prices", emoji='💸')
async def set_prices_button(self, interaction: discord.Interaction, button: discord.ui.Button):
await handle_admin_panel_interaction(interaction, "admin_set_prices")

@discord.ui.button(label="Update Payments", style=discord.ButtonStyle.secondary, custom_id="admin_set_payments", emoji="💳")
async def set_payments_button(self, interaction: discord.Interaction, button: discord.ui.Button):
await handle_admin_panel_interaction(interaction, "admin_set_payments")

@discord.ui.button(label="Update ToS", style=discord.ButtonStyle.secondary, custom_id="admin_set_tos", emoji="📜")
async def set_tos_button(self, interaction: discord.Interaction, button: discord.ui.Button):
await handle_admin_panel_interaction(interaction, "admin_set_tos")

@discord.ui.button(label="Reset Info Embed", style=discord.ButtonStyle.red, custom_id="admin_reset_embed", emoji="🔄")
async def reset_embed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
await handle_admin_panel_interaction(interaction, "admin_reset_embed")


# -------------------------------------------------
# COMPLETION LOGIC
    @discord.ui.button(label="Set Address", style=discord.ButtonStyle.blurple)
    async def addr(self, i, b): await i.response.send_modal(AddressModal())
    @discord.ui.button(label="Set QR", style=discord.ButtonStyle.blurple)
    async def qr(self, i, b): await i.response.send_modal(QRModal())
    @discord.ui.button(label="Fake Order", style=discord.ButtonStyle.green)
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
    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.blurple)
    async def buy(self, i, b):
        if i.user.id in active_flows:
            await i.response.send_message(f"{EMOJI_WARNING} You already have a thread!", ephemeral=True)
            return
        info = bot.get_channel(INFO_CHANNEL_ID)
        thread = await info.create_thread(name=f"Purchase-{i.user.name}-{random.randint(1000,9999)}", type=discord.ChannelType.private_thread)
        await thread.add_user(i.user)
        flow = PurchaseFlow(i.user.id, thread)
        active_flows[i.user.id] = flow
        await i.response.send_message(f"Started in {thread.mention}", ephemeral=True)
        await flow.send_step(1)

@bot.command()
async def setup(ctx):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    embed = discord.Embed(title="Robux Town™", description="Click to buy!", color=0x00A3FF)
    await channel.send(embed=embed, view=BuyView())

# -------------------------------------------------
# FAKE ORDERS
# -------------------------------------------------
async def send_completed_order(amount, price, method):
channel = bot.get_channel(COMPLETED_CHANNEL_ID)
if not channel: return

order_id = str(int(time.time() * 1000))[4:] + str(random.randint(100, 999)) 
user_name = "Hidden" 
rating_stars = "⭐⭐⭐⭐ (4/5)" 

embed = discord.Embed(title=f"✅ New Completed Order", color=0x38B750) 

embed.set_thumbnail(url="https://i.ibb.co/whbgBHWz/9c5fd434-f30f-4e24-8212-ea40fa098678.png") 

    # FIX: Corrected f-string syntax here: value=f"**{user_name}**"
embed.add_field(name="👤 User", value=f"**{user_name}**", inline=True) 
embed.add_field(name="💳 Payment Method", value=f"**{method}**", inline=True)

embed.add_field(name=f"{EMOJI_ROBUX} Robux Purchased", value=f"**{amount:,} Robux**", inline=False) 
embed.add_field(name="💶 USD Spent", value=f"**${price:.2f}**", inline=True)
embed.add_field(name="⭐ Rating", value=rating_stars, inline=True)

embed.add_field(name="📄 Order ID", value=f"`{order_id}`", inline=False)

embed.set_footer(text=f"Powered by Robux Town • discord.gg/robuxtown • {datetime.now().strftime('%B %d, %Y at %H:%M UTC')} ")

await channel.send(embed=embed)

# -------------------------------------------------
# PRICE LIST EMBED 
# -------------------------------------------------
async def send_price_embed(force_new: bool = False):
channel = bot.get_channel(PRICE_CHANNEL_ID)
if not channel:
print("Price channel not found!")
return

embed = discord.Embed(
title="📢 Robux Town | Information:",
description=(
f"**Welcome to Robux Town!** We pride ourselves on fast, reliable delivery and industry-low prices. We are currently accepting orders up to **800,000** {EMOJI_ROBUX}.\n\n"
f"• You will not get **Banned** for buying robux from us.\n"
f"• Robux is delivered via **Gamepass**.\n"
f"• Max Purchase Limit: **800,000** {EMOJI_ROBUX} {EMOJI_MAX}\n"
),
color=0x2E639A
)
embed.set_thumbnail(url="https://i.ibb.co/v4rqV5Pj/9c5fd434-f30f-4e24-8212-ea40fa098678.png")

products_list = []

products_list.append("**Most Popular** 🔥")
products_list.extend([
f"• {EMOJI_ROBUX} **{p['label']}** | **${p['price']:.2f}**"
for r, p in ROBUX_PRODUCTS.items() if p['style'] == 'fire'
])

products_list.append("\n**Best Deal** 💰")
products_list.extend([
f"• {EMOJI_ROBUX} **{p['label']}** | **${p['price']:.2f}**"
for r, p in ROBUX_PRODUCTS.items() if p['style'] == 'deal'
])

products_list.append("\n**Other Packages**")
products_list.extend([
f"• {EMOJI_ROBUX} **{p['label']}** | **${p['price']:.2f}**"
for r, p in ROBUX_PRODUCTS.items() if p['style'] == 'default'
])

products_field_value = "\n".join(products_list)

embed.add_field(name=f"{EMOJI_ROBUX} **Available Packages**:", 
value=products_field_value, 
inline=False)

embed.set_image(url="https://i.ibb.co/FbRfdH7D/Screenshot-2025-11-10-at-6-58-42-PM.png") 

try:
if not force_new:
messages = [m async for m in channel.history(limit=5)]
for msg in messages:
if msg.author == bot.user and msg.embeds and "Robux Town | Information:" in msg.embeds[0].title:
print("Existing Price embed found and preserved.")
return
except Exception as e:
print(f"Error checking for existing price embed: {e}")

await channel.send(embed=embed)
print("Price List embed sent.")

# -------------------------------------------------
# INFO EMBED 
# -------------------------------------------------
async def send_info_embed(force_new: bool = False):
channel = bot.get_channel(INFO_CHANNEL_ID)
if not channel:
print("Info channel not found! Cannot send info embed.")
return

embed = discord.Embed(color=0x00A3FF)
embed.set_author(name="Robux Town™", icon_url="https://i.ibb.co/v4rqV5Pj/9c5fd434-f30f-4e24-8212-ea40fa098678.png")
embed.description = (
"**Automated Purchase**\nSecure, instant Robux delivery.\n\n"
"**Under 10 Minutes**\nRobux delivered via Gamepass.\n\n"
"**Smart Payments**\nFully automated.\n\n"
"**Bank-Level Security**\nYou will NOT get banned.\n\n"
"**Payment Options**\n"
f"• 🪙 Crypto (BTC/LTC/ETH/SOL)\n"
f"• 💳 Card (G2A)\n"
f"• 💵 PayPal (Eneba)\n"
f"• 🎁 Giftcards\n\n"
f"{EMOJI_ROBUX} **Rate:** **${ROBUX_RATE_PER_1000:.2f}** per 1,000 Robux"
)
embed.set_image(url="https://i.ibb.co/FbRfdH7D/Screenshot-2025-11-10-at-6-58-42-PM.png")

try:
if not force_new:
messages = [m async for m in channel.history(limit=5)]
for msg in messages:
if msg.author == bot.user and msg.components and not force_new:
print("Existing Info embed found and preserved.")
return
except Exception as e:
print(f"Error checking for existing info embed: {e}")

view = PersistentPurchaseButton()
await channel.send(embed=embed, view=view)
print("Info embed sent (BLUE BORDER)")

# -------------------------------------------------
# TERMS OF SERVICE EMBED (NEW)
# -------------------------------------------------
async def send_tos_embed(force_new: bool = False):
channel = bot.get_channel(TOS_CHANNEL_ID)
if not channel:
print("ToS channel not found!")
return

embed = discord.Embed(
title="📜 Robux Town Terms of Service",
description="By using our services, you agree to the following terms:",
color=0x404040
)

embed.add_field(
name="1. Delivery and Tax",
value="All Robux is delivered via Gamepass. Roblox takes a 30% tax, which is calculated into your final price.",
inline=False
)
embed.add_field(
name="2. Refunds",
value="Refunds are **not guaranteed** after payment submission. Disputes may result in a permanent ban.",
inline=False
)
embed.add_field(
name="3. Safety",
value="We guarantee **zero bans** related to our service. Your account safety is our priority.",
inline=False
)
embed.set_footer(text="Last Updated: November 2025")

if not force_new:
try:
if [m async for m in channel.history(limit=1)]: return
except: pass

await channel.send(embed=embed)
print("ToS embed sent.")

# -------------------------------------------------
# PAYMENT METHODS EMBED (NEW)
# -------------------------------------------------
async def send_payment_methods_embed(force_new: bool = False):
channel = bot.get_channel(PAYMENT_METHOD_CHANNEL_ID)
if not channel:
print("Payment Method channel not found!")
return

embed = discord.Embed(
title="💳 Accepted Payment Methods",
description="We offer fully automated payment processing for instant Robux delivery.",
color=0x00A3FF
)

embed.add_field(
name="1. 🪙 Cryptocurrency",
value="**Instant Confirmation:** Bitcoin (BTC), Litecoin (LTC), Ethereum (ETH), Solana (SOL).",
inline=False
)

embed.add_field(
name="2. 💳 Card (via G2A Rewarble)",
value=f"Purchase a **Rewarble Card on G2A** and submit the code. [G2A Link]({G2A_REWARBLE_LINK})",
inline=False
)

embed.add_field(
name="3. 💵 PayPal (via Eneba Rewarble)",
value=f"Purchase a **Rewarble Card on Eneba** using PayPal/Card and submit the code. [Eneba Link]({ENEBA_REWARBLE_LINK})",
inline=False
)

embed.add_field(
name="4. 🎁 Giftcards",
value="We accept various gift cards on request. Please start a purchase flow to see current accepted gift cards.",
inline=False
)

if not force_new:
try:
if [m async for m in channel.history(limit=1)]: return
except: pass

await channel.send(embed=embed)
print("Payment Methods embed sent.")

# -------------------------------------------------
# STARTUP/TASKS
# -------------------------------------------------
    channel = bot.get_channel(COMPLETED_CHANNEL_ID)
    if not channel: return
    order_id = str(int(time.time() * 1000))[4:] + str(random.randint(100, 999))
    embed = discord.Embed(title="New Completed Order", color=0x38B750)
    embed.add_field(name="User", value="**Hidden**", inline=True)
    embed.add_field(name="Method", value=f"**{method}**", inline=True)
    embed.add_field(name="Robux", value=f"**{amount:,} Robux**", inline=False)
    embed.add_field(name="USD", value=f"**${price:.2f}**", inline=True)
    embed.add_field(name="Rating", value="Rating (4/5)", inline=True)
    embed.add_field(name="Order ID", value=f"`{order_id}`", inline=False)
    await channel.send(embed=embed)

@tasks.loop(hours=random.uniform(5, 10))
async def automated_fake_completion_loop():
amount = random.choice([10000, 25000, 50000, 100000, 250000])
price = get_price(amount)
method = random.choice(["Crypto", "Card", "PayPal", "Giftcard"])

await send_completed_order(amount, price, method)
    amount = random.choice([10000, 25000, 50000, 100000, 250000])
    price = get_price(amount)
    method = random.choice(["Crypto", "Card", "PayPal", "Giftcard"])
    await send_completed_order(amount, price, method)

# -------------------------------------------------
# STARTUP
# -------------------------------------------------
@bot.event
async def on_ready():
print(f"Logged in as {bot.user}")

try:
persistent_view = PersistentPurchaseButton()
bot.add_view(persistent_view)
except Exception as e:
print(f"Error adding persistent view: {e}")

await send_info_embed()
await send_price_embed() 
await send_payment_methods_embed() 
await send_tos_embed()             

if not automated_fake_completion_loop.is_running():
automated_fake_completion_loop.start()
    print(f"Logged in as {bot.user}")
    bot.add_view(BuyView())
    if not automated_fake_completion_loop.is_running():
        automated_fake_completion_loop.start()

# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("--- WARNING ---")
        print("Please replace 'YOUR_DISCORD_BOT_TOKEN_HERE' with your actual bot token.")
        print("The bot will not start correctly without a valid token.")
    try:
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        print("Error: The provided BOT_TOKEN is invalid. Please check your token.")
    except Exception as e:
        print(f"An unexpected error occurred during bot startup: {e}")
bot.run(BOT_TOKEN)
