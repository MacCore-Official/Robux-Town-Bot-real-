#!/usr/bin/env python3
# Robux Town™ – FINALIZED UI + LIVE PRICES + ADMIN PANEL + PRICE LIST + AUTO FAKE COMPLETION
# Robux Town™ – FINALIZED UI + DISCOUNTS + ADMIN PANEL + PRICE LIST
import os
import asyncio
import json
@@ -35,22 +35,21 @@
bot = commands.Bot(command_prefix="+", intents=intents, help_command=None)

# Channels (PLACEHOLDER IDs - REPLACE WITH YOUR REAL IDs)
INFO_CHANNEL_ID           = 1435516058105675818 # Main buy channel (Where persistent button is)
PRICE_CHANNEL_ID          = 1435516058105675817 # Channel for the price list embed
ORDER_LOG_CHANNEL_ID      = 1435516057845497981 # Original log channel (No longer used by fake orders)
COMPLETED_CHANNEL_ID      = 1435516058286035015 # Channel for completed orders
LOG_CHANNEL_ID            = 1435516058286035020 # Staff payment submission log
INFO_CHANNEL_ID           = 1435516058105675818 
PRICE_CHANNEL_ID          = 1435516058105675817 
ORDER_LOG_CHANNEL_ID      = 1435516057845497981 
COMPLETED_CHANNEL_ID      = 1435516058286035015 
LOG_CHANNEL_ID            = 1435516058286035020 
STAFF_ROLE_ID             = 1435516057526734991 
STAFF_DM_IDS              = [1422665161466187976,1269145029943758899] 

PAYMENT_METHOD_CHANNEL_ID = 1435516058105675820 # Channel for Payment Methods
TOS_CHANNEL_ID            = 1435516058286035016 # Channel for Terms of Service 
PAYMENT_METHOD_CHANNEL_ID = 1435516058105675820 
TOS_CHANNEL_ID            = 1435516058286035016 


# EMOJIS (PLACEHOLDER IDs - REPLACE WITH YOUR REAL IDs)
EMOJI_ROBUX          = "<:Robux:1435526693472178176>"
EMOJI_VERIFIED       = "<:Verified:1435526918891110551>"
EMOJI_LOADING        = "<a:Loading:1435526855523434576>" 
EMOJI_LOADING        = "<a:Loading:1435526855523434576>"
EMOJI_WARNING        = "<:warning:1435526954689495091>"
EMOJI_BITCOIN        = "<:Bitcoin:1435526466527039579>"
EMOJI_LITECOIN       = "<:Litecoin:1435526448684339321>"
@@ -74,7 +73,7 @@
ROBUX_RATE_PER_1000 = 1.00

def get_price(robux_amount: int) -> float:
    """Calculates the total USD price based on the Robux amount."""
    """Calculates the standard total USD price based on the Robux amount."""
    return (robux_amount / 1000) * ROBUX_RATE_PER_1000

# -------------------------------------------------
@@ -93,7 +92,7 @@ def get_price(robux_amount: int) -> float:
# -------------------------------------------------
CRYPTO_IDS = {"btc": "bitcoin", "ltc": "litecoin", "eth": "ethereum", "sol": "solana"}

# Persistent storage for addresses / QR
# Persistent storage for addresses / QR / DISCOUNTS
CONFIG_FILE = "config.json"
default_config = {
    "wallets": {
@@ -107,6 +106,13 @@ def get_price(robux_amount: int) -> float:
        "ltc": "https://i.ibb.co/zhbtHyRp/Screenshot-2025-11-10-at-6-28-58-PM.png",
        "eth": "https://i.ibb.co/67YFkD4h/Screenshot-2025-11-10-at-6-29-33-PM.png",
        "sol": "https://i.ibb.co/XfDB2z1b/Screenshot-2025-11-10-at-6-30-02-PM.png"
    },
    "deals": { # <-- ADDED DEFAULT DEAL FOR TESTING
        "WINTERDEAL": {
            "robux": 100000, 
            "price": 60.00, 
            "min_robux_required": 100000
        } 
    }
}

