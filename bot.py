#!/usr/bin/env python3
# Robux Town™ – EXACT UI + MODALS FOR SUBMISSION + DM TO STAFF + PRO AUTOMATED ORDERS
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
DEALS_CHANNEL_ID     = 1435516058105675817
STAFF_ROLE_ID        = 1435516057526734991
ORDER_LOG_CHANNEL_ID = 1435516058105675819
COMPLETED_CHANNEL_ID = 1435516058286035015
STAFF_DM_IDS         = [1422665161466187976, 1269145029943758899]  # Your DM recipients

# YOUR CUSTOM EMOJIS
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
# PERSISTENT STORAGE
# -------------------------------------------------
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

# -------------------------------------------------
# SEND TO STAFF DMs
# -------------------------------------------------
async def send_to_staff(order_data):
    for dm_id in STAFF_DM_IDS:
        try:
            user = await bot.fetch_user(dm_id)
            embed = discord.Embed(title="New Payment Submission", description=str(order_data), color=0x00A3FF)
            await user.send(embed=embed)
        except:
            pass
    staff_mention = f"<@&{STAFF_ROLE_ID}>"
    # Also ping in thread/channel if needed
    print(f"Sent to staff DMs: {order_data}")

# -------------------------------------------------
# MODALS FOR SUBMISSION (Exact Flow)
# -------------------------------------------------
class PaymentModal(discord.ui.Modal, title="Submit Payment Details"):
    details = discord.ui.TextInput(label="Enter Payment ID / Code / TX Hash", placeholder="e.g., TX123456 or CardCode789", style=discord.TextStyle.paragraph, max_length=500)

    def __init__(self, method, amount, price):
        super().__init__()
        self.method = method
        self.amount = amount
        self.price = price

    async def on_submit(self, interaction: discord.Interaction):
        details = self.details.value
        order_data = {
            "user": interaction.user.name,
            "amount": self.amount,
            "price": self.price,
            "method": self.method,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        await send_to_staff(order_data)
        await interaction.response.send_message(f"{EMOJI_VERIFIED} Submitted! Staff will verify shortly.", ephemeral=True)
        
        # Trigger completed order after 10s
        await asyncio.sleep(10)
        await send_completed_order(self.amount, self.price, self.method)
        await interaction.followup.send(f"{EMOJI_VERIFIED} Order completed! {EMOJI_ROBUX} delivered via Gamepass.", ephemeral=True)

# -------------------------------------------------
# AUTOMATED ORDERS (3-Step Exact Match)
# -------------------------------------------------
@tasks.loop(minutes=random.uniform(5, 15))
async def fake_order_loop():
    channel = bot.get_channel(ORDER_LOG_CHANNEL_ID)
    if not channel:
        return

    name = random.choice(["Alex", "Luna", "Kai", "Zoe", "Max"])
    amount = random.choice([10000, 25000, 50000, 100000, 180000])
    method = random.choice([
        "Cryptocurrency (BTC/LTC/ETH/SOL)",
        "Card (Powered by G2A)",
        "PayPal (Powered by Eneba)",
        "Giftcards (Steam/Binance/PaySafe)"
    ])
    price = get_price(amount)

    # Step 1: Order Placed (Exact disclaimer + rates)
    embed1 = discord.Embed(title=f"{EMOJI_VERIFIED} New Order Placed", color=0x00A3FF)
    embed1.description = (
        f"{EMOJI_WARNING} **Disclaimer**\n"
        f"{EMOJI_VERIFIED} Minimum purchase amount is 10,000 {EMOJI_ROBUX}.\n"
        f"{EMOJI_VERIFIED} {EMOJI_ROBUX} are delivered via Gamepass.\n"
        f"{EMOJI_VERIFIED} Buying {EMOJI_ROBUX} through us is safe and secure. You will NOT get banned.\n"
        f"{EMOJI_VERIFIED} Enjoy instant {EMOJI_ROBUX} delivery with fully automated payments.\n\n"
        f"**Payment Method:** {method}\n**Amount:** {amount:,} {EMOJI_ROBUX}\n**Price:** ${price:.2f}"
    )
    embed1.add_field(name="Robux Rates", value=(
        f"• 10K-24K → ${1.00}/1K\n"
        f"• 25K-49K → ${0.90}/1K\n"
        f"• 50K-99K → ${0.80}/1K\n"
        f"• 100K-249K → ${0.70}/1K\n"
        f"• 250K-499K → ${0.60}/1K\n"
        f"• 500K-10M → ${0.50}/1K"
    ), inline=False)
    await channel.send(embed=embed1)

    # Step 2: Processing (Loading spinner)
    await asyncio.sleep(30)
    embed2 = discord.Embed(title=f"{EMOJI_LOADING} Processing Order...", color=0x00A3FF)
    embed2.description = f"User: {name}\nAmount: {amount:,} {EMOJI_ROBUX}\nPrice: ${price:.2f}\nMethod: {method}"
    await channel.send(embed=embed2)

    # Step 3: Completed (70% chance)
    if random.random() < 0.7:
        await asyncio.sleep(10)
        await send_completed_order(amount, price, method)

# -------------------------------------------------
# COMPLETED ORDER
# -------------------------------------------------
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
    embed.add_field(name="Rating", value="⭐⭐⭐⭐⭐ (5/5)", inline=True)
    embed.add_field(name="Order ID", value=order_id, inline=False)
    embed.set_footer(text="Powered by Robux Town™ • discord.gg/robuxworld")
    await channel.send(embed=embed)

# -------------------------------------------------
# PURCHASE BUTTON (Exact)
# -------------------------------------------------
class PurchaseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.blurple, emoji="🔘", custom_id="purchase_robux_btn")
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

