#!/usr/bin/env python3
# robux_town_bot.py — Auto-Order Bot (discord.py 2.6.4)
# Fixed panel (only LOGO & BANNER editable). Payment methods:
# - Eneba (select a saved link)
# - G2A (buyer enters gift card code in a modal)
# - Crypto (shows BTC/LTC/ETH/USDT wallets set via /setbtc /setltc /seteth /setusdt)
# - Giftcard (generic code entry via modal)
#
# Env:
#   BOT_TOKEN (required)
#   DB_PATH   (optional, default: robux_autoorder.db)

import os
import sqlite3
from typing import Optional, List, Dict
from datetime import datetime, timezone

import discord
from discord.ext import commands
from discord import app_commands

# ====== CONFIG ======
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("Missing BOT_TOKEN environment variable.")
DB_PATH = os.getenv("DB_PATH", "robux_autoorder.db")

PAYMENT_TYPES = ("eneba",)  # /addlink is ONLY for eneba now
STAFF_ROLE_ID = 1291897728061931520
DEFAULT_ROBUX_LOGO_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Robux_2019_Logo_white.svg/1883px-Robux_2019_Logo_white.svg.png"
)

# ====== INTENTS ======
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # enable in Dev Portal → Bot → Privileged Gateway Intents

# ====== BOT CORE ======
class RTBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.db: Optional[sqlite3.Connection] = None

    async def setup_hook(self):
        await self._init_db()
        await self.tree.sync()
        print("[SYNC] Slash commands synced.")

    async def _init_db(self):
        self.db = sqlite3.connect(DB_PATH)
        self.db.row_factory = sqlite3.Row
        cur = self.db.cursor()
        cur.executescript("""
        PRAGMA journal_mode=WAL;

        CREATE TABLE IF NOT EXISTS links (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          guild_id   INTEGER NOT NULL,
          type       TEXT    NOT NULL,
          url        TEXT    NOT NULL,
          created_at TEXT    NOT NULL
        );

        -- Branding: ONLY logo & banner are editable.
        CREATE TABLE IF NOT EXISTS branding (
          guild_id    INTEGER PRIMARY KEY,
          logo_url    TEXT,
          banner_url  TEXT
        );

        -- Crypto wallets per guild
        CREATE TABLE IF NOT EXISTS crypto_wallets (
          guild_id INTEGER PRIMARY KEY,
          btc TEXT, ltc TEXT, eth TEXT, usdt TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          guild_id   INTEGER NOT NULL,
          user_id    INTEGER NOT NULL,
          amount     INTEGER NOT NULL,
          pay_type   TEXT    NOT NULL,
          link_used  TEXT,
          created_at TEXT    NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_links_guild  ON links(guild_id);
        CREATE INDEX IF NOT EXISTS idx_orders_guild ON orders(guild_id);
        """)
        self.db.commit()
        print(f"[DB] Ready at {DB_PATH}")

    # ----- DB helpers -----
    def save_branding(self, guild_id: int, logo: Optional[str], banner: Optional[str]):
        cur = self.db.cursor()
        cur.execute("INSERT OR IGNORE INTO branding(guild_id, logo_url, banner_url) VALUES (?, NULL, NULL)", (guild_id,))
        if logo   is not None: cur.execute("UPDATE branding SET logo_url=?   WHERE guild_id=?", (logo,   guild_id))
        if banner is not None: cur.execute("UPDATE branding SET banner_url=? WHERE guild_id=?", (banner, guild_id))
        self.db.commit()

    def load_branding(self, guild_id: int) -> Dict[str, Optional[str]]:
        cur = self.db.cursor()
        cur.execute("SELECT logo_url,banner_url FROM branding WHERE guild_id=?", (guild_id,))
        row = cur.fetchone()
        if not row:
            return {"logo_url": DEFAULT_ROBUX_LOGO_URL, "banner_url": None}
        data = dict(row)
        if not data.get("logo_url"):
            data["logo_url"] = DEFAULT_ROBUX_LOGO_URL
        return data

    def add_link(self, guild_id: int, t: str, url: str) -> int:
        if t not in PAYMENT_TYPES:
            raise ValueError("invalid type")
        cur = self.db.cursor()
        cur.execute(
            "INSERT INTO links(guild_id, type, url, created_at) VALUES(?, ?, ?, ?)",
            (guild_id, t, url, datetime.now(timezone.utc).isoformat()),
        )
        self.db.commit()
        return cur.lastrowid

    def remove_link(self, guild_id: int, link_id: int) -> bool:
        cur = self.db.cursor()
        cur.execute("DELETE FROM links WHERE id=? AND guild_id=?", (link_id, guild_id))
        self.db.commit()
        return cur.rowcount > 0

    def list_links_grouped(self, guild_id: int) -> Dict[str, List[dict]]:
        cur = self.db.cursor()
        cur.execute("SELECT id, type, url FROM links WHERE guild_id=? ORDER BY type, id", (guild_id,))
        grouped: Dict[str, List[dict]] = {"eneba": []}
        for r in cur.fetchall():
            grouped.setdefault(r["type"], []).append({"id": r["id"], "url": r["url"]})
        return grouped

    def links_for_type(self, guild_id: int, t: str) -> List[dict]:
        cur = self.db.cursor()
        cur.execute("SELECT id, url FROM links WHERE guild_id=? AND type=? ORDER BY id", (guild_id, t))
        return [{"id": r["id"], "url": r["url"]} for r in cur.fetchall()]

    def set_wallet(self, guild_id: int, kind: str, value: Optional[str]):
        assert kind in ("btc","ltc","eth","usdt")
        cur = self.db.cursor()
        cur.execute("INSERT OR IGNORE INTO crypto_wallets(guild_id) VALUES (?)", (guild_id,))
        cur.execute(f"UPDATE crypto_wallets SET {kind}=? WHERE guild_id=?", (value, guild_id))
        self.db.commit()

    def get_wallets(self, guild_id: int) -> Dict[str, Optional[str]]:
        cur = self.db.cursor()
        cur.execute("SELECT btc,ltc,eth,usdt FROM crypto_wallets WHERE guild_id=?", (guild_id,))
        row = cur.fetchone()
        if not row:
            return {"btc": None, "ltc": None, "eth": None, "usdt": None}
        return dict(row)

    def log_order(self, guild_id: int, user_id: int, amount: int, pay_type: str, link_used: str):
        cur = self.db.cursor()
        cur.execute(
            "INSERT INTO orders(guild_id, user_id, amount, pay_type, link_used, created_at) VALUES(?, ?, ?, ?, ?, ?)",
            (guild_id, user_id, amount, pay_type, link_used, datetime.now(timezone.utc).isoformat()),
        )
        self.db.commit()

