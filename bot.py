import discord
from discord import app_commands
import os
import asyncio
import random
import json
from datetime import datetime, timedelta, timezone

# --- Load environment variables ---
from dotenv import load_dotenv
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_SERVER_ID = int(os.getenv("DISCORD_SERVER_ID"))
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
APPLY_CHANNEL_ID = int(os.getenv("APPLY_CHANNEL_ID"))
PING_CTA_CHANNEL_ID = int(os.getenv("PING_CTA_CHANNEL_ID"))

# --- Vietnam timezone ---
VIETNAM_TZ = timezone(timedelta(hours=7))

# --- Intents setup ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# --- ZvZ Alert Storage ---
ALERTS_FILE = "zvz_alerts.json"

def load_alerts():
    if not os.path.exists(ALERTS_FILE):
        return []
    with open(ALERTS_FILE, "r") as f:
        return json.load(f)

def save_alerts(alerts):
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f, indent=4)

scheduled_alerts = load_alerts()

# --- Bot Client ---
class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=DISCORD_SERVER_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        self.bg_task = asyncio.create_task(zvz_alert_loop())

client = MyClient()

# --- Welcome new members ---
@client.event
async def on_member_join(member):
    channel = client.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🐉✨ Welcome! ✨🐉",
            description=(
                f"Welcome {member.mention} to **{member.guild.name}**! 🎉\n\n"
                f"If {member.mention} want to apply for a guild 🏰⚔️, please visit <#{APPLY_CHANNEL_ID}> 🌼"
            ),
            color=discord.Color.pink()
        )
        embed.set_footer(text=f"Member #{len(member.guild.members)}")
        await channel.send(embed=embed)

# --- Group command /clear messages ---
clear_messages_group = app_commands.Group(name="clear", description="Clear Messages commands.")

@clear_messages_group.command(name="messages", description="Delete a number of recent messages.")
@app_commands.describe(number="How many messages to delete (max 100).")
async def clear_messages(interaction: discord.Interaction, number: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "🚫 You don't have permission to use this command.", ephemeral=True
        )
        return

    if number < 1 or number > 100:
        await interaction.response.send_message(
            "Please specify a number between 1 and 100.", ephemeral=True
        )
        return

    await interaction.response.defer(thinking=False)

    deleted = await interaction.channel.purge(limit=number + 1)

    confirm = await interaction.channel.send(
        embed=discord.Embed(
            description=(f"✅ Deleted {len(deleted) - 1} messages.\n\n"
                         f"This message will disappear in 10 seconds..."),
            color=discord.Color.green()
        )
    )

    for remaining in range(9, 0, -1):
        await asyncio.sleep(1)
        await confirm.edit(
            embed=discord.Embed(
                description=(f"✅ Deleted {len(deleted) - 1} messages.\n\n"
                             f"This message will disappear in {remaining} seconds..."),
                color=discord.Color.green()
            )
        )

    await confirm.delete()

client.tree.add_command(clear_messages_group)

# --- Group command /set cta ---
voice_members_group = app_commands.Group(name="voice", description="Voice Members commands.")

