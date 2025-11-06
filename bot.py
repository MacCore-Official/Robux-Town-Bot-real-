#!/usr/bin/env python3
# Robux Town — Automatic Order Flow (Clean, Persistent, and Restart-Safe)

import os
import asyncio
import random
import json
import re
from typing import Dict, Any, Optional
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
    # Custom Payment Icons
    "paypal": "<:PayPal:1435526543513354354>",
    "bitcoin": "<:Bitcoin:1435526466527039579>",
    "ethereum": "<:Ethereum:1435526479126597745>",
    "litecoin": "<:Litecoin:1435526448684339321>",
    "solana": "<:Solana:1435526514115350549>",
    "card": "<:Card:1435526554783318047>",
    "rewarble": "<:Rewarble:1435526590472650763>",
    # Status/Standard Icons
    "loading": "<:loading:1435526855523434576>",
    "warning": "<:warning:1435526954689495091>",
    "robux": "<:Robux:1290924165792272418>",
    "check": "✅",
    # Labels
    "user_lbl": "👤 User",
    "pay_lbl": "<:PAYMENT_SUPPORT:1435526984011874434> Payment Method",
    "usd_lbl": "💶 USD Spent",
    "rating_lbl": "⭐ Rating",
    "order_lbl": "🧾 Order ID",
    "cart": "🛒"
}

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
    "This bot streamlines purchasing and distributing Robux.\n\n"
    "**Instant Robux Delivery:**\n"
    "Receive your Robux within moments of purchase.\n\n"
    "**Fully Automated Payments:**\n"
    "Seamless transactions with our automated flow.\n\n"
    "**Transaction Security:**\n"
    "Safe and secure payment process every time.\n\n"
    "**Diverse Payment Options:**\n"
    "Cryptocurrency, PayPal (via Eneba), or Card (via G2A).\n"
)

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
        "vouch_footer_url": "https://i.ibb.co/5XbkKq64/robux-town-banner.png",  # used as a visual footer on some embeds
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

# --- UTILITIES & BOT CLASS ---

def admin_only():
    async def predicate(ctx):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("🚫 Admin Only: You need **Manage Server** to use this.", delete_after=10)
            return False
        return True
    return commands.check(predicate)

class RTBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="+", intents=INTENTS, help_command=None)
bot = RTBot()

    def _emoji(self, key: str, default: str = "") -> str:
        return str(EMOJIS.get(key, default))

    async def on_ready(self):
        print(f"[READY] Logged in as {self.user} ({self.user.id})")
        print("[INFO] Prefix '+' | Admin-only operational commands")

        # Register persistent component views across restarts
        try:
            self.add_view(PurchaseButtonView())
            print("[UI] Registered persistent PurchaseButtonView.")
        except Exception as e:
            print(f"[UI] Failed to register persistent view: {e}")

# --- VIEWS & MODALS ---

class AmountModal(discord.ui.Modal, title="Enter Robux Amount (2/5)"):
    def __init__(self, thread: discord.Thread):
        super().__init__(timeout=180)
        self.thread = thread

    amount = discord.ui.TextInput(
        label="Robux to buy",
        placeholder="e.g., 50,000",
        required=True,
        max_length=12
    )

    async def on_submit(self, interaction: discord.Interaction):
        raw = str(self.amount.value).strip()
        digits = re.sub(r"[^\d]", "", raw)  # allow commas/spaces
        if not digits or len(digits) > 7:
            await interaction.response.send_message("❌ Enter a valid amount (4–7 digits).", ephemeral=True)
            return

        robux_amount = int(digits)
        min_robux = BOT_CONFIG.get('min_robux_order', MIN_ROBUX)
        max_robux = BOT_CONFIG.get('max_robux_order', 1_000_000)
        if robux_amount < min_robux or robux_amount > max_robux:
            await interaction.response.send_message(
                f"❌ Amount must be between {min_robux:,} and {max_robux:,} Robux.",
                ephemeral=True
            )
            return

        usd_amount = robux_amount / ROBUX_RATE

        confirm_embed = discord.Embed(
            title="Would you like to purchase this amount of Robux? (3/5)",
            description=(
                f"Are you sure you want to purchase **{robux_amount:,} Robux**?\n"
                f"Current Rate: **${1.0 / ROBUX_RATE * 1000:.1f} per 1,000 Robux**\n"
                f"Price in USD: **${usd_amount:.1f}**"
            ),
            color=discord.Color.blue()
        )
        confirm_msg = await self.thread.send(embed=confirm_embed)
        await confirm_msg.edit(view=OrderConfirmationView(robux_amount, confirm_msg))

        await interaction.response.send_message("✅ Amount received — check the ticket for confirmation.", ephemeral=True)

class OrderConfirmationView(discord.ui.View):
    def __init__(self, robux_amount: int, message: discord.Message):
        super().__init__(timeout=180)
        self.robux_amount = robux_amount
        self.usd_amount = robux_amount / ROBUX_RATE
        self.message = message

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="✅ Confirmed.", view=None)

        select_embed = discord.Embed(
            title="Please select your preferred payment method (4/5)",
            description="Choose a payment method below.",
            color=discord.Color.blue()
        )
        select_msg = await interaction.channel.send(embed=select_embed, view=PaymentMethodSelect(self.robux_amount, None))
        await select_msg.edit(view=PaymentMethodSelect(self.robux_amount, select_msg))
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ Cancelled.", view=None)
        await interaction.channel.send("Purchase cancelled. Send a new Robux amount to restart.", delete_after=30)
        self.stop()

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(content="❌ Purchase timed out.", view=None)
            except Exception:
                pass

class CryptoSelectionView(discord.ui.View):
    def __init__(self, robux_amount: int, message: Optional[discord.Message]):
        super().__init__(timeout=300)
        self.robux_amount = robux_amount
        self.usd_amount = robux_amount / ROBUX_RATE
        self.message = message

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

        mock_crypto_address = "bc1qexampleexampleexampleexampleexample"  # placeholder
        mock_crypto_amount = round(self.usd_amount / random.uniform(20000, 30000), 8)

        invoice_embed = discord.Embed(
            title=f"{crypto.upper()} Payment Invoice (5/5)",
            description=(
                f"This transaction is approximately **${self.usd_amount:.1f}**.\n"
                f"Send exactly **{mock_crypto_amount:.8f} {crypto.upper()}** to the address below."
            ),
            color=discord.Color.dark_green()
        )
        invoice_embed.add_field(name="Payment Address", value=f"```\n{mock_crypto_address}\n```", inline=False)
        invoice_embed.add_field(name=f"Amount {crypto.upper()}", value=f"```\n{mock_crypto_amount:.8f}\n```", inline=True)
        invoice_embed.add_field(name="Amount USD", value=f"${self.usd_amount:.1f}", inline=True)

        monitoring_embed = discord.Embed(
            title="Checking For Transactions",
            description=f"{EMOJIS['loading']} We are monitoring transactions. Proceed with your payment.",
            color=discord.Color.gold()
        )

        await interaction.response.edit_message(embed=monitoring_embed, content=f"You selected **{crypto.upper()}**.", view=None)
        await interaction.channel.send(embed=invoice_embed)
        self.stop()

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(content="❌ Crypto selection timed out.", view=None)
            except Exception:
                pass

class PurchaseSubmitDetails(discord.ui.View):
    def __init__(self, robux_amount: int, payment_method_name: str):
        super().__init__(timeout=300)
        self.robux_amount = robux_amount
        self.payment_method_name = payment_method_name

    @discord.ui.button(label="Submit a Giftcard", style=discord.ButtonStyle.secondary)
    async def submit_giftcard(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PurchaseDetailsModal(interaction.user.id, self.payment_method_name))
        self.stop()

