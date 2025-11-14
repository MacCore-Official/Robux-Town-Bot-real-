#!/usr/bin/env python3
# Robux Town™ – FINAL STABLE VERSION (ALL FEATURES + AESTHETICS + INTERACTION FIX)
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

# --- Rewarble Links (Needed for payment invoices) ---
ENEBA_REWARBLE_LINK = "https://www.eneba.com/rewarble-rewarble-visa-10-usd-voucher-global"
G2A_REWARBLE_LINK = "https://www.g2a.com/rewarble-visa-gift-card-10-usd-by-rewarble-key-global-i10000502992001?suid=960beb55-4797-46d5-b14c-94995fd68f31"

# --- Banner (For Main Embed) ---
EMBED_BANNER = "https://i.ibb.co/FbRfdH7D/Screenshot-2025-11-10-at-6-58-42-PM.png"
EMBED_THUMBNAIL = "https://i.ibb.co/v4rqV5Pj/9c5fd434-f30f-4e24-8212-ea40fa098678.png"

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
active_flows = {} # Global dictionary for tracking user flows


# Channels (PLACEHOLDER IDs - REPLACE WITH YOUR REAL IDs)
INFO_CHANNEL_ID           = 1435516058105675818 # Where the 'Purchase Robux' button will live
LOG_CHANNEL_ID            = 1435516058286035020 # Staff payment submission log
STAFF_ROLE_ID             = 1435516057526734991 # For +admin and discount-by-message
STAFF_DM_IDS              = [1422665161466187976,1269145029943758899] # Staff to notify on payment


# EMOJIS (Only those used in the purchase flow)
EMOJI_ROBUX          = "<:Robux:1435526693472178176>"
EMOJI_VERIFIED       = "<:Verified:1435526918891110551>"
EMOJI_WARNING        = "<:warning:1435526954689495091>"
EMOJI_CRYPTO         = "<:Crypto:1437309415551406222>"
EMOJI_CARD           = "<:Card:1435526554783318047>"
EMOJI_PAYPAL         = "<:PayPal:1435526543513354354>"
EMOJI_PAYMENT_SUPPORT= "<:PAYMENT_SUPPORT:1435526984011874434>"
EMOJI_LOADING        = "<a:Loading:1435526855523434576>"
EMOJI_BITCOIN        = "<:Bitcoin:1435526466527039579>"
EMOJI_LITECOIN       = "<:Litecoin:1435526448684339321>"
EMOJI_ETHEREUM       = "<:Ethereum:1435526479126597745>"
EMOJI_SOLANA         = "<:Solana:1435526514115350549>"
EMOJI_COG            = "⚙️" 
EMOJI_LOCK           = "🔒" 
EMOJI_MAX            = "🛑" 

# -------------------------------------------------
# PRICING
# -------------------------------------------------
ROBUX_RATE_PER_1000 = 1.00
def get_price(robux_amount: int) -> float:
    """Calculates the standard total USD price based on the Robux amount."""
    return (robux_amount / 1000) * ROBUX_RATE_PER_1000

# -------------------------------------------------
# CONFIG (WALLETS & DEALS)
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
        except json.JSONDecodeError:
            print("Error reading config.json. Using defaults.")
            return default_config.copy()
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
        # Fallback prices if CoinGecko fails
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
            pass # Ignore if staff DMs are closed
            
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

# -------------------------------------------------
# ADMIN MODALS (FOR +ADMIN)
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

class DeleteDiscountView(discord.ui.Select):
    def __init__(self, discounts):
        options = [
            discord.SelectOption(label=f"{code} ({details['robux']:,} R$ for ${details['price']:.2f})", value=code) 
            for code, details in discounts.items()
        ]
        if not options:
            options = [discord.SelectOption(label="No discounts found to delete.", value="none")]
            
        super().__init__(placeholder="Select code to DELETE permanently", options=options, min_values=1, max_values=1)
        
    async def callback(self, interaction: discord.Interaction):
        code_to_delete = self.values[0]
        if code_to_delete == "none":
            await interaction.response.send_message("No action taken.", ephemeral=True)
            return
            
        if code_to_delete in config['deals']:
            del config['deals'][code_to_delete]
            save_config(config)
            await interaction.response.send_message(f"🗑️ Discount code **{code_to_delete}** has been successfully deleted.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{EMOJI_WARNING} Code not found.", ephemeral=True)