bot = RTBot()

# ====== FIXED TEXT / EMBEDS ======
SAFETY_NOTE = (
    "Please keep **all** deal conversation inside this ticket.\n"
    "Our staff will **never** DM you for payments or codes."
)

def mk_panel_embed(branding: Dict[str, Optional[str]], guild: discord.Guild) -> discord.Embed:
    title = "Automated Purchase"
    desc = (
        "This bot is designed to streamline the process of purchasing and distributing **Robux**.\n\n"
        "**Instant Robux Delivery:**\n"
        "• Receive your Robux within moments of purchase.\n\n"
        "**Fully Automated Payments:**\n"
        "• Experience seamless transactions with our fully automated payment system.\n\n"
        "**Transaction Security:**\n"
        "• Safe and secure processing inside ticket threads only.\n\n"
        "**Diverse Payment Options:**\n"
        "• Eneba, G2A, Crypto & Giftcards."
    )

    e = discord.Embed(title=title, description=desc, color=discord.Color.from_str("#2b6cff"))
    e.set_footer(text=f"{guild.name} • Powered by Robux Town")
    e.timestamp = datetime.now(timezone.utc)
    e.set_thumbnail(url=branding.get("logo_url") or DEFAULT_ROBUX_LOGO_URL)
    if branding.get("banner_url"):
        e.set_image(url=branding["banner_url"])
    return e

def mk_note_embed() -> discord.Embed:
    e = discord.Embed(title="⚠️ Safety Note", description=SAFETY_NOTE, color=discord.Color.from_str("#ffb200"))
    e.set_footer(text="Stay safe — trades only inside tickets")
    e.timestamp = datetime.now(timezone.utc)
    return e

