#!/usr/bin/env python3
# Robux Town — Final Script: Full Interactive Purchase Flow & Prefix Admin (Fixes + Auto-Vouch)

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

# Hardcoded Emojis and Links (Unchanged)
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

# --- CONFIGURATION MANAGEMENT ---

def load_config() -> Dict[str, Any]:
    # ... (load_config logic remains the same)
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
        "staff_user_ids": [1422665161466187976, 1269145029943758899],
        # --- AUTO VOUCH CONFIG ---
        "vouch_channel_id": None,
        "min_hours": 10,
        "max_hours": 30
    }

def save_config(config: Dict[str, Any]):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print("[CONFIG] Saved to disk.")
    except Exception as e:
        print(f"[CONFIG] Persist error: {e}")

BOT_CONFIG = load_config()

# --- UTILITIES & BOT CLASS ---

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
        self.vouch_task: Optional[asyncio.Task] = None
        
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
        
        # --- AUTO VOUCH START ---
        if not self.vouch_task:
            self.vouch_task = asyncio.create_task(self.auto_vouch_loop())
            print("[VOUCH] Auto-vouch loop started.")

    # --- AUTO VOUCH LOOP (Restored) ---
    async def auto_vouch_loop(self):
        await self.wait_until_ready()
        
        while not self.is_closed():
            vch_id = BOT_CONFIG.get("vouch_channel_id")
            min_h = BOT_CONFIG.get("min_hours", 10)
            max_h = BOT_CONFIG.get("max_hours", 30)

            if vch_id and min_h >= 1 and max_h >= min_h:
                try:
                    channel = self.get_channel(vch_id) or await self.fetch_channel(vch_id)
                    
                    # Calculate wait time in seconds (random within min/max hours)
                    wait_h = random.randint(min_h, max_h)
                    wait_s = wait_h * 3600
                    
                    print(f"[VOUCH] Next post scheduled in {wait_h} hours.")
                    await asyncio.sleep(wait_s)
                    
                    if isinstance(channel, discord.TextChannel):
                        await post_one_fake_vouch_to_channel(channel)
                        
                except Exception as e:
                    print(f"[VOUCH] Error in loop/posting: {e}")
                    await asyncio.sleep(600) # Sleep for 10 minutes on error
            else:
                print("[VOUCH] Loop waiting: Channel ID not configured or invalid timing.")
                await asyncio.sleep(300) # Sleep for 5 minutes if not configured

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
    
    # --- TWO-COLUMN LAYOUT (Matching the requested image) ---
    e.add_field(name=f"{bot._emoji('user_lbl')}", value="🔒 Hidden", inline=True)
    e.add_field(name=f"{bot._emoji('pay_lbl')}", value=payment_method, inline=True)
    
    e.add_field(name=f"{bot._emoji('robux')} Robux Purchased", value=f"{robux:,} Robux", inline=False) 
    
    e.add_field(name=f"{bot._emoji('usd_lbl')} USD Spent", value=f"${usd:.2f}", inline=True)
    stars_text = "★"*stars + "☆"*(5-stars) + f" ({stars}/5)"
    e.add_field(name=f"{bot._emoji('rating_lbl')}", value=stars_text, inline=True)
    
    e.add_field(name=f"{bot._emoji('order_lbl')} Order ID", value=order_id, inline=False) 

    # --- Footer and Image ---
    if BOT_CONFIG.get("vouch_footer_url"):
        e.set_image(url=BOT_CONFIG["vouch_footer_url"])
    
    e.set_footer(text=f"Powered by Robux Town • discord.gg/robuxworld")

    try:
        await channel.send(embed=e)
        print(f"[VOUCH] Auto-posted fake vouch (R${usd:.2f}) to {channel.name}")
    except Exception as ex:
        print(f"[VOUCH] Auto-post failed: {ex}")
        
# --- TICKET SYSTEM VIEWS & FLOW (Unchanged) ---
# ... (Views remain the same as the previous script) ...