class PurchaseDetailsModal(discord.ui.Modal, title="Submit Gift Card / Payment Details"):
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
        await interaction.response.send_message(f"{EMOJIS['loading']} Submitting details for staff verification...", ephemeral=True)

        details_text = self.details.value
        user = interaction.user
        thread = interaction.channel

        # Notify staff via DM
        for staff_id in BOT_CONFIG.get("staff_user_ids", []):
            try:
                staff_user = bot.get_user(staff_id) or await bot.fetch_user(staff_id)
                if staff_user:
                    staff_embed = discord.Embed(
                        title=f"{EMOJIS['warning']} PENDING PAYMENT CHECK ({self.payment_method_name})",
                        description=f"**User:** {user.mention} (`{user.id}`)\n**Thread:** {thread.mention}\n\n**Details Submitted:**",
                        color=discord.Color.red(),
                        timestamp=datetime.now(timezone.utc)
                    )
                    staff_embed.add_field(name="Payment Input", value=details_text[:1024], inline=False)
                    await staff_user.send(embed=staff_embed)
            except Exception as e:
                print(f"[STAFF_DM] Failed to DM staff {staff_id}: {e}")

        final_embed = discord.Embed(
            title=f"{EMOJIS['loading']} Awaiting Staff Verification",
            description=(
                f"Thank you, {user.mention}. Your details were forwarded to staff.\n\n"
                f"**Next Steps:** Staff will update this thread once verification is complete."
            ),
            color=discord.Color.orange()
        )

        await thread.send(embed=final_embed, view=TicketStaffView(user.id))
        self.stop()