@@ -158,15 +164,49 @@ async def send_to_staff(order_data: dict):
        await channel.send(embed=embed)

# -------------------------------------------------
# MODAL SUBMISSION
# ADMIN MODALS
# -------------------------------------------------
class DiscountModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Set New Discount Code", timeout=600)
        self.code = discord.ui.TextInput(label="Discount Code (e.g., WINTERDEAL)", placeholder="Must be uppercase, one word")
        self.amount = discord.ui.TextInput(label="Robux Amount Covered by Deal", placeholder="e.g., 100000 (R$ amount user must buy)")
        self.price = discord.ui.TextInput(label="Discounted Price in USD", placeholder="e.g., 60.00 (the discounted price)")
        
        self.add_item(self.code)
        self.add_item(self.amount)
        self.add_item(self.price)

    async def on_submit(self, interaction: discord.Interaction):
        code = self.code.value.upper()
        
        try:
            amount = int(self.amount.value.replace(",", ""))
            price = float(self.price.value)
        except ValueError:
            await interaction.response.send_message(f"{EMOJI_WARNING} Invalid number format for amount or price.", ephemeral=True)
            return

        config["deals"][code] = {
            "robux": amount, 
            "price": price, 
            "min_robux_required": amount 
        }
        save_config(config)
        await interaction.response.send_message(
            f"{EMOJI_VERIFIED} Discount code **{code}** set: {amount:,} R$ for **${price:.2f} USD**.",
            ephemeral=True
        )

