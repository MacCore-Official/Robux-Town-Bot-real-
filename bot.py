#!/usr/bin/env python3
# Robux Town™ – FINALIZED UI + LIVE PRICES + ADMIN PANEL + PRICE LIST + INFO EMBEDS
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

# --- Rewarble Links (Defined at the top for easy access) ---
ENEBA_REWARBLE_LINK = "https://www.eneba.com/rewarble-rewarble-visa-10-usd-voucher-global"
G2A_REWARBLE_LINK = "https://www.g2a.com/rewarble-visa-gift-card-10-usd-by-rewarble-key-global-i10000502992001?suid=960beb55-4797-46d5-b14c-94995fd68f31"
# --------------------------------------------------------


# -------------------------------------------------
# CONFIG
# -------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    # NOTE: You must set your BOT_TOKEN environment variable to run this.
    # raise SystemExit("BOT_TOKEN not set!")
    # Using a placeholder to allow code inspection, replace with your actual token
    BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE" 

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Change command prefix to something less common for better admin separation
bot = commands.Bot(command_prefix="+", intents=intents, help_command=None)

# Channels (PLACEHOLDER IDs - REPLACE WITH YOUR REAL IDs)
INFO_CHANNEL_ID           = 1435516058105675818 # Main buy channel (Where persistent button is)
PRICE_CHANNEL_ID          = 1435516058105675817 # Channel for the price list embed
ORDER_LOG_CHANNEL_ID      = 1435516057845497981 # Channel for placing the order (pre-completion)
COMPLETED_CHANNEL_ID      = 1435516058286035015 # Channel for completed orders
LOG_CHANNEL_ID            = 1435516058286035020 # Staff payment submission log
STAFF_ROLE_ID             = 1435516057526734991 
STAFF_DM_IDS              = [1422665161466187976,1269145029943758899] 

PAYMENT_METHOD_CHANNEL_ID = 1435516058105675820 # <-- NEW: Channel for Payment Methods
TOS_CHANNEL_ID            = 1435516058286035016 # <-- NEW: Channel for Terms of Service 


# EMOJIS (PLACEHOLDER IDs - REPLACE WITH YOUR REAL IDs)
EMOJI_ROBUX          = "<:Robux:1435526693472178176>"
EMOJI_VERIFIED       = "<:Verified:1435526918891110551>"
EMOJI_LOADING        = "<a:Loading:1435526855523434576>" # FIXED: Animated emoji definition
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
# -------------------------------------------------
ROBUX_RATE_PER_1000 = 1.00

def get_price(robux_amount: int) -> float:
    """Calculates the total USD price based on the Robux amount."""
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
}

# -------------------------------------------------
# CRYPTO (LIVE PRICES + CUSTOM ADDRESS/QR)
# -------------------------------------------------
CRYPTO_IDS = {"btc": "bitcoin", "ltc": "litecoin", "eth": "ethereum", "sol": "solana"}

# Persistent storage for addresses / QR
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
            print(f"Could not DM staff user {user_id}")
            pass

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