def step1_embed() -> discord.Embed:
    return discord.Embed(
        title="Start Purchase (1/5)",
        description="Click **Yes** to begin your Robux order.",
        color=discord.Color.from_str("#2b6cff"),
    )

def step2_embed() -> discord.Embed:
    return discord.Embed(
        title="Amount (2/5)",
        description="Enter how many Robux you want.\n**Example:** `10000`   •   **Minimum:** `10000`",
        color=discord.Color.from_str("#2b6cff"),
    )

def step3_embed(amount: int, rate_per_1k: float = 1.0) -> discord.Embed:
    usd = (amount / 1000.0) * rate_per_1k
    e = discord.Embed(
        title="Confirm (3/5)",
        description=(
            f"You're purchasing **{amount:,}** Robux\n"
            f"Current Rate: **${rate_per_1k:.2f} per 1,000 Robux**\n"
            f"Estimated: **${usd:.2f} USD**"
        ),
        color=discord.Color.from_str("#2b6cff"),
    )
    e.set_footer(text="Confirm to continue to payment method")
    return e

def step4_embed() -> discord.Embed:
    return discord.Embed(
        title="Payment Method (4/5)",
        description="Pick your payment method below.",
        color=discord.Color.from_str("#2b6cff"),
    )

def crypto_embed(wallets: Dict[str, Optional[str]]) -> discord.Embed:
    lines = []
    if wallets.get("btc"):  lines.append(f"**BTC:** `{wallets['btc']}`")
    if wallets.get("ltc"):  lines.append(f"**LTC:** `{wallets['ltc']}`")
    if wallets.get("eth"):  lines.append(f"**ETH:** `{wallets['eth']}`")
    if wallets.get("usdt"): lines.append(f"**USDT:** `{wallets['usdt']}`")
    desc = "Send payment to one of the configured wallets below, then **reply with TXID** in this ticket.\n\n"
    desc += ("\n".join(lines) if lines else "_No wallets configured yet._")
    e = discord.Embed(title="Crypto Payment (5/5)", description=desc, color=discord.Color.from_str("#2b6cff"))
    e.set_footer(text="Press Done after paying")
    return e

def eneba_embed(link_text: str) -> discord.Embed:
    e = discord.Embed(
        title="Eneba Payment (5/5)",
        description=f"Use this Eneba link:\n{link_text}\nThen reply with proof in this ticket.",
        color=discord.Color.from_str("#2b6cff"),
    )
    e.set_footer(text="Press Done when completed")
    return e

def g2a_embed() -> discord.Embed:
    e = discord.Embed(
        title="G2A Gift Card (5/5)",
        description="Enter your **G2A gift card code** in the modal. A staff member will verify it.",
        color=discord.Color.from_str("#2b6cff"),
    )
    e.set_footer(text="Submit code, then press Done")
    return e

def giftcard_embed() -> discord.Embed:
    e = discord.Embed(
        title="Giftcard (5/5)",
        description="Enter your **gift card code** in the modal. A staff member will verify it.",
        color=discord.Color.from_str("#2b6cff"),
    )
    e.set_footer(text="Submit code, then press Done")
    return e

# ====== ADMIN COMMANDS ======
@bot.tree.command(description="Set only the LOGO and BANNER images for the panel.")
@app_commands.describe(
    logo="Logo URL (square). Default is the official white Robux mark.",
    banner="Banner URL (wide). Optional."
)
@app_commands.checks.has_permissions(manage_guild=True)
async def setbranding(interaction: discord.Interaction, logo: Optional[str] = None, banner: Optional[str] = None):
    bot.save_branding(interaction.guild.id, logo, banner)
    await interaction.response.send_message("✅ Branding updated (logo/banner).", ephemeral=True)

@bot.tree.command(description="Add an Eneba payment link (per guild).")
@app_commands.describe(url="Eneba link")
@app_commands.checks.has_permissions(manage_guild=True)
async def addlink(interaction: discord.Interaction, url: str):
    lid = bot.add_link(interaction.guild.id, "eneba", url)
    await interaction.response.send_message(f"✅ Added Eneba link with ID **{lid}**.", ephemeral=True)

