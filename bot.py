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

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="+", intents=intents, help_command=None)

# -------------------------------------------------
# CONFIG & CHANNELS
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
EMOJI_MAX = "⚠️"  # Define missing emoji

# -------------------------------------------------
# PRICING
# -------------------------------------------------
ROBUX_RATE_PER_1000 = 1.00

def get_price(robux_amount: int) -> float:
    """Calculates the standard total USD price based on the Robux amount."""
    return (robux_amount / 1000) * ROBUX_RATE_PER_1000

# -------------------------------------------------
# CRYPTO & CONFIG
# -------------------------------------------------
CRYPTO_IDS = {"btc": "bitcoin", "ltc": "litecoin", "eth": "ethereum", "sol": "solana"}
CONFIG_FILE = "config.json"

default_config = {
    "wallets": {
        "btc": "bc1qexampleaddress123456789",
        "ltc": "Lexampleaddress123456789",
        "eth": "0xExampleAddress123456789",
        "sol": "ExampleSolAddress123456789"
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
# HELPER: SEND TO STAFF
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
        self.price = discord.ui.TextInput(label="Discounted Price USD", placeholder="e.g., 60.00")
        self.add_item(self.code)
        self.add_item(self.amount)
        self.add_item(self.price)

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
            f"{EMOJI_VERIFIED} Discount **{code}** set: {amount:,} R$ → **${price:.2f}**", ephemeral=True
        )

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
            placeholder="Paste your transaction hash or gift card code here",
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.details)

    async def on_submit(self, interaction: discord.Interaction):
        method_name = self.crypto.upper() if self.crypto else self.method.capitalize()
        order_data = {
            "User": interaction.user.mention,
            "Robux": f"{self.amount:,} {EMOJI_ROBUX}",
            "USD": f"${self.price:.2f}",
            "Method": method_name,
            "Details": self.details.value,
            "Discount": self.discount_code or "None",
            "Thread": interaction.channel.mention,
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        await interaction.response.send_message(f"{EMOJI_VERIFIED} **Payment Submitted!** Awaiting verification.", ephemeral=True)
        await send_to_staff(order_data)

class AddressModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Set Crypto Address", timeout=600)
        self.coin = discord.ui.TextInput(label="Coin (btc, ltc, eth, sol)", placeholder="e.g., btc", max_length=3)
        self.address = discord.ui.TextInput(label="New Address", placeholder="Paste wallet address", style=discord.TextStyle.paragraph)
        self.add_item(self.coin)
        self.add_item(self.address)

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
        super().__init__(title="Set Crypto QR URL", timeout=600)
        self.coin = discord.ui.TextInput(label="Coin (btc, ltc, eth, sol)", placeholder="e.g., btc", max_length=3)
        self.url = discord.ui.TextInput(label="QR Image URL", placeholder="Direct link to image", style=discord.TextStyle.paragraph)
        self.add_item(self.coin)
        self.add_item(self.url)

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
# CLOSE TICKET VIEW
# -------------------------------------------------
class CloseTicketView(discord.ui.View):
    def __init__(self, thread_id):
        super().__init__(timeout=None)
        self.thread_id = thread_id

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji="🔒")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        thread = bot.get_channel(self.thread_id)
        if thread and isinstance(thread, discord.Thread):
            try:
                await interaction.response.send_message("Closing ticket...", ephemeral=False)
                await thread.edit(archived=True, locked=True)
                active_flows.pop(interaction.user.id, None)
            except discord.Forbidden:
                await interaction.response.send_message(f"{EMOJI_WARNING} Missing permissions to close.", ephemeral=True)

async def send_disclaimer_embed(thread: discord.Thread):
    embed = discord.Embed(title="Disclaimer", color=0xFF0000)
    embed.description = (
        "By proceeding, you agree to our [Terms of Service](https://discord.com/channels/@me/{TOS_CHANNEL_ID}) "
        "and understand that **all sales are final**. No refunds."
    )
    view = CloseTicketView(thread.id)
    await thread.send(embed=embed, view=view)

# -------------------------------------------------
# DISCOUNT HELPER
# -------------------------------------------------
async def apply_discount(flow, code):
    flow.discount_code = None
    flow.price = get_price(flow.robux)  # Set base price
    if not code or code.upper() == "SKIP":
        return
    deal = config["deals"].get(code.upper())
    if deal and flow.robux >= deal.get("min_robux_required", 0):
        flow.price = deal["price"]
        flow.discount_code = code.upper()
        await flow.thread.send(f"{EMOJI_VERIFIED} Coupon **{code.upper()}** applied! New price: **${flow.price:.2f}**", delete_after=10)
    else:
        await flow.thread.send(f"{EMOJI_WARNING} Invalid or ineligible coupon. Using standard pricing.", delete_after=10)

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
            embed = discord.Embed(title="Start Buying Robux? (1/6)", color=color)
            embed.description = "Click **Yes** to begin."
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_1"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_1"))
            await self.thread.send(embed=embed, view=view)

        elif step == 2:
            embed = discord.Embed(title="How much Robux? (2/6)", color=color)
            embed.description = "Enter amount (min 10,000, max 800,000):"
            await self.thread.send(embed=embed)

        elif step == 3:
            embed = discord.Embed(title="Discount Code? (3/6)", color=color)
            embed.description = "Enter code or type **SKIP**."
            await self.thread.send(embed=embed)

        elif step == 4:
            rate_per_1k = get_price(1000)
            discount_info = f"**COUPON:** {self.discount_code}\n" if self.discount_code else ""
            embed = discord.Embed(title="Confirm Purchase (4/6)", color=color)
            embed.description = (
                f"**{self.robux:,} {EMOJI_ROBUX}**\n"
                f"Rate: **${rate_per_1k:.2f}/1K**\n"
                f"{discount_info}"
                f"**Total: ${self.price:.2f}**"
            )
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_4"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_4"))
            await self.thread.send(embed=embed, view=view)

        elif step == 5:
            embed = discord.Embed(title="Payment Method (5/6)", color=color)
            embed.description = "Select payment method:"
            select = discord.ui.Select(placeholder="Choose method", custom_id="payment_select")
            select.options = [
                discord.SelectOption(label="Crypto", value="crypto", emoji=EMOJI_BITCOIN),
                discord.SelectOption(label="PayPal", value="paypal", emoji=EMOJI_PAYMENT_SUPPORT),
                discord.SelectOption(label="Card", value="card", emoji=EMOJI_PAYMENT_SUPPORT),
                discord.SelectOption(label="Giftcards", value="gift", emoji=EMOJI_PAYMENT_SUPPORT),
            ]
            async def callback(interaction: discord.Interaction):
                await self.payment_callback(interaction)
            select.callback = callback
            view = discord.ui.View(timeout=None)
            view.add_item(select)
            await self.thread.send(embed=embed, view=view)

    async def payment_callback(self, interaction: discord.Interaction):
        self.method = interaction.data["values"][0]
        await interaction.response.defer()
        if self.method == "crypto":
            embed = discord.Embed(title="Select Crypto (6/6)", color=0x00A3FF)
            select = discord.ui.Select(placeholder="Choose coin", custom_id="crypto_select")
            select.options = [
                discord.SelectOption(label="BTC", value="btc", emoji=EMOJI_BITCOIN),
                discord.SelectOption(label="LTC", value="ltc", emoji=EMOJI_LITECOIN),
                discord.SelectOption(label="ETH", value="eth", emoji=EMOJI_ETHEREUM),
                discord.SelectOption(label="SOL", value="sol", emoji=EMOJI_SOLANA),
            ]
            async def crypto_callback(interaction: discord.Interaction):
                await self.crypto_callback(interaction)
            select.callback = crypto_callback
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
        coin_price = 50000.0  # Replace with real API later
        amount_coin = round(price_usd / coin_price, 8) if coin_price else 0.0
        address = config["wallets"].get(self.crypto, "Not Set")
        qr_url = config["qr_urls"].get(self.crypto)
        if not qr_url or not qr_url.startswith("http"):
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={address}&size=200x200"
        expiry_time = datetime.now() + timedelta(minutes=20)
        expiry_timestamp = int(expiry_time.timestamp())
        embed = discord.Embed(title=f"{self.crypto.upper()} Invoice (6/6)", color=0x00A3FF)
        embed.description = (
            f"Send **exactly** `{amount_coin:.8f}` {self.crypto.upper()}\n"
            f"**Expires:** <t:{expiry_timestamp}:R>"
        )
        embed.add_field(name="Address", value=f"```{address}```", inline=False)
        embed.add_field(name="Amount", value=f"`{amount_coin:.8f}`", inline=False)
        embed.set_image(url=qr_url)
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit TX Hash", style=discord.ButtonStyle.blurple, custom_id="submit_tx"))
        await interaction.followup.send(embed=embed, view=view)

    async def send_payment_invoice(self, interaction: discord.Interaction):
        name = "Giftcard" if self.method == "gift" else self.method.capitalize()
        embed = discord.Embed(title=f"{name} Invoice (6/6)", color=0x00A3FF)
        details = ""
        if self.method == "card":
            details = "**Buy Rewarble Card from G2A** and submit code.\nhttps://g2a.com/..."
        elif self.method == "paypal":
            details = "Send to: `paypal@example.com`"
        embed.description = f"Submit your {name} details below.\n\n{details}"
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
        await flow.thread.send("Purchase cancelled.")
        await flow.thread.edit(archived=True, locked=True)
        active_flows.pop(user_id, None)
    elif cid == "flow_yes_4" and flow:
        await interaction.response.defer()
        await flow.send_step(5)
    elif cid == "flow_no_4" and flow:
        await interaction.response.defer()
        await flow.thread.send("Restarting...")
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
# MESSAGE HANDLER (Robux + Discount)
# -------------------------------------------------
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.channel.name.startswith("Purchase-"):
        return await bot.process_commands(message)

    flow = active_flows.get(message.author.id)
    if not flow or flow.thread.id != message.channel.id:
        return await bot.process_commands(message)

    content = message.content.strip()

    # Step 2: Robux Amount
    if flow.robux == 0 and re.fullmatch(r"[\d,]+", content):
        try:
            amount = int(content.replace(",", ""))
            if amount < 10000:
                await message.reply(f"{EMOJI_WARNING} Minimum: 10,000 R$.", delete_after=5)
                return
            if amount > 800000:
                await message.reply(f"{EMOJI_MAX} Maximum: 800,000 R$.", delete_after=5)
                return
            flow.robux = amount
            await message.delete()
            await flow.send_step(3)
        except ValueError:
            pass

    # Step 3: Discount Code
    elif flow.robux > 0 and flow.price == 0.0:
        await message.delete()
        await apply_discount(flow, content)
        await flow.send_step(4)

    await bot.process_commands(message)