# -------------------------------------------------
# MODAL SUBMISSION
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
            "Thread": interaction.channel.mention,
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        await interaction.response.send_message(f"{EMOJI_VERIFIED} **Payment Submitted!** Your details have been sent to staff for manual verification. Please wait.", ephemeral=True)
        await send_to_staff(order_data)

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
            try:
                await interaction.response.send_message("Closing the ticket...", ephemeral=False)
                # Archive and lock the thread
                await thread.edit(archived=True, locked=True)
                # Remove flow from active list
                active_flows.pop(interaction.user.id, None)
            except discord.Forbidden:
                await interaction.response.send_message(f"{EMOJI_WARNING} I do not have permission to close this ticket.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"{EMOJI_WARNING} An error occurred while closing the ticket: {e}", ephemeral=True)
        else:
            await interaction.response.send_message(f"{EMOJI_WARNING} Could not find the thread.", ephemeral=True)

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
            await send_disclaimer_embed(self.thread) 
            
            embed = discord.Embed(title="Would you like to start buying robux? (1/5)", color=color)
            embed.description = "Please click \"Yes\" to begin."
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_1"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_1"))
            await self.thread.send(embed=embed, view=view)

        elif step == 2:
            embed = discord.Embed(title="How much robux would you like to buy? (2/5)", color=color)
            embed.description = "Please specify the amount of Robux you would like to purchase:\n**The minimum order amount is 10,000 Robux**"
            await self.thread.send(embed=embed)

        elif step == 3:
            self.price = get_price(self.robux)
            rate_per_1k = get_price(1000)
            embed = discord.Embed(title="Would you like to purchase this amount of Robux? (3/5)", color=color)
            embed.description = (
                f"Are you sure you want to purchase **{self.robux:,} {EMOJI_ROBUX}**?\n"
                f"Current Rate: **${rate_per_1k:.2f} per 1,000 {EMOJI_ROBUX}**\n"
                f"Total Price in USD: **${self.price:.2f}**"
            )
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_3"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_3"))
            await self.thread.send(embed=embed, view=view)

        elif step == 4:
            embed = discord.Embed(title="Please select your preferred payment method (4/5)", color=color)
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
            # Assign callback to the select component
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
            # Assign callback to the crypto select component
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
        # Ensure we don't divide by zero
        amount_coin = round(price_usd / coin_price, 8) if coin_price else 0.0
        
        address = config["wallets"].get(self.crypto, "Address Not Set")
        qr_url = config["qr_urls"].get(self.crypto)
        if not qr_url or not qr_url.startswith("http"):
             qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={address}&size=200x200"

        # --- UPDATED: Calculate expiry time (20 minutes from now) ---
        expiry_time = datetime.now() + timedelta(minutes=20)
        expiry_timestamp = int(expiry_time.timestamp())
        
        embed = discord.Embed(title=f"{self.crypto.upper()} Payment Invoice (5/5)", color=0x00A3FF)
        embed.description = (
            f"This transaction is **${price_usd:.2f} USD**.\n"
            f"Please send the **exact** amount of `{amount_coin:.8f}` {self.crypto.upper()} to the address below.\n\n"
            f"**Invoice Expires:** <t:{expiry_timestamp}:R> (<t:{expiry_timestamp}:T>)" # Discord timestamp formatting
        )
        embed.add_field(name="Payment Address", value=f"```\n{address}\n```", inline=False)
        embed.add_field(name=f"Amount ({self.crypto.upper()})", value=f"`{amount_coin:.8f}`", inline=False)
        embed.add_field(name="Amount USD", value=f"**${price_usd:.2f}**", inline=False)
        embed.set_image(url=qr_url)
        
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit TX Hash", style=discord.ButtonStyle.blurple, custom_id="submit_tx"))
        await interaction.followup.send(embed=embed, view=view)

        # Checking embed is also updated with expiry time
        check_embed = discord.Embed(title="Checking For Transactions", color=0x00A3FF)
        check_embed.description = (
            f"{EMOJI_LOADING} We are actively monitoring transactions. Please proceed with your payment to complete the transaction process.\n"
            f"This invoice will expire <t:{expiry_timestamp}:R>."
        )
        await interaction.followup.send(embed=check_embed)

    async def send_payment_invoice(self, interaction: discord.Interaction):
        name = "Giftcard" if self.method == "gift" else self.method
        embed = discord.Embed(title=f"{name.upper()} Payment Invoice (5/5)", color=0x00A3FF)
        
        details = ""
        # --- UPDATED: Rewarble links added ---
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
# INTERACTION HANDLER (Buttons, Selects, Modals)
# -------------------------------------------------
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data or "custom_id" not in interaction.data:
        # Pass non-button/select/modal interactions to commands
        return await bot.process_commands(interaction.message)

    cid = interaction.data["custom_id"]
    user_id = interaction.user.id
    flow = active_flows.get(user_id)

    # --- PURCHASE FLOW BUTTONS ---
    if cid.startswith("flow_") and flow:
        if cid == "flow_yes_1":
            await interaction.response.defer()
            await flow.send_step(2)

        elif cid == "flow_no_1" or cid == "flow_no_3":
            await interaction.response.defer()
            await flow.thread.send("Purchase flow cancelled.")
            await flow.thread.edit(archived=True, locked=True)
            active_flows.pop(user_id, None)

        elif cid == "flow_yes_3":
            await interaction.response.defer()
            await flow.send_step(4)
    
    # --- SUBMISSION BUTTONS ---
    elif cid == "submit_tx" and flow:
        modal = PaymentModal("Cryptocurrency", flow.robux, flow.price, flow.crypto)
        await interaction.response.send_modal(modal)

    elif cid == "submit_details" and flow:
        modal = PaymentModal(flow.method, flow.robux, flow.price)
        await interaction.response.send_modal(modal)

    # Process commands if it was a message interaction that bypassed on_message
    await bot.process_commands(interaction.message)

