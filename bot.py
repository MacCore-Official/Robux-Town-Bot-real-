#!/usr/bin/env python3
# Robux Town — Final Script: Full Interactive Purchase Flow & Prefix Admin

import os
import asyncio
import random
import json
import re # For input validation
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone

import discord
from discord.ext import commands

# --- CONFIGURATION & SETUP ---

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("Missing BOT_TOKEN")

CONFIG_FILE = "config.json"
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True

# Hardcoded Emojis and Payment Links
EMOJIS: Dict[str, str] = {
    "paypal": "<:PayPal:1435526543513354354>",
    "bitcoin": "<:Bitcoin:1435526466527039579>",
    "ethereum": "<:Ethereum:1435526479126597745>",
    "litecoin": "<:Litecoin:1435526448684339321>", 
    "solana": "<:Solana:1435526514115350549>",     
    "card": "<:Card:1435526554783318047>",
    "rewarble": "<:Rewarble:1435526590472650763>",
    "loading": "<:loading:1435526855523434576>",
    "warning": "<:warning:1435526954689495091>",
    "robux": "<:Robux:1290924165792272418>", 
    "check": "✅",
    "user_lbl": "👤 User", "user_val": "🔒 Hidden",
    "pay_lbl": "💸 Payment Method", "usd_lbl": "💶 USD Spent",
    "rating_lbl": "⭐ Rating", "order_lbl": "🧾 Order ID"
}

# --- CORRECTED PANEL TEXT ---
PANEL_TEXT = (
    "This bot is a Discord bot designed to streamline the process of purchasing and distributing Robux, the virtual currency used in Roblox.\n"
    "\n"
    "**Instant Robux Delivery:**\n"
    "Receive your Robux within moments of purchase.\n"
    "\n"
    "**Fully Automated Payments:**\n"
    "Experience seamless transactions with our fully automated payment system.\n"
    "\n"
    "**Transaction Security:**\n"
    "Our bot guarantees a safe and secure payment process every time.\n"
    "\n"
    "**Diverse Payment Options:**\n"
    "Enjoy a variety of automated payment methods including Cryptocurrency, PayPal, and more!\n"
)

# --- Rate (1:1000) and Minimum/Maximums (Unchanged) ---
ROBUX_RATE = 1000 
MIN_USD = 10.0
MIN_ROBUX = 10000

# --- Eneba (PayPal) & G2A (Card) Links (Unchanged) ---
ENEBA_LINKS = {
    5: "https://www.eneba.com/rewarble-rewarble-visa-5-usd-voucher-global",
    10: "https://www.eneba.com/rewarble-rewarble-visa-10-usd-voucher-global",
    15: "https://www.eneba.com/rewarble-rewarble-visa-15-usd-voucher-global",
    20: "https://www.eneba.com/rewarble-rewarble-visa-20-usd-voucher-global",
}
G2A_LINKS = {
    5: "https://www.g2a.com/rewarble-visa-gift-card-5-usd-by-rewarble-key-global-i10000502992002",
    10: "https://www.g2a.com/rewarble-visa-gift-card-10-usd-by-rewarble-key-global-i10000502992001",
    20: "https://www.g2a.com/rewarble-visa-gift-card-20-usd-by-rewarble-key-global-i10000502992006",
    25: "https://www.g2a.com/rewarble-visa-gift-card-25-usd-by-rewarble-key-global-i10000502992003",
}

# --- CONFIGURATION MANAGEMENT (Unchanged) ---

def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[CONFIG] Failed reading config.json: {e}. Using defaults.")
    
    return {
        "logo_url": "https://i.ibb.co/FkDYg7gc/robux-town.png",
        "auto_banner_url": "https://i.ibb.co/ZRzkHH9N/robux-town-automatic-order.png",
        "vouch_footer_url": "https://i.ibb.co/5XbkKq64/robux-town-banner.png",
        "min_usd": 10.0,
        "max_usd": 150.0,
        "min_robux_order": 10000,
        "max_robux_order": 1000000,
        "staff_user_ids": [1422665161466187976, 1269145029943758899]
    }