class DiscountListModal(discord.ui.Modal):
    # This modal is just a way to *trigger* the Select menu, since modals are better for user flow.
    def __init__(self):
        super().__init__(title="Active Discounts", timeout=None)
        active_deals = config.get("deals", {})
        
        default_text = "\n".join([f"  - {code}: {details['robux']:,} R$ for ${details['price']:.2f}" for code, details in active_deals.items()])
        if not default_text:
            default_text = "No Active Discounts Found."

        self.add_item(discord.ui.TextInput(
            label=f"Listing {len(active_deals)} Active Discounts:",
            default=default_text,
            style=discord.TextStyle.paragraph, 
            required=False
        ))
        self.active_deals = active_deals

    async def on_submit(self, interaction: discord.Interaction):
        # When user clicks "Submit" (which is like "OK"), show them the delete dropdown
        if not self.active_deals:
            await interaction.response.send_message("No discounts to delete.", ephemeral=True)
            return

        await interaction.response.send_message(
            "Select the code you wish to delete permanently:",
            view=discord.ui.View().add_item(DeleteDiscountView(self.active_deals)),
            ephemeral=True
        )

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
# PAYMENT MODAL (Core logic)
# -------------------------------------------------
class PaymentModal(discord.ui.Modal):
    def __init__(self, method, amount, price, crypto=None, discount_code=None):
        super().__init__(title=f"Submit {method.upper()} Details", timeout=None)
        self.method = method; self.amount = amount; self.price = price; self.crypto = crypto; self.discount_code = discount_code
        self.details = discord.ui.TextInput(label="Payment ID / TX Hash / Code", placeholder="e.g., TXabc123", style=discord.TextStyle.paragraph)
        self.add_item(self.details)

    async def on_submit(self, interaction: discord.Interaction):
        method_name = self.crypto.upper() if self.crypto else self.method
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
        await interaction.response.send_message(f"{EMOJI_VERIFIED} **Payment Submitted!** Staff have been notified.", ephemeral=True)
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
            await interaction.response.send_message("Closing the ticket...", ephemeral=False)
            await thread.edit(archived=True, locked=True)
            active_flows.pop(interaction.user.id, None)

# -------------------------------------------------
# DISCLAIMER EMBED
# -------------------------------------------------
async def send_disclaimer_embed(thread: discord.Thread) -> discord.Message:
    """Sends the disclaimer embed and returns the message object."""
    embed = discord.Embed(
        title="⚠️ Please Note",
        description=(
            "Please make sure that all conversations related to the deal are done within this ticket. Failing to do so may put you at risk of being scammed.\n\n"
            "Our staff will **never DM you** regarding any deals that are active or have already been completed."
        ),
        color=0xFFA500
    )
    view = CloseTicketView(thread.id)
    message = await thread.send(embed=embed, view=view)
    return message

# -------------------------------------------------
# PURCHASE FLOW HELPER
# -------------------------------------------------
async def apply_discount(flow, code):
    """Applies discount to flow.price and flow.discount_code if code is valid."""
    flow.discount_code = None
    flow.price = get_price(flow.robux) # Always set standard price first

    if code.upper() == "SKIP" or not code:
        return # User skipped, use standard price
    
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
# --- ALL-IN-ONE PURCHASE FLOW (CLASSES) ---
# -------------------------------------------------

