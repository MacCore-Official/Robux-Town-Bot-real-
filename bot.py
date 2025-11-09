#!/usr/bin/env python3
# Robux Town™ – EXACT UI + LIVE PRICES + COMMANDS + FIXED INTERACTION + LOG 1435516058286035020
import os
import asyncio
import json
import re
import random
from datetime import datetime
import requests
import discord
from discord.ext = commands, tasks

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN not set!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="+", intents=intents, help_command=None)

# Channels
INFO_CHANNEL_ID      = 1435516058105675818
ORDER_LOG_CHANNEL_ID = 1435516058105675819
COMPLETED_CHANNEL_ID = 1435516058286035015
LOG_CHANNEL_ID       = 1435516058286035020  # NEW LOG
STAFF_ROLE_ID        = 1435516057526734991
STAFF_DM_IDS         = [1422665161466187976, 1269145029943758899]

# EMOJIS
EMOJI_ROBUX          = "<:Robux:1435526693472178176>"
EMOJI_VERIFIED       = "<:Verified:1435526918891110551>"
EMOJI_LOADING        = "<:Loading:1435526855523434576>"  # YOUR LOADING ID
EMOJI_WARNING        = "<:warning:1435526954689495091>"
EMOJI_BITCOIN        = "<:Bitcoin:1435526466527039579>"
EMOJI_LITECOIN       = "<:Litecoin:1435526448684339321>"
EMOJI_ETHEREUM       = "<:Ethereum:1435526479126597745>"
EMOJI_SOLANA         = "<:Solana:1435526514115350549>"
EMOJI_CARD           = "<:Card:1435526554783318047>"
EMOJI_PAYPAL         = "<:PayPal:1435526543513354354>"
EMOJI_PAYMENT_SUPPORT= "<:PAYMENT_SUPPORT:1435526984011874434>"

# -------------------------------------------------
# CRYPTO (LIVE PRICES + CUSTOM ADDRESS/QR)
# -------------------------------------------------
CRYPTO_IDS = {"btc": "bitcoin", "ltc": "litecoin", "eth": "ethereum", "sol": "solana"}

