#!/usr/bin/env python3
# Robux Town — Prefix Command Bot (Final Version: Config.json & Full Ticket Flow)

import os
import asyncio
import random
import json
from typing import Dict, Any, Optional, List
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

# Hardcoded Emojis and Texts (using the Custom IDs you provided)
EMOJIS: Dict[str, str] = {
    "paypal": "<:PayPal:1435526543513354354>",
    "bitcoin": "<:Bitcoin:1435526466527039579>",
    "card": "<:Card:1435526554783318047>",
    "ethereum": "<:Ethereum:1435526479126597745>",
    "rewarble": "<:Rewarble:1435526590472650763>",
    "loading": "<:loading:1435526855523434576>",
    "warning": "<:warning:1435526954689495091>",
    "robux": "<:Robux:1290924165792272418>", # Assuming this is the Robux emoji from the original
    "check": "✅",
    "user_lbl": "👤 User", "user_val": "🔒 Hidden",
    "pay_lbl": "💸 Payment Method", 
    "usd_lbl": "💶 USD Spent",
    "rating_lbl": "⭐ Rating",
    "order_lbl": "🧾 Order ID"
}

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

# --- CONFIGURATION MANAGEMENT ---

def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[CONFIG] Failed reading config.json: {e}")
    
    # Return defaults if file not found or load failed
    return {
        "logo_url": "https://i.ibb.co/FkDYg7gc/robux-town.png",
        "auto_banner_url": "https://i.ibb.co/ZRzkHH9N/robux-town-automatic-order.png",
        "vouch_footer_url": "https://i.ibb.co/5XbkKq64/robux-town-banner.png",
        "min_usd": 10.0,
        "max_usd": 150.0,
        "staff_user_ids": [1422665161466187976, 1269145029943758899] # Your specific staff IDs
    }

def save_config(config: Dict[str, Any]):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print("[CONFIG] Saved to disk.")
    except Exception as e:
        print(f"[CONFIG] Persist error: {e}")

# --- BOT CLASS & DECORATORS ---

BOT_CONFIG = load_config()

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
        # Prefix is now '+'
        super().__init__(command_prefix="+", intents=INTENTS, help_command=None)
        
    def _emoji(self, key: str, default: str = "") -> str:
        """Helper to safely retrieve hardcoded emojis."""
        return str(EMOJIS.get(key, default))

    async def on_ready(self):
        print(f"[READY] Logged in as {self.user}")
        print(f"[INFO] Command prefix is '+'")
        print(f"[INFO] Operational commands are admin-only.")

bot = RTBot()

# --- VOUCH LOGIC ---

async def post_one_fake_vouch_to_channel(channel: discord.TextChannel):
    """Generates and posts a single fake vouch embed to the specified channel."""
    
    min_usd = BOT_CONFIG.get("min_usd", 10.0)
    max_usd = BOT_CONFIG.get("max_usd", 150.0)
    
    usd = round(random.uniform(min_usd, max_usd), 2)
    robux = int(usd) * 1000
    stars = random.choices([5,4,3,2,1], weights=[60,25,10,4,1], k=1)[0]
    order_id = str(random.randrange(10**15, 10**18))

    e = discord.Embed(color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
    e.title = f"{bot._emoji('check')} New Completed Order"
    
    e.add_field(name=f"{bot._emoji('user_lbl')}", value=f"{bot._emoji('user_val')}", inline=True)
    # Using 'bitcoin' as a default crypto emoji for the fake vouch
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

# --- TICKET SYSTEM VIEWS ---

class TicketStaffView(discord.ui.View):
    """View only for staff, added to the final thread message."""
    def __init__(self, invoker_id: int):
        super().__init__(timeout=None)
        self.invoker_id = invoker_id

    @discord.ui.button(label="Complete Order", style=discord.ButtonStyle.success)
    async def complete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="✅ **Order Completed.** Staff verified payment and delivered Robux.", view=None)
        self.stop()
    
    @discord.ui.button(label="Invalid / Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ **Order Closed.** Payment failed verification or user cancelled.", view=None)
        self.stop()
        
