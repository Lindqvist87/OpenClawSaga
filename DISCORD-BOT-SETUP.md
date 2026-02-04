# Discord Bot Setup for OpenClaw
## Two-way communication (send & receive)

---

## What We Need

1. **Discord Bot Token** - Create a bot at https://discord.com/developers/applications
2. **Bot Permissions** - Read messages, send messages, embed links
3. **Channel ID** - Where the bot should listen/respond
4. **OpenClaw Integration** - Connect Discord bot to OpenClaw

---

## Step 1: Create Discord Bot

1. Go to https://discord.com/developers/applications
2. Click "New Application" → Name it (e.g., "Saga Bot")
3. Go to "Bot" section → Click "Add Bot"
4. Copy the **Token** (save this securely!)
5. Enable these intents:
   - MESSAGE CONTENT INTENT (to read messages)
   - SERVER MEMBERS INTENT
   - PRESENCE INTENT

---

## Step 2: Add Bot to Server

1. Go to "OAuth2" → "URL Generator"
2. Select scopes: `bot`
3. Select permissions:
   - Send Messages
   - Read Message History
   - Embed Links
   - Attach Files
   - Mention Everyone
4. Copy the generated URL
5. Open URL in browser → Select your server → Authorize

---

## Step 3: Get Channel ID

1. In Discord, enable Developer Mode (User Settings → Advanced)
2. Right-click your desired channel → "Copy Channel ID"
3. Save this ID

---

## Step 4: Configure OpenClaw

Add to `~/.openclaw/config.json`:

```json
{
  "plugins": {
    "entries": {
      "discord": {
        "enabled": true,
        "token": "YOUR_BOT_TOKEN_HERE",
        "channel_id": "YOUR_CHANNEL_ID_HERE",
        "prefix": "!"
      }
    }
  }
}
```

---

## Step 5: Install Discord Skill

```bash
npx clawhub install discord
```

Or manually:
- The discord skill is already installed: `skills/discord/`

---

## Step 6: Test

Send message in Discord channel:
```
!hello
```

Bot should respond!

---

## Usage Once Setup

**From Discord, you can:**
- Send messages directly to me
- Use commands like `!status` to check trading bot
- Get instant responses

**I'll respond:**
- In real-time to your messages
- With the same capabilities as webchat
- Including all skills (trading, research, etc.)

---

## Security Notes

⚠️ **Never share your bot token publicly!**
- If leaked, regenerate immediately at Discord Developer Portal
- Store token in environment variable, not in code

⚠️ **Bot Permissions**
- Only give necessary permissions
- Don't give Administrator unless absolutely needed

---

## Troubleshooting

**Bot not responding?**
1. Check if bot is online (green dot in member list)
2. Verify token is correct
3. Check channel permissions (bot needs send/read access)
4. Check OpenClaw logs for errors

**Can't add bot to server?**
- You need "Manage Server" permission
- Or ask server admin to add it

---

*Once you have the bot token and channel ID, I can help configure it!*