class PurchaseFlow:
    """Manages the state and progression of a single purchase flow."""
    def __init__(self, user_id, thread):
        self.user_id = user_id
        self.thread = thread
        self.robux = 0
        self.price = 0.0
        self.method = ""
        self.crypto = ""
        self.discount_code = None
        self.current_step = 0
        self.message: discord.Message = None # To store the message we are editing

    async def start_flow(self):
        """Starts the flow by sending step 1."""
        await self.send_step(1)

    async def send_step(self, step: int):
        self.current_step = step
        color = 0x00A3FF
        embed = None
        view = discord.ui.View(timeout=None)

        if step == 1:
            try:
                disclaimer_message = await send_disclaimer_embed(self.thread)
                await disclaimer_message.pin()
            except discord.Forbidden:
                print(f"Warning: Missing 'Manage Messages' permission in thread {self.thread.id} to pin.")
            except Exception as e:
                print(f"Error pinning message: {e}")
            
            embed = discord.Embed(title="Would you like to start buying robux? (1/6)", color=color)
            embed.description = "\n\nPlease click \"Yes\" if you would like to start purchasing your Robux."
            view.add_item(Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_1", flow=self))
            view.add_item(Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_1", flow=self))
            
        elif step == 2:
            embed = discord.Embed(title="How much robux would you like to buy? (2/6)", color=color)
            embed.description = "\n\nPlease specify the amount of Robux you would like to purchase:\n\n**The minimum order amount is 10,000 Robux**"
            
        elif step == 3:
            embed = discord.Embed(title="Do you have a discount code? (3/6)", color=color)
            embed.description = "\n\nEnter your coupon code below, or type **'SKIP'** to continue to the standard pricing."
            
        elif step == 4:
            rate_per_1k = get_price(1000)
            discount_info = f"**COUPON APPLIED:** {self.discount_code}\n\n" if self.discount_code else ""
            embed = discord.Embed(title="Would you like to purchase this amount of Robux? (4/6)", color=color)
            embed.description = (
                f"\n\nAre you sure you want to purchase **{self.robux:,} {EMOJI_ROBUX}**?\n\n"
                f"{discount_info}"
                f"Standard Rate: **${rate_per_1k:.2f} per 1,000 {EMOJI_ROBUX}**\n\n"
                f"Total Price in USD: **${self.price:.2f}**"
            )
            view.add_item(Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_4", flow=self))
            view.add_item(Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_4", flow=self))

        elif step == 5:
            embed = discord.Embed(title="Please select your preferred payment method (5/6)", color=color)
            embed.description = "\n\nChoose your payment method below:"
            view.add_item(PaymentSelect(flow=self))
        
        if embed:
            if view.children: # Only send view if it has buttons/selects
                self.message = await self.thread.send(embed=embed, view=view)
            else:
                self.message = await self.thread.send(embed=embed)

    async def send_payment_invoice(self, interaction: discord.Interaction):
        name = "Giftcard" if self.method == "gift" else self.method
        details = ""
        if self.method == "card":
             details = f"**You must purchase a Rewarble Card from G2A** for the amount and submit the code.\n**G2A Link:** [Buy Rewarble Card Here]({G2A_REWARBLE_LINK})"
        elif self.method == "paypal":
             details = f"**You must purchase a Rewarble Card from Eneba** using PayPal/Card and submit the code.\n**Eneba Link:** [Buy Rewarble Card Here]({ENEBA_REWARBLE_LINK})"
        else:
             details = "Please purchase the necessary giftcard and prepare to submit the code/details."
             
        embed = discord.Embed(title=f"{name.upper()} Payment Invoice (6/6)", color=0x00A3FF)
        embed.description = f"Send **${self.price:.2f} USD** via **{name}**.\n\n{details}"
        
        view = discord.ui.View(timeout=None)
        view.add_item(Button(label="Submit Details", style=discord.ButtonStyle.blurple, custom_id="submit_details", flow=self))
        await interaction.followup.send(embed=embed, view=view) # Use followup

    async def send_crypto_invoice(self, interaction: discord.Interaction):
        price_usd = self.price
        coin_price = await get_crypto_price(self.crypto)
        amount_coin = round(price_usd / coin_price, 8) if coin_price else 0.0
        address = config["wallets"].get(self.crypto, "Address Not Set")
        qr_url = config["qr_urls"].get(self.crypto)
        if not qr_url or not qr_url.startswith("http"):
             qr_url = f"https_://api.qrserver.com/v1/create-qr-code/?data={address}&size=200x200"
        expiry_time = datetime.now() + timedelta(minutes=20)
        expiry_timestamp = int(expiry_time.timestamp())
        
        embed = discord.Embed(title=f"{self.crypto.upper()} Payment Invoice (6/6)", color=0x00A3FF)
        embed.description = (
            f"This transaction is **${price_usd:.2f} USD**.\n\n"
            f"Please send the **exact** amount of `{amount_coin:.8f}` {self.crypto.upper()} to the address below.\n\n"
            f"**Invoice Expires:** <t:{expiry_timestamp}:R> (<t:{expiry_timestamp}:T>)"
        )
        embed.add_field(name="Payment Address", value=f"```\n{address}\n```", inline=False)
        embed.add_field(name=f"Amount ({self.crypto.upper()})", value=f"`{amount_coin:.8f}`", inline=False)
        embed.add_field(name="Amount USD", value=f"**${price_usd:.2f}**", inline=False)
        embed.set_image(url=qr_url)
        
        view = discord.ui.View(timeout=None)
        view.add_item(Button(label="Submit TX Hash", style=discord.ButtonStyle.blurple, custom_id="submit_tx", flow=self))
        await interaction.followup.send(embed=embed, view=view) # Use followup

# --- Custom Button Class for Purchase Flow ---
class Button(discord.ui.Button):
    def __init__(self, label: str, style: discord.ButtonStyle, custom_id: str, flow: PurchaseFlow, emoji: str = None):
        super().__init__(label=label, style=style, custom_id=custom_id, emoji=emoji)
        self.flow = flow

    async def callback(self, interaction: discord.Interaction):
        # --- FIXED: Defer first, then edit ---
        # 1. Acknowledge the interaction immediately
        await interaction.response.defer()
        
        # 2. Get the view from the original message and disable its components
        view = self.view
        for item in view.children:
            item.disabled = True
        # 3. Edit the original message with the disabled view
        await interaction.edit_original_response(view=view)

        # --- Button Logic ---
        if self.custom_id == "flow_yes_1":
            await self.flow.send_step(2)
        elif self.custom_id == "flow_no_1":
            await self.flow.thread.send("Purchase flow cancelled.")
            await self.flow.thread.edit(archived=True, locked=True)
            active_flows.pop(self.flow.user_id, None)
        elif self.custom_id == "flow_yes_4":
            await self.flow.send_step(5)
        elif self.custom_id == "flow_no_4":
            await self.flow.thread.send("Cancelled. Restarting...")
            await self.flow.thread.edit(archived=True, locked=True)
            active_flows.pop(self.flow.user_id, None)
            
            # Start a new thread
            info_channel = bot.get_channel(INFO_CHANNEL_ID)
            thread = await info_channel.create_thread(
                name=f"Purchase-{interaction.user.name}-{random.randint(1000,9999)}",
                auto_archive_duration=1440,
                type=discord.ChannelType.private_thread
            )
            await thread.add_user(interaction.user)
            new_flow = PurchaseFlow(interaction.user.id, thread)
            active_flows[interaction.user.id] = new_flow
            await new_flow.start_flow()
        
        elif self.custom_id == "submit_tx":
            modal = PaymentModal("Cryptocurrency", self.flow.robux, self.flow.price, self.flow.crypto, self.flow.discount_code)
            await interaction.followup.send_modal(modal) # Use followup.send_modal
        elif self.custom_id == "submit_details":
            modal = PaymentModal(self.flow.method, self.flow.robux, self.flow.price, discount_code=self.flow.discount_code)
            await interaction.followup.send_modal(modal) # Use followup.send_modal

# --- Custom Select Menus for Purchase Flow ---
class PaymentSelect(discord.ui.Select):
    def __init__(self, flow: PurchaseFlow):
        self.flow = flow
        options = [
            discord.SelectOption(label="Cryptocurrency", value="crypto", emoji=EMOJI_CRYPTO),
            discord.SelectOption(label="Card (G2A)", value="card", emoji=EMOJI_CARD),
            discord.SelectOption(label="PayPal (Eneba)", value="paypal", emoji=EMOJI_PAYPAL),
            discord.SelectOption(label="Giftcards", value="gift", emoji=EMOJI_PAYMENT_SUPPORT),
        ]
        super().__init__(placeholder="Select your payment method", options=options, custom_id="payment_select")

    async def callback(self, interaction: discord.Interaction):
        # 1. Set the flow's method
        self.flow.method = self.values[0]
        
        # 2. Defer and disable the view
        await interaction.response.defer() # Defer first
        view = self.view
        for item in view.children:
            if isinstance(item, discord.ui.Select):
                item.disabled = True
                item.placeholder = self.values[0].capitalize()
        await interaction.edit_original_response(view=view)

        # 3. Check the method and proceed
        if self.flow.method == "crypto":
            # Send the *new* crypto selection menu
            embed = discord.Embed(title="Select Cryptocurrency", color=0x00A3FF)
            embed.description = "\n\nWhich coin will you be sending?"
            crypto_view = discord.ui.View(timeout=None)
            crypto_view.add_item(CryptoSelect(flow=self.flow)) # Add the *next* step's view
            await interaction.followup.send(embed=embed, view=crypto_view)
        else:
            # It's Card, PayPal, or Giftcard, so send the invoice
            await self.flow.send_payment_invoice(interaction)

class CryptoSelect(discord.ui.Select):
    def __init__(self, flow: PurchaseFlow):
        self.flow = flow
        options = [
            discord.SelectOption(label="BTC", value="btc", emoji=EMOJI_BITCOIN),
            discord.SelectOption(label="LTC", value="ltc", emoji=EMOJI_LITECOIN),
            discord.SelectOption(label="ETH", value="eth", emoji=EMOJI_ETHEREUM),
            discord.SelectOption(label="SOL", value="sol", emoji=EMOJI_SOLANA),
        ]
        super().__init__(placeholder="Select your crypto", options=options, custom_id="crypto_select")

    async def callback(self, interaction: discord.Interaction):
        # 1. Set the flow's crypto choice
        self.flow.crypto = self.values[0]
        
        # 2. Defer and disable the view
        await interaction.response.defer() # Defer first
        view = self.view
        for item in view.children:
            if isinstance(item, discord.ui.Select):
                item.disabled = True
                item.placeholder = self.values[0].upper()
        await interaction.edit_original_response(view=view)
        
        # 3. Call the final step
        await self.flow.send_crypto_invoice(interaction) 


# -------------------------------------------------
# PERSISTENT PURCHASE BUTTON (Main entry point)
# -------------------------------------------------
class PersistentPurchaseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent

    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.blurple, custom_id="purchase_robux_btn")
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        
        if user_id in active_flows:
            flow = active_flows[user_id]
            # Check if thread exists and is not archived
            if flow.thread and not flow.thread.archived:
                await interaction.response.send_message(f"{EMOJI_WARNING} You already have an active purchase flow in {flow.thread.mention}!", ephemeral=True)
                return
            else:
                # Clean up stale flow
                active_flows.pop(user_id, None)
        
        await interaction.response.defer(ephemeral=True)
        thread_name = f"Purchase-{interaction.user.name}-{random.randint(1000,9999)}"
        
        # Ensure thread is created in the main info channel
        info_channel = bot.get_channel(INFO_CHANNEL_ID)
        if not info_channel:
            info_channel = interaction.channel # Fallback
        
        try:
            thread = await info_channel.create_thread(
                name=thread_name,
                auto_archive_duration=1440,
                type=discord.ChannelType.private_thread
            )
        except discord.Forbidden:
            await interaction.followup.send(f"{EMOJI_WARNING} I don't have permission to create threads in {info_channel.mention}. Please contact staff.", ephemeral=True)
            return
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
            return

        await thread.add_user(interaction.user)
        
        flow = PurchaseFlow(interaction.user.id, thread)
        active_flows[interaction.user.id] = flow
        await interaction.followup.send(f"{EMOJI_VERIFIED} Purchase started! Check your new private thread: {thread.mention}", ephemeral=True)
        await flow.start_flow() # Use the new start_flow method


# -------------------------------------------------
# ON_MESSAGE (Handles Discounts & Purchase Flow Input)
# -------------------------------------------------
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return await bot.process_commands(message) # Allow commands from other bots if needed

    # === DISCOUNT VIA MESSAGE (STAFF) ===
    # Check if the user has the staff role
    if isinstance(message.author, discord.Member) and STAFF_ROLE_ID in [r.id for r in message.author.roles]:
        content = message.content.strip()
        # Check for the 'CODE, ROBUX, PRICE' format
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
                        return # Stop processing, this was a staff command
                except:
                    pass # Failed to parse, just ignore and treat as normal message

    # === PURCHASE FLOW MESSAGES ===
    if not message.channel.name.startswith("Purchase-"):
        return await bot.process_commands(message) # Process commands if not in a thread

    flow = active_flows.get(message.author.id)
    if not flow or not flow.thread or flow.thread.id != message.channel.id:
        return await bot.process_commands(message) # Process commands if not their thread

    # Check 1: Waiting for Robux Amount (Step 2)
    if flow.current_step == 2 and flow.robux == 0 and re.fullmatch(r"[\d,]+", message.content.strip()):
        try:
            amount = int(message.content.replace(",", "").strip())
            if amount < 10000:
                await message.reply(f"{EMOJI_WARNING} The **minimum order** is 10,000 {EMOJI_ROBUX}.", delete_after=5)
                return
            if amount > 800000:
                await message.reply(f"{EMOJI_MAX} The **maximum order** is 800,000 {EMOJI_ROBUX}.", delete_after=5)
                return
            
            flow.robux = amount
            # --- MODIFIED: DO NOT DELETE USER MESSAGE ---
            # await message.delete() 
            await flow.send_step(3) # Move to discount step
            return
        except ValueError:
            pass # Not a valid number

    # Check 2: Waiting for Discount Code (Step 3)
    if flow.current_step == 3 and flow.robux > 0 and flow.price == 0.0:
        code = message.content.strip()
        # --- MODIFIED: DO NOT DELETE USER MESSAGE ---
        # await message.delete() 
        
        await apply_discount(flow, code) # Helper function handles logic
        
        await flow.send_step(4) # Move to confirmation step
        return

    # Process any other commands (like +help)
    await bot.process_commands(message)

# -------------------------------------------------
# STAFF ADMIN PANEL COMMANDS (+admin)
# -------------------------------------------------
def is_staff():
    async def predicate(ctx):
        if not ctx.guild:
            return False
        if STAFF_ROLE_ID:
            role = ctx.guild.get_role(STAFF_ROLE_ID)
            if role:
                return role in ctx.author.roles
        # Fallback to admin perms if role ID is not set or invalid
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

# --- NEW: Helper function to close all tickets ---
async def close_all_active_tickets(guild: discord.Guild):
    """Finds all active 'Purchase-' threads, archives/locks them, and clears the cache."""
    closed_count = 0
    # Fetch all active threads in the guild
    for thread in guild.threads:
        if thread.name.startswith("Purchase-") and not thread.archived:
            try:
                await thread.edit(archived=True, locked=True)
                closed_count += 1
            except Exception as e:
                print(f"Failed to close thread {thread.id}: {e}")
    
    # Clear the active flow cache
    active_flows.clear()
    return closed_count

@bot.command(name="admin")
@is_staff()
async def admin_panel(ctx):
    """Opens the interactive staff administration panel."""
    embed = discord.Embed(
        title=f"{EMOJI_COG} Staff Administration Panel",
        description="Select an action to manage bot settings.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=AdminPanel(), ephemeral=True)

# --- CENTRALIZED HANDLER FOR ADMIN BUTTONS ---
async def handle_admin_panel_interaction(interaction: discord.Interaction, cid: str):
    if cid == "admin_set_address":
        await interaction.response.send_modal(AddressModal())
    elif cid == "admin_set_qr":
        await interaction.response.send_modal(QRModal())
    elif cid == "admin_set_discount":
        await interaction.response.send_modal(DiscountModal())
    elif cid == "admin_list_discounts":
        # This now opens the modal that *then* shows the select menu
        await interaction.response.send_modal(DiscountListModal())
    elif cid == "admin_reset_embed":
        await interaction.response.defer(ephemeral=True)
        await send_info_embed(force_new=True) # This is the main purchase button embed
        await interaction.followup.send(f"{EMOJI_VERIFIED} Main Purchase Embed has been reset.", ephemeral=True)
    elif cid == "admin_close_all_tickets":
        await interaction.response.defer(ephemeral=True)
        closed_count = await close_all_active_tickets(interaction.guild)
        await interaction.followup.send(f"{EMOJI_VERIFIED} Successfully closed and cleared **{closed_count}** active tickets. All purchase flows have been reset.", ephemeral=True)


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

    @discord.ui.button(label="Reset Purchase Embed", style=discord.ButtonStyle.red, custom_id="admin_reset_embed", emoji="🔄")
    async def reset_embed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_reset_embed")
        
    @discord.ui.button(label="Close All Tickets", style=discord.ButtonStyle.danger, custom_id="admin_close_all_tickets", emoji="🚨", row=2)
    async def close_all_tickets_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_close_all_tickets")

# -------------------------------------------------
# INFO EMBED (Main Purchase Button)
# -------------------------------------------------
async def send_info_embed(force_new: bool = False):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if not channel:
        print(f"ERROR: INFO_CHANNEL_ID ({INFO_CHANNEL_ID}) not found.")
        return

    # --- MODIFIED: New embed description and layout ---
    embed = discord.Embed(
        title="Welcome to Robux Town™",
        description=(
            "This bot is a Discord bot designed to streamline the process of "
            "purchasing and distributing Robux, the virtual currency used in Roblox."
        ),
        color=0x00A3FF
    )
    embed.set_thumbnail(url=EMBED_THUMBNAIL)
    
    embed.add_field(
        name="🚀 Instant Robux Delivery",
        value="Receive your Robux within moments of purchase.",
        inline=False
    )
    embed.add_field(
        name="🤖 Fully Automated Payments",
        value="Experience seamless transactions with our fully automated payment system.",
        inline=False
    )
    embed.add_field(
        name="🔒 Transaction Security",
        value="Our bot guarantees a safe and secure payment process every time.",
        inline=False
    )
    embed.add_field(
        name="💳 Diverse Payment Options",
        value="Enjoy a variety of automated payment methods including Cryptocurrency, PayPal, and more!",
        inline=False
    )
    
    embed.set_image(url=EMBED_BANNER) # Banner at the bottom

    if force_new:
        # If forcing new, delete old messages from the bot
        try:
            async for msg in channel.history(limit=10):
                if msg.author == bot.user:
                    await msg.delete()
        except discord.Forbidden:
            print("Warning: Missing permissions to delete old messages in info channel.")
        except Exception as e:
            print(f"Error clearing old info embeds: {e}")
    else:
        # Check if a message with the button already exists
        try:
            async for msg in channel.history(limit=10):
                if msg.author == bot.user and msg.components:
                    print("Info embed with button already exists. Skipping.")
                    return
        except Exception as e:
            print(f"Error checking for existing info embed: {e}")

    view = PersistentPurchaseButton()
    await channel.send(embed=embed, view=view)

# -------------------------------------------------
# ON READY
# -------------------------------------------------
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user} and ready!")
    
    # Add the persistent view so the "Purchase Robux" button works after restarts
    bot.add_view(PersistentPurchaseButton())
    
    # Post the main purchase button embed
    # This will only post if it doesn't find one already
    await send_info_embed(force_new=False) 
    print("Core services (Purchase Flow, Discounts) are active.")


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
