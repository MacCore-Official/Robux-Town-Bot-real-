#!/usr/bin/env python3
# Robux Town™ – FINALIZED UI + DISCOUNTS + PREMIUM GIVEAWAY (STABLE VERSION)
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

# --- Giveaway Branding Assets (Ensure these are here for global access) ---
EMOJI_GIVEAWAY_REACT = "<:giveawaygift:1437688517089165442>"
EMOJI_CROWN_WINNER   = "👑" 
GIVEAWAY_THUMBNAIL   = "https://i.ibb.co/v4rqV5Pj/9c5fd434-f30f-4e24-8212-ea40fa098678.png" 
GIVEAWAY_BANNER      = "https://i.ibb.co/FbRfdH7D/Screenshot-2025-11-10-at-6-58-42-PM.png"
# --------------------------------------------------------


# -------------------------------------------------
# CONFIG
# -------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE" 

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


# EMOJIS (PLACEHOLDER IDs - REPLACE WITH YOUR REAL IDs)
EMOJI_ROBUX          = "<:Robux:1435526693472178176>"
EMOJI_VERIFIED       = "<:Verified:1435526918891110551>"
EMOJI_LOADING        = "<a:Loading:1435526855523434576>" 
EMOJI_WARNING        = "<:warning:1435526954689495091>"
EMOJI_CROWN          = "👑" 

# -------------------------------------------------
# PRICE CALCULATION 
# -------------------------------------------------
ROBUX_RATE_PER_1000 = 1.00

def get_price(robux_amount: int) -> float:
    """Calculates the standard total USD price based on the Robux amount."""
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
# SEND TO STAFF DMs + LOG CHANNEL (Remains the same)
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
# ADMIN MODALS
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

        config["deals"][code] = {
            "robux": amount, 
            "price": price, 
            "min_robux_required": amount 
        }
        save_config(config)
        await interaction.response.send_message(
            f"{EMOJI_VERIFIED} Discount code **{code}** set: {amount:,} R$ for **${price:.2f} USD**.",
            ephemeral=True
        )

class GiveawayModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Start New Rigged Giveaway", timeout=600)
        
        self.channel_id = discord.ui.TextInput(
            label="Target Channel ID", 
            placeholder="e.g., 1437675911079002173 (Where the announcement goes)", 
            required=True
        )
        self.prize = discord.ui.TextInput(
            label="Prize Description", 
            placeholder=f"e.g., 50,000 {EMOJI_ROBUX} or Nitro", 
            max_length=100
        )
        self.winner_id = discord.ui.TextInput(
            label="Rigged Winner ID (User ID)", 
            placeholder="Enter the User ID or 0 for random winner", 
            required=True
        )
        self.duration = discord.ui.TextInput(
            label="Duration (in Minutes)", 
            placeholder="e.g., 60 (for 1 hour)", 
            required=True
        )
        
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

        await start_new_giveaway(
            target_id,
            self.prize.value,
            duration_minutes,
            winner_id
        )
        
        await interaction.followup.send(f"{EMOJI_GIVEAWAY_REACT} Giveaway for '{self.prize.value}' initiated in {target_channel.mention}.", ephemeral=True)