@bot.tree.command(description="Remove any saved link by ID.")
@app_commands.checks.has_permissions(manage_guild=True)
async def removelink(interaction: discord.Interaction, id: int):
    ok = bot.remove_link(interaction.guild.id, id)
    if ok:
        await interaction.response.send_message(f"🗑️ Removed link **{id}**.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Link not found for this guild.", ephemeral=True)

@bot.tree.command(description="List saved Eneba links (per guild).")
@app_commands.checks.has_permissions(manage_guild=True)
async def listlinks(interaction: discord.Interaction):
    grouped = bot.list_links_grouped(interaction.guild.id)
    items = grouped.get("eneba", [])
    parts = ["**ENEBA**"]
    if items:
        for it in items:
            parts.append(f"• ID `{it['id']}` — {it['url']}")
    else:
        parts.append("_none_")
    await interaction.response.send_message("\n".join(parts), ephemeral=True)

# --- Crypto wallet commands (B selected) ---
@bot.tree.command(description="Set BTC wallet address for Crypto payments.")
@app_commands.checks.has_permissions(manage_guild=True)
async def setbtc(interaction: discord.Interaction, address: str):
    bot.set_wallet(interaction.guild.id, "btc", address.strip())
    await interaction.response.send_message("✅ BTC wallet saved.", ephemeral=True)

@bot.tree.command(description="Set LTC wallet address for Crypto payments.")
@app_commands.checks.has_permissions(manage_guild=True)
async def setltc(interaction: discord.Interaction, address: str):
    bot.set_wallet(interaction.guild.id, "ltc", address.strip())
    await interaction.response.send_message("✅ LTC wallet saved.", ephemeral=True)

@bot.tree.command(description="Set ETH wallet address for Crypto payments.")
@app_commands.checks.has_permissions(manage_guild=True)
async def seteth(interaction: discord.Interaction, address: str):
    bot.set_wallet(interaction.guild.id, "eth", address.strip())
    await interaction.response.send_message("✅ ETH wallet saved.", ephemeral=True)

@bot.tree.command(description="Set USDT wallet address for Crypto payments.")
@app_commands.describe(address="Include network if needed, e.g., TRC20/ERC20")
@app_commands.checks.has_permissions(manage_guild=True)
async def setusdt(interaction: discord.Interaction, address: str):
    bot.set_wallet(interaction.guild.id, "usdt", address.strip())
    await interaction.response.send_message("✅ USDT wallet saved.", ephemeral=True)

@bot.tree.command(description="Show configured crypto wallets (ephemeral).")
@app_commands.checks.has_permissions(manage_guild=True)
async def listwallets(interaction: discord.Interaction):
    w = bot.get_wallets(interaction.guild.id)
    lines = []
    for k, label in (("btc","BTC"),("ltc","LTC"),("eth","ETH"),("usdt","USDT")):
        lines.append(f"**{label}:** {('`'+w[k]+'`') if w.get(k) else '_none_'}")
    await interaction.response.send_message("\n".join(lines), ephemeral=True)

# ====== PANEL (embed as 1 msg, button as 2nd) ======
class PurchaseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.primary, custom_id="purchase_btn")
    async def purchase(self, interaction: discord.Interaction, _):
        parent = interaction.channel
        # Create private ticket thread (fallback to public if needed)
        try:
            thread = await parent.create_thread(
                name=f"Order — {interaction.user.display_name}",
                auto_archive_duration=10080,  # 7 days
                type=discord.ChannelType.private_thread,
                invitable=False,
            )
        except Exception:
            thread = await parent.create_thread(
                name=f"Order — {interaction.user.display_name}",
                auto_archive_duration=10080,
            )

        try:
            await thread.add_user(interaction.user)
        except Exception:
            pass

        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role:
            try:
                await thread.send(f"{staff_role.mention} New order started by {interaction.user.mention}")
            except Exception:
                pass

        await interaction.response.send_message(f"🧵 Created thread: {thread.mention}", ephemeral=True)

        note_msg = await thread.send(embed=mk_note_embed(), view=CloseThreadView())
        try:
            await note_msg.pin()
        except Exception:
            pass

        await thread.send(embed=step1_embed(), view=StartYesNoView(interaction.user.id))

