import requests

webhook_url = "https://discord.com/api/webhooks/1468661709098192949/zcK1T8XJTi1mV77gyBldtn2pA8BhtZUm1q8ePVkzHY3y_rpEIJ_ldvZmBSqvFB6UIyLe"

message = {
    "content": "🦞 **Saga är nu ansluten!**",
    "embeds": [
        {
            "title": "Discord Integration Active",
            "description": "Jag kan nu skicka meddelanden till denna kanal.",
            "color": 3066993,
            "fields": [
                {"name": "Status", "value": "🟢 Online", "inline": True},
                {"name": "Kanal", "value": "1468296618401992827", "inline": True}
            ]
        }
    ]
}

response = requests.post(webhook_url, json=message)
print(f"Status: {response.status_code}")