# -------------------------------------------------
# MESSAGE: AMOUNT (Step 2 input)
# -------------------------------------------------
@bot.event
async def on_message(message: discord.Message):
    # Only process non-bot messages in an active purchase thread
    if message.author.bot or not message.channel.name.startswith("Purchase-"):
        return await bot.process_commands(message) # Still process commands

    if re.fullmatch(r"[\d,]+", message.content.strip()):
        try:
            amount = int(message.content.replace(",", "").strip())
            
            # Check if this message is from an active flow user
            flow = active_flows.get(message.author.id)
            if flow and flow.thread.id == message.channel.id:
                if amount < 10000:
                    await message.reply(f"{EMOJI_WARNING} The **minimum order** is 10,000 {EMOJI_ROBUX}. Please enter a higher amount.")
                    return
                # NOTE: Max limit is 800,000 based on price list
                if amount > 800000:
                    await message.reply(f"{EMOJI_MAX} The **maximum order** is 800,000 {EMOJI_ROBUX}. Please enter a lower amount.")
                    return
                
                # Proceed to step 3
                flow.robux = amount
                await message.delete()
                await flow.send_step(3)
            else:
                 await bot.process_commands(message) # If not a flow-related message, check for commands
        except ValueError:
             await bot.process_commands(message)
    else:
        await bot.process_commands(message)

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

# -------------------------------------------------
# MANUAL FAKE ORDER TRIGGER LOGIC (New/Re-implemented)
# -------------------------------------------------
async def trigger_fake_order_now():
    """Generates and sends a single fake order (start and completion) immediately."""
    order_channel = bot.get_channel(ORDER_LOG_CHANNEL_ID)
    if not order_channel: return

    amount = random.choice([10000, 25000, 50000, 100000])
    price = get_price(amount)
    method = random.choice(["Crypto", "Card", "PayPal", "Giftcard"])

    # 1. Start Order Embed (Sent to ORDER_LOG_CHANNEL_ID)
    embed1 = discord.Embed(title=f"🤖 New Public Order Placed", color=0x00A3FF)
    embed1.description = (
        f"A user has placed an order for **{amount:,} {EMOJI_ROBUX}** (Price: **${price:.2f}**) via **{method}**.\n"
        f"Processing will begin shortly. Place your order now!"
    )
    await order_channel.send(embed=embed1)
    
    # 2. Completion Embed (Sent to COMPLETED_CHANNEL_ID)
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
        await interaction.followup.send(f"{EMOJI_VERIFIED} Fake order triggered to the log channels.", ephemeral=True)
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
# -------------------------------------------------------------------------


# -------------------------------------------------
# ADMIN PANEL VIEW (The Interactive Menu)
# -------------------------------------------------
class AdminPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300) 

    @discord.ui.button(label="Set Crypto Address", style=discord.ButtonStyle.blurple, custom_id="admin_set_address", emoji=EMOJI_CRYPTO)
    async def set_address_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_set_address")

    @discord.ui.button(label="Set Crypto QR URL", style=discord.ButtonStyle.blurple, custom_id="admin_set_qr", emoji="🖼️")
    async def set_qr_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_set_qr")

    @discord.ui.button(label="Trigger Fake Order", style=discord.ButtonStyle.green, custom_id="admin_fake_order", emoji="🤖")
    async def fake_order_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_fake_order")

    @discord.ui.button(label="Update Price List", style=discord.ButtonStyle.green, custom_id="admin_set_prices", emoji=EMOJI_ROBUX)
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
# ADMIN PANEL MODALS (For Crypto Settings)
# -------------------------------------------------
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

