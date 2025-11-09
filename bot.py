#!/usr/bin/env python3
# Robux Town™ – FIXED PERSISTENT VIEWS + NO REQUESTS + FULLY WORKING
import os
import asyncio
import json
import re
import random
from datetime import datetime
import discord
from discord.ext import commands, tasks

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

# Channels & Roles
INFO_CHANNEL_ID      = 1435516058105675818
ORDER_LOG_CHANNEL_ID = 1435516058105675819
COMPLETED_CHANNEL_ID = 1435516058286035015
STAFF_ROLE_ID        = 1435516057526734991
STAFF_DM_IDS         = [1422665161466187976, 1269145029943758899]

# EMOJIS
EMOJI_ROBUX          = "<:Robux:1435526693472178176>"
EMOJI_VERIFIED       = "<:Verified:1435526918891110551>"
EMOJI_LOADING        = "<:Loading:1435526855523434576>"
EMOJI_WARNING        = "<:warning:1435526954689495091>"
EMOJI_BITCOIN        = "<:Bitcoin:1435526466527039579>"
EMOJI_LITECOIN       = "<:Litecoin:1435526448684339321>"
EMOJI_ETHEREUM       = "<:Ethereum:1435526479126597745>"
EMOJI_SOLANA         = "<:Solana:1435526514115350549>"
EMOJI_CARD           = "<:Card:1435526554783318047>"
EMOJI_PAYPAL         = "<:PayPal:1435526543513354354>"
EMOJI_PAYMENT_SUPPORT= "<:PAYMENT_SUPPORT:1435526984011874434>"

# -------------------------------------------------
# CRYPTO FALLBACK PRICES (No external API)
# -------------------------------------------------
FALLBACK_PRICES = {
    "btc": 60000.0,
    "ltc": 80.0,
    "eth": 3000.0,
    "sol": 100.0
}

WALLETS = {
    "btc": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    "ltc": "Labc123xyz...",
    "eth": "0x1234567890abcdef1234567890abcdef12345678",
    "sol": "SoL123abc..."
}

# -------------------------------------------------
# TIERED RATES
# -------------------------------------------------
ROBUX_TIERS = [
    {"min": 10000, "max": 24999, "rate": 1.00},
    {"min": 25000, "max": 49999, "rate": 0.90},
    {"min": 50000, "max": 99999, "rate": 0.80},
    {"min": 100000, "max": 249999, "rate": 0.70},
    {"min": 250000, "max": 499999, "rate": 0.60},
    {"min": 500000, "max": 10000000, "rate": 0.50}
]

def get_price(amount: int) -> float:
    for tier in ROBUX_TIERS:
        if tier["min"] <= amount <= tier["max"]:
            return round((amount / 1000) * tier["rate"], 2)
    return round((amount / 1000) * 1.00, 2)

# -------------------------------------------------
# SEND TO STAFF DMs
# -------------------------------------------------
async def send_to_staff(order_data: dict):
    embed = discord.Embed(title="New Payment Submission", color=0x00A3FF)
    for k, v in order_data.items():
        embed.add_field(name=k.title(), value=str(v)[:1024], inline=False)
    for user_id in STAFF_DM_IDS:
        try:
            user = await bot.fetch_user(user_id)
            await user.send(embed=embed)
        except Exception as e:
            print(f"DM failed: {e}")

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
# PURCHASE FLOW (Per User)
# -------------------------------------------------
active_flows = {}

class PurchaseFlow(discord.ui.View):
    def __init__(self, user_id, thread):
        super().__init__(timeout=None)  # Persistent
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
            embed.description = "Type amount below (min 10,000)"
            await self.thread.send(embed=embed)

        elif step == 3:
            self.price = get_price(self.robux)
            embed = discord.Embed(title="Confirm Purchase (3/5)", color=color)
            embed.description = f"{self.robux:,} {EMOJI_ROBUX}\nPrice: ${self.price:.2f}"
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_3"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_3"))
            await self.thread.send(embed=embed, view=view)

        elif step == 4:
            embed = discord.Embed(title="Select Payment Method (4/5)", color=color)
            select = discord.ui.Select(
                placeholder="Choose method",
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
                placeholder="Choose coin",
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
            await self.send_non_crypto_invoice(interaction)

    async def crypto_callback(self, interaction: discord.Interaction):
        self.crypto = interaction.data["values"][0]
        await interaction.response.defer()
        price_usd = self.price
        coin_price = FALLBACK_PRICES[self.crypto]
        amount_coin = round(price_usd / coin_price, 8)
        address = WALLETS[self.crypto]
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={address}&size=200x200"

        embed = discord.Embed(title=f"Send {amount_coin} {self.crypto.upper()}", color=0x00A3FF)
        embed.description = f"**Amount:** `{amount_coin}`\n**Address:** `{address}`"
        embed.set_image(url=qr_url)
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit TX Hash", style=discord.ButtonStyle.blurple, custom_id="submit_tx"))
        await interaction.followup.send(embed=embed, view=view)

    async def send_non_crypto_invoice(self, interaction: discord.Interaction):
        method_map = {"card": "Card (G2A)", "paypal": "PayPal (Eneba)", "gift": "Giftcard"}
        name = method_map.get(self.method, self.method)
        embed = discord.Embed(title=f"{name} Payment", color=0x00A3FF)
        embed.description = f"Submit **${self.price:.2f}** via {name}"
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit Details", style=discord.ButtonStyle.blurple, custom_id="submit_details"))
        await interaction.followup.send(embed=embed, view=view)

# -------------------------------------------------
# PERSISTENT PURCHASE BUTTON (FIXED)
# -------------------------------------------------
class PersistentPurchaseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # REQUIRED

    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.blurple, custom_id="purchase_robux_btn")
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        thread = await interaction.channel.create_thread(
            name=f"Purchase-{interaction.user.name}-{random.randint(1000,9999)}",
            auto_archive_duration=1440
        )
        await thread.add_user(interaction.user)
        flow = PurchaseFlow(interaction.user.id, thread)
        active_flows[interaction.user.id] = flow
        await flow.send_step(1)
        await interaction.followup.send("Purchase started! Check your thread.", ephemeral=True)