def save_config(config: Dict[str, Any]):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print("[CONFIG] Saved to disk.")
    except Exception as e:
        print(f"[CONFIG] Persist error: {e}")

BOT_CONFIG = load_config()

# --- UTILITIES & BOT CLASS (Unchanged) ---

def admin_only():
    """Custom check to ensure the user has 'manage_guild' permission."""
    async def predicate(ctx):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("🚫 **Admin Only:** You need 'Manage Server' permissions to use this command.", ephemeral=True, delete_after=10)
            return False
        return True
    return commands.check(predicate)

class RTBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="+", intents=INTENTS, help_command=None)
        
    def _emoji(self, key: str, default: str = "") -> str:
        """Helper to safely retrieve hardcoded emojis."""
        return str(EMOJIS.get(key, default))

    async def on_ready(self):
        print(f"[READY] Logged in as {self.user}")
        print(f"[INFO] Command prefix is '+'")
        print(f"[INFO] Operational commands are admin-only.")
        # --- COMMAND SYNC: DELETION ---
        # Running this on startup ensures the old global slash commands are removed.
        # This only needs to run once.
        await self.tree.sync()
        if self.tree.get_commands():
             print("[SYNC] Detected existing slash commands. Attempting to clear global commands...")
             self.tree.clear_commands(guild=None) 
             await self.tree.sync()
             print("[SYNC] Global slash commands cleared.")
        # -------------------------------


bot = RTBot()

# --- VOUCH LOGIC (Unchanged) ---

async def post_one_fake_vouch_to_channel(channel: discord.TextChannel):
    # ... (Logic is unchanged)
    min_usd = BOT_CONFIG.get("min_usd", 10.0)
    max_usd = BOT_CONFIG.get("max_usd", 150.0)
    
    usd = round(random.uniform(min_usd, max_usd), 2)
    robux = int(usd) * 1000
    stars = random.choices([5,4,3,2,1], weights=[60,25,10,4,1], k=1)[0]
    order_id = str(random.randrange(10**15, 10**18))

    e = discord.Embed(color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
    e.title = f"{bot._emoji('check')} New Completed Order"
    
    e.add_field(name=f"{bot._emoji('user_lbl')}", value=f"{bot._emoji('user_val')}", inline=True)
    e.add_field(name=f"{bot._emoji('pay_lbl')}", value=f"{bot._emoji('bitcoin')} Crypto", inline=True) 
    e.add_field(name=f"{bot._emoji('robux')} Robux Purchased", value=f"{robux:,} Robux", inline=False)
    e.add_field(name=f"{bot._emoji('usd_lbl')}", value=f"${usd:.2f}", inline=True)
    
    stars_text = "★"*stars + "☆"*(5-stars) + f" ({stars}/5)"
    e.add_field(name=f"{bot._emoji('rating_lbl')}", value=stars_text, inline=True)
    e.add_field(name=f"{bot._emoji('order_lbl')}", value=order_id, inline=False)

    if BOT_CONFIG.get("vouch_footer_url"):
        e.set_image(url=BOT_CONFIG["vouch_footer_url"])

    try:
        await channel.send(embed=e)
    except Exception as ex:
        print(f"[VOUCH] Post failed: {ex}")
        
# --- TICKET SYSTEM VIEWS & FLOW (Minor Fixes Only) ---

class PurchaseButtonView(discord.ui.View):
    """Initial view posted by +post_autoorder."""
    def __init__(self): 
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.primary, custom_id="purchase_btn", emoji="💠")
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        parent = interaction.channel
        
        try:
            # 1. Create the thread
            th = await parent.create_thread(name=f"Order — {interaction.user.display_name}", auto_archive_duration=10080)
            
            # 2. Respond to the user IN THE ORIGINAL CHANNEL, referencing the new thread
            await interaction.response.send_message(
                f"Ticket created! → {th.mention}", # Uses the desired format
                ephemeral=True
            )
            
            # 3. Send the starting message inside the thread
            # Step 1/5: Start Buying Robux
            await th.send(
                embed=discord.Embed(
                    title="Would you like to start buying robux? (1/5)",
                    description="Please click \"Yes\" if you would like to start purchasing your Robux.",
                    color=discord.Color.blue()
                ),
                view=StartBuyingView(interaction.user.id)
            )
            # Send initial disclaimer message
            await th.send(
                embed=discord.Embed(
                    title="⚠️ Please Note",
                    description="Please make sure that all conversations related to the deal are done within this ticket. Failing to do so may put you at risk of being scamming.\n\nOur staff will never DM you regarding any deals that are active or have already been completed.",
                    color=discord.Color.orange()
                )
            )

        except Exception as e: 
            print(f"[ORDER] Failed to create thread: {e}")
            # If thread creation fails (e.g., permissions), send error to the user
            await interaction.response.send_message("❌ Error: Could not start the purchase process. Check bot permissions.", ephemeral=True)
            