@bot.tree.command(description="Post the Automated Purchase panel (embed + button).")
@app_commands.checks.has_permissions(manage_guild=True)
async def post_autoorder(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True, thinking=False)
    branding = bot.load_branding(interaction.guild.id)

    # 1) Embed (fixed text, editable images)
    await interaction.channel.send(embed=mk_panel_embed(branding, interaction.guild))
    # 2) Button
    await interaction.channel.send(view=PurchaseButton())

    await interaction.followup.send("✅ Posted.", ephemeral=True)

# ====== WIZARD UI ======
class CloseThreadView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.secondary, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, _):
        if isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("Closing ticket...", ephemeral=True)
            try:
                await interaction.channel.edit(archived=True, locked=True)
            except Exception:
                pass
        else:
            await interaction.response.send_message("Use inside a ticket thread.", ephemeral=True)

class StartYesNoView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your order.", ephemeral=True)
            return
        await interaction.response.send_message(embed=step2_embed(), view=AmountView(self.user_id))

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, _):
        await interaction.response.send_message("No problem. Use the panel anytime to start.", ephemeral=True)

class AmountModal(discord.ui.Modal, title="Enter Robux amount"):
    amount = discord.ui.TextInput(label="Amount", placeholder="10000", required=True, max_length=12)

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amt = int(str(self.amount).replace(",", "").strip())
            if amt < 10000:
                raise ValueError
        except Exception:
            await interaction.response.send_message("Invalid amount. Minimum 10,000.", ephemeral=True)
            return
        await interaction.response.send_message(embed=step3_embed(amt), view=ConfirmAmountView(self.user_id, amt))