# -------------------------------------------------
# COMPLETED ORDER
# -------------------------------------------------
async def send_completed_order(amount, price, method):
    channel = bot.get_channel(COMPLETED_CHANNEL_ID)
    if not channel:
        return
    embed = discord.Embed(title="New Completed Order", color=0x38B750)
    embed.set_thumbnail(url="https://i.ibb.co/whbgBHWz/9c5fd434-f30f-4e24-8212-ea40fa098678.png")
    embed.add_field(name="Amount", value=f"{amount:,} {EMOJI_ROBUX}", inline=True)
    embed.add_field(name="Price", value=f"${price:.2f}", inline=True)
    embed.add_field(name="Method", value=method, inline=True)
    await channel.send(embed=embed)

# -------------------------------------------------
# FAKE ORDER LOOP
# -------------------------------------------------
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
    @discord.ui.button(label="Set Address", style=discord.ButtonStyle.gray, custom_id="admin_set_address")
    async def set_address(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(AddressModal())
    @discord.ui.button(label="Set QR", style=discord.ButtonStyle.gray, custom_id="admin_set_qr")
    async def set_qr(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(QRModal())
    @discord.ui.button(label="Set Discount", style=discord.ButtonStyle.blurple, custom_id="admin_set_discount", emoji="Tag")
    async def set_discount(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(DiscountModal())
    @discord.ui.button(label="Fake Order", style=discord.ButtonStyle.green, custom_id="admin_fake_order", emoji="Robot")
    async def fake_order(self, interaction: discord.Interaction, button):
        await interaction.response.defer(ephemeral=True)
        await send_completed_order(50000, 50.0, "Crypto")
        await interaction.followup.send(f"{EMOJI_VERIFIED} Fake order sent.", ephemeral=True)

@bot.command()
@commands.has_role(STAFF_ROLE_ID)
async def admin(ctx):
    embed = discord.Embed(title="Robux Town™ Admin Panel", color=0x00A3FF)
    await ctx.send(embed=embed, view=AdminPanel())

# -------------------------------------------------
# STARTUP
# -------------------------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    if not automated_fake_completion_loop.is_running():
        automated_fake_completion_loop.start()

# -------------------------------------------------
# PERSISTENT BUY BUTTON
# -------------------------------------------------
class BuyView(discord.ui.View):
    @discord.ui.button(label="Buy Robux", style=discord.ButtonStyle.green, emoji=EMOJI_ROBUX)
    async def buy(self, interaction: discord.Interaction, button):
        info_channel = bot.get_channel(INFO_CHANNEL_ID)
        thread = await info_channel.create_thread(
            name=f"Purchase-{interaction.user.name}-{random.randint(1000,9999)}",
            auto_archive_duration=1440,
            type=discord.ChannelType.private_thread
        )
        await thread.add_user(interaction.user)
        flow = PurchaseFlow(interaction.user.id, thread)
        active_flows[interaction.user.id] = flow
        await interaction.response.send_message(f"Purchase started in {thread.mention}", ephemeral=True)
        await flow.send_step(1)

@bot.command()
async def setup(ctx):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    embed = discord.Embed(title="Robux Town™", description="Click below to buy Robux!", color=0x00A3FF)
    await channel.send(embed=embed, view=BuyView())

# -------------------------------------------------
# RUN BOT
# -------------------------------------------------
bot.run("YOUR_BOT_TOKEN_HERE")