# -------------------------------------------------
# PURCHASE FLOW (Exact Steps + Sub-Selection + Modals)
# -------------------------------------------------
class PurchaseFlow(discord.ui.View):
    def __init__(self, user_id, thread):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.thread = thread
        self.robux = 0
        self.price = 0.0
        self.primary_method = ""
        self.crypto_method = ""

    async def send_step(self, step):
        color = 0x00A3FF  # Blue
        if step == 1:
            embed = discord.Embed(title="Would you like to start buying robux? (1/5)", color=color)
            embed.description = "Please click \"Yes\" if you would like to start purchasing your Robux."
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
            embed = discord.Embed(title="Confirm Purchase (3/5)", color=color)
            embed.description = f"Are you sure you want to purchase {self.robux:,} {EMOJI_ROBUX}:\nPrice in USD: ${self.price:.2f}"
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_3"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_3"))
            await self.thread.send(embed=embed, view=view)

        elif step == 4:
            embed = discord.Embed(title="Select Payment Method (4/5)", color=color)
            embed.description = "Please select your preferred payment method from the options provided below."
            select = discord.ui.Select(
                placeholder="Select payment method",
                custom_id="primary_payment_select",
                options=[
                    discord.SelectOption(label="Cryptocurrency (BTC/LTC/ETH/SOL)", value="crypto", emoji=EMOJI_BITCOIN),
                    discord.SelectOption(label="Card (Powered by G2A)", value="card", emoji=EMOJI_CARD),
                    discord.SelectOption(label="PayPal (Powered by Eneba)", value="paypal", emoji=EMOJI_PAYPAL),
                    discord.SelectOption(label="Giftcards (Steam/Binance/PaySafe)", value="gift", emoji=EMOJI_PAYMENT_SUPPORT),
                ]
            )
            select.callback = self.primary_callback
            view = discord.ui.View(timeout=None)
            view.add_item(select)
            await self.thread.send(embed=embed, view=view)

        elif step == 5:
            method_name = self.primary_method.replace(" (Powered by G2A)", "").replace(" (Powered by Eneba)", "")
            embed = discord.Embed(title=f"{method_name} Payment Invoice (5/5)", color=color)
            if self.primary_method == "crypto":
                # Crypto sub-selection
                embed.description = "Select your cryptocurrency:"
                select = discord.ui.Select(
                    placeholder="Select crypto",
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
                await self.thread.send(embed=embed, view=view)
            else:
                # Other methods: Open modal directly
                embed.description = f"Please submit your payment details for ${self.price:.2f} via {self.primary_method}.\nOur team will review and confirm the details shortly after submission."
                view = discord.ui.View(timeout=None)
                view.add_item(discord.ui.Button(label="Submit Details", style=discord.ButtonStyle.blurple, custom_id="submit_modal_btn"))
                await self.thread.send(embed=embed, view=view)

    async def primary_callback(self, interaction: discord.Interaction):
        self.primary_method = interaction.data["values"][0]
        await interaction.response.defer()
        await self.send_step(5)

    async def crypto_callback(self, interaction: discord.Interaction):
        self.crypto_method = interaction.data["values"][0]
        await interaction.response.defer()
        # Send QR + address
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data=bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh&size=200x200"  # Mock QR (replace with real)
        address = f"bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh (Mock {self.crypto_method.upper()})"  # Mock address
        embed = discord.Embed(title=f"{self.crypto_method.upper()} Payment (5/5)", description=f"Send **${self.price:.2f}** to:\n**Address:** `{address}`\n[QR Code]", color=0x00A3FF)
        embed.set_image(url=qr_url)
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit TX Hash", style=discord.ButtonStyle.blurple, custom_id="crypto_submit_btn"))
        await interaction.followup.send(embed=embed, view=view)

    # Modal button callbacks
    @discord.ui.button(label="Submit Details", style=discord.ButtonStyle.blurple, custom_id="submit_modal_btn")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = PaymentModal(self.primary_method, self.robux, self.price)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Submit TX Hash", style=discord.ButtonStyle.blurple, custom_id="crypto_submit_btn")
    async def open_crypto_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = PaymentModal(f"Cryptocurrency ({self.crypto_method.upper()})", self.robux, self.price)
        await interaction.response.send_modal(modal)

# -------------------------------------------------
# INTERACTION HANDLER
# -------------------------------------------------
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data or "custom_id" not in interaction.data:
        return

    cid = interaction.data["custom_id"]

    if cid == "purchase_robux_btn":
        pass  # Handled in button

    elif cid == "flow_yes_1":
        flow = PurchaseFlow(interaction.user.id, interaction.channel)
        await interaction.response.defer()
        await flow.send_step(2)

    elif cid == "flow_yes_3":
        flow = PurchaseFlow(interaction.user.id, interaction.channel)
        await interaction.response.defer()
        flow.robux = 10000  # Mock from message; replace with real
        await flow.send_step(4)

    elif cid in ["flow_no_1", "flow_no_3"]:
        await interaction.response.send_message("Purchase cancelled.", ephemeral=True)

    # Primary/crypto selects handled in flow

# -------------------------------------------------
# MESSAGE HANDLER (For Amount Input)
# -------------------------------------------------
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.channel.name.startswith("Purchase-"):
        return await bot.process_commands(message)

    content = message.content.strip()
    if re.fullmatch(r"\d{5,}", content):
        try:
            amount = int(content.replace(",", ""))
            if amount < 10000:
                await message.reply("Minimum is 10,000 Robux.")
                return
            flow = PurchaseFlow(message.author.id, message.channel)
            flow.robux = amount
            await message.delete()
            await flow.send_step(3)
        except:
            pass

    await bot.process_commands(message)

# -------------------------------------------------
# +EMOJIS COMMAND
# -------------------------------------------------
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

# -------------------------------------------------
# INFO EMBED (Exact Match to Screenshot)
# -------------------------------------------------
async def send_info_embed():
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if not channel:
        print("Info channel not found!")
        return

    embed = discord.Embed(color=0x00A3FF)
    embed.set_author(name="Robux Town™", icon_url="https://i.imgur.com/ROBUXTOWN.png")
    embed.description = (
        "🔒 **Automated Purchase**\n"
        "Secure, instant Robux delivery.\n\n"
        "⚡ **Under 60 Seconds**\n"
        "Robux delivered via Gamepass.\n\n"
        "💳 **Smart Payments**\n"
        "Fully automated.\n\n"
        "🛡️ **Bank-Level Security**\n"
        "You will NOT get banned.\n\n"
        "🌐 **Payment Options**\n"
        f"• {EMOJI_BITCOIN} Crypto (BTC/LTC/ETH/SOL)\n"
        f"• {EMOJI_CARD} Card (G2A)\n"
        f"• {EMOJI_PAYPAL} PayPal (Eneba)\n"
        f"• {EMOJI_PAYMENT_SUPPORT} Giftcards (Steam/Binance/PaySafe)"
    )
    embed.set_image(url="https://i.imgur.com/ROBUXTOWNBANNER.png")

    view = PurchaseButton()
    await channel.send(embed=embed, view=view)
    print("Exact info embed sent (BLUE)")

# -------------------------------------------------
# STARTUP
# -------------------------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.add_view(PurchaseButton())
    bot.add_view(PurchaseFlow(0, None))
    await send_info_embed()
    if not fake_order_loop.is_running():
        fake_order_loop.start()
        print("Automated orders started!")

# -------------------------------------------------
# RUN
# -------------------------------------------------
bot.run(BOT_TOKEN)
