#!/usr/bin/env python3
# Robux Town — Prefix Command Bot (Admin Only, Channel Persistent Config)
#
# Prefix: +
# Access: Admin only (manage_guild permission).
# Configuration: Stored and loaded from a specific Discord message (Message ID set via +setconfigmsg).

import os
import asyncio
import random
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone

import discord
from discord.ext import commands

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("Missing BOT_TOKEN")

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True

# --- GLOBAL CHANNEL CONFIGURATION (Hardcoded for initial setup) ---
CONFIG_CHANNEL_ID = 1435516058500071478 
CONFIG_MESSAGE_ID: Optional[int] = None # This must be set via command first!

# --- DEFAULT CONFIG STRUCTURE ---
# This dictionary structure will be stored in the config message
DEFAULT_CONFIG_STATE: Dict[str, Any] = {
    "logo_url": "https://i.ibb.co/FkDYg7gc/robux-town.png",
    "auto_banner_url": "https://i.ibb.co/ZRzkHH9N/robux-town-automatic-order.png",
    "vouch_footer_url": "https://i.ibb.co/5XbkKq64/robux-town-banner.png",
    "min_usd": 5.0,
    "max_usd": 119.0,
    # Emojis and panel text remain hardcoded constants for simplicity/stability
}

# --- IN-MEMORY STATE (Initialized from defaults) ---
BOT_STATE = DEFAULT_CONFIG_STATE.copy()

# 2. Text Content (Hardcoded)
PANEL_TEXT = (
    "This bot is a Discord bot designed to streamline the process of purchasing and distributing Robux, the virtual currency used in Roblox.\n\n"
    "**Instant Robux Delivery:**\n"
    "• Receive your Robux within moments of purchase.\n"
    "**Fully Automated Payments:**\n"
    "• Experience seamless transactions with our fully automated payment system.\n"
    "**Transaction Security:**\n"
    "• Our bot guarantees a safe and secure payment process every time.\n"
    "**Diverse Payment Options:**\n"
    "• Enjoy a variety of automated payment methods including Cryptocurrency, PayPal, and more!\n"
)

# 3. Emojis and Labels (Hardcoded)
EMOJIS: Dict[str, str] = {
    "btc": "₿", "ltc": "🟦", "eth": "💠", "sol": "🔷",
    "eneba": "🅴", "g2a": "💳", "giftcard": "🎟️", "crypto": "🪙",
    "check": "✅",
    "user_lbl": "👤 User", "user_val": "🔒 Hidden",
    "pay_lbl": "💸 Payment Method", 
    "robux_lbl": "<:Robux:1290924165792272418> Robux Purchased", 
    "usd_lbl": "💶 USD Spent",
    "rating_lbl": "⭐ Rating",
    "order_lbl": "🧾 Order ID"
}

# --- ADMIN CHECK DECORATOR ---

def admin_only():
    """Custom check to ensure the user has 'manage_guild' permission."""
    async def predicate(ctx):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("🚫 **Admin Only:** You need 'Manage Server' permissions to use this command.", ephemeral=True, delete_after=10)
            return False
        return True
    return commands.check(predicate)

# --- BOT CLASS & PERSISTENCE LOGIC ---

class RTBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="+", intents=INTENTS, help_command=None)
        
    def _emoji(self, key: str, default: str) -> str:
        """Helper to safely retrieve hardcoded emojis."""
        return str(EMOJIS.get(key, default))

    def _get_config_message_content(self) -> str:
        """Formats the current in-memory state into a fenced JSON string."""
        return "RobuxTown Config Message. **DO NOT DELETE OR MODIFY MANUALLY.**\n```json\n" + json.dumps(BOT_STATE, indent=2) + "\n```"

    async def _update_config_message(self, ctx: commands.Context):
        """Edits the pinned config message with the current BOT_STATE."""
        global CONFIG_MESSAGE_ID

        if not CONFIG_MESSAGE_ID:
            await ctx.send("❌ Config message ID is not set. Use `+setconfigmsg <message_id>` first.", delete_after=15)
            return False

        try:
            channel = self.get_channel(CONFIG_CHANNEL_ID)
            if not channel:
                channel = await self.fetch_channel(CONFIG_CHANNEL_ID)

            if isinstance(channel, discord.TextChannel):
                message = await channel.fetch_message(CONFIG_MESSAGE_ID)
                await message.edit(content=self._get_config_message_content())
                return True
            else:
                await ctx.send("❌ Config channel is not a text channel.", delete_after=15)
                return False
        except discord.NotFound:
            await ctx.send(f"❌ Config message ID `{CONFIG_MESSAGE_ID}` not found in the config channel. Please reset using `+setconfigmsg`.", delete_after=20)
            CONFIG_MESSAGE_ID = None # Clear invalid ID
            return False
        except Exception as e:
            await ctx.send(f"❌ Failed to persist config to message: {e}", delete_after=20)
            print(f"[CONFIG] Error persisting: {e}")
            return False

    async def _load_config_from_channel(self):
        """Fetches the config message content and updates BOT_STATE."""
        global CONFIG_MESSAGE_ID, BOT_STATE
        
        # In a real deployment, CONFIG_MESSAGE_ID would likely be saved externally 
        # (e.g., another file or database) if it's not hardcoded. 
        # For this exercise, assume it must be set manually on first run.
        if not CONFIG_MESSAGE_ID:
            print("[CONFIG] No Message ID set. Using defaults.")
            return

        try:
            channel = self.get_channel(CONFIG_CHANNEL_ID)
            if not channel:
                channel = await self.fetch_channel(CONFIG_CHANNEL_ID)
            
            if isinstance(channel, discord.TextChannel):
                message = await channel.fetch_message(CONFIG_MESSAGE_ID)
                content = message.content

                # Find the JSON block and parse it
                start = content.find("```json\n") + len("```json\n")
                end = content.rfind("\n```")
                json_data = content[start:end].strip()

                if json_data:
                    loaded_state = json.loads(json_data)
                    # Merge loaded state over defaults to ensure stability
                    BOT_STATE.update(loaded_state) 
                    print(f"[CONFIG] Successfully loaded state from message {CONFIG_MESSAGE_ID}")
                else:
                    print("[CONFIG] Message content empty or malformed.")
            else:
                print(f"[CONFIG] Channel {CONFIG_CHANNEL_ID} is not a text channel.")

        except Exception as e:
            print(f"[CONFIG] Failed to load config from channel: {e}")
            pass # Continue startup with defaults

    async def setup_hook(self):
        # 1. Attempt to load the message ID if it were persisted (not done here, must be manual for now)
        # For initial testing, you must manually set CONFIG_MESSAGE_ID in the script or via +setconfigmsg
        
        # 2. Load the configuration from the message on startup
        await self._load_config_from_channel()
        print("[SYNC] Commands ready.")

    async def on_ready(self):
        print(f"[READY] Logged in as {self.user}")
        print(f"[INFO] Command prefix is '+'")

bot = RTBot()

# --- VOUCH LOGIC (Uses current BOT_STATE) ---

async def post_one_fake_vouch_to_channel(channel: discord.TextChannel):
    """Generates and posts a single fake vouch embed to the specified channel."""
    
    min_usd = BOT_STATE.get("min_usd", 5.0)
    max_usd = BOT_STATE.get("max_usd", 119.0)
    
    usd = round(random.uniform(min_usd, max_usd), 2)
    robux = int(usd) * 1000
    stars = random.choices([5,4,3,2,1], weights=[60,25,10,4,1], k=1)[0]
    order_id = str(random.randrange(10**15, 10**18))

    e = discord.Embed(color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
    e.title = f"{bot._emoji('check','✅')} New Completed Order"
    
    e.add_field(name=f"{bot._emoji('user_lbl','👤 User')}", value=f"{bot._emoji('user_val','🔒 Hidden')}", inline=True)
    e.add_field(name=f"{bot._emoji('pay_lbl','💸 Payment Method')}", value=f"{bot._emoji('crypto','🪙')} Crypto", inline=True)
    e.add_field(name=f"{bot._emoji('robux_lbl','<:Robux:1290924165792272418> Robux Purchased')}", value=f"{robux:,} Robux", inline=False)
    e.add_field(name=f"{bot._emoji('usd_lbl','💶 USD Spent')}", value=f"${usd:.2f}", inline=True)
    
    stars_text = "★"*stars + "☆"*(5-stars) + f" ({stars}/5)"
    e.add_field(name=f"{bot._emoji('rating_lbl','⭐ Rating')}", value=stars_text, inline=True)
    e.add_field(name=f"{bot._emoji('order_lbl','🧾 Order ID')}", value=order_id, inline=False)

    if BOT_STATE.get("vouch_footer_url"):
        e.set_image(url=BOT_STATE["vouch_footer_url"])

    try:
        await channel.send(embed=e)
        # ... log successful post ...
    except Exception as ex:
        # ... log failure ...
        pass

# --- COMMANDS ---

@bot.command(name="help")
async def custom_help(ctx: commands.Context):
    """Displays all available admin commands."""
    
    if not ctx.author.guild_permissions.manage_guild:
        await ctx.send("This bot uses the `+` prefix. Operational commands are restricted to server administrators.", ephemeral=True, delete_after=10)
        return

    help_embed = discord.Embed(
        title="✨ Robux Bot Admin Commands",
        description="All commands use the `+` prefix and require **Manage Server** permission.",
        color=discord.Color.gold()
    )
    
    help_embed.add_field(name="`+help`", value="Displays this message.", inline=False)
    help_embed.add_field(name="`+post_autoorder`", value="Posts the Automated Purchase panel in the current channel.", inline=False)
    help_embed.add_field(name="`+fakevouchnow`", value="Posts one fake vouch in the current channel.", inline=False)
    help_embed.add_field(name="`+setbranding <logo_url> [banner_url]`", value="Updates Logo and Auto-Order Banner (Persists to Config Message).", inline=False)
    help_embed.add_field(name="`+setvouchrange <min_usd> <max_usd>`", value="Sets the min/max USD range for fake vouch posts (Persists).", inline=False)
    help_embed.add_field(name="`+setconfigmsg <message_id>`", value="**Crucial first step!** Sets the ID of the message used to save/load all config.", inline=False)

    await ctx.send(embed=help_embed)


@bot.command(name="post_autoorder")
@admin_only()
async def post_autoorder_cmd(ctx: commands.Context):
    """Posts the Automated Purchase panel using current branding."""
    
    em = discord.Embed(
        title="🛒 Automated Purchase", 
        description=PANEL_TEXT, 
        color=discord.Color.dark_magenta()
    )
    
    if BOT_STATE.get("logo_url"): em.set_thumbnail(url=BOT_STATE["logo_url"])
    if BOT_STATE.get("auto_banner_url"): em.set_image(url=BOT_STATE["auto_banner_url"])

    class PurchaseButton(discord.ui.View):
        def __init__(self): 
            super().__init__(timeout=None) 
            
        @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.primary, custom_id="purchase_btn", emoji="💠")
        async def purchase(self, i: discord.Interaction, button: discord.ui.Button):
            await i.response.send_message("A staff member will assist you shortly in this thread.", ephemeral=True)
            parent = i.channel
            try:
                th = await parent.create_thread(name=f"Order — {i.user.display_name}", auto_archive_duration=10080)
                await th.send(f"Welcome {i.user.mention}! Please state your desired Robux amount and preferred payment method.")
            except Exception: 
                pass

    await ctx.send(embed=em, view=PurchaseButton())
    await ctx.message.delete()


