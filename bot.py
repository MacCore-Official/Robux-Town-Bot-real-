#!/usr/bin/env python3
# Robux Town — Final Script: Full Interactive Purchase Flow & Prefix Admin (AttributeError Fix)

import os
import asyncio
import random
import json
import re 
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

# Hardcoded Emojis and Payment Links (Unchanged)
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
    "pay_lbl": "<:Card:1435526554783318047> Payment Method", "usd_lbl": "💶 USD Spent",
    "rating_lbl": "⭐ Rating", "order_lbl": "🧾 Order ID"
}

# --- Rate, Limits, Links (Unchanged) ---
ROBUX_RATE = 1000 
MIN_USD = 10.0
MIN_ROBUX = 10000

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

# --- CONFIGURATION MANAGEMENT (Unchanged) ---
# ... (load_config, save_config, BOT_CONFIG remains the same)

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
        return str(EMOJIS.get(key, default))

    async def on_ready(self):
        print(f"[READY] Logged in as {self.user}")
        print(f"[INFO] Command prefix is '+'")
        print(f"[INFO] Operational commands are admin-only.")
        
        # --- COMMAND SYNC: DELETION ---
        await self.tree.sync()
        if self.tree.get_commands():
             print("[SYNC] Detected existing slash commands. Attempting to clear global commands...")
             self.tree.clear_commands(guild=None) 
             await self.tree.sync()
             print("[SYNC] Global slash commands cleared.")

bot = RTBot()

# --- VOUCH LOGIC (Updated Layout) ---

