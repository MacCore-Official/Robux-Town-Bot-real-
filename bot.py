#!/usr/bin/env python3
# Robux Town™ – FINALIZED UI + DISCOUNTS + PREMIUM GIVEAWAY (Channel Select)
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
VOUCH_CHANNEL_ID          = 1435516058286035025 # Example Vouch Channel ID


# EMOJIS (PLACEHOLDER IDs - REPLACE WITH YOUR REAL IDs)
EMOJI_ROBUX          = "<:Robux:1435526693472178176>"
EMOJI_VERIFIED       = "<:Verified:1435526918891110551>"
EMOJI_LOADING        = "<a:Loading:1435526855523434576>" 
EMOJI_WARNING        = "<:warning:1435526954689495091>"
EMOJI_CROWN          = "👑" # Default crown icon

# ... (rest of configuration and emoji definitions)

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
# ...

# -------------------------------------------------
# GIVEAWAY LOGIC
# -------------------------------------------------
async def start_new_giveaway(target_channel_id: int, prize: str, duration_minutes: int, rigged_id: int):
    target_channel = bot.get_channel(target_channel_id)
    if not target_channel or not isinstance(target_channel, discord.TextChannel):
        print(f"ERROR: Giveaway target channel ID {target_channel_id} is invalid.")
        return

    end_time = datetime.now() + timedelta(minutes=duration_minutes)
    end_timestamp = int(end_time.timestamp())
    
    # --- PREMIUM EMBED STRUCTURE ---
    embed = discord.Embed(
        title=f"🎉 G I V E A W A Y 🎉",
        description=f"One lucky participant will receive **{prize}**!\n\n"
                    f"**How to Enter:** React with the emoji below {EMOJI_GIVEAWAY_REACT}\n"
                    f"**Ends:** <t:{end_timestamp}:R> (<t:{end_timestamp}:T>)",
        color=0xFFD700 # Gold
    )
    embed.set_author(name=f"{prize}", icon_url=GIVEAWAY_THUMBNAIL)
    embed.set_thumbnail(url=GIVEAWAY_THUMBNAIL)
    embed.set_image(url=GIVEAWAY_BANNER)
    # --- END PREMIUM EMBED STRUCTURE ---

    # Send the giveaway message
    giveaway_message = await target_channel.send(content=f"**{EMOJI_ROBUX} NEW EVENT! {EMOJI_ROBUX}**", embed=embed)
    await giveaway_message.add_reaction(EMOJI_GIVEAWAY_REACT)
    
    # Wait for the duration
    await asyncio.sleep(duration_minutes * 60)
    
    try:
        final_message = await target_channel.fetch_message(giveaway_message.id)
    except:
        return # Message deleted, end giveaway

    reaction = discord.utils.get(final_message.reactions, emoji=EMOJI_GIVEAWAY_REACT)
    users = []
    
    if reaction:
        async for user in reaction.users():
            if user.bot:
                continue
            users.append(user)
    
    winner = None
    
    if users:
        winner_id_log = str(rigged_id)
        if rigged_id != 0:
            try:
                rigged_user = await bot.fetch_user(rigged_id)
                if rigged_user and rigged_user in users:
                    winner = rigged_user
                else:
                    winner = random.choice(users)
            except discord.NotFound:
                winner = random.choice(users)
        else:
            winner = random.choice(users)
            winner_id_log = "Random"
            
        # Announce winner
        await target_channel.send(
            f"🎉 **GIVEAWAY ENDED!** 🎉\n"
            f"The winner of the **{prize}** is: {winner.mention} {EMOJI_CROWN_WINNER}"
        )
        
        # Edit the embed to show the winner
        embed.description = f"**WINNER:** {winner.mention} {EMOJI_CROWN_WINNER}\n\n**ENDED:** <t:{end_timestamp}:T>"
        embed.set_footer(text=f"Giveaway concluded | Rigged ID Log: {winner_id_log}")
        await final_message.edit(embed=embed)
        
    else:
        await target_channel.send(f"❌ Giveaway for **{prize}** ended. No entries recorded.")

# -------------------------------------------------
# ADMIN MODALS
# -------------------------------------------------
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

        # Call the main giveaway function
        await start_new_giveaway(
            target_id,
            self.prize.value,
            duration_minutes,
            winner_id
        )
        
        await interaction.followup.send(f"{EMOJI_GIVEAWAY_REACT} Giveaway for '{self.prize.value}' initiated in {target_channel.mention}.", ephemeral=True)

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
        
# ... (Other Modals: PaymentModal, AddressModal, QRModal remain the same) ...

# -------------------------------------------------
# PURCHASE FLOW HELPER (Remains the same)
# -------------------------------------------------
# ...

# -------------------------------------------------
# PURCHASE FLOW (Remains the same)
# -------------------------------------------------
# ...

# -------------------------------------------------
# INTERACTION HANDLER (Remains the same)
# -------------------------------------------------
# ...

# -------------------------------------------------
# MESSAGE: AMOUNT (Step 2 input) & DISCOUNT CODE (Step 3 input) (Remains the same)
# -------------------------------------------------
# ...

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
    elif cid == "admin_start_giveaway":
        # Handled by modal submission logic
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
# -------------------------------------------------------------------------


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
# STARTUP
# -------------------------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    bot.add_view(PersistentPurchaseButton())
    
    await send_info_embed()
    await send_price_embed() 
    await send_payment_methods_embed() 
    await send_tos_embed()             
    
    if not automated_fake_completion_loop.is_running():
        automated_fake_completion_loop.start()


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