class PaymentMethodSelect(discord.ui.View):
    def __init__(self, robux_amount: int, message: Optional[discord.Message]):
        super().__init__(timeout=300)
        self.robux_amount = robux_amount
        self.message = message

    @discord.ui.select(
        placeholder="Select your payment method...",
        options=[
            discord.SelectOption(label="Cryptocurrency", value="crypto", emoji=EMOJIS["bitcoin"], description="BTC, LTC, ETH, SOL"),
            discord.SelectOption(label="PayPal (via Eneba)", value="paypal", emoji=EMOJIS["paypal"], description="Buy Rewarble Visa on Eneba"),
            discord.SelectOption(label="Card (via G2A)", value="card", emoji=EMOJIS["card"], description="Buy Rewarble Visa on G2A"),
            discord.SelectOption(label="Giftcards", value="giftcard", emoji=EMOJIS["rewarble"], description="Rewarble, Steam, etc."),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        method = select.values[0]
        usd = self.robux_amount / ROBUX_RATE

        await interaction.response.edit_message(content="✅ Method Selected.", view=None)

        if method == "crypto":
            crypto_embed = discord.Embed(
                title="Select your crypto (4/5)",
                description="You selected **Cryptocurrency**. What will you send?",
                color=discord.Color.blue()
            )
            crypto_select_msg = await interaction.channel.send(embed=crypto_embed, view=CryptoSelectionView(self.robux_amount, None))
            await crypto_select_msg.edit(view=CryptoSelectionView(self.robux_amount, crypto_select_msg))
            return

        if method in ["paypal", "card", "giftcard"]:
            link_list = ENEBA_LINKS if method == "paypal" else G2A_LINKS
            link_type = "Eneba" if method == "paypal" else "G2A"

            links_to_show = {price: link for price, link in link_list.items() if price >= usd}
            if not links_to_show:
                links_to_show = link_list

            link_embed = discord.Embed(
                title=f"Purchase via {method.capitalize()} on {link_type}",
                description=(
                    f"Buy **Rewarble Visa Gift Card** on {link_type}. "
                    f"If the exact amount isn’t available, combine codes."
                ),
                color=discord.Color.dark_grey()
            )

            # Display links in neat columns
            prices_sorted = sorted(links_to_show.keys())
            chunk, chunk_size = [], 3
            for i, price in enumerate(prices_sorted, 1):
                chunk.append(f"[${price:.0f} Voucher]({links_to_show[price]})")
                if i % chunk_size == 0 or i == len(prices_sorted):
                    link_embed.add_field(
                        name="Voucher Links" if i <= chunk_size else "Voucher Links (cont.)",
                        value="\n".join(chunk),
                        inline=True
                    )
                    chunk = []

            invoice_embed = discord.Embed(
                title=f"{method.capitalize()} Payment Invoice (5/5)",
                description=(
                    f"Purchase a **Rewarble Visa Gift Card** with the required value for your transaction.\n"
                    f"Then submit the card information for verification.\n\n"
                    f"**Amount USD:** ${usd:.1f}"
                ),
                color=discord.Color.blue()
            )

            await interaction.channel.send(embeds=[link_embed, invoice_embed])

            waiting_embed = discord.Embed(
                title="Waiting For A Giftcard",
                description="⚪ Submit a gift card when ready. Staff will verify it here.",
                color=discord.Color.light_grey()
            )
            await interaction.channel.send(embed=waiting_embed, view=PurchaseSubmitDetails(self.robux_amount, method))

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(content="❌ Payment method selection timed out.", view=None)
            except Exception:
                pass

class TicketStaffView(discord.ui.View):
    def __init__(self, invoker_id: int):
        super().__init__(timeout=None)
        self.invoker_id = invoker_id

    @discord.ui.button(label="Complete Order", style=discord.ButtonStyle.success)
    async def complete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in BOT_CONFIG.get("staff_user_ids", []):
            await interaction.response.send_message("❌ Staff only.", ephemeral=True)
            return
        await interaction.response.edit_message(content=f"✅ **Order Completed by {interaction.user.mention}.**", view=None)
        self.stop()

    @discord.ui.button(label="Invalid / Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in BOT_CONFIG.get("staff_user_ids", []):
            await interaction.response.send_message("❌ Staff only.", ephemeral=True)
            return
        await interaction.response.edit_message(content=f"❌ **Order Closed by {interaction.user.mention}.**", view=None)
        self.stop()

class PurchaseButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.primary, custom_id="purchase_btn", emoji="💠")
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        parent = interaction.channel
        user = interaction.user

        # Channel + permission checks
        if not isinstance(parent, discord.TextChannel):
            await interaction.response.send_message("❌ Use this in a text channel.", ephemeral=True)
            return
        perms = parent.permissions_for(parent.guild.me)
        if not (perms.send_messages and perms.create_public_threads):
            await interaction.response.send_message("❌ I need **Send Messages** and **Create Public Threads**.", ephemeral=True)
            return

        # Reuse an active thread for this user if present
        existing = None
        for th in parent.threads:
            if not th.archived and (str(user.id) in th.name or user.display_name in th.name):
                existing = th
                break

        try:
            th = existing or await parent.create_thread(
                name=f"Order — {user.display_name} ({user.id})",
                auto_archive_duration=10080
            )

            # Ticket safety note
            await th.send(
                embed=discord.Embed(
                    title="⚠️ Please Note",
                    description=(
                        "Keep all conversations for this deal **inside this ticket**.\n"
                        "Our staff will **never DM you** about an active or completed deal."
                    ),
                    color=discord.Color.orange()
                )
            )

            # Open modal to capture amount (first response = modal)
            await interaction.response.send_modal(AmountModal(th))

        except Exception as e:
            print(f"[ORDER] Thread setup failed: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Could not set up the ticket. Check my permissions.", ephemeral=True)

# --- LISTENER (Optional free-text fallback inside threads) ---

class FreeTextGuard:
    number_re = re.compile(r"^\d{4,7}$")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.Thread):
        thread = message.channel
        content = message.content.strip()

        if FreeTextGuard.number_re.fullmatch(content):
            try:
                robux_amount = int(content)
                min_robux = BOT_CONFIG.get('min_robux_order', MIN_ROBUX)
                max_robux = BOT_CONFIG.get('max_robux_order', 1_000_000)
                if not (min_robux <= robux_amount <= max_robux):
                    await thread.send(
                        f"{message.author.mention} ❌ Enter between {min_robux:,} and {max_robux:,} Robux.",
                        delete_after=15
                    )
                    await message.delete()
                    return

                usd_amount = robux_amount / ROBUX_RATE
                confirm_embed = discord.Embed(
                    title="Would you like to purchase this amount of Robux? (3/5)",
                    description=(
                        f"Are you sure you want to purchase **{robux_amount:,} Robux**?\n"
                        f"Current Rate: **${1.0 / ROBUX_RATE * 1000:.1f} per 1,000 Robux**\n"
                        f"Price in USD: **${usd_amount:.1f}**"
                    ),
                    color=discord.Color.blue()
                )
                confirm_msg = await thread.send(embed=confirm_embed)
                await confirm_msg.edit(view=OrderConfirmationView(robux_amount, confirm_msg))
                await message.delete()
                return
            except Exception:
                pass

    await bot.process_commands(message)

# --- PREFIX COMMANDS (Admin Only) ---


@bot.command(name="help")
async def custom_help(ctx: commands.Context):
    if not ctx.author.guild_permissions.manage_guild:
        await ctx.send("This bot uses the `+` prefix. Admin-only operational commands.", delete_after=10)
        return

    help_embed = discord.Embed(
        title="✨ Robux Bot Admin Commands",
        description="All commands use the `+` prefix and require **Manage Server** permission.",
        color=discord.Color.gold()
    )
    help_embed.add_field(name="`+help`", value="Show this help.", inline=False)
    help_embed.add_field(name="`+post_autoorder`", value="Post the Automated Purchase panel and button in this channel.", inline=False)
    help_embed.add_field(name="`+setbranding <logo_url> [banner_url]`", value="Update Logo and Auto-Order Banner (saved to config.json).", inline=False)
    help_embed.add_field(name="`+currentconfig`", value="Show current configuration.", inline=False)
    await ctx.send(embed=help_embed)

@bot.command(name="post_autoorder")
@admin_only()
async def post_autoorder_cmd(ctx: commands.Context):
    em = discord.Embed(
        title=f"{EMOJIS['cart']} Automated Purchase",
        description=PANEL_TEXT,
        color=discord.Color.dark_magenta()
    )
    if BOT_CONFIG.get("logo_url"):
        em.set_thumbnail(url=BOT_CONFIG["logo_url"])
    if BOT_CONFIG.get("auto_banner_url"):
        em.set_image(url=BOT_CONFIG["auto_banner_url"])
    await ctx.send(embed=em, view=PurchaseButtonView())
    try:
        await ctx.message.delete()
    except Exception:
        pass

@bot.command(name="setbranding")
@admin_only()
async def set_branding_cmd(ctx: commands.Context, logo_url: Optional[str] = None, banner_url: Optional[str] = None):
    if not logo_url and not banner_url:
        await ctx.send("❌ Usage: `+setbranding <new_logo_url> [new_banner_url]`", delete_after=15)
        return
    updated = []
    if logo_url:
        BOT_CONFIG["logo_url"] = logo_url
        updated.append("Logo URL")
    if banner_url:
        BOT_CONFIG["auto_banner_url"] = banner_url
        updated.append("Auto-Order Banner URL")
    save_config(BOT_CONFIG)
    await ctx.send(f"✅ Updated: **{', '.join(updated)}**.", delete_after=10)

@bot.command(name="currentconfig")
@admin_only()
async def current_config_cmd(ctx: commands.Context):
    embed = discord.Embed(title="⚙️ Current Bot Configuration (config.json)", color=discord.Color.blue())
    staff_mentions = [f"<@{uid}> (`{uid}`)" for uid in BOT_CONFIG.get("staff_user_ids", [])]
    embed.add_field(name="Branding URLs", value=f"Logo: {BOT_CONFIG.get('logo_url','N/A')}\nBanner: {BOT_CONFIG.get('auto_banner_url','N/A')}", inline=False)
    embed.add_field(name="Staff Notifications", value="\n".join(staff_mentions) if staff_mentions else "None set.", inline=False)
    embed.add_field(name="Order Limits", value=f"Min Robux: {BOT_CONFIG.get('min_robux_order', 10000):,}\nMax Robux: {BOT_CONFIG.get('max_robux_order', 1000000):,}", inline=False)
    await ctx.send(embed=embed)

# --- MAIN ---

def main():
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    main()