# Persistent storage for addresses / QR
CONFIG_FILE = "config.json"
default_config = {
    "wallets": {
        "btc": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        "ltc": "Labc123xyz...",
        "eth": "0x1234567890abcdef1234567890abcdef12345678",
        "sol": "SoL123abc..."
    },
    "qr_urls": {
        "btc": "",
        "ltc": "",
        "eth": "",
        "sol": ""
    }
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return default_config.copy()

def save_config(data):
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

    # Log to new channel
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

# -------------------------------------------------
# MODAL
# -------------------------------------------------
class PaymentModal(discord.ui.Modal):
    def __init__(self, method, amount, price, crypto=None):
        super().__init__(title=f"Submit {method.upper()} Details", timeout=None)
        self.method = method
        self.amount = amount
        self.price = price
        self.crypto = crypto

        self.details = discord.ui.TextInput(
            label="Payment ID / TX Hash / Code",
            placeholder="e.g., TXabc123",
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.details)

    async def on_submit(self, interaction: discord.Interaction):
        method_name = self.method
        if self.crypto:
            method_name = f"{self.crypto.upper()}"

        order_data = {
            "User": f"{interaction.user}",
            "Robux": f"{self.amount:,}",
            "USD": f"${self.price:.2f}",
            "Method": method_name,
            "Details": self.details.value,
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        await send_to_staff(order_data)
        await interaction.response.send_message(f"{EMOJI_VERIFIED} Submitted!", ephemeral=True)

        await asyncio.sleep(8)
        await send_completed_order(self.amount, self.price, method_name)
        await interaction.followup.send(f"{EMOJI_VERIFIED} Order completed!", ephemeral=True)

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

    async def send_step(self, step: int):
        color = 0x00A3FF
        if step == 1:
            embed = discord.Embed(title="Would you like to start buying robux? (1/5)", color=color)
            embed.description = "Please click \"Yes\" to begin."
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_1"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_1"))
            await self.thread.send(embed=embed, view=view)

        elif step == 2:
            embed = discord.Embed(title="How much robux would you like to buy? (2/5)", color=color)
            embed.description = "Please specify the amount of Robux you would like to purchase:\nThe minimum order amount is 10,000 Robux"
            await self.thread.send(embed=embed)

        elif step == 3:
            self.price = get_price(self.robux)
            embed = discord.Embed(title="Would you like to purchase this amount of Robux? (3/5)", color=color)
            embed.description = f"Are you sure you want to purchase {self.robux:,} Robux:\nCurrent Rate: ${self.price:.2f} per 1,000 Robux\nPrice in USD: ${self.price:.2f}"
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_3"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_3"))
            await self.thread.send(embed=embed, view=view)

        elif step == 4:
            embed = discord.Embed(title="Please select your preferred payment method (4/5)", color=color)
            embed.description = "You have selected Cryptocurrency as your sending payment. What crypto will you be sending?"
            select = discord.ui.Select(
                placeholder="Select your crypto",
                custom_id="payment_select",
                options=[
                    discord.SelectOption(label="Cryptocurrency", value="crypto", emoji=EMOJI_BITCOIN),
                    discord.SelectOption(label="Card (G2A)", value="card", emoji=EMOJI_CARD),
                    discord.SelectOption(label="PayPal (Eneba)", value="paypal", emoji=EMOJI_PAYPAL),
                    discord.SelectOption(label="Giftcards", value="gift", emoji=EMOJI_PAYMENT_SUPPORT),
                ]
            )
            select.callback = self.payment_callback
            view = discord.ui.View(timeout=None)
            view.add_item(select)
            await self.thread.send(embed=embed, view=view)

    async def payment_callback(self, interaction: discord.Interaction):
        self.method = interaction.data["values"][0]
        await interaction.response.defer()

        if self.method == "crypto":
            embed = discord.Embed(title="Select Cryptocurrency", color=0x00A3FF)
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
            select.callback = self.crypto_callback
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
        amount_coin = round(price_usd / coin_price, 8)
        address = config["wallets"][self.crypto]
        qr_url = config["qr_urls"][self.crypto] or f"https://api.qrserver.com/v1/create-qr-code/?data={address}&size=200x200"

        embed = discord.Embed(title=f"{self.crypto.upper()} Payment Invoice (5/5)", color=0x00A3FF)
        embed.description = f"This transaction is approximately ${price_usd:.2f}, however to ensure we can validate your payment successfully, please copy and paste the value of {amount_coin} and send it to our address."
        embed.add_field(name="Payment Address", value=address, inline=False)
        embed.add_field(name="Amount {self.crypto.upper()}", value=amount_coin, inline=False)
        embed.add_field(name="Amount USD", value=f"${price_usd:.2f}", inline=False)
        embed.set_image(url=qr_url)
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit TX Hash", style=discord.ButtonStyle.blurple, custom_id="submit_tx"))
        await interaction.followup.send(embed=embed, view=view)

        # Checking embed
        check_embed = discord.Embed(title="Checking For Transactions", color=0x00A3FF)
        check_embed.description = f"{EMOJI_LOADING} We are actively monitoring transactions. Please proceed with your payment to complete the transaction process."
        await interaction.followup.send(embed=check_embed)

    async def send_payment_invoice(self, interaction: discord.Interaction):
        name = "Giftcard" if self.method == "gift" else self.method
        embed = discord.Embed(title=f"{name.upper()} Payment Invoice (5/5)", color=0x00A3FF)
        embed.description = f"Send ${self.price:.2f} via {name}. Reply with ID."
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
    flow = active_flows.get(interaction.user.id)

    if cid == "flow_yes_1" and flow:
        await interaction.response.defer()
        await flow.send_step(2)

    elif cid == "flow_no_1" and flow:
        await interaction.response.defer()
        await flow.thread.send("Cancelled.")
        await flow.thread.edit(archived=True, locked=True)
        active_flows.pop(interaction.user.id, None)

    elif cid == "flow_yes_3" and flow:
        await interaction.response.defer()
        await flow.send_step(4)

    elif cid == "flow_no_3" and flow:
        await interaction.response.defer()
        await flow.thread.send("Cancelled. Restarting...")
        await flow.thread.edit(archived=True, locked=True)
        active_flows.pop(interaction.user.id, None)
        thread = await interaction.channel.create_thread(
            name=f"automatic-order | Purchase-{interaction.user.name}-{random.randint(1000,9999)}",
            auto_archive_duration=1440
        )
        await thread.add_user(interaction.user)
        new_flow = PurchaseFlow(interaction.user.id, thread)
        active_flows[interaction.user.id] = new_flow
        await new_flow.send_step(1)

    elif cid == "submit_tx" and flow:
        modal = PaymentModal("Cryptocurrency", flow.robux, flow.price, flow.crypto)
        await interaction.response.send_modal(modal)

    elif cid == "submit_details" and flow:
        modal = PaymentModal(flow.method, flow.robux, flow.price)
        await interaction.response.send_modal(modal)

    elif cid == "close_ticket" and flow:
        await interaction.response.defer()
        await flow.thread.send("Ticket closed.")
        await flow.thread.edit(archived=True, locked=True)
        active_flows.pop(interaction.user.id, None)

