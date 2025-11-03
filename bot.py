#!/usr/bin/env python3
# Robux Town — Auto Order + Auto Fake Vouch Bot
#
# Highlights
# - Reads & hot-reloads config from a pinned JSON message in CONFIG_CHANNEL_ID.
# - Per-coin + per-method emojis: btc, ltc, eth, sol, eneba, g2a, giftcard, crypto.
# - Auto fake vouch posts to configured vouch channel at random intervals (default 10–30h).
# - Branding images: logo, auto-order banner (panel), normal banner (vouch footer).
# - Commands:
#     /post_autoorder   -> posts panel with your branding and emojis
#     /fakevouchnow     -> post one fake vouch immediately
#     /saveconfig       -> write current config back to the config channel (refresh pin)
#     /setchannels      -> set vouch/log channels into config
#
# Env:
#   BOT_TOKEN (required)
#   DB_PATH   (optional, default: /data/robux_autoorder.db)  # only used for future growth
#
# Notes:
# - Config lives as JSON in a pinned message in CONFIG_CHANNEL_ID. Editing that JSON live
#   will be detected and applied automatically without restarts.
# - A copy of the config is persisted to /data/rt_config.json so the bot can boot even if
#   it can't read the channel initially.

import os
import json
import asyncio
import random
from typing import Optional, Dict, Any
from datetime import datetime, timezone

import discord
from discord.ext import commands
from discord import app_commands

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("Missing BOT_TOKEN")