# --- LISTENER FOR USER INPUT (Fix for CommandNotFound) ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Check for thread input first
    if isinstance(message.channel, discord.Thread):
        thread = message.channel
        
        try:
            # Logic for reading Robux amount
            if re.fullmatch(r"^\d{4,7}$", message.content.strip()):
                robux_amount = int(message.content.strip())
                usd_amount = robux_amount / ROBUX_RATE
                
                min_robux = BOT_CONFIG.get('min_robux_order', MIN_ROBUX)
                max_robux = BOT_CONFIG.get('max_robux_order', 1000000)

                if robux_amount < min_robux or robux_amount > max_robux:
                    await thread.send(f"{message.author.mention} ❌ Invalid amount. Please enter a value between {min_robux:,} and {max_robux:,} Robux.", delete_after=15)
                    await message.delete() 
                    return

                # Send confirmation message
                confirm_msg = await thread.send(
                    embed=discord.Embed(
                        title=f"Would you like to purchase this amount of Robux? (3/5)",
                        description=f"Are you sure you want to purchase **{robux_amount:,} Robux**:\nCurrent Rate: **${1.0 / ROBUX_RATE * 1000:.1f} per 1,000 Robux**\nPrice in USD: **${usd_amount:.1f}**",
                        color=discord.Color.blue()
                    ),
                    view=OrderConfirmationView(robux_amount, confirm_msg)
                )
                await message.delete()
                return
        
        except Exception:
            pass

    # Process prefix commands last (This placement fixes the CommandNotFound issue)
    await bot.process_commands(message)

# --- PREFIX COMMANDS (Admin Only) ---

@bot.command(name="help")
# ... (Help command remains the same) ...
async def custom_help(ctx: commands.Context):
    if not ctx.author.guild_permissions.manage_guild:
        await ctx.send("This bot uses the `+` prefix. Operational commands are restricted to server administrators.", ephemeral=True, delete_after=10)
        return

    help_embed = discord.Embed(
        title="✨ Robux Bot Admin Commands",
        description="All commands use the `+` prefix and require **Manage Server** permission.",
        color=discord.Color.gold()
    )
    
    help_embed.add_field(name="`+help`", value="Displays this message.", inline=False)
    help_embed.add_field(name="`+post_autoorder`", value="Posts the main Automated Purchase panel and button in the current channel.", inline=False)
    help_embed.add_field(name="`+fakevouchnow`", value="Posts one fake vouch immediately (uses config.json range).", inline=False)
    help_embed.add_field(name="`+setautovouch <channel> <min_h> <max_h>`", value="**Enables** the auto-vouch loop and sets the channel and time interval.", inline=False)
    help_embed.add_field(name="`+setbranding <logo_url> [banner_url]`", value="Updates Logo and Auto-Order Banner URLs (Saves to config.json).", inline=False)
    help_embed.add_field(name="`+setvouchrange <min_usd> <max_usd>`", value="Sets the min/max USD range for fake vouch posts (Saves to config.json).", inline=False)
    help_embed.add_field(name="`+currentconfig`", value="Shows the currently loaded configuration and file status.", inline=False)

    await ctx.send(embed=help_embed)

@bot.command(name="setautovouch")
@admin_only()
async def set_autovouch_cmd(ctx: commands.Context, channel: discord.TextChannel, min_hours: int, max_hours: int):
    """Enables and configures the automatic vouch loop."""
    
    if min_hours < 1 or max_hours < min_hours:
        await ctx.send("❌ Error: `min_hours` must be at least 1, and `max_hours` must be greater than or equal to `min_hours`.", delete_after=15)
        return

    # Update global config and save
    BOT_CONFIG["vouch_channel_id"] = channel.id
    BOT_CONFIG["min_hours"] = min_hours
    BOT_CONFIG["max_hours"] = max_hours
    save_config(BOT_CONFIG)
    
    await ctx.send(f"✅ Auto Vouch enabled: Posting to {channel.mention} every **{min_hours} to {max_hours} hours**.")
    
    # If the task is running, restarting it will pick up the new channel/timing immediately
    if bot.vouch_task:
        bot.vouch_task.cancel()
        bot.vouch_task = asyncio.create_task(bot.auto_vouch_loop())
        print("[VOUCH] Auto-vouch task restarted with new config.")