@voice_members_group.command(name="members", description="List all members in a selected voice channel.")
@app_commands.describe(channel="Select the voice channel.")
async def voice_members(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await interaction.response.defer(thinking=False)

    if channel.members:
        member_list = "\n".join(
            [f"{i+1}. {member.display_name}" for i, member in enumerate(channel.members)]
        )
        content = f"🎙 **Members currently in {channel.name}:**\n{member_list}"
    else:
        content = f"No one is in **{channel.name}** right now."

    await interaction.followup.send(content, ephemeral=True)

client.tree.add_command(voice_members_group)

# --- Group command /move all ---
move_all_group = app_commands.Group(name="move", description="Move All commands.")

@move_all_group.command(name="all", description="Move all members from one voice channel to another.")
@app_commands.describe(
    source="The voice channel to move members from.",
    destination="The voice channel to move members to."
)
async def move_all(interaction: discord.Interaction, source: discord.VoiceChannel, destination: discord.VoiceChannel):
    if not interaction.user.guild_permissions.move_members:
        await interaction.response.send_message(
            "🚫 You don't have permission to move members.", ephemeral=True
        )
        return

    if not source.members:
        await interaction.response.send_message(
            f"❌ No members in **{source.name}** to move.", ephemeral=True
        )
        return

    moved = 0
    for member in source.members:
        try:
            await member.move_to(destination)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Failed to move {member.display_name}: {e}")


    await interaction.response.send_message(
        f"✅ Moved {moved} member(s) from **{source.name}** to **{destination.name}**.",
        ephemeral=True
    )

client.tree.add_command(move_all_group)

# --- Group command /lucky draw ---
lucky_draw_group = app_commands.Group(name="lucky", description="Lucky Draw commands.")

@lucky_draw_group.command(name="draw", description="Pick random member(s) from a voice channel.")
@app_commands.describe(
    channel="Select the voice channel.",
    winners="Number of winners to pick.",
    role="Only pick from members with this role (optional).",
    title="Custom title for the draw."
)
async def lucky_draw(
    interaction: discord.Interaction,
    channel: discord.VoiceChannel,
    winners: int,
    role: discord.Role = None,
    title: str = "Lucky Draw"
):
    await interaction.response.defer(thinking=False)

    eligible = []
    for member in channel.members:
        if member.bot:
            continue
        if role and role not in member.roles:
            continue
        eligible.append(member)

    if not eligible:
        await interaction.followup.send(
            f"❌ No eligible members found in **{channel.name}**.",
            ephemeral=True
        )
        return

    if winners > len(eligible):
        winners = len(eligible)

    selected = random.sample(eligible, winners)

    winner_list = "\n".join(
        [f"{i+1}. {member.display_name}" for i, member in enumerate(selected)]
    )

    embed = discord.Embed(
        title=f"🎉 {title} 🎉",
        description=(f"**Channel:** {channel.name}\n"
                     f"**Winners ({winners}):**\n{winner_list}"),
        color=discord.Color.gold()
    )

    await interaction.followup.send(embed=embed)

client.tree.add_command(lucky_draw_group)

# --- Group command /set cta ---
cta_group = app_commands.Group(name="set", description="Set CTA commands.")

@cta_group.command(name="cta", description="Schedule a Massing CTA alert.")
async def set_cta(interaction: discord.Interaction, time: str, massing_time: str, location: str, role: discord.Role, message: str, drive_link: str = None):
    await interaction.response.defer(thinking=False)
    try:
        alert_dt = datetime.strptime(time, "%H:%M %d-%m-%Y").replace(tzinfo=VIETNAM_TZ)
        massing_dt = datetime.strptime(massing_time, "%H:%M %d-%m-%Y").replace(tzinfo=VIETNAM_TZ)
    except ValueError:
        await interaction.followup.send("❌ Invalid time format.", ephemeral=True)
        return
    now = datetime.now(VIETNAM_TZ)
    if alert_dt < now:
        await interaction.followup.send("❌ Alert time must be future.", ephemeral=True)
        return

    embed = discord.Embed(title="✅ Massing CTA scheduled!", color=discord.Color.pink())
    embed.add_field(name=f"🏷 Location:  {location}", value="\u200b", inline=False)
    embed.add_field(name=f"🕒 Massing time:  {massing_dt.strftime('%H:%M %d-%m-%Y')} (Vietnam time)", value="\u200b", inline=False)
    embed.add_field(name=f"⏰ Alert time:  {alert_dt.strftime('%H:%M %d-%m-%Y')} (Vietnam time)", value="\u200b", inline=False)
    embed.add_field(name=f"📝 Message:  {message}", value="\u200b", inline=False)
    embed.add_field(name="🔗 Fill role: ", value=drive_link if drive_link else "No link provided", inline=False)
    embed.set_footer(text="This is an automated message. Please do not reply.")

    msg = await interaction.followup.send(content=role.mention, embed=embed)

    scheduled_alerts.append({
        "time": time,
        "massing_time": massing_time,
        "location": location,
        "role_id": role.id,
        "message": message,
        "drive_link": drive_link,
        "message_id": msg.id,
        "channel_id": msg.channel.id
    })
    save_alerts(scheduled_alerts)

    asyncio.create_task(update_cta_countdown(msg, alert_dt, massing_dt, location, role.id, message, drive_link))

client.tree.add_command(cta_group)

async def update_cta_countdown(message_obj, alert_dt, massing_dt, location, role_id, message, drive_link):
    while True:
        now = datetime.now(VIETNAM_TZ)
        if now >= alert_dt:
            break
        alert_countdown = str(alert_dt - now).split('.')[0]
        massing_countdown = str(massing_dt - now).split('.')[0]

        embed = discord.Embed(title="✅ Massing CTA scheduled!", color=discord.Color.pink())
        embed.add_field(name=f"🏷 Location: {location}", value="\u200b", inline=False)
        embed.add_field(name=f"🕒 Massing time: {massing_dt.strftime('%H:%M %d-%m-%Y')} (Vietnam time)", value=f"(Starts in {massing_countdown})", inline=False)
        embed.add_field(name=f"⏰ Alert time: {alert_dt.strftime('%H:%M %d-%m-%Y')} (Vietnam time)", value=f"(Starts in {alert_countdown})", inline=False)
        embed.add_field(name=f"📝 Message: {message}", value="\u200b", inline=False)
        embed.add_field(name="🔗 Fill role: ", value=drive_link if drive_link else "No link provided", inline=False)
        embed.set_footer(text="This is an automated message. Please do not reply.")

        try:
            await message_obj.edit(embed=embed)
        except discord.NotFound:
            break  # message deleted or missing

        await asyncio.sleep(60)  # update every minute

# --- Background task to send alerts ---
async def zvz_alert_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        now = datetime.now(VIETNAM_TZ)
        to_send = []

        for alert in scheduled_alerts:
            try:
                # Accepts times with seconds
                alert_dt = datetime.strptime(alert["time"], "%H:%M:%S %d-%m-%Y").replace(tzinfo=VIETNAM_TZ)
                massing_dt = datetime.strptime(alert["massing_time"], "%H:%M:%S %d-%m-%Y").replace(tzinfo=VIETNAM_TZ)
            except ValueError:
                # If old format without seconds, try fallback
                alert_dt = datetime.strptime(alert["time"], "%H:%M %d-%m-%Y").replace(tzinfo=VIETNAM_TZ)
                massing_dt = datetime.strptime(alert["massing_time"], "%H:%M %d-%m-%Y").replace(tzinfo=VIETNAM_TZ)

            if now >= alert_dt:
                # Calculate how long until massing
                massing_countdown = str(massing_dt - now).split('.')[0]
                to_send.append((alert, massing_countdown))

        for alert, massing_countdown in to_send:
            channel = client.get_channel(PING_CTA_CHANNEL_ID)
            role = discord.utils.get(channel.guild.roles, id=alert["role_id"])

            if channel and role:
                embed = discord.Embed(
                    title="🔔 Massing CTA Alert!",
                    color=discord.Color.red()
                )
                embed.add_field(name=f"🏷 Location: {alert['location']}", value="\u200b", inline=False)
                embed.add_field(name=f"🕒 Massing time: {alert['massing_time']}", value=f"(Starts in {massing_countdown})", inline=False)
                embed.add_field(name=f"📝 Message: {alert['message']}", value="\u200b", inline=False)
                embed.add_field(name=f"🔗 Fill role: ", value=alert["drive_link"] if alert["drive_link"] else "No link provided", inline=False)
                embed.set_footer(text="This is an automated message. Please do not reply.")

                await channel.send(content=role.mention, embed=embed)

            # Remove alert from schedule
            scheduled_alerts.remove(alert)

        if to_send:
            save_alerts(scheduled_alerts)

        await asyncio.sleep(30)

# --- Run the bot ---
client.run(DISCORD_BOT_TOKEN)