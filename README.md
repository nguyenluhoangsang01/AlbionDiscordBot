
# Children of The Dragon Guild Bot

A professional Discord bot for managing **Children of The Dragon** guild activities including:
- Welcome messages
- Clearing chat
- Voice channel utilities
- Lucky draw
- Massing CTA alert system with auto-reminders (Vietnam timezone)

## 🚀 Features

- 🐉 Welcome new members with a custom embed.
- 🧹 Clear recent messages with countdown confirmation.
- 🎙 List members currently in any voice channel.
- 🎯 Move all members from one voice channel to another.
- 🎉 Lucky draw from voice channel members (with role filtering and multiple winners).
- 🔔 Schedule **Massing CTA** alerts with location, massing time, and role ping.
- 🌏 Full Vietnam time zone support (`Asia/Ho_Chi_Minh` / UTC+7).
- 🔒 Role-based permissions for sensitive commands.

## 📝 Commands

| Command | Description |
|---------|-------------|
| `/clear messages` | Clear a specified number of recent messages. |
| `/voice members` | List all members in a specified voice channel. |
| `/move all` | Move all members from one voice channel to another. |
| `/lucky draw` | Randomly pick members from a voice channel. |
| `/set cta` | Schedule a future Massing CTA alert with time, location, and role ping. |

## ⚙️ Setup

### 1️⃣ Requirements

- Python 3.9+
- `discord.py` 2.3+
- `python-dotenv`

### 2️⃣ Installation

```bash
pip install -r requirements.txt
```

### 3️⃣ .env Example

```env
DISCORD_TOKEN=your_bot_token_here
DISCORD_SERVER_ID=your_DISCORD_SERVER_ID_here
WELCOME_CHANNEL_ID=welcome_channel_id_here
APPLY_CHANNEL_ID=apply_channel_id_here
```

### 4️⃣ Run the Bot

```bash
python albion_bot.py
```

## 📅 Massing CTA Example

**Schedule a Massing CTA alert:**

```plaintext
/set cta
time: 17:00 08-05-2025
massing_time: 17:30 08-05-2025
location: Sunfang Wasteland
role: ZvZ Team
message: ZvZ starting in 30 minutes!
```

## 🕒 Time Format

All times use **HH:MM DD-MM-YYYY** format in **Vietnam time (UTC+7)**.

## 🤝 Contributing

Feel free to suggest improvements or request new Children of The Dragon guild features!

---

**Made for Children of The Dragon guilds. Always be ready for the next CTA! 🏰⚔️**