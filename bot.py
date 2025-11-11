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
# --------------------------------------------------------

# --- Robux Town Branding Assets (Used in Giveaway) ---
GIVEAWAY_THUMBNAIL   = "https://i.ibb.co/v4rqV5Pj/9c5fd434-f30f-4e24-8212-ea40fa098678.png" # Robux Town Icon
GIVEAWAY_BANNER      = "https://i.ibb.co/FbRfdH7D/Screenshot-2025-11-10-at-6-58-42-PM.png" # Robux Town Banner

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
# ... (Crypto, Card, PayPal, etc. emojis remain)
EMOJI_GIVEAWAY_REACT = "<:giveawaygift:1437688517089165442>" # Custom reaction emoji
EMOJI_CROWN          = "👑" # Crown icon for winner

# -------------------------------------------------
# PRICE CALCULATION 
# -------------------------------------------------
ROBUX_RATE_PER_1000 = 1.00

def get_price(robux_amount: int) -> float:
    """Calculates the standard total USD price based on the Robux amount."""
    return (robux_amount / 1000) * ROBUX_RATE_PER_1000

# -------------------------------------------------
# CONFIG LOAD/SAVE (Remains the same)
# -------------------------------------------------
CRYPTO_IDS = {"btc": "bitcoin", "ltc": "litecoin", "eth": "ethereum", "sol": "solana"}
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

# ... (get_crypto_price, send_to_staff remain the same)

# -------------------------------------------------
# GIVEAWAY LOGIC (UPDATED)
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
        return # Message deleted

    reaction = discord.utils.get(final_message.reactions, emoji=EMOJI_GIVEAWAY_REACT)
    users = []
    
    if reaction:
        async for user in reaction.users():
            if user.bot:
                continue
            users.append(user)
    
    winner = None
    
    if users:
        # --- RIGGED WINNER SELECTION ---
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
            f"The winner of the **{prize}** is: {winner.mention} {EMOJI_CROWN}"
        )
        
        # Edit the embed to show the winner
        embed.description = f"**WINNER:** {winner.mention} {EMOJI_CROWN}\n\n**ENDED:** <t:{end_timestamp}:T>"
        # Log rigging info discreetly in the footer
        embed.set_footer(text=f"Giveaway concluded | Rigged ID Log: {winner_id_log}")
        await final_message.edit(embed=embed)
        
    else:
        await target_channel.send(f"❌ Giveaway for **{prize}** ended. No entries recorded.")

# -------------------------------------------------
# ADMIN MODALS (UPDATED)
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

# ... (Rest of the script remains the same)