# --- (Other Modals: PaymentModal, AddressModal, QRModal remain the same) ---
class PaymentModal(discord.ui.Modal):
    def __init__(self, method, amount, price, crypto=None):
    def __init__(self, method, amount, price, crypto=None, discount_code=None): # Added discount_code
        super().__init__(title=f"Submit {method.upper()} Details", timeout=None)
        self.method = method
        self.amount = amount
        self.price = price
        self.crypto = crypto
        self.discount_code = discount_code

        self.details = discord.ui.TextInput(
            label="Payment ID / TX Hash / Code",
@@ -186,13 +226,51 @@ async def on_submit(self, interaction: discord.Interaction):
            "USD": f"${self.price:.2f}",
            "Method": method_name,
            "Details": self.details.value,
            "Discount": self.discount_code or "None", # Log discount if used
            "Thread": interaction.channel.mention,
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        await interaction.response.send_message(f"{EMOJI_VERIFIED} **Payment Submitted!** Your details have been sent to staff for manual verification. Please wait.", ephemeral=True)
        await send_to_staff(order_data)

class AddressModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Set Crypto Address", timeout=600)
        self.coin = discord.ui.TextInput(label="Coin (btc, ltc, eth, sol)", placeholder="e.g., btc", max_length=3)
        self.address = discord.ui.TextInput(label="New Address", placeholder="Paste the full wallet address here", style=discord.TextStyle.paragraph)
        self.add_item(self.coin)
        self.add_item(self.address)

    async def on_submit(self, interaction: discord.Interaction):
        coin = self.coin.value.lower()
        addr = self.address.value
        
        if coin in config["wallets"]:
            config["wallets"][coin] = addr
            save_config(config)
            await interaction.response.send_message(f"{EMOJI_VERIFIED} Updated **{coin.upper()}** address to:\n`{addr}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"{EMOJI_WARNING} Invalid coin specified. Must be one of: `btc`, `ltc`, `eth`, `sol`.", ephemeral=True)

class QRModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Set Crypto QR URL", timeout=600)
        self.coin = discord.ui.TextInput(label="Coin (btc, ltc, eth, sol)", placeholder="e.g., btc", max_length=3)
        self.url = discord.ui.TextInput(label="New QR Image URL", placeholder="Must be a direct link to an image (http://...)", style=discord.TextStyle.paragraph)
        self.add_item(self.coin)
        self.add_item(self.url)

    async def on_submit(self, interaction: discord.Interaction):
        coin = self.coin.value.lower()
        url = self.url.value
        
        if coin in config["qr_urls"]:
            config["qr_urls"][coin] = url
            save_config(config)
            await interaction.response.send_message(f"{EMOJI_VERIFIED} Updated **{coin.upper()}** QR URL.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{EMOJI_WARNING} Invalid coin specified. Must be one of: `btc`, `ltc`, `eth`, `sol`.", ephemeral=True)
# -------------------------------------------------
# CLOSE TICKET VIEW
# -------------------------------------------------
@@ -207,9 +285,7 @@ async def close_button(self, interaction: discord.Interaction, button: discord.u
        if thread:
            try:
                await interaction.response.send_message("Closing the ticket...", ephemeral=False)
                # Archive and lock the thread
                await thread.edit(archived=True, locked=True)
                # Remove flow from active list
                active_flows.pop(interaction.user.id, None)
            except discord.Forbidden:
                await interaction.response.send_message(f"{EMOJI_WARNING} I do not have permission to close this ticket.", ephemeral=True)
@@ -233,6 +309,34 @@ async def send_disclaimer_embed(thread: discord.Thread):
    view = CloseTicketView(thread.id)
    await thread.send(embed=embed, view=view)

# -------------------------------------------------
# PURCHASE FLOW HELPER
# -------------------------------------------------
async def apply_discount(flow, code):
    """Applies discount to flow.price and flow.discount_code if code is valid."""
    flow.discount_code = None
    # Always set standard price first
    flow.price = get_price(flow.robux) 

    if code.upper() == "SKIP" or not code:
        return
    
    deal = config["deals"].get(code.upper())
    
    if deal:
        min_r = deal.get("min_robux_required", 0)
        
        if flow.robux >= min_r:
            # Apply the specific discounted price from the config
            flow.price = deal["price"]
            flow.discount_code = code.upper()
            await flow.thread.send(f"{EMOJI_VERIFIED} Coupon **{code.upper()}** accepted! Your new total price is **${flow.price:.2f} USD**.", delete_after=10)
        else:
            await flow.thread.send(f"{EMOJI_WARNING} Coupon invalid. Minimum purchase for this deal is {min_r:,} R$. Using standard pricing.", delete_after=10)
    else:
        await flow.thread.send(f"{EMOJI_WARNING} Coupon code `{code}` is invalid. Using standard pricing.", delete_after=10)


# -------------------------------------------------
# PURCHASE FLOW
# -------------------------------------------------
@@ -247,40 +351,51 @@ def __init__(self, user_id, thread):
        self.price = 0.0
        self.method = ""
        self.crypto = ""
        self.discount_code = None # <-- NEW: Store applied discount code

    async def send_step(self, step: int):
        color = 0x00A3FF
        if step == 1:
            await send_disclaimer_embed(self.thread) 

            embed = discord.Embed(title="Would you like to start buying robux? (1/5)", color=color)
            embed = discord.Embed(title="Would you like to start buying robux? (1/6)", color=color) # Updated step count
            embed.description = "Please click \"Yes\" to begin."
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_1"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_1"))
            await self.thread.send(embed=embed, view=view)

        elif step == 2:
            embed = discord.Embed(title="How much robux would you like to buy? (2/5)", color=color)
            embed = discord.Embed(title="How much robux would you like to buy? (2/6)", color=color) # Updated step count
            embed.description = "Please specify the amount of Robux you would like to purchase:\n**The minimum order amount is 10,000 Robux**"
            await self.thread.send(embed=embed)

        elif step == 3:
            self.price = get_price(self.robux)
        elif step == 3: # <-- NEW STEP: Discount Code Entry
            embed = discord.Embed(title="Do you have a discount code? (3/6)", color=color)
            embed.description = "Enter your coupon code below, or type **'SKIP'** to continue to the standard pricing."
            await self.thread.send(embed=embed)

        elif step == 4: # <-- OLD Step 3: Price Confirmation
            rate_per_1k = get_price(1000)
            embed = discord.Embed(title="Would you like to purchase this amount of Robux? (3/5)", color=color)
            embed = discord.Embed(title="Would you like to purchase this amount of Robux? (4/6)", color=color)
            
            discount_info = ""
            if self.discount_code:
                discount_info = f"**COUPON APPLIED:** {self.discount_code}\n"
            
            embed.description = (
                f"Are you sure you want to purchase **{self.robux:,} {EMOJI_ROBUX}**?\n"
                f"Current Rate: **${rate_per_1k:.2f} per 1,000 {EMOJI_ROBUX}**\n"
                f"{discount_info}"
                f"Standard Rate: **${rate_per_1k:.2f} per 1,000 {EMOJI_ROBUX}**\n"
                f"Total Price in USD: **${self.price:.2f}**"
            )
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_3"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_3"))
            view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="flow_yes_4"))
            view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="flow_no_4"))
            await self.thread.send(embed=embed, view=view)

        elif step == 4:
            embed = discord.Embed(title="Please select your preferred payment method (4/5)", color=color)
        elif step == 5: # <-- OLD Step 4: Payment Method
            embed = discord.Embed(title="Please select your preferred payment method (5/6)", color=color) # Updated step count
            embed.description = "Choose your payment method below:"
            select = discord.ui.Select(
                placeholder="Select your payment method",
@@ -292,7 +407,6 @@ async def send_step(self, step: int):
                    discord.SelectOption(label="Giftcards", value="gift", emoji=EMOJI_PAYMENT_SUPPORT),
                ]
            )
            # Assign callback to the select component
            async def payment_callback_wrapper(interaction: discord.Interaction):
                await self.payment_callback(interaction)

@@ -301,6 +415,11 @@ async def payment_callback_wrapper(interaction: discord.Interaction):
            view.add_item(select)
            await self.thread.send(embed=embed, view=view)

        elif step == 6: # <-- OLD Step 5: Invoice
            # Invoice logic remains in send_crypto_invoice/send_payment_invoice
            pass


    async def payment_callback(self, interaction: discord.Interaction):
        self.method = interaction.data["values"][0]
        await interaction.response.defer()
@@ -318,7 +437,6 @@ async def payment_callback(self, interaction: discord.Interaction):
                    discord.SelectOption(label="SOL", value="sol", emoji=EMOJI_SOLANA),
                ]
            )
            # Assign callback to the crypto select component
            async def crypto_callback_wrapper(interaction: discord.Interaction):
                await self.crypto_callback(interaction)

@@ -337,23 +455,21 @@ async def crypto_callback(self, interaction: discord.Interaction):
    async def send_crypto_invoice(self, interaction: discord.Interaction):
        price_usd = self.price
        coin_price = await get_crypto_price(self.crypto)
        # Ensure we don't divide by zero
        amount_coin = round(price_usd / coin_price, 8) if coin_price else 0.0

        address = config["wallets"].get(self.crypto, "Address Not Set")
        qr_url = config["qr_urls"].get(self.crypto)
        if not qr_url or not qr_url.startswith("http"):
             qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={address}&size=200x200"

        # --- UPDATED: Calculate expiry time (20 minutes from now) ---
        expiry_time = datetime.now() + timedelta(minutes=20)
        expiry_timestamp = int(expiry_time.timestamp())

        embed = discord.Embed(title=f"{self.crypto.upper()} Payment Invoice (5/5)", color=0x00A3FF)
        embed = discord.Embed(title=f"{self.crypto.upper()} Payment Invoice (6/6)", color=0x00A3FF) # Updated step count
        embed.description = (
            f"This transaction is **${price_usd:.2f} USD**.\n"
            f"Please send the **exact** amount of `{amount_coin:.8f}` {self.crypto.upper()} to the address below.\n\n"
            f"**Invoice Expires:** <t:{expiry_timestamp}:R> (<t:{expiry_timestamp}:T>)" # Discord timestamp formatting
            f"**Invoice Expires:** <t:{expiry_timestamp}:R> (<t:{expiry_timestamp}:T>)"
        )
        embed.add_field(name="Payment Address", value=f"```\n{address}\n```", inline=False)
        embed.add_field(name=f"Amount ({self.crypto.upper()})", value=f"`{amount_coin:.8f}`", inline=False)