# -------------------------------------------------
# INTERACTION HANDLER
# -------------------------------------------------
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data or "custom_id" not in interaction.data:
        return

    cid = interaction.data["custom_id"]
    flow = active_flows.get(interaction.user.id)

    # === PURCHASE BUTTON ===
    if cid == "purchase_robux_btn":
        await interaction.response.defer(ephemeral=True)
        thread = await interaction.channel.create_thread(
            name=f"Purchase-{interaction.user.name}-{random.randint(1000,9999)}",
            auto_archive_duration=1440
        )
        await thread.add_user(interaction.user)
        flow = PurchaseFlow(interaction.user.id, thread)
        active_flows[interaction.user.id] = flow
        await flow.send_step(1)
        await interaction.followup.send("Purchase started!", ephemeral=True)

    # === FLOW BUTTONS ===
    elif cid == "flow_yes_1" and flow:
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
        # Restart
        thread = await interaction.channel.create_thread(
            name=f"Purchase-{interaction.user.name}-{random.randint(1000,9999)}",
            auto_archive_duration=1440
        )
        await thread.add_user(interaction.user)
        new_flow = PurchaseFlow(interaction.user.id, thread)
        active_flows[interaction.user.id] = new_flow
        await new_flow.send_step(1)

    # === PAYMENT SUBMIT ===
    elif cid == "submit_tx" and flow:
        modal = PaymentModal("Cryptocurrency", flow.robux, flow.price, flow.crypto)
        await interaction.response.send_modal(modal)

    elif cid == "submit_details" and flow:
        modal = PaymentModal(flow.method, flow.robux, flow.price)
        await interaction.response.send_modal(modal)

# -------------------------------------------------
# MESSAGE: AMOUNT
# -------------------------------------------------
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.channel.name.startswith("Purchase-"):
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
# AUTOMATED ORDERS
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
    await channel.send(embed=discord.Embed(title=f"{EMOJI_LOADING} Processing...", color=0x00A3FF))
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
# INFO EMBED
# -------------------------------------------------
async def send_info_embed():
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if not channel: return
    embed = discord.Embed(color=0x00A3FF)
    embed.set_author(name="Robux Town™", icon_url="https://i.imgur.com/ROBUXTOWN.png")
    embed.description = (
        "Automated Purchase\nSecure, instant Robux delivery.\n\n"
        "Under 60 Seconds\nRobux delivered via Gamepass.\n\n"
        "Smart Payments\nFully automated.\n\n"
        "Bank-Level Security\nYou will NOT get banned.\n\n"
        "Payment Options\n"
        f"• {EMOJI_BITCOIN} Crypto (BTC/LTC/ETH/SOL)\n"
        f"• {EMOJI_CARD} Card (G2A)\n"
        f"• {EMOJI_PAYPAL} PayPal (Eneba)\n"
        f"• {EMOJI_PAYMENT_SUPPORT} Giftcards"
    )
    embed.set_image(url="https://i.imgur.com/ROBUXTOWNBANNER.png")
    view = PersistentPurchaseButton()  # Persistent!
    await channel.send(embed=embed, view=view)

# -------------------------------------------------
# STARTUP — REGISTER PERSISTENT VIEW
# -------------------------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # Register persistent purchase button
    bot.add_view(PersistentPurchaseButton())
    await send_info_embed()
    if not fake_order_loop.is_running():
        fake_order_loop.start()

# -------------------------------------------------
# RUN
# -------------------------------------------------
bot.run(BOT_TOKEN)
