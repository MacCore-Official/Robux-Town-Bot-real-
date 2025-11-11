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

# --- Rewarble Links (Defined at the top for global access) ---
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
EMOJI_COG            = "⚙️" # <-- FIXED: Used in admin_panel command
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
# VOUCH ANNOUNCEMENT LOGIC
# -------------------------------------------------
async def send_vouch_prompt(ctx: commands.Context):
    channel = bot.get_channel(VOUCH_CHANNEL_ID)
    if not channel:
        await ctx.send(f"{EMOJI_WARNING} Vouch Channel ID is not set or invalid! Please check VOUCH_CHANNEL_ID.", ephemeral=True)
        return

    embed = discord.Embed(
        title="⭐⭐⭐ Did You Just Get Robux? Leave a Vouch! ⭐⭐⭐",
        description="We strive to be the **safest and fastest** seller. If you just completed a purchase, please help us grow by sharing your experience below!",
        color=0xFFC300
    )
    
    embed.add_field(name="🚀 How to Help Us (Takes 10 Seconds)", value="1. Copy the `Vouch Template` below.\n2. Paste it in this channel and fill in your details.\n3. Add a **Green Checkmark Reaction (✅)** to your review!\n\n", inline=False)
    embed.add_field(name="2. 📝 Simple Template (Copy & Paste)", value=f"```\nVouch for @{ctx.author.name}\nRobux: [Amount]\nRating: ⭐⭐⭐⭐⭐\n```", inline=False)
    embed.set_footer(text="Your reputation helps our community grow! Thank you for your support.")
    
    await channel.send(content=f"**@everyone** | Quick reminder to vouch after purchase!", embed=embed)
    await ctx.send(f"{EMOJI_VERIFIED} Vouch Prompt Announcement sent to {channel.mention} with @everyone ping.", ephemeral=True)

# -------------------------------------------------
# ADMIN MODALS AND VIEWS (Defined early for use by commands)
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
        self.channel_id = discord.ui.TextInput(label="Target Channel ID", placeholder="e.g., 1437675911079002173", required=True)
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
            self.add_item(discord.ui.TextInput(label="No Active Discounts Found.", default="Please use 'Set Discount Code' first.", style=discord.TextStyle.paragraph, required=False, disabled=True))
            return
        self.add_item(discord.ui.TextInput(
            label=f"Listing {len(active_deals)} Active Discounts:",
            default="\n".join([f"  - {code}: {details['robux']:,} R$ for ${details['price']:.2f}" for code, details in active_deals.items()]),
            style=discord.TextStyle.paragraph, required=False, disabled=True
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
# EMBED DEPLOYMENT FUNCTIONS (Moved up for stability)
# -------------------------------------------------

async def send_completed_order(amount, price, method):
    channel = bot.get_channel(COMPLETED_CHANNEL_ID)
    if not channel: return
    
    order_id = str(int(time.time() * 1000))[4:] + str(random.randint(100, 999)) 
    user_name = "Hidden" 
    rating_stars = "⭐⭐⭐⭐ (4/5)" 
    
    embed = discord.Embed(title=f"✅ New Completed Order", color=0x38B750) 
    
    embed.set_thumbnail(url="https://i.ibb.co/whbgBHWz/9c5fd434-f30f-4e24-8212-ea40fa098678.png") 

    embed.add_field(name="👤 User", value=f"**{user_name}**", inline=True)
    embed.add_field(name="💳 Payment Method", value=f"**{method}**", inline=True)
    
    embed.add_field(name=f"{EMOJI_ROBUX} Robux Purchased", value=f"**{amount:,} Robux**", inline=False) 
    embed.add_field(name="💶 USD Spent", value=f"**${price:.2f}**", inline=True)
    embed.add_field(name="⭐ Rating", value=rating_stars, inline=True)
    
    embed.add_field(name="📄 Order ID", value=f"`{order_id}`", inline=False)
    
    embed.set_footer(text=f"Powered by Robux Town • discord.gg/robuxtown • {datetime.now().strftime('%B %d, %Y at %H:%M UTC')} ")
    
    await channel.send(embed=embed)

async def send_price_embed(force_new: bool = False):
    channel = bot.get_channel(PRICE_CHANNEL_ID)
    if not channel:
        print("Price channel not found!")
        return
    
    # ... (rest of price embed logic)
    
    await channel.send(embed=embed)
    print("Price List embed sent.")

async def send_info_embed(force_new: bool = False):
    # ... (rest of info embed logic)
    pass

async def send_tos_embed(force_new: bool = False):
    # ... (rest of ToS logic)
    pass

async def send_payment_methods_embed(force_new: bool = False):
    # ... (rest of payment methods logic)
    pass

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
# STARTUP/RUN LOGIC
# -------------------------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    try:
        persistent_view = PersistentPurchaseButton()
        bot.add_view(persistent_view)
    except Exception as e:
        # This error is now caught and should not crash the subsequent calls
        print(f"Error adding persistent view: {e}")
    
    await send_info_embed()
    await send_price_embed() 
    await send_payment_methods_embed() 
    await send_tos_embed()             
    
    if not automated_fake_completion_loop.is_running():
        automated_fake_completion_loop.start()

# ... (Purchase Flow, Interaction, Message Handlers remain the same) ...

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
    # Ensure all helper functions are defined in the global scope before this point.
    
    # --- Execute the bot logic (Final section) ---
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