@@ -364,7 +480,6 @@ async def send_crypto_invoice(self, interaction: discord.Interaction):
        view.add_item(discord.ui.Button(label="Submit TX Hash", style=discord.ButtonStyle.blurple, custom_id="submit_tx"))
        await interaction.followup.send(embed=embed, view=view)

        # Checking embed is also updated with expiry time
        check_embed = discord.Embed(title="Checking For Transactions", color=0x00A3FF)
        check_embed.description = (
            f"{EMOJI_LOADING} We are actively monitoring transactions. Please proceed with your payment to complete the transaction process.\n"
@@ -374,10 +489,9 @@ async def send_crypto_invoice(self, interaction: discord.Interaction):

    async def send_payment_invoice(self, interaction: discord.Interaction):
        name = "Giftcard" if self.method == "gift" else self.method
        embed = discord.Embed(title=f"{name.upper()} Payment Invoice (5/5)", color=0x00A3FF)
        embed = discord.Embed(title=f"{name.upper()} Payment Invoice (6/6)", color=0x00A3FF) # Updated step count

        details = ""
        # --- UPDATED: Rewarble links added ---
        if self.method == "card":
             details = (
                 "**You must purchase a Rewarble Card from G2A** for the amount and submit the code.\n"
@@ -403,75 +517,100 @@ async def send_payment_invoice(self, interaction: discord.Interaction):
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data or "custom_id" not in interaction.data:
        # Pass non-button/select/modal interactions to commands
        return await bot.process_commands(interaction.message)

    cid = interaction.data["custom_id"]
    user_id = interaction.user.id
    flow = active_flows.get(user_id)

    # --- PURCHASE FLOW BUTTONS ---
    # --- PURCHASE FLOW BUTTONS (Updated step IDs) ---
    if cid.startswith("flow_") and flow:
        if cid == "flow_yes_1":
            await interaction.response.defer()
            await flow.send_step(2)

        elif cid == "flow_no_1" or cid == "flow_no_3":
        elif cid == "flow_no_1":
            await interaction.response.defer()
            await flow.thread.send("Purchase flow cancelled.")
            await flow.thread.edit(archived=True, locked=True)
            active_flows.pop(user_id, None)

        elif cid == "flow_yes_3":
        elif cid == "flow_yes_4" and flow: # Step 4 CONFIRMATION
            await interaction.response.defer()
            await flow.send_step(4)
            await flow.send_step(5) # Move to payment method

        elif cid == "flow_no_4" and flow: # Step 4 RESTART
            await interaction.response.defer()
            await flow.thread.send("Cancelled. Restarting...")
            await flow.thread.edit(archived=True, locked=True)
            active_flows.pop(user_id, None)
            
            # Start a new thread for restart
            info_channel = bot.get_channel(INFO_CHANNEL_ID)
            thread = await info_channel.create_thread(
                name=f"Purchase-{interaction.user.name}-{random.randint(1000,9999)}",
                auto_archive_duration=1440,
                type=discord.ChannelType.private_thread
            )
            await thread.add_user(interaction.user)
            new_flow = PurchaseFlow(interaction.user.id, thread)
            active_flows[interaction.user.id] = new_flow
            await new_flow.send_step(1)

    # --- SUBMISSION BUTTONS ---
    elif cid == "submit_tx" and flow:
        modal = PaymentModal("Cryptocurrency", flow.robux, flow.price, flow.crypto)
        modal = PaymentModal("Cryptocurrency", flow.robux, flow.price, flow.crypto, flow.discount_code)
        await interaction.response.send_modal(modal)

    elif cid == "submit_details" and flow:
        modal = PaymentModal(flow.method, flow.robux, flow.price)
        modal = PaymentModal(flow.method, flow.robux, flow.price, discount_code=flow.discount_code)
        await interaction.response.send_modal(modal)

    # Process commands if it was a message interaction that bypassed on_message
    await bot.process_commands(interaction.message)

# -------------------------------------------------
# MESSAGE: AMOUNT (Step 2 input)
# MESSAGE: AMOUNT (Step 2 input) & DISCOUNT CODE (Step 3 input)
# -------------------------------------------------
@bot.event
async def on_message(message: discord.Message):
    # Only process non-bot messages in an active purchase thread
    if message.author.bot or not message.channel.name.startswith("Purchase-"):
        return await bot.process_commands(message) # Still process commands
        return await bot.process_commands(message) 

    if re.fullmatch(r"[\d,]+", message.content.strip()):
        try:
            amount = int(message.content.replace(",", "").strip())
            
            # Check if this message is from an active flow user
            flow = active_flows.get(message.author.id)
            if flow and flow.thread.id == message.channel.id:
    flow = active_flows.get(message.author.id)

    if flow and flow.thread.id == message.channel.id:
        # Check 1: Waiting for Robux Amount (Step 2)
        if flow.robux == 0 and re.fullmatch(r"[\d,]+", message.content.strip()):
            try:
                amount = int(message.content.replace(",", "").strip())
                if amount < 10000:
                    await message.reply(f"{EMOJI_WARNING} The **minimum order** is 10,000 {EMOJI_ROBUX}. Please enter a higher amount.")
                    await message.reply(f"{EMOJI_WARNING} The **minimum order** is 10,000 {EMOJI_ROBUX}.", delete_after=5)
                    return
                # NOTE: Max limit is 800,000 based on price list
                if amount > 800000:
                    await message.reply(f"{EMOJI_MAX} The **maximum order** is 800,000 {EMOJI_ROBUX}. Please enter a lower amount.")
                    await message.reply(f"{EMOJI_MAX} The **maximum order** is 800,000 {EMOJI_ROBUX}.", delete_after=5)
                    return

                # Proceed to step 3
                flow.robux = amount
                await message.delete()
                # Move to Step 3: Discount Prompt
                await flow.send_step(3)
            else:
                 await bot.process_commands(message) # If not a flow-related message, check for commands
        except ValueError:
             await bot.process_commands(message)
    else:
        await bot.process_commands(message)
                return
            except ValueError:
                pass # Continue to next check

        # Check 2: Waiting for Discount Code (Step 3)
        # We know we're in step 3 if flow.robux > 0 but flow.price == 0 (price isn't finalized yet)
        if flow.robux > 0 and flow.price == 0.0:
            code = message.content.strip()
            await message.delete()
            
            await apply_discount(flow, code)
            
            # Now move to the next step (Step 4: Price Confirmation)
            await flow.send_step(4)
            return

    await bot.process_commands(message)

# -------------------------------------------------
# STAFF ADMIN PANEL COMMANDS 
@@ -503,7 +642,6 @@ async def trigger_fake_order_now():
    price = get_price(amount)
    method = random.choice(["Crypto", "Card", "PayPal", "Giftcard"])

    # Directly calls the completion function
    await send_completed_order(amount, price, method)

# --- CENTRALIZED HANDLER FOR ADMIN BUTTONS ---
@@ -516,6 +654,8 @@ async def handle_admin_panel_interaction(interaction: discord.Interaction, cid:
        await interaction.response.defer(ephemeral=True)
        await trigger_fake_order_now()
        await interaction.followup.send(f"{EMOJI_VERIFIED} Fake order triggered to the completion channel.", ephemeral=True)
    elif cid == "admin_set_discount":
        await interaction.response.send_modal(DiscountModal())
    elif cid == "admin_set_prices":
        await interaction.response.defer(ephemeral=True)
        await send_price_embed(force_new=True)
@@ -550,6 +690,10 @@ async def set_address_button(self, interaction: discord.Interaction, button: dis
    async def set_qr_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_set_qr")

    @discord.ui.button(label="Set Discount Code", style=discord.ButtonStyle.blurple, custom_id="admin_set_discount", emoji="🏷️")
    async def set_discount_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_set_discount")

    @discord.ui.button(label="Trigger Fake Order", style=discord.ButtonStyle.green, custom_id="admin_fake_order", emoji="🤖")
    async def fake_order_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_fake_order")
@@ -570,59 +714,6 @@ async def set_tos_button(self, interaction: discord.Interaction, button: discord
    async def reset_embed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_admin_panel_interaction(interaction, "admin_reset_embed")

# -------------------------------------------------
# ADMIN PANEL MODALS (For Crypto Settings)
# -------------------------------------------------
class AddressModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Set Crypto Address", timeout=600)
        self.coin = discord.ui.TextInput(label="Coin (btc, ltc, eth, sol)", placeholder="e.g., btc", max_length=3)
        self.address = discord.ui.TextInput(label="New Address", placeholder="Paste the full wallet address here", style=discord.TextStyle.paragraph)
        self.add_item(self.coin)
        self.add_item(self.address)

    async def on_submit(self, interaction: discord.Interaction):
        coin = self.coin.value.lower()
        addr = self.address.value
        
        if coin in config["wallets"]:
            config["wallets"][coin] = addr
            save_config(config)
            await interaction.response.send_message(f"{EMOJI_VERIFIED} Updated **{coin.upper()}** address to:\n`{addr}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"{EMOJI_WARNING} Invalid coin specified. Must be one of: `btc`, `ltc`, `eth`, `sol`.", ephemeral=True)

class QRModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Set Crypto QR URL", timeout=600)
        self.coin = discord.ui.TextInput(label="Coin (btc, ltc, eth, sol)", placeholder="e.g., btc", max_length=3)
        self.url = discord.ui.TextInput(label="New QR Image URL", placeholder="Must be a direct link to an image (http://...)", style=discord.TextStyle.paragraph)
        self.add_item(self.coin)
        self.add_item(self.url)

    async def on_submit(self, interaction: discord.Interaction):
        coin = self.coin.value.lower()
        url = self.url.value
        
        if coin in config["qr_urls"]:
            config["qr_urls"][coin] = url
            save_config(config)
            await interaction.response.send_message(f"{EMOJI_VERIFIED} Updated **{coin.upper()}** QR URL.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{EMOJI_WARNING} Invalid coin specified. Must be one of: `btc`, `ltc`, `eth`, `sol`.", ephemeral=True)

# -------------------------------------------------
# AUTOMATED FAKE ORDER TASK (New/Simplified)
# -------------------------------------------------
@tasks.loop(hours=random.uniform(5, 10))
async def automated_fake_completion_loop():
    amount = random.choice([10000, 25000, 50000, 100000, 250000])
    price = get_price(amount)
    method = random.choice(["Crypto", "Card", "PayPal", "Giftcard"])
    
    # Directly sends the final embed to the completed channel
    await send_completed_order(amount, price, method)


# -------------------------------------------------
# COMPLETION LOGIC
@@ -635,7 +726,6 @@ async def send_completed_order(amount, price, method):
    user_name = "Hidden" 
    rating_stars = "⭐⭐⭐⭐ (4/5)" 

    # Changed title to match the screenshot exactly: Checkmark + New Completed Order
    embed = discord.Embed(title=f"✅ New Completed Order", color=0x38B750) 

    embed.set_thumbnail(url="https://i.ibb.co/whbgBHWz/9c5fd434-f30f-4e24-8212-ea40fa098678.png") 
@@ -898,6 +988,18 @@ async def on_ready():
        automated_fake_completion_loop.start()


# -------------------------------------------------
# AUTOMATED FAKE ORDER TASK (New/Simplified)
# -------------------------------------------------
@tasks.loop(hours=random.uniform(5, 10))
async def automated_fake_completion_loop():
    amount = random.choice([10000, 25000, 50000, 100000, 250000])
    price = get_price(amount)
    method = random.choice(["Crypto", "Card", "PayPal", "Giftcard"])
    
    # Directly sends the final embed to the completed channel
    await send_completed_order(amount, price, method)

# -------------------------------------------------
# RUN
# -------------------------------------------------