@bot.command(name="fakevouchnow")
@admin_only()
async def fakevouchnow_cmd(ctx: commands.Context):
    """Posts one fake vouch in the current channel."""
    
    if not isinstance(ctx.channel, discord.TextChannel):
        await ctx.send("❌ This command must be run in a text channel.", delete_after=10)
        return
    
    await post_one_fake_vouch_to_channel(ctx.channel)
    
    try:
        await ctx.message.delete()
    except Exception:
        pass


@bot.command(name="setbranding")
@admin_only()
async def set_branding_cmd(ctx: commands.Context, logo_url: Optional[str] = None, banner_url: Optional[str] = None):
    """Updates the Logo and Auto-Order Banner URLs and persists the config."""
    
    if not logo_url and not banner_url:
        await ctx.send("❌ Usage: `+setbranding <new_logo_url> [new_banner_url]` (Provide at least one URL).", delete_after=15)
        return

    updated = []
    if logo_url:
        BOT_STATE["logo_url"] = logo_url
        updated.append("Logo URL")
    
    if banner_url:
        BOT_STATE["auto_banner_url"] = banner_url
        updated.append("Auto-Order Banner URL")
    
    if await bot._update_config_message(ctx):
        await ctx.send(f"✅ Branding updated and persisted: **{', '.join(updated)}**.", delete_after=10)


@bot.command(name="setvouchrange")
@admin_only()
async def set_vouch_range_cmd(ctx: commands.Context, min_usd: float, max_usd: float):
    """Sets the minimum and maximum USD range for fake vouch posts and persists the config."""
    
    if min_usd <= 0 or max_usd <= min_usd:
        await ctx.send("❌ Error: `min_usd` must be positive and less than `max_usd`.", delete_after=15)
        return
    
    BOT_STATE["min_usd"] = min_usd
    BOT_STATE["max_usd"] = max_usd
    
    if await bot._update_config_message(ctx):
        min_robux = int(min_usd) * 1000
        max_robux = int(max_usd) * 1000
        await ctx.send(f"✅ Vouch range updated and persisted: **${min_usd:.2f} to ${max_usd:.2f}** ({min_robux:,} to {max_robux:,} Robux).", delete_after=10)


@bot.command(name="setconfigmsg")
@admin_only()
async def set_config_msg_cmd(ctx: commands.Context, message_id: int):
    """Sets the Message ID used for configuration persistence and immediately loads/saves the state."""
    global CONFIG_MESSAGE_ID

    if ctx.channel.id != CONFIG_CHANNEL_ID:
        await ctx.send(f"❌ This command must be run in the designated config channel (<#{CONFIG_CHANNEL_ID}>).", delete_after=15)
        return

    CONFIG_MESSAGE_ID = message_id

    # 1. Attempt to load existing config from the new message ID
    await bot._load_config_from_channel()

    # 2. Immediately save the current BOT_STATE back to that message (persists any local changes and confirms connectivity)
    if await bot._update_config_message(ctx):
        await ctx.send(f"✅ Config Message ID set to **`{message_id}`**. State loaded and saved.", delete_after=10)
    else:
        # If persistence failed, revert the message ID
        CONFIG_MESSAGE_ID = None
        await ctx.send("⚠️ Failed to load or save to the new message ID. Reverting change.", delete_after=15)


# --- MAIN ---

def main():
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    main()