DATA_DIR = "/data"
os.makedirs(DATA_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(DATA_DIR, "rt_config.json")

# Your config channel (where pinned JSON lives)
CONFIG_CHANNEL_ID = 1434779226279514186

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True

# Defaults that will be written if no config exists yet
DEFAULT_CONFIG: Dict[str, Any] = {
    "branding": {
        "logo_url": "https://i.ibb.co/FkDYg7gc/robux-town.png",
        "auto_banner_url": "https://i.ibb.co/ZRzkHH9N/robux-town-automatic-order.png",
        "vouch_footer_url": "https://i.ibb.co/5XbkKq64/robux-town-banner.png",
    },
    "emojis": {
        "btc": "₿",
        "ltc": "🟦",
        "eth": "💠",
        "sol": "🔷",
        "eneba": "🅴",
        "g2a": "💳",
        "giftcard": "🎟️",
        "crypto": "🪙",
    },
    "vouch": {
        "enabled": True,
        "min_hours": 10,
        "max_hours": 30,
        "vouch_channel_id": None
    },
    "logs": {
        "log_channel_id": None
    }
}

PANEL_TEXT = (
    "This bot streamlines buying **Robux**.\n"
    "• **Instant Delivery** — as soon as payment is confirmed\n"
    "• **Secure** — all deals handled in-thread by staff\n"
    "• **Multiple Payment Options** — Crypto, Eneba, G2A, Giftcards\n"
)

def fenced_json(d: Dict[str, Any]) -> str:
    return "RobuxTown Config — edit the JSON below and save.\n```json\n" + json.dumps(d, ensure_ascii=False, indent=2) + "\n```"

def extract_json_from_message(content: str) -> Optional[Dict[str, Any]]:
    # Extract JSON from a ```json ...``` block or fallback to whole content
    if "```" in content:
        parts = content.split("```")
        # look for a block that starts with 'json\n'
        for i in range(len(parts)-1):
            if parts[i].lower().strip().endswith("json"):
                try:
                    return json.loads(parts[i+1])
                except Exception:
                    pass
    # fallback
    try:
        return json.loads(content)
    except Exception:
        return None

class RTBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=INTENTS)
        self.config: Dict[str, Any] = {}
        self.cfg_msg_id: Optional[int] = None
        self.vouch_next_ts: Dict[int, float] = {}  # per-guild scheduling
        self.vouch_task: Optional[asyncio.Task] = None

    # --------------- CONFIG ---------------
    async def load_config_boot(self):
        # First try file cache
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                print("[CONFIG] Loaded from file cache.")
            except Exception as e:
                print(f"[CONFIG] Failed reading cache: {e}")
        # Then try channel pin
        await self.refresh_config_from_channel()

        # If still empty, write defaults
        if not self.config:
            self.config = DEFAULT_CONFIG.copy()
            await self.write_config_to_channel()
            await self.pin_and_remember()

        # Always persist to file
        self.persist_config()

    def persist_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CONFIG] Persist error: {e}")

    async def get_config_channel(self) -> Optional[discord.TextChannel]:
        try:
            ch = self.get_channel(CONFIG_CHANNEL_ID) or await self.fetch_channel(CONFIG_CHANNEL_ID)
            if isinstance(ch, discord.TextChannel):
                return ch
        except Exception as e:
            print(f"[CONFIG] Cannot access config channel {CONFIG_CHANNEL_ID}: {e}")
        return None

    async def refresh_config_from_channel(self):
        ch = await self.get_config_channel()
        if not ch:
            return
        try:
            pins = await ch.pins()
            # Prefer bot-authored latest pin containing JSON
            for m in pins:
                data = extract_json_from_message(m.content)
                if data:
                    self.config = data
                    self.cfg_msg_id = m.id
                    self.persist_config()
                    print("[CONFIG] Loaded from pinned message.")
                    return
        except Exception as e:
            print(f"[CONFIG] Failed to read pins: {e}")

    async def write_config_to_channel(self):
        ch = await self.get_config_channel()
        if not ch:
            print("[CONFIG] No access to config channel to write.")
            return
        try:
            msg = await ch.send(fenced_json(self.config))
            self.cfg_msg_id = msg.id
            print("[CONFIG] Wrote config message.")
        except Exception as e:
            print(f"[CONFIG] Write failed: {e}")

    async def pin_and_remember(self):
        ch = await self.get_config_channel()
        if not ch or not self.cfg_msg_id:
            return
        try:
            msg = await ch.fetch_message(self.cfg_msg_id)
            await msg.pin()
            # Unpin older config pins (keep most recent)
            pins = await ch.pins()
            for m in pins:
                if m.id != self.cfg_msg_id and extract_json_from_message(m.content):
                    try:
                        await m.unpin()
                    except Exception:
                        pass
            print("[CONFIG] Pinned config message.")
        except Exception as e:
            print(f"[CONFIG] Pin failed: {e}")

    async def update_config_from_message(self, message: discord.Message):
        data = extract_json_from_message(message.content or "")
        if not data:
            return
        self.config = data
        self.cfg_msg_id = message.id
        self.persist_config()
        print("[CONFIG] Hot-reloaded from edit/new message.")

    # --------------- AUTO VOUCH ---------------
    async def auto_vouch_loop(self):
        await self.wait_until_ready()
        print("[VOUCH] loop started")
        while not self.is_closed():
            now = datetime.now(timezone.utc).timestamp()
            cfg_v = self.config.get("vouch", {})
            if cfg_v.get("enabled"):
                vch_id = cfg_v.get("vouch_channel_id")
                if vch_id:
                    # schedule per guild not critical here; single channel used globally
                    next_ts = self.vouch_next_ts.get(vch_id, 0)
                    if now >= next_ts:
                        await self.post_one_fake_vouch()
                        min_h = int(cfg_v.get("min_hours", 10))
                        max_h = int(cfg_v.get("max_hours", 30))
                        wait_h = max(min_h, min(max_h, random.randint(min_h, max_h)))
                        self.vouch_next_ts[vch_id] = now + wait_h * 3600
            await asyncio.sleep(300)

    def _emoji(self, key: str, default: str) -> str:
        return str(self.config.get("emojis", {}).get(key, default))

    async def post_one_fake_vouch(self):
        cfg_v = self.config.get("vouch", {})
        vch_id = cfg_v.get("vouch_channel_id")
        if not vch_id:
            return
        ch = self.get_channel(vch_id) or await self.fetch_channel(vch_id)
        if not isinstance(ch, (discord.TextChannel, discord.Thread)):
            return

        # Randomized payload
        usd = round(random.uniform(5.0, 119.0), 2)
        robux = int(usd) * 1000
        stars = random.choices([5,4,3,2,1], weights=[60,25,10,4,1], k=1)[0]
        order_id = str(random.randrange(10**15, 10**18))

        # Build embed using emojis
        e = discord.Embed(color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
        e.title = f"{self._emoji('check','✅')} New Completed Order"
        e.add_field(name=f"{self._emoji('user_lbl','👤 User')}", value=f"{self._emoji('user_val','🔒 Hidden')}", inline=True)
        # For the fake vouch, show 'Payment Method' label and example (use generic crypto emoji by default)
        e.add_field(name=f"{self._emoji('pay_lbl',':PAYMENT_SUPPORT: Payment Method')}", value=f"{self._emoji('crypto','🪙')} Crypto", inline=True)
        e.add_field(name=f"{self._emoji('robux_lbl',':Robux~1: Robux Purchased')}", value=f"{robux:,} Robux", inline=False)
        e.add_field(name=f"{self._emoji('usd_lbl','💶 USD Spent')}", value=f"${usd:.2f}", inline=True)
        stars_text = "★"*stars + "☆"*(5-stars) + f" ({stars}/5)"
        e.add_field(name=f"{self._emoji('rating_lbl','⭐ Rating')}", value=stars_text, inline=True)
        e.add_field(name=f"{self._emoji('order_lbl','🧾 Order ID')}", value=order_id, inline=False)

        footer_img = self.config.get("branding", {}).get("vouch_footer_url")
        if footer_img:
            e.set_image(url=footer_img)

        try:
            await ch.send(embed=e)
            print(f"[VOUCH] posted in #{vch_id}")
        except Exception as ex:
            print(f"[VOUCH] failed to post: {ex}")

    # --------------- Lifecycle ---------------
    async def setup_hook(self):
        await self.load_config_boot()
        await self.tree.sync()
        if not self.vouch_task:
            self.vouch_task = asyncio.create_task(self.auto_vouch_loop())
        print("[SYNC] commands synced")

    async def on_ready(self):
        print(f"[READY] Logged in as {self.user}")

    async def on_message(self, message: discord.Message):
        await self.process_commands(message)
        if message.channel.id == CONFIG_CHANNEL_ID and not message.author.bot:
            await self.update_config_from_message(message)

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.channel.id == CONFIG_CHANNEL_ID and not after.author.bot:
            await self.update_config_from_message(after)


bot = RTBot()

# --------------- Slash Commands ---------------
@bot.tree.command(description="Post the Automated Purchase panel.")
@app_commands.checks.has_permissions(manage_guild=True)
async def post_autoorder(interaction: discord.Interaction):
    cfg = bot.config
    brand = cfg.get("branding", {})
    em = discord.Embed(
        title="🛒 Automated Purchase",
        description=PANEL_TEXT,
        color=discord.Color.blurple(),
    )
    if brand.get("logo_url"):
        em.set_thumbnail(url=brand["logo_url"])
    if brand.get("auto_banner_url"):
        em.set_image(url=brand["auto_banner_url"])

    class PurchaseButton(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.primary, custom_id="purchase_btn")
        async def purchase(self, i: discord.Interaction, b: discord.ui.Button):
            await i.response.send_message("A staff member will assist you shortly in this thread.", ephemeral=True)
            parent = i.channel
            try:
                th = await parent.create_thread(
                    name=f"Order — {i.user.display_name}", auto_archive_duration=10080
                )
                await th.send("Welcome! Please state your desired Robux amount and preferred payment method.")
            except Exception:
                pass

    await interaction.response.send_message(embed=em, view=PurchaseButton())


@bot.tree.command(description="Post one fake vouch now (uses current config).")
@app_commands.checks.has_permissions(manage_guild=True)
async def fakevouchnow(interaction: discord.Interaction):
    await bot.post_one_fake_vouch()
    await interaction.response.send_message("✅ Posted one fake vouch.", ephemeral=True)


@bot.tree.command(description="Save current config back to the config channel (pins latest).")
@app_commands.checks.has_permissions(manage_guild=True)
async def saveconfig(interaction: discord.Interaction):
    await bot.write_config_to_channel()
    await bot.pin_and_remember()
    await interaction.response.send_message("✅ Config written & pinned.", ephemeral=True)


@bot.tree.command(description="Set channels inside config (no restart needed).")
@app_commands.checks.has_permissions(manage_guild=True)
async def setchannels(
    interaction: discord.Interaction,
    vouch_channel: Optional[discord.TextChannel] = None,
    log_channel: Optional[discord.TextChannel] = None,
):
    cfg = bot.config
    if vouch_channel:
        cfg.setdefault("vouch", {})["vouch_channel_id"] = vouch_channel.id
    if log_channel:
        cfg.setdefault("logs", {})["log_channel_id"] = log_channel.id
    bot.persist_config()
    await bot.write_config_to_channel()
    await bot.pin_and_remember()
    await interaction.response.send_message("✅ Channels saved to config.", ephemeral=True)


def main():
    bot.run(BOT_TOKEN)


if __name__ == "__main__":
    main()