# -------------------------------------------------
# MESSAGE: AMOUNT
# -------------------------------------------------
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.channel.name.startswith("automatic-order | Purchase-"):
        return

    if re.fullmatch(r"\d{5,}", message.content.strip()):
        try:
            amount = int(message.content.replace(",", ""))
            if amount < 10000:
                await message.reply("Minimum: 10,000")
                return
            flow = active_flows.get(message.author.id)
            if flow:
                flow.robux = amount
                await message.delete()
                await flow.send_step(3)
        except:
            pass

# -------------------------------------------------
# AUTOMATED ORDERS (EXACT + GOOD LOOKING)
# -------------------------------------------------
@tasks.loop(minutes=random.uniform(5, 15))
async def fake_order_loop():
    channel = bot.get_channel(ORDER_LOG_CHANNEL_ID)
    if not channel: return

    amount = random.choice([10000, 25000, 50000, 100000])
    price = get_price(amount)
    method = random.choice(["Crypto", "Card", "PayPal", "Giftcard"])

    embed1 = discord.Embed(title=f"{EMOJI_VERIFIED} New Order Placed", color=0x00A3FF)
    embed1.description = (
        f"{EMOJI_WARNING} **Disclaimer**\n"
        f"{EMOJI_VERIFIED} Minimum purchase amount is 10,000 {EMOJI_ROBUX}.\n"
        f"{EMOJI_VERIFIED} {EMOJI_ROBUX} are delivered via Gamepass.\n"
        f"{EMOJI_VERIFIED} Buying {EMOJI_ROBUX} through us is safe and secure. You will NOT get banned.\n"
        f"{EMOJI_VERIFIED} Enjoy instant {EMOJI_ROBUX} delivery with fully automated payments.\n\n"
        f"**Payment Method:** {method} • **Amount:** {amount:,} {EMOJI_ROBUX} • **Price:** ${price:.2f}"
    )
    await channel.send(embed=embed1)

    await asyncio.sleep(30)
    embed2 = discord.Embed(title=f"{EMOJI_LOADING} Processing...", color=0x00A3FF)
    embed2.description = f"Amount: {amount:,} {EMOJI_ROBUX}\nPrice: ${price:.2f}"
    await channel.send(embed=embed2)

    if random.random() < 0.7:
        await asyncio.sleep(10)
        await send_completed_order(amount, price, method)

async def send_completed_order(amount, price, method):
    channel = bot.get_channel(COMPLETED_CHANNEL_ID)
    if not channel: return
    embed = discord.Embed(title=f"{EMOJI_VERIFIED} New Completed Order", color=0x00A3FF)
    embed.add_field(name="Robux", value=f"{amount:,} (via Gamepass)", inline=False)
    embed.add_field(name="USD", value=f"${price:.2f}", inline=True)
    embed.add_field(name="Method", value=method, inline=True)
    embed.set_footer(text="Robux Town™")
    await channel.send(embed=embed)

# -------------------------------------------------
# COMMANDS
# -------------------------------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def address(ctx, coin: str, addr: str):
    coin = coin.lower()
    if coin in config["wallets"]:
        config["wallets"][coin] = addr
        save_config(config)
        await ctx.send(f"{EMOJI_VERIFIED} Updated {coin.upper()} address to {addr}")
    else:
        await ctx.send(f"Invalid coin: {coin}. Use btc/ltc/eth/sol")

@bot.command()
@commands.has_permissions(administrator=True)
async def qr(ctx, coin: str, url: str):
    coin = coin.lower()
    if coin in config["qr_urls"]:
        config["qr_urls"][coin] = url
        save_config(config)
        await ctx.send(f"{EMOJI_VERIFIED} Updated {coin.upper()} QR to {url}")
    else:
        await ctx.send(f"Invalid coin: {coin}. Use btc/ltc/eth/sol")

@bot.command()
@commands.has_permissions(administrator=True)
async def fake(ctx):
    await fake_order_loop()
    await ctx.send(f"{EMOJI_VERIFIED} Triggered fake order.")

@bot.command()
@commands.has_permissions(administrator=True)
async def deal(ctx, amount: int, old: float, new: float):
    deals_data["deals"].append({"amount": amount, "old": old, "new": new})
    save_deals(deals_data)
    await ctx.send(f"{EMOJI_VERIFIED} Added deal: {amount} Robux → ~~${old}~~ ${new}")

# -------------------------------------------------
# STARTUP
# -------------------------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.add_view(PersistentPurchaseButton())
    await send_info_embed()
    if not fake_order_loop.is_running():
        fake_order_loop.start()

# -------------------------------------------------
# RUN
# -------------------------------------------------
bot.run(BOT_TOKEN)