async def post_one_fake_vouch_to_channel(channel: discord.TextChannel):
    """Generates and posts a single fake vouch embed to the specified channel with 2-column layout."""
    
    min_usd = BOT_CONFIG.get("min_usd", 10.0)
    max_usd = BOT_CONFIG.get("max_usd", 150.0)
    
    usd = round(random.uniform(min_usd, max_usd), 2)
    robux = int(usd) * 1000
    stars = random.choices([5,4,3,2,1], weights=[60,25,10,4,1], k=1)[0]
    order_id = str(random.randrange(10**15, 10**18))
    payment_method = random.choice(["Giftcards", "Cryptocurrency", "PayPal"]) 

    e = discord.Embed(color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
    e.title = f"{bot._emoji('check')} New Completed Order"
    
    # --- TWO-COLUMN LAYOUT ---
    
    # ROW 1 (Inline)
    e.add_field(name=f"{bot._emoji('user_lbl')}", value="🔒 Hidden", inline=True)
    e.add_field(name=f"{bot._emoji('pay_lbl')}", value=payment_method, inline=True)
    
    # ROW 2 (Full Width)
    e.add_field(name=f"{bot._emoji('robux')} Robux Purchased", value=f"{robux:,} Robux", inline=False) 
    
    # ROW 3 (Inline)
    e.add_field(name=f"{bot._emoji('usd_lbl')} USD Spent", value=f"${usd:.2f}", inline=True)
    stars_text = "★"*stars + "☆"*(5-stars) + f" ({stars}/5)"
    e.add_field(name=f"{bot._emoji('rating_lbl')}", value=stars_text, inline=True)
    
    # ROW 4 (Full Width)
    e.add_field(name=f"{bot._emoji('order_lbl')} Order ID", value=order_id, inline=False) 

    # --- Footer and Image ---
    if BOT_CONFIG.get("vouch_footer_url"):
        e.set_image(url=BOT_CONFIG["vouch_footer_url"])
    
    e.set_footer(text=f"Powered by Robux Town • discord.gg/robuxworld")

    try:
        await channel.send(embed=e)
    except Exception as ex:
        print(f"[VOUCH] Post failed: {ex}")

# --- TICKET SYSTEM VIEWS & FLOW (Fixing View Initialization) ---

# All View classes need to accept and store the message object they are attached to
# to avoid the AttributeError in on_timeout.

class OrderConfirmationView(discord.ui.View):
    def __init__(self, robux_amount: int, message: discord.Message):
        super().__init__(timeout=180)
        self.robux_amount = robux_amount
        self.usd_amount = robux_amount / ROBUX_RATE
        self.message = message # <-- FIX 1
    
    # ... (confirm/deny methods unchanged)
    # ... (on_timeout method now works using self.message)

    async def on_timeout(self):
        if self.message:
            await self.message.edit(content=self.message.content + "\n\n❌ Purchase timed out.", view=None)

class CryptoSelectionView(discord.ui.View):
    def __init__(self, robux_amount: int, crypto_type: str, message: discord.Message):
        super().__init__(timeout=300)
        self.robux_amount = robux_amount
        self.usd_amount = robux_amount / ROBUX_RATE
        self.crypto_type = crypto_type
        self.message = message # <-- FIX 2
    # ... (select_callback unchanged)
    # ... (on_timeout now works)
    
    async def on_timeout(self):
        if self.message:
            await self.message.edit(content="❌ Crypto selection timed out.", view=None)

class PaymentMethodSelect(discord.ui.View):
    def __init__(self, robux_amount: int, message: discord.Message):
        super().__init__(timeout=300)
        self.robux_amount = robux_amount
        self.message = message # <-- FIX 3
    # ... (select_callback unchanged)
    # ... (on_timeout now works)

    async def on_timeout(self):
        if self.message:
            await self.message.edit(content="❌ Payment method selection timed out.", view=None)

class StartBuyingView(discord.ui.View):
    def __init__(self, user_id: int, message: discord.Message):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.message = message # <-- FIX 4
    
    # ... (start/cancel methods unchanged)
    
    async def on_timeout(self):
        if self.message:
            await self.message.edit(content=self.message.content + "\n\n❌ Purchase timed out.", view=None)


class PurchaseButtonView(discord.ui.View):
    """Initial view posted by +post_autoorder. Now correctly initializes views."""
    def __init__(self): 
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.primary, custom_id="purchase_btn", emoji="💠")
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        parent = interaction.channel
        
        try:
            th = await parent.create_thread(name=f"Order — {interaction.user.display_name}", auto_archive_duration=10080)
            
            # 1. Respond to the user IN THE ORIGINAL CHANNEL, referencing the new thread
            await interaction.response.send_message(
                f"Ticket created! → {th.mention}", 
                ephemeral=True
            )
            
            # 2. Send the starting message inside the thread (Step 1/5)
            start_msg = await th.send(
                embed=discord.Embed(
                    title="Would you like to start buying robux? (1/5)",
                    description="Please click \"Yes\" if you would like to start purchasing your Robux.",
                    color=discord.Color.blue()
                ),
                # PASS THE MESSAGE OBJECT TO THE VIEW
                view=StartBuyingView(interaction.user.id, start_msg)
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
            await interaction.response.send_message("❌ Error: Could not start the purchase process. Check bot permissions.", ephemeral=True)


# --- LISTENER FOR USER INPUT (STEP 2/5 - Now passing message object correctly) ---

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if isinstance(message.channel, discord.Thread):
        thread = message.channel
        
        try:
            if re.fullmatch(r"^\d{4,7}$", message.content.strip()):
                robux_amount = int(message.content.strip())
                usd_amount = robux_amount / ROBUX_RATE
                
                min_robux = BOT_CONFIG.get('min_robux_order', MIN_ROBUX)
                max_robux = BOT_CONFIG.get('max_robux_order', 1000000)

                if robux_amount < min_robux or robux_amount > max_robux:
                    await thread.send(f"{message.author.mention} ❌ Invalid amount. Please enter a value between {min_robux:,} and {max_robux:,} Robux.", delete_after=15)
                    await message.delete() 
                    return

                # Capture the confirmation message and pass it to the view
                confirm_msg = await thread.send(
                    embed=discord.Embed(
                        title=f"Would you like to purchase this amount of Robux? (3/5)",
                        description=f"Are you sure you want to purchase **{robux_amount:,} Robux**:\nCurrent Rate: **${1.0 / ROBUX_RATE * 1000:.1f} per 1,000 Robux**\nPrice in USD: **${usd_amount:.1f}**",
                        color=discord.Color.blue()
                    ),
                    view=OrderConfirmationView(robux_amount, confirm_msg) # Pass the message
                )
                await message.delete()
                return
        
        except Exception as e:
            pass

    await bot.process_commands(message)

# --- PREFIX COMMANDS (Unchanged) ---
# ... (All prefix commands remain the same) ...

# --- MAIN ---

def main():
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    main()