class AmountView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id

    @discord.ui.button(label="Enter Amount", style=discord.ButtonStyle.primary)
    async def enter(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your order.", ephemeral=True)
            return
        await interaction.response.send_modal(AmountModal(self.user_id))

class ConfirmAmountView(discord.ui.View):
    def __init__(self, user_id: int, amount: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.amount = amount

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your order.", ephemeral=True)
            return
        await interaction.response.send_message(embed=step4_embed(), view=PayTypeView(self.user_id, self.amount))

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, _):
        await interaction.response.send_message("Okay, start again with the button.", ephemeral=True)

# ---- Payment selection & flows ----
class PayTypeSelect(discord.ui.Select):
    def __init__(self):
        # Plain text labels (no logos). You can add simple emojis if you want.
        options = [
            discord.SelectOption(label="Eneba", value="eneba"),
            discord.SelectOption(label="G2A (Gift Card Code)", value="g2a"),
            discord.SelectOption(label="Crypto (BTC/LTC/ETH/USDT)", value="crypto"),
            discord.SelectOption(label="Giftcard (Generic Code)", value="giftcard"),
        ]
        super().__init__(placeholder="Select your payment method", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        view: "PayTypeView" = self.view  # type: ignore
        if interaction.user.id != view.user_id:
            await interaction.response.send_message("This is not your order.", ephemeral=True)
            return

        choice = self.values[0]
        if choice == "eneba":
            links = bot.links_for_type(interaction.guild.id, "eneba")
            if not links:
                await interaction.response.send_message("No **Eneba** links configured yet.", ephemeral=True)
                return
            await interaction.response.send_message("Pick an Eneba link:", view=EnebaChoiceView(view.user_id, view.amount, links), ephemeral=True)

        elif choice == "crypto":
            wallets = bot.get_wallets(interaction.guild.id)
            await interaction.response.send_message(embed=crypto_embed(wallets), view=FinishView(view.user_id, view.amount, "crypto", link_used="wallets shown"), ephemeral=True)

        elif choice == "g2a":
            await interaction.response.send_message(embed=g2a_embed(), ephemeral=True)
            await interaction.followup.send("Enter your G2A gift card code:", ephemeral=True)
            await interaction.response.send_modal(GiftCodeModal(view.user_id, view.amount, "g2a"))

        elif choice == "giftcard":
            await interaction.response.send_message(embed=giftcard_embed(), ephemeral=True)
            await interaction.followup.send("Enter your gift card code:", ephemeral=True)
            await interaction.response.send_modal(GiftCodeModal(view.user_id, view.amount, "giftcard"))

class PayTypeView(discord.ui.View):
    def __init__(self, user_id: int, amount: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.amount = amount
        self.add_item(PayTypeSelect())

class EnebaChoiceSelect(discord.ui.Select):
    def __init__(self, links: List[dict]):
        options = [discord.SelectOption(label=link["url"][:100], value=str(link["id"])) for link in links[:25]]
        super().__init__(placeholder="Select an Eneba link", min_values=1, max_values=1, options=options)
        self.links = links

    async def callback(self, interaction: discord.Interaction):
        view: "EnebaChoiceView" = self.view  # type: ignore
        if interaction.user.id != view.user_id:
            await interaction.response.send_message("This is not your order.", ephemeral=True)
            return
        chosen_id = int(self.values[0])
        match = next((x for x in self.links if x["id"] == chosen_id), None)
        if not match:
            await interaction.response.send_message("Not found. Try again.", ephemeral=True)
            return
        await interaction.response.send_message(
            embed=eneba_embed(match["url"]),
            view=FinishView(view.user_id, view.amount, "eneba", link_used=match["url"]),
            ephemeral=True,
        )

class EnebaChoiceView(discord.ui.View):
    def __init__(self, user_id: int, amount: int, links: List[dict]):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.amount = amount
        self.add_item(EnebaChoiceSelect(links))

class GiftCodeModal(discord.ui.Modal, title="Enter Gift Card Code"):
    code = discord.ui.TextInput(label="Code", placeholder="XXXX-XXXX-XXXX-XXXX", required=True, max_length=64)

    def __init__(self, user_id: int, amount: int, pay_type: str):
        super().__init__()
        self.user_id = user_id
        self.amount = amount
        self.pay_type = pay_type  # "g2a" or "giftcard"

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your order.", ephemeral=True)
            return
        code_str = str(self.code).strip()
        masked = code_str[:4] + "…" + code_str[-4:] if len(code_str) >= 8 else "submitted"
        # Log immediately with masked code
        bot.log_order(interaction.guild.id, interaction.user.id, self.amount, self.pay_type, f"code:{masked}")
        await interaction.response.send_message(f"✅ Code received (`{masked}`). A staff member will verify it.", ephemeral=True)
        try:
            await interaction.channel.send(
                f"🔐 Gift code received from {interaction.user.mention} for **{self.pay_type.upper()}**.\n"
                f"Amount: **{self.amount:,}** Robux\n"
                f"Masked code: `{masked}`"
            )
        except Exception:
            pass
        # Offer to finish
        await interaction.followup.send(view=FinishView(self.user_id, self.amount, self.pay_type, f"code:{masked}"), ephemeral=True)

class FinishView(discord.ui.View):
    def __init__(self, user_id: int, amount: int, pay_type: str, link_used: str):
        super().__init__(timeout=600)
        self.user_id = user_id
        self.amount = amount
        self.pay_type = pay_type
        self.link_used = link_used

    @discord.ui.button(label="Done", style=discord.ButtonStyle.success)
    async def done(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your order.", ephemeral=True)
            return
        # If not already logged (e.g., crypto/eneba path already logs on Done; code modal logged earlier)
        if self.pay_type in ("crypto", "eneba") and interaction.response.is_done() is False:
            bot.log_order(interaction.guild.id, interaction.user.id, self.amount, self.pay_type, self.link_used)
        try:
            await interaction.channel.send(
                f"✅ Order logged for {interaction.user.mention}\n"
                f"**Amount:** {self.amount:,} Robux\n"
                f"**Payment:** {self.pay_type}\n"
                f"**Details:** {self.link_used}"
            )
            await interaction.response.send_message("Closing ticket. Thank you!", ephemeral=True)
            await interaction.channel.edit(archived=True, locked=True)
        except Exception:
            await interaction.response.send_message("Logged. Could not lock thread automatically.", ephemeral=True)

# ====== EVENTS / RUN ======
@bot.event
async def on_ready():
    print(f"[READY] Logged in as {bot.user} (ID: {bot.user.id})")

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
