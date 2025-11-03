#!/usr/bin/env python3
# Robux Town / Robux World — Auto Order Bot (Pella-ready, button wizard)
# - /post_autoorder: posts an info embed (title, bullets, banner, logo) + "Purchase Robux" button
# - Button opens thread and runs a 5-step wizard using buttons/selects/modals (no slash steps)
# - Admin management:
#     /addlink type:<eneba|g2a|crypto|giftcard> url:<...>
#     /removelink id:<int>
#     /listlinks
#     /setbranding logo:<url> banner:<url> note:<text>
# - Links + Branding stored per guild in SQLite
# - Orders logged to DB and thread archived/locked at end
# - message_content intent enabled
#
# Env:
#   BOT_TOKEN  (required)
#   DB_PATH    (optional, default: robux_autoorder.db)

import os
import sqlite3
from typing import Optional, Literal, List, Dict
from datetime import datetime, timezone

import discord
from discord import app_commands
print("discord module file:", getattr(discord, "__file__", "unknown"))
print("discord.py version:", getattr(discord, "__version__", "unknown"))
assert hasattr(discord, "ext"), "discord.ext missing → wrong module shadowing"

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("Missing BOT_TOKEN")

DB_PATH = os.getenv("DB_PATH", "robux_autoorder.db")
PAYMENT_TYPES = ("eneba", "g2a", "crypto", "giftcard")