class DeleteDiscountView(discord.ui.Select):
    def __init__(self, discounts):
        options = [
            discord.SelectOption(
                label=f"{code} ({details['robux']:,} R$ for ${details['price']:.2f})",
                value=code
            ) for code, details in discounts.items()
        ]
        super().__init__(placeholder="Select code to DELETE permanently", options=options, min_values=1, max_values=1)
        
    async def callback(self, interaction: discord.Interaction):
        code_to_delete = self.values[0]
        
        if code_to_delete in config['deals']:
            del config['deals'][code_to_delete]
            save_config(config)
            await interaction.response.send_message(
                f"🗑️ Discount code **{code_to_delete}** has been successfully deleted.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(f"{EMOJI_WARNING} Code not found.", ephemeral=True)


class DiscountListModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Active Discounts", timeout=None)
        
        active_deals = config.get("deals", {})
        
        if not active_deals:
            self.add_item(discord.ui.TextInput(
                label="No Active Discounts Found.", 
                default="Please use 'Set Discount Code' first.",
                style=discord.TextStyle.paragraph, 
                required=False,
                disabled=True
            ))
            return

        self.add_item(discord.ui.TextInput(
            label=f"Listing {len(active_deals)} Active Discounts:",
            default="\n".join([f"  - {code}: {details['robux']:,} R$ for ${details['price']:.2f}" for code, details in active_deals.items()]),
            style=discord.TextStyle.paragraph,
            required=False,
            disabled=True
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

# -------------------------------------------------
# CLOSE TICKET VIEW
# -------------------------------------------------
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
            await self.thread.send(embed=embed, view=view)

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
# -------------------------------------------------
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data or "custom_id" not in interaction.data:
        return await bot.process_commands(interaction.message)

    cid = interaction.data["custom_id"]
    user_id = interaction.user.id
    flow = active_flows.get(user_id)

    # --- PURCHASE FLOW BUTTONS (Updated step IDs) ---
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
            active_flows[interaction.user.id] = new_flow
            await new_flow.send_step(1)
    
    # --- SUBMISSION BUTTONS ---
    elif cid == "submit_tx" and flow:
        modal = PaymentModal("Cryptocurrency", flow.robux, flow.price, flow.crypto, flow.discount_code)
        await interaction.response.send_modal(modal)

    elif cid == "submit_details" and flow:
        modal = PaymentModal(flow.method, flow.robux, flow.price, discount_code=flow.discount_code)
        await interaction.response.send_modal(modal)

    await bot.process_commands(interaction.message)

# -------------------------------------------------
# MESSAGE: AMOUNT (Step 2 input) & DISCOUNT CODE (Step 3 input) (Remains the same)
# -------------------------------------------------
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.channel.name.startswith("Purchase-"):
        return await bot.process_commands(message) 

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
                # Move to Step 3: Discount Prompt
                await flow.send_step(3)
                return
            except ValueError:
                pass 

        # Check 2: Waiting for Discount Code (Step 3)
        if flow.robux > 0 and flow.price == 0.0:
            code = message.content.strip()
            await message.delete()
            
            await apply_discount(flow, code)
            
            # Now move to the next step (Step 4: Price Confirmation)
            await flow.send_step(4)
            return

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
# COMPLETION LOGIC (Remains the same)
# -------------------------------------------------
async def send_completed_order(amount, price, method):
    channel = bot.get_channel(COMPLETED_CHANNEL_ID)
    if not channel: return
    
    # ... (rest of completion logic)

# -------------------------------------------------
# PRICE LIST EMBED (Remains the same)
# -------------------------------------------------
async def send_price_embed(force_new: bool = False):
    # ... (rest of price list logic)

# -------------------------------------------------
# PERSISTENT PURCHASE BUTTON
# -------------------------------------------------
class PersistentPurchaseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # REQUIRED

    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.blurple, custom_id="purchase_robux_btn")
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ... (rest of purchase button logic)
        pass

# -------------------------------------------------
# INFO EMBED 
# -------------------------------------------------
async def send_info_embed(force_new: bool = False):
    # ... (rest of info embed logic)
    pass

# -------------------------------------------------
# TERMS OF SERVICE EMBED (NEW)
# -------------------------------------------------
async def send_tos_embed(force_new: bool = False):
    # ... (rest of ToS logic)
    pass

# -------------------------------------------------
# PAYMENT METHODS EMBED (NEW)
# -------------------------------------------------
async def send_payment_methods_embed(force_new: bool = False):
    # ... (rest of payment methods logic)
    pass

# -------------------------------------------------
# STARTUP
# -------------------------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    # FIX: Using try/except block to handle persistent view re-addition safely
    try:
        # Instantiate the view using the class name before adding it
        persistent_view = PersistentPurchaseButton()
        bot.add_view(persistent_view)
    except Exception as e:
        print(f"Error adding persistent view: {e}")
    
    # All functions are defined BEFORE this point, so NameErrors are fixed.
    await send_info_embed()
    await send_price_embed() 
    await send_payment_methods_embed() 
    await send_tos_embed()             
    
    if not automated_fake_completion_loop.is_running():
        automated_fake_completion_loop.start()


# -------------------------------------------------
# AUTOMATED FAKE ORDER TASK (Remains the same)
# -------------------------------------------------
@tasks.loop(hours=random.uniform(5, 10))
async def automated_fake_completion_loop():
    amount = random.choice([10000, 25000, 50000, 100000, 250000])
    price = get_price(amount)
    method = random.choice(["Crypto", "Card", "PayPal", "Giftcard"])
    
    await send_completed_order(amount, price, method)

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