class PurchaseDetailsModal(discord.ui.Modal, title="Submit Gift Card / Payment Details"):
    """Modal to capture payment info (like gift card codes or screenshots)."""
    
    details = discord.ui.TextInput(
        label="Code, details, or link to screenshot:",
        style=discord.TextStyle.paragraph,
        placeholder="e.g., ABC-XYZ-123 or image link",
        required=True,
        max_length=1500
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{bot._emoji('loading')} Submitting details for staff verification...", ephemeral=True)
        
        details_text = self.details.value
        user = interaction.user
        thread = interaction.channel
        
        # 1. Notify Staff via DM
        for staff_id in BOT_CONFIG.get("staff_user_ids", []):
            try:
                staff_user = bot.get_user(staff_id) or await bot.fetch_user(staff_id)
                if staff_user:
                    staff_embed = discord.Embed(
                        title=f"{bot._emoji('warning')} PENDING PAYMENT CHECK",
                        description=f"**User:** {user.mention} (`{user.id}`)\n**Thread:** {thread.mention}\n\n**Details Submitted:**",
                        color=discord.Color.red(),
                        timestamp=datetime.now(timezone.utc)
                    )
                    staff_embed.add_field(name="Payment Input", value=details_text[:1024], inline=False)
                    await staff_user.send(embed=staff_embed)
            except Exception as e:
                print(f"[STAFF_DM] Failed to DM staff {staff_id}: {e}")
        
        # 2. Update Thread for user/staff
        final_embed = discord.Embed(
            title=f"{bot._emoji('loading')} Awaiting Staff Verification",
            description=f"Thank you, {user.mention}. Your details have been securely forwarded to staff for review.\n\n"
                        f"**Next Steps:** Staff will update this thread once verification is complete.",
            color=discord.Color.orange()
        )
        
        await thread.send(embed=final_embed, view=TicketStaffView(user.id))
        self.stop()


class PaymentMethodView(discord.ui.View):
    """View presented in the thread to choose a payment method."""
    def __init__(self, invoker_id: int):
        super().__init__(timeout=300)
        self.invoker_id = invoker_id

    @discord.ui.select(
        placeholder="Choose your preferred payment method...",
        options=[
            discord.SelectOption(label="PayPal", value="paypal", emoji=EMOJIS["paypal"], description="Purchase via Eneba (PayPal is accepted there)."),
            discord.SelectOption(label="Bitcoin", value="bitcoin", emoji=EMOJIS["bitcoin"], description="Use Bitcoin (BTC) for direct crypto purchase."),
            discord.SelectOption(label="Ethereum", value="ethereum", emoji=EMOJIS["ethereum"], description="Use Ethereum (ETH) for direct crypto purchase."),
            discord.SelectOption(label="Gift Card / Card", value="card", emoji=EMOJIS["card"], description="Amazon, Visa, etc. (Purchased via G2A/Rewarble)."),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        method = select.values[0]
        
        # Update thread to show selection
        await interaction.response.edit_message(content=f"You selected: **{bot._emoji(method)} {method.capitalize()}**.", view=None)

        # Prompt for details using the modal
        await interaction.followup.send_modal(PurchaseDetailsModal())

    async def on_timeout(self):
        # Graceful timeout cleanup
        if self.message:
            await self.message.edit(content="❌ Session expired. Please send a message to restart the process.", view=None)


class PurchaseButtonView(discord.ui.View):
    """Initial view posted by +post_autoorder."""
    def __init__(self): 
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.primary, custom_id="purchase_btn", emoji="💠")
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("A staff member will assist you shortly in this thread.", ephemeral=True)
        parent = interaction.channel
        
        try:
            # 1. Create a thread
            th = await parent.create_thread(name=f"Order — {interaction.user.display_name}", auto_archive_duration=10080)
            
            # 2. Send initial welcome and prompt
            initial_message = await th.send(
                f"Welcome {interaction.user.mention}! Please state your desired **Robux amount** (e.g., 50k, 100k) and then use the menu below to select your **preferred payment method**.",
                view=PaymentMethodView(interaction.user.id)
            )
            # Store the message reference in the view for easy editing on timeout
            PaymentMethodView(interaction.user.id).message = initial_message 

        except Exception as e: 
            print(f"[ORDER] Failed to create thread: {e}")
            await interaction.followup.send("❌ Error: Could not start the purchase process. Check bot permissions.", ephemeral=True)


# --- PREFIX COMMANDS (Admin Only) ---

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
    help_embed.add_field(name="`+post_autoorder`", value="Posts the main Automated Purchase panel and button in the current channel.", inline=False)
    help_embed.add_field(name="`+fakevouchnow`", value="Posts one fake vouch in the current channel (uses config.json range).", inline=False)
    help_embed.add_field(name="`+setbranding <logo_url> [banner_url]`", value="Updates Logo and Auto-Order Banner URLs (Saves to config.json).", inline=False)
    help_embed.add_field(name="`+setvouchrange <min_usd> <max_usd>`", value="Sets the min/max USD range for fake vouch posts (Saves to config.json).", inline=False)
    help_embed.add_field(name="`+currentconfig`", value="Shows the currently loaded configuration and file status.", inline=False)

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
    
    if BOT_CONFIG.get("logo_url"): em.set_thumbnail(url=BOT_CONFIG["logo_url"])
    if BOT_CONFIG.get("auto_banner_url"): em.set_image(url=BOT_CONFIG["auto_banner_url"])

    await ctx.send(embed=em, view=PurchaseButtonView())
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
        BOT_CONFIG["logo_url"] = logo_url
        updated.append("Logo URL")
    
    if banner_url:
        BOT_CONFIG["auto_banner_url"] = banner_url
        updated.append("Auto-Order Banner URL")
    
    save_config(BOT_CONFIG)
    await ctx.send(f"✅ Branding updated and persisted: **{', '.join(updated)}**.", delete_after=10)


@bot.command(name="setvouchrange")
@admin_only()
async def set_vouch_range_cmd(ctx: commands.Context, min_usd: float, max_usd: float):
    """Sets the minimum and maximum USD range for fake vouch posts and persists the config."""
    
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
async def current_config_cmd(ctx: commands.Context):
    """Displays the currently loaded configuration settings."""
    
    embed = discord.Embed(
        title="⚙️ Current Bot Configuration (config.json)",
        color=discord.Color.blue()
    )
    
    staff_mentions = [f"<@{uid}> (`{uid}`)" for uid in BOT_CONFIG.get("staff_user_ids", [])]
    
    embed.add_field(name="Vouch Range (USD)", 
                    value=f"Min: **${BOT_CONFIG.get('min_usd', 10.0):.2f}** | Max: **${BOT_CONFIG.get('max_usd', 150.0):.2f}**", inline=False)
    embed.add_field(name="Branding URLs", 
                    value=f"Logo: {BOT_CONFIG.get('logo_url', 'N/A')}\nBanner: {BOT_CONFIG.get('auto_banner_url', 'N/A')}", inline=False)
    embed.add_field(name="Staff Notifications",
                    value="\n".join(staff_mentions) if staff_mentions else "None set.", inline=False)
    
    await ctx.send(embed=embed)


# --- MAIN ---

def main():
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    main()