# ---------- Intents (message content enabled) ----------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class Bot(commands.Bot):
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
          id        INTEGER PRIMARY KEY AUTOINCREMENT,
          guild_id  INTEGER NOT NULL,
          type      TEXT    NOT NULL,
          url       TEXT    NOT NULL,
          created_at TEXT   NOT NULL
        );

        CREATE TABLE IF NOT EXISTS branding (
          guild_id   INTEGER PRIMARY KEY,
          logo_url   TEXT,
          banner_url TEXT,
          note_text  TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
          id        INTEGER PRIMARY KEY AUTOINCREMENT,
          guild_id  INTEGER NOT NULL,
          user_id   INTEGER NOT NULL,
          amount    INTEGER NOT NULL,
          pay_type  TEXT    NOT NULL,
          link_used TEXT,
          created_at TEXT   NOT NULL
        );
        """)
        self.db.commit()
        print(f"[DB] Ready at {DB_PATH}")

    # ---------- DB helpers ----------
    def add_link(self, guild_id: int, t: str, url: str) -> int:
        if t not in PAYMENT_TYPES:
            raise ValueError("Invalid type")
        cur = self.db.cursor()
        cur.execute(
            "INSERT INTO links (guild_id, type, url, created_at) VALUES (?, ?, ?, ?)",
            (guild_id, t, url, datetime.now(timezone.utc).isoformat())
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
        grouped = {t: [] for t in PAYMENT_TYPES}
        for row in cur.fetchall():
            grouped[row["type"]].append({"id": row["id"], "url": row["url"]})
        return grouped

    def get_links_by_type(self, guild_id: int, t: str) -> List[dict]:
        cur = self.db.cursor()
        cur.execute("SELECT id, url FROM links WHERE guild_id=? AND type=? ORDER BY id", (guild_id, t))
        return [{"id": r["id"], "url": r["url"]} for r in cur.fetchall()]

    def save_branding(self, guild_id: int, logo: Optional[str], banner: Optional[str], note: Optional[str]):
        cur = self.db.cursor()
        cur.execute("INSERT OR IGNORE INTO branding(guild_id, logo_url, banner_url, note_text) VALUES (?, NULL, NULL, NULL)", (guild_id,))
        if logo is not None:
            cur.execute("UPDATE branding SET logo_url=? WHERE guild_id=?", (logo, guild_id))
        if banner is not None:
            cur.execute("UPDATE branding SET banner_url=? WHERE guild_id=?", (banner, guild_id))
        if note is not None:
            cur.execute("UPDATE branding SET note_text=? WHERE guild_id=?", (note, guild_id))
        self.db.commit()

    def load_branding(self, guild_id: int) -> dict:
        cur = self.db.cursor()
        cur.execute("SELECT logo_url, banner_url, note_text FROM branding WHERE guild_id=?", (guild_id,))
        row = cur.fetchone()
        return dict(row) if row else {"logo_url": None, "banner_url": None, "note_text": None}

    def log_order(self, guild_id: int, user_id: int, amount: int, pay_type: str, link_used: str):
        cur = self.db.cursor()
        cur.execute(
            "INSERT INTO orders (guild_id, user_id, amount, pay_type, link_used, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (guild_id, user_id, amount, pay_type, link_used, datetime.now(timezone.utc).isoformat())
        )
        self.db.commit()


bot = Bot()

# ---------- Admin Commands ----------

@bot.tree.command(description="Add a payment link (per guild).")
@discord.app_commands.describe(type="eneba, g2a, crypto, giftcard", url="Link or address/text")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def addlink(interaction: discord.Interaction, type: str, url: str):
    t = type.lower().strip()
    if t not in PAYMENT_TYPES:
        await interaction.response.send_message(f"Type must be one of: {', '.join(PAYMENT_TYPES)}", ephemeral=True)
        return
    lid = bot.add_link(interaction.guild.id, t, url)
    await interaction.response.send_message(f"✅ Added **{t}** link with ID **{lid}**.", ephemeral=True)

@bot.tree.command(description="Remove link by ID (per guild).")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def removelink(interaction: discord.Interaction, id: int):
    ok = bot.remove_link(interaction.guild.id, id)
    if ok:
        await interaction.response.send_message(f"🗑️ Removed link **{id}**.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Link not found for this guild.", ephemeral=True)

@bot.tree.command(description="List saved links (per guild).")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def listlinks(interaction: discord.Interaction):
    grouped = bot.list_links_grouped(interaction.guild.id)
    lines = []
    for t in PAYMENT_TYPES:
        items = grouped.get(t, [])
        lines.append(f"**{t.upper()}**")
        if items:
            for it in items:
                lines.append(f"• ID `{it['id']}` — {it['url']}")
        else:
            lines.append("_none_")
    await interaction.response.send_message("\n".join(lines), ephemeral=True)

@bot.tree.command(description="Set branding (logo/banner/note) for /post_autoorder.")
@discord.app_commands.describe(logo="Logo URL (square)", banner="Banner URL (wide)", note="Pinned note text shown in thread")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def setbranding(interaction: discord.Interaction, logo: Optional[str] = None, banner: Optional[str] = None, note: Optional[str] = None):
    bot.save_branding(interaction.guild.id, logo, banner, note)
    await interaction.response.send_message("✅ Branding updated.", ephemeral=True)

# ---------- Post auto-order panel ----------

class PurchaseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.primary, custom_id="purchase_btn")
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        parent = interaction.channel
        thread = await parent.create_thread(name=f"Order — {interaction.user.display_name}", auto_archive_duration=10080)  # 7d
        await interaction.response.send_message(f"🧵 Created thread: {thread.mention}", ephemeral=True)

        # Pinned note (like screenshot)
        branding = bot.load_branding(interaction.guild.id)
        note_text = branding.get("note_text") or (
            "Please make sure all conversations related to the deal are done within this ticket. "
            "Our staff will never DM you regarding active or completed deals."
        )
        note_embed = discord.Embed(title="⚠️ Please Note", description=note_text, color=discord.Color.orange())
        note_msg = await thread.send(embed=note_embed, view=CloseThreadView())
        try:
            await note_msg.pin()
        except Exception:
            pass

        # Step 1
        await thread.send(embed=step1_embed(), view=StartYesNoView(interaction.user.id))

def header_embed(branding: dict) -> discord.Embed:
    em = discord.Embed(
        title="🛒 Automated Purchase",
        description=(
            "This bot streamlines buying **Robux**.\n"
            "• **Instant Delivery** — as soon as payment is confirmed\n"
            "• **Secure** — all deals handled in-thread by staff\n"
            "• **Multiple Payment Options** — Crypto, Eneba, G2A, Giftcards\n"
        ),
        color=discord.Color.blurple(),
    )
    if branding.get("logo_url"):
        em.set_thumbnail(url=branding["logo_url"])
    if branding.get("banner_url"):
        em.set_image(url=branding["banner_url"])
    return em

@bot.tree.command(description="Post the 'Automated Purchase' panel with button.")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def post_autoorder(interaction: discord.Interaction):
    branding = bot.load_branding(interaction.guild.id)
    em = header_embed(branding)
    view = PurchaseButton()
    await interaction.response.send_message(embed=em, view=view)

# ---------- Wizard UI ----------

def step1_embed() -> discord.Embed:
    e = discord.Embed(
        title="Would you like to start buying robux? (1/5)",
        description="Please click **Yes** if you'd like to start purchasing your Robux.",
        color=discord.Color.blurple()
    )
    return e

def step2_embed() -> discord.Embed:
    e = discord.Embed(
        title="How much robux would you like to buy? (2/5)",
        description="Please specify the amount of Robux you would like to purchase:\n**Example:** `10,000`\n**Minimum:** `10,000` Robux",
        color=discord.Color.blurple()
    )
    return e

def step3_embed(amount: int, rate_per_1k: float = 1.0) -> discord.Embed:
    usd = (amount / 1000.0) * rate_per_1k
    e = discord.Embed(
        title="Would you like to purchase this amount of Robux? (3/5)",
        description=(
            f"Are you sure you want to purchase **{amount:,}** Robux:\n"
            f"Current Rate: **${rate_per_1k:.2f} per 1,000 Robux**\n"
            f"Price in USD: **${usd:.2f}**"
        ),
        color=discord.Color.blurple()
    )
    return e

def step4_embed() -> discord.Embed:
    e = discord.Embed(
        title="Please select your preferred payment method (4/5)",
        description="Choose a payment method from the dropdown below.",
        color=discord.Color.blurple()
    )
    return e

def step5_embed(pay_type: str, link_text: str) -> discord.Embed:
    title_map = {
        "eneba": "Eneba Payment (5/5)",
        "g2a": "G2A Payment (5/5)",
        "crypto": "Crypto Payment (5/5)",
        "giftcard": "Giftcard Instructions (5/5)",
    }
    desc_map = {
        "eneba": f"Please use the selected Eneba link:\n{link_text}\nAfter payment, reply here with proof.",
        "g2a": f"Please use the selected G2A link:\n{link_text}\nAfter payment, reply here with proof.",
        "crypto": f"Please pay to this address / link:\n{link_text}\nInclude TXID and network.",
        "giftcard": f"Please purchase the required gift card and send the code here:\n{link_text}\nOur staff will verify.",
    }
    e = discord.Embed(
        title=title_map.get(pay_type, "Payment (5/5)"),
        description=desc_map.get(pay_type, link_text),
        color=discord.Color.blurple()
    )
    return e

class CloseThreadView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.secondary, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, b: discord.ui.Button):
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
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your order.", ephemeral=True)
            return
        await interaction.response.send_message(embed=step2_embed(), view=AmountView(self.user_id))

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("No problem. Use the button anytime to start.", ephemeral=True)

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
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
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
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your order.", ephemeral=True)
            return
        await interaction.response.send_message(embed=step4_embed(), view=PayTypeView(self.user_id, self.amount))

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Okay, start again with the button.", ephemeral=True)

class PayTypeView(discord.ui.View):
    def __init__(self, user_id: int, amount: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.amount = amount

        self.add_item(discord.ui.Select(
            placeholder="Select your payment method",
            min_values=1, max_values=1,
            options=[
                discord.SelectOption(label="Eneba", value="eneba"),
                discord.SelectOption(label="G2A", value="g2a"),
                discord.SelectOption(label="Crypto", value="crypto"),
                discord.SelectOption(label="Giftcard", value="giftcard"),
            ]
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your order.", ephemeral=True)
            return False
        return True

    @discord.ui.select()
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        pay_type = select.values[0]
        links = bot.get_links_by_type(interaction.guild.id, pay_type)
        if not links:
            await interaction.response.send_message(f"No **{pay_type}** links configured yet.", ephemeral=True)
            return

        # Build a new select for the specific links
        options = []
        for item in links[:25]:
            label = item["url"][:100]
            options.append(discord.SelectOption(label=label, value=str(item["id"])))

        v = LinkChoiceView(self.user_id, self.amount, pay_type, links, options)
        await interaction.response.send_message("Pick a link:", view=v, ephemeral=True)

class LinkChoiceView(discord.ui.View):
    def __init__(self, user_id: int, amount: int, pay_type: str, links: List[dict], options: List[discord.SelectOption]):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.amount = amount
        self.pay_type = pay_type
        self.links = links

        self.select = discord.ui.Select(placeholder=f"Select a {pay_type} option", min_values=1, max_values=1, options=options)
        self.add_item(self.select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your order.", ephemeral=True)
            return False
        return True

    @discord.ui.select()
    async def choose(self, interaction: discord.Interaction, select: discord.ui.Select):
        chosen_id = int(select.values[0])
        match = next((x for x in self.links if x["id"] == chosen_id), None)
        if not match:
            await interaction.response.send_message("Not found. Try again.", ephemeral=True)
            return
        # Show step 5 and finish
        await interaction.response.send_message(embed=step5_embed(self.pay_type, match["url"]), view=FinishView(self.user_id, self.amount, self.pay_type, match["url"]), ephemeral=True)

class FinishView(discord.ui.View):
    def __init__(self, user_id: int, amount: int, pay_type: str, link_used: str):
        super().__init__(timeout=600)
        self.user_id = user_id
        self.amount = amount
        self.pay_type = pay_type
        self.link_used = link_used

    @discord.ui.button(label="Done", style=discord.ButtonStyle.success)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your order.", ephemeral=True)
            return
        # Log + close
        bot.log_order(interaction.guild.id, interaction.user.id, self.amount, self.pay_type, self.link_used)
        try:
            await interaction.channel.send(
                f"✅ Order logged for {interaction.user.mention}\nAmount: **{self.amount:,}** Robux\nPayment: **{self.pay_type}**\nLink: {self.link_used}"
            )
            await interaction.response.send_message("Closing ticket. Thank you!", ephemeral=True)
            await interaction.channel.edit(archived=True, locked=True)
        except Exception:
            await interaction.response.send_message("Logged. Could not lock thread automatically.", ephemeral=True)


@bot.event
async def on_ready():
    print(f"[READY] Logged in as {bot.user} (ID: {bot.user.id})")

def main():
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    main()