# --- REST OF VIEWS AND LOGIC (UNCHANGED) ---

# ... (OrderConfirmationView, CryptoSelectionView, PurchaseSubmitDetails, 
# PurchaseDetailsModal, PaymentMethodSelect, StartBuyingView, TicketStaffView remain the same) ...

# --- LISTENER FOR USER INPUT (STEP 2/5) ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Check if the message is within a thread/channel where a purchase flow might be active
    if isinstance(message.channel, discord.Thread):
        thread = message.channel
        
        try:
            # Simple check for a message containing only a number (the Robux amount)
            if re.fullmatch(r"^\d{4,7}$", message.content.strip()):
                robux_amount = int(message.content.strip())
                usd_amount = robux_amount / ROBUX_RATE
                
                min_robux = BOT_CONFIG.get('min_robux_order', MIN_ROBUX)
                max_robux = BOT_CONFIG.get('max_robux_order', 1000000)

                if robux_amount < min_robux or robux_amount > max_robux:
                    await thread.send(f"{message.author.mention} ❌ Invalid amount. Please enter a value between {min_robux:,} and {max_robux:,} Robux.", delete_after=15)
                    await message.delete() 
                    return

                # Step 3/5: Confirmation
                await thread.send(
                    embed=discord.Embed(
                        title=f"Would you like to purchase this amount of Robux? (3/5)",
                        description=f"Are you sure you want to purchase **{robux_amount:,} Robux**:\nCurrent Rate: **${1.0 / ROBUX_RATE * 1000:.1f} per 1,000 Robux**\nPrice in USD: **${usd_amount:.1f}**",
                        color=discord.Color.blue()
                    ),
                    view=OrderConfirmationView(robux_amount)
                )
                await message.delete()
                return
        
        except Exception as e:
            pass

    # Process prefix commands after checking for internal flow input
    await bot.process_commands(message)

# --- PREFIX COMMANDS (Admin Only) ---

@bot.command(name="post_autoorder")
@admin_only()
async def post_autoorder_cmd(ctx: commands.Context):
    em = discord.Embed(
        title="🛒 Automated Purchase", 
        description=PANEL_TEXT, # Uses the new clean text
        color=discord.Color.dark_magenta()
    )
    if BOT_CONFIG.get("logo_url"): em.set_thumbnail(url=BOT_CONFIG["logo_url"])
    if BOT_CONFIG.get("auto_banner_url"): em.set_image(url=BOT_CONFIG["auto_banner_url"])
    await ctx.send(embed=em, view=PurchaseButtonView())
    await ctx.message.delete()

# --- OTHER COMMANDS (Unchanged) ---
# ... (+help, +fakevouchnow, +setbranding, +setvouchrange, +currentconfig remain the same) ...

# --- MAIN ---

def main():
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    main()