@bot.command(name="post_autoorder")
@admin_only()
# ... (post_autoorder remains the same)
async def post_autoorder_cmd(ctx: commands.Context):
    em = discord.Embed(
        title="🛒 Automated Purchase", 
        description=PANEL_TEXT, 
        color=discord.Color.dark_magenta()
    )
    if BOT_CONFIG.get("logo_url"): em.set_thumbnail(url=BOT_CONFIG["logo_url"])
    if BOT_CONFIG.get("auto_banner_url"): em.set_image(url=BOT_CONFIG["auto_banner_url"])
    await ctx.send(embed=em, view=PurchaseButtonView())
    await ctx.message.delete()

@bot.command(name="fakevouchnow")
@admin_only()
# ... (fakevouchnow remains the same)
async def fakevouchnow_cmd(ctx: commands.Context):
    if not isinstance(ctx.channel, discord.TextChannel):
        await ctx.send("❌ This command must be run in a text channel.", delete_after=10)
        return
    await post_one_fake_vouch_to_channel(ctx.channel)
    try: await ctx.message.delete()
    except Exception: pass

@bot.command(name="setbranding")
@admin_only()
# ... (setbranding remains the same)
async def set_branding_cmd(ctx: commands.Context, logo_url: Optional[str] = None, banner_url: Optional[str] = None):
    if not logo_url and not banner_url:
        await ctx.send("❌ Usage: `+setbranding <new_logo_url> [new_banner_url]` (Provide at least one URL).", delete_after=15)
        return
    updated = []
    if logo_url:
        BOT_CONFIG["logo_url"] = logo_url
        updated.append("Logo URL")
    if banner_url:
        BOT_CONFIG["auto_banner_url"] = banner_url
        updated.append("Auto-Order Banner URL")
    save_config(BOT_CONFIG)
    await ctx.send(f"✅ Branding updated and persisted: **{', '.join(updated)}**.", delete_after=10)

@bot.command(name="setvouchrange")
@admin_only()
# ... (setvouchrange remains the same)
async def set_vouch_range_cmd(ctx: commands.Context, min_usd: float, max_usd: float):
    if min_usd <= 0 or max_usd <= min_usd:
        await ctx.send("❌ Error: `min_usd` must be positive and less than `max_usd`.", delete_after=15)
        return
    BOT_CONFIG["min_usd"] = min_usd
    BOT_CONFIG["max_usd"] = max_usd
    save_config(BOT_CONFIG)
    min_robux = int(min_usd) * 1000
    max_robux = int(max_usd) * 1000
    await ctx.send(f"✅ Vouch range updated and persisted: **${min_usd:.2f} to ${max_usd:.2f}** ({min_robux:,} to {max_robux:,} Robux).", delete_after=10)

@bot.command(name="currentconfig")
@admin_only()
# ... (currentconfig remains the same)
async def current_config_cmd(ctx: commands.Context):
    embed = discord.Embed(title="⚙️ Current Bot Configuration (config.json)", color=discord.Color.blue())
    staff_mentions = [f"<@{uid}> (`{uid}`)" for uid in BOT_CONFIG.get("staff_user_ids", [])]
    embed.add_field(name="Vouch Range (USD)", value=f"Min: **${BOT_CONFIG.get('min_usd', 10.0):.2f}** | Max: **${BOT_CONFIG.get('max_usd', 150.0):.2f}**", inline=False)
    embed.add_field(name="Auto Vouch", value=f"Channel: <#{BOT_CONFIG.get('vouch_channel_id')}>\nInterval: {BOT_CONFIG.get('min_hours', 10)}—{BOT_CONFIG.get('max_hours', 30)} hours", inline=False)
    embed.add_field(name="Branding URLs", value=f"Logo: {BOT_CONFIG.get('logo_url', 'N/A')}\nBanner: {BOT_CONFIG.get('auto_banner_url', 'N/A')}", inline=False)
    embed.add_field(name="Staff Notifications", value="\n".join(staff_mentions) if staff_mentions else "None set.", inline=False)
    embed.add_field(name="Order Limits", value=f"Min Robux: {BOT_CONFIG.get('min_robux_order', 10000):,}\nMax Robux: {BOT_CONFIG.get('max_robux_order', 1000000):,}", inline=False)
    await ctx.send(embed=embed)
    
# --- MAIN ---

def main():
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    main()