# -------------------------------------------------
# COMPLETION LOGIC
# -------------------------------------------------
async def send_completed_order(amount, price, method):
    channel = bot.get_channel(COMPLETED_CHANNEL_ID)
    if not channel: return
    
    order_id = str(int(time.time() * 1000))[4:] + str(random.randint(100, 999)) 
    user_name = "Hidden" 
    rating_stars = "⭐⭐⭐⭐ (4/5)" 
    
    embed = discord.Embed(title=f"✅ New Completed Order", color=0x38B750) 
    
    embed.set_thumbnail(url="https://i.ibb.co/whbgBHWz/9c5fd434-f30f-4e24-8212-ea40fa098678.png") 

    embed.add_field(name=f"{EMOJI_USER} User", value=f"**{user_name}**", inline=True)
    embed.add_field(name="💳 Payment Method", value=f"**{method}**", inline=True)
    
    embed.add_field(name=f"{EMOJI_ROBUX} Robux Purchased", value=f"**{amount:,} Robux**", inline=False) 
    embed.add_field(name=f"{EMOJI_USD} USD Spent", value=f"**${price:.2f}**", inline=True)
    embed.add_field(name=f"{EMOJI_RATING} Rating", value=rating_stars, inline=True)
    
    embed.add_field(name=f"{EMOJI_ORDER_ID} Order ID", value=f"`{order_id}`", inline=False)
    
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
    
    try:
        if not force_new:
            messages = [m async for m in channel.history(limit=5)]
            for msg in messages:
                if msg.author == bot.user and msg.embeds and "Robux Town | Information:" in msg.embeds[0].title:
                    print("Existing Price embed found and preserved.")
                    return
    except Exception as e:
        print(f"Error checking for existing price embed: {e}")

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

    await channel.send(embed=embed)
    print("Price List embed sent.")

# -------------------------------------------------
# PERSISTENT PURCHASE BUTTON
# -------------------------------------------------
class PersistentPurchaseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # REQUIRED

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

# -------------------------------------------------
# INFO EMBED 
# -------------------------------------------------
async def send_info_embed(force_new: bool = False):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if not channel:
        print("Info channel not found! Cannot send info embed.")
        return

    try:
        messages = [m async for m in channel.history(limit=5)]
        for msg in messages:
            if msg.author == bot.user and msg.components and not force_new:
                print("Existing Info embed found and preserved.")
                return
    except Exception as e:
        print(f"Error checking for existing info embed: {e}")

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
    print("Info embed sent (BLUE BORDER)")

# -------------------------------------------------
# TERMS OF SERVICE EMBED (NEW)
# -------------------------------------------------
async def send_tos_embed(force_new: bool = False):
    channel = bot.get_channel(TOS_CHANNEL_ID)
    if not channel:
        print("ToS channel not found!")
        return
    
    if not force_new:
        try:
            if [m async for m in channel.history(limit=1)]: return
        except: pass

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

    if not force_new:
        try:
            if [m async for m in channel.history(limit=1)]: return
        except: pass
    
    embed = discord.Embed(
        title="💳 Accepted Payment Methods",
        description="We offer fully automated payment processing for instant Robux delivery.",
        color=0x00A3FF
    )
    
    embed.add_field(
        name=f"1. {EMOJI_CRYPTO} Cryptocurrency",
        value="**Instant Confirmation:** Bitcoin (BTC), Litecoin (LTC), Ethereum (ETH), Solana (SOL).",
        inline=False
    )
    
    embed.add_field(
        name=f"2. {EMOJI_CARD} Card (via G2A Rewarble)",
        value=f"Purchase a **Rewarble Card on G2A** and submit the code. [G2A Link]({G2A_REWARBLE_LINK})",
        inline=False
    )
    
    embed.add_field(
        name=f"3. {EMOJI_PAYPAL} PayPal (via Eneba Rewarble)",
        value=f"Purchase a **Rewarble Card on Eneba** using PayPal/Card and submit the code. [Eneba Link]({ENEBA_REWARBLE_LINK})",
        inline=False
    )
    
    embed.add_field(
        name=f"4. {EMOJI_PAYMENT_SUPPORT} Giftcards",
        value="We accept various gift cards on request. Please start a purchase flow to see current accepted gift cards.",
        inline=False
    )

    await channel.send(embed=embed)
    print("Payment Methods embed sent.")


# -------------------------------------------------
# STARTUP
# -------------------------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    # Add persistent view back in case of bot restart
    bot.add_view(PersistentPurchaseButton())
    
    # Ensure the info embeds are present and up-to-date
    await send_info_embed()
    await send_price_embed() 
    await send_payment_methods_embed() # <-- NEW: Send Payment Methods
    await send_tos_embed()             # <-- NEW: Send ToS
    

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
