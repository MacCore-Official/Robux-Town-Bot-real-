#!/usr/bin/env python3
# Robux Town — Auto Order + Auto Fake Vouch Bot (GUI Admin Panel)
#
# New: /adminpanel → interactive GUI to edit config (branding, emojis, channels, vouch settings)
# No need to edit pinned messages anymore.
#
# Existing features:
# - Auto fake vouch posts to configured vouch channel at random intervals (default 10–30h)
# - Branding images for panel and vouch footer
# - Per-coin + per-method emojis: btc, ltc, eth, sol, eneba, g2a, giftcard, crypto
# - /post_autoorder, /fakevouchnow, /saveconfig, /setchannels
#
# Env:
#   BOT_TOKEN (required)
#
# Notes:
# - Config is persisted to /data/rt_config.json
# - If you still want a pinned config, /saveconfig writes it to CONFIG_CHANNEL_ID (optional)

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

# Optional config channel for exporting JSON (not required for GUI)
CONFIG_CHANNEL_ID = 1434779226279514186

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True

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
        "check": "✅",
        "user_lbl": "👤 User",
        "user_val": "🔒 Hidden",
        "pay_lbl": ":PAYMENT_SUPPORT: Payment Method",
        "robux_lbl": ":Robux~1: Robux Purchased",
        "usd_lbl": "💶 USD Spent",
        "rating_lbl": "⭐ Rating",
        "order_lbl": "🧾 Order ID"
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

def pretty_json(d: Dict[str, Any]) -> str:
    return json.dumps(d, ensure_ascii=False, indent=2)

def fenced_json(d: Dict[str, Any]) -> str:
    return "RobuxTown Config — edit in GUI or copy this for backup.\n```json\n" + pretty_json(d) + "\n```"

class RTBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=INTENTS)
        self.config: Dict[str, Any] = {}

        # auto vouch scheduling per vouch channel id
        self.vouch_next_ts: Dict[int, float] = {}
        self.vouch_task: Optional[asyncio.Task] = None

    # --------------- CONFIG ---------------
    def load_from_disk(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                print("[CONFIG] Loaded from disk")
            except Exception as e:
                print(f"[CONFIG] Failed reading cache: {e}")

        if not self.config:
            self.config = DEFAULT_CONFIG.copy()
            self.persist()

    def persist(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print("[CONFIG] Saved to disk")
        except Exception as e:
            print(f"[CONFIG] Persist error: {e}")

    async def write_config_to_channel(self):
        try:
            ch = self.get_channel(CONFIG_CHANNEL_ID) or await self.fetch_channel(CONFIG_CHANNEL_ID)
            if isinstance(ch, discord.TextChannel):
                await ch.send(fenced_json(self.config))
                print("[CONFIG] Exported to channel")
        except Exception as e:
            print(f"[CONFIG] Export error: {e}")

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
                    next_ts = self.vouch_next_ts.get(vch_id, 0)
                    if now >= next_ts:
                        await self.post_one_fake_vouch()
                        min_h = int(max(1, cfg_v.get("min_hours", 10)))
                        max_h = int(max(min_h, cfg_v.get("max_hours", 30)))
                        wait_h = random.randint(min_h, max_h)
                        self.vouch_next_ts[vch_id] = now + wait_h * 3600
            await asyncio.sleep(300)

    def _emoji(self, key: str, default: str) -> str:
        return str(self.config.get("emojis", {}).get(key, default))

    async def post_one_fake_vouch(self):
        cfg_v = self.config.get("vouch", {})
        vch_id = cfg_v.get("vouch_channel_id")
        if not vch_id:
            return
        channel = self.get_channel(vch_id) or await self.fetch_channel(vch_id)
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return

        usd = round(random.uniform(5.0, 119.0), 2)
        robux = int(usd) * 1000
        stars = random.choices([5,4,3,2,1], weights=[60,25,10,4,1], k=1)[0]
        order_id = str(random.randrange(10**15, 10**18))

        e = discord.Embed(color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
        e.title = f"{self._emoji('check','✅')} New Completed Order"
        e.add_field(name=f"{self._emoji('user_lbl','👤 User')}", value=f"{self._emoji('user_val','🔒 Hidden')}", inline=True)
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
            await channel.send(embed=e)
            print(f"[VOUCH] posted to {vch_id}")
        except Exception as ex:
            print(f"[VOUCH] post failed: {ex}")

    # --------------- Lifecycle ---------------
    async def setup_hook(self):
        self.load_from_disk()
        await self.tree.sync()
        if not self.vouch_task:
            self.vouch_task = asyncio.create_task(self.auto_vouch_loop())
        print("[SYNC] commands synced")

    async def on_ready(self):
        print(f"[READY] Logged in as {self.user}")


bot = RTBot()

# --------------- GUI: Admin Panel ---------------
def config_summary_embed(cfg: Dict[str, Any]) -> discord.Embed:
    brand = cfg.get("branding", {})
    v = cfg.get("vouch", {})
    emj = cfg.get("emojis", {})
    logs = cfg.get("logs", {})

    e = discord.Embed(title="⚙️ RobuxTown Admin Panel", color=discord.Color.blurple())
    e.add_field(name="Branding", value=(
        f"Logo: {brand.get('logo_url') or '—'}\n"
        f"Auto Banner: {brand.get('auto_banner_url') or '—'}\n"
        f"Vouch Footer: {brand.get('vouch_footer_url') or '—'}"
    ), inline=False)
    e.add_field(name="Vouch", value=(
        f"Enabled: {v.get('enabled')}\n"
        f"Interval: {v.get('min_hours')}-{v.get('max_hours')}h\n"
        f"Vouch Channel: {v.get('vouch_channel_id') or '—'}"
    ), inline=False)
    e.add_field(name="Logs", value=f"Log Channel: {logs.get('log_channel_id') or '—'}", inline=False)
    e.add_field(name="Emojis", value=(
        f"btc: {emj.get('btc','')}, ltc: {emj.get('ltc','')}, eth: {emj.get('eth','')}, sol: {emj.get('sol','')}\n"
        f"eneba: {emj.get('eneba','')}, g2a: {emj.get('g2a','')}, giftcard: {emj.get('giftcard','')}, crypto: {emj.get('crypto','')}"
    ), inline=False)
    if brand.get("auto_banner_url"):
        e.set_image(url=brand["auto_banner_url"])
    if brand.get("logo_url"):
        e.set_thumbnail(url=brand["logo_url"])
    return e


class BrandingModal(discord.ui.Modal, title="Branding URLs"):
    logo = discord.ui.TextInput(label="Logo URL", required=False, max_length=300)
    auto_banner = discord.ui.TextInput(label="Auto-Order Banner URL", required=False, max_length=300)
    vouch_footer = discord.ui.TextInput(label="Vouch Footer (banner) URL", required=False, max_length=300)

    def __init__(self, cfg: Dict[str, Any]):
        super().__init__()
        b = cfg.get("branding", {})
        self.logo.default = b.get("logo_url") or ""
        self.auto_banner.default = b.get("auto_banner_url") or ""
        self.vouch_footer.default = b.get("vouch_footer_url") or ""

    async def on_submit(self, interaction: discord.Interaction):
        cfg = bot.config
        cfg.setdefault("branding", {})
        if self.logo.value: cfg["branding"]["logo_url"] = str(self.logo.value).strip()
        if self.auto_banner.value: cfg["branding"]["auto_banner_url"] = str(self.auto_banner.value).strip()
        if self.vouch_footer.value: cfg["branding"]["vouch_footer_url"] = str(self.vouch_footer.value).strip()
        bot.persist()
        await interaction.response.edit_message(embed=config_summary_embed(cfg))


class CoinEmojisModal(discord.ui.Modal, title="Set Coin Emojis"):
    btc = discord.ui.TextInput(label="btc", required=False, max_length=64)
    ltc = discord.ui.TextInput(label="ltc", required=False, max_length=64)
    eth = discord.ui.TextInput(label="eth", required=False, max_length=64)
    sol = discord.ui.TextInput(label="sol", required=False, max_length=64)

    def __init__(self, cfg: Dict[str, Any]):
        super().__init__()
        e = cfg.get("emojis", {})
        for k in ("btc","ltc","eth","sol"):
            if k in e:
                getattr(self, k).default = str(e[k])

    async def on_submit(self, interaction: discord.Interaction):
        cfg = bot.config
        cfg.setdefault("emojis", {})
        for k in ("btc","ltc","eth","sol"):
            v = str(getattr(self, k).value).strip()
            if v:
                cfg["emojis"][k] = v
        bot.persist()
        await interaction.response.edit_message(embed=config_summary_embed(cfg))

class PayEmojisModal(discord.ui.Modal, title="Set Payment Emojis"):
    eneba = discord.ui.TextInput(label="eneba", required=False, max_length=64)
    g2a = discord.ui.TextInput(label="g2a", required=False, max_length=64)
    giftcard = discord.ui.TextInput(label="giftcard", required=False, max_length=64)
    crypto = discord.ui.TextInput(label="crypto", required=False, max_length=64)

    def __init__(self, cfg: Dict[str, Any]):
        super().__init__()
        e = cfg.get("emojis", {})
        for k in ("eneba","g2a","giftcard","crypto"):
            if k in e:
                getattr(self, k).default = str(e[k])

    async def on_submit(self, interaction: discord.Interaction):
        cfg = bot.config
        cfg.setdefault("emojis", {})
        for k in ("eneba","g2a","giftcard","crypto"):
            v = str(getattr(self, k).value).strip()
            if v:
                cfg["emojis"][k] = v
        bot.persist()
        await interaction.response.edit_message(embed=config_summary_embed(cfg))


class ChannelsModal(discord.ui.Modal, title="Channel IDs"):
    vouch_channel_id = discord.ui.TextInput(label="Vouch Channel ID", required=False, max_length=25)
    log_channel_id = discord.ui.TextInput(label="Log Channel ID", required=False, max_length=25)

    def __init__(self, cfg: Dict[str, Any]):
        super().__init__()
        v = cfg.get("vouch", {})
        l = cfg.get("logs", {})
        self.vouch_channel_id.default = str(v.get("vouch_channel_id") or "")
        self.log_channel_id.default = str(l.get("log_channel_id") or "")

    async def on_submit(self, interaction: discord.Interaction):
        cfg = bot.config
        cfg.setdefault("vouch", {})
        cfg.setdefault("logs", {})
        if self.vouch_channel_id.value:
            try:
                cfg["vouch"]["vouch_channel_id"] = int(str(self.vouch_channel_id.value).strip())
            except ValueError:
                pass
        if self.log_channel_id.value:
            try:
                cfg["logs"]["log_channel_id"] = int(str(self.log_channel_id.value).strip())
            except ValueError:
                pass
        bot.persist()
        await interaction.response.edit_message(embed=config_summary_embed(cfg))


class VouchModal(discord.ui.Modal, title="Vouch Settings"):
    enabled = discord.ui.TextInput(label="Enabled? (true/false)", required=False, max_length=5)
    min_hours = discord.ui.TextInput(label="Min hours (>=1)", required=False, max_length=4)
    max_hours = discord.ui.TextInput(label="Max hours (>= min)", required=False, max_length=4)

    def __init__(self, cfg: Dict[str, Any]):
        super().__init__()
        v = cfg.get("vouch", {})
        self.enabled.default = "true" if v.get("enabled", True) else "false"
        self.min_hours.default = str(v.get("min_hours", 10))
        self.max_hours.default = str(v.get("max_hours", 30))

    async def on_submit(self, interaction: discord.Interaction):
        cfg = bot.config
        cfg.setdefault("vouch", {})
        en = (str(self.enabled.value).strip().lower() == "true") if self.enabled.value else cfg["vouch"].get("enabled", True)
        try:
            mi = int(self.min_hours.value) if self.min_hours.value else cfg["vouch"].get("min_hours", 10)
        except ValueError:
            mi = cfg["vouch"].get("min_hours", 10)
        try:
            ma = int(self.max_hours.value) if self.max_hours.value else cfg["vouch"].get("max_hours", 30)
        except ValueError:
            ma = cfg["vouch"].get("max_hours", 30)
        mi = max(1, mi); ma = max(mi, ma)
        cfg["vouch"]["enabled"] = en
        cfg["vouch"]["min_hours"] = mi
        cfg["vouch"]["max_hours"] = ma
        bot.persist()
        # reset schedule
        vch = cfg["vouch"].get("vouch_channel_id")
        if vch: bot.vouch_next_ts[vch] = 0
        await interaction.response.edit_message(embed=config_summary_embed(cfg))


class AdminPanel(discord.ui.View):
    def __init__(self, invoker_id: int):
        super().__init__(timeout=600)
        self.invoker_id = invoker_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.invoker_id and not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Not allowed.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Branding", style=discord.ButtonStyle.primary)
    async def branding(self, interaction: discord.Interaction, b: discord.ui.Button):
        await interaction.response.send_modal(BrandingModal(bot.config))

    @discord.ui.button(label="Coin Emojis", style=discord.ButtonStyle.primary)
    async def coin_emojis(self, interaction: discord.Interaction, b: discord.ui.Button):
        await interaction.response.send_modal(CoinEmojisModal(bot.config))

    @discord.ui.button(label="Pay Emojis", style=discord.ButtonStyle.primary)
    async def pay_emojis(self, interaction: discord.Interaction, b: discord.ui.Button):
        await interaction.response.send_modal(PayEmojisModal(bot.config))

    @discord.ui.button(label="Channels", style=discord.ButtonStyle.secondary)
    async def channels(self, interaction: discord.Interaction, b: discord.ui.Button):
        await interaction.response.send_modal(ChannelsModal(bot.config))

    @discord.ui.button(label="Vouch Settings", style=discord.ButtonStyle.secondary)
    async def vouch(self, interaction: discord.Interaction, b: discord.ui.Button):
        await interaction.response.send_modal(VouchModal(bot.config))

    @discord.ui.button(label="Save / Export", style=discord.ButtonStyle.success)
    async def save(self, interaction: discord.Interaction, b: discord.ui.Button):
        bot.persist()
        await bot.write_config_to_channel()
        await interaction.response.send_message("✅ Saved & exported (if channel accessible).", ephemeral=True)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, b: discord.ui.Button):
        await interaction.message.delete()

# --------------- Slash Commands ---------------
@bot.tree.command(description="Open the admin GUI panel (Manage Server required).")
@app_commands.checks.has_permissions(manage_guild=True)
async def adminpanel(interaction: discord.Interaction):
    await interaction.response.send_message(embed=config_summary_embed(bot.config), view=AdminPanel(interaction.user.id), ephemeral=True)

@bot.tree.command(description="Post the Automated Purchase panel.")
@app_commands.checks.has_permissions(manage_guild=True)
async def post_autoorder(interaction: discord.Interaction):
    brand = bot.config.get("branding", {})
    em = discord.Embed(title="🛒 Automated Purchase", description=PANEL_TEXT, color=discord.Color.blurple())
    if brand.get("logo_url"): em.set_thumbnail(url=brand["logo_url"])
    if brand.get("auto_banner_url"): em.set_image(url=brand["auto_banner_url"])

    class PurchaseButton(discord.ui.View):
        def __init__(self): super().__init__(timeout=None)
        @discord.ui.button(label="Purchase Robux", style=discord.ButtonStyle.primary, custom_id="purchase_btn")
        async def purchase(self, i: discord.Interaction, b: discord.ui.Button):
            await i.response.send_message("A staff member will assist you shortly in this thread.", ephemeral=True)
            parent = i.channel
            try:
                th = await parent.create_thread(name=f"Order — {i.user.display_name}", auto_archive_duration=10080)
                await th.send("Welcome! Please state your desired Robux amount and preferred payment method.")
            except Exception: pass

    await interaction.response.send_message(embed=em, view=PurchaseButton())

@bot.tree.command(description="Post one fake vouch now (uses current config).")
@app_commands.checks.has_permissions(manage_guild=True)
async def fakevouchnow(interaction: discord.Interaction):
    await bot.post_one_fake_vouch()
    await interaction.response.send_message("✅ Posted one fake vouch.", ephemeral=True)

@bot.tree.command(description="Save current config to disk and export to config channel (if accessible).")
@app_commands.checks.has_permissions(manage_guild=True)
async def saveconfig(interaction: discord.Interaction):
    bot.persist()
    await bot.write_config_to_channel()
    await interaction.response.send_message("✅ Saved & exported.", ephemeral=True)

@bot.tree.command(description="Set channels via command (optional, same as GUI).")
@app_commands.checks.has_permissions(manage_guild=True)
async def setchannels(interaction: discord.Interaction, vouch_channel: Optional[discord.TextChannel] = None, log_channel: Optional[discord.TextChannel] = None):
    if vouch_channel:
        bot.config.setdefault("vouch", {})["vouch_channel_id"] = vouch_channel.id
        bot.vouch_next_ts[vouch_channel.id] = 0
    if log_channel:
        bot.config.setdefault("logs", {})["log_channel_id"] = log_channel.id
    bot.persist()
    await interaction.response.send_message("✅ Channels updated.", ephemeral=True)

# --------------- Main ---------------
def main():
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    main()
