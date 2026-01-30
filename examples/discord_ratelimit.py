"""
Example: Discord Bot Rate Limiting
Shows how to protect Discord bot commands from abuse
"""
from hexarch_guardrails import Guardian

guardian = Guardian()


@guardian.check("rate_limit", context={"service": "discord"})
def send_discord_message(channel_id: str, message: str) -> bool:
    """
    Send a message to Discord, but respect rate limits
    """
    # This would use discord.py in real code
    # client = discord.Client()
    # channel = client.get_channel(channel_id)
    # await channel.send(message)
    return True


@guardian.check("rate_limit", context={"service": "discord", "priority": "high"})
def send_discord_embed(channel_id: str, embed_data: dict) -> bool:
    """
    Send an embed to Discord with rate limiting
    """
    return True


if __name__ == "__main__":
    print("Hexarch Guardrails - Discord Bot Rate Limiting")
    print("=" * 50)
    print(f"✓ Guardian initialized")
    print(f"✓ Available policies: {guardian.list_policies()}")
    print()
    print("To use:")
    print("  from examples.discord_ratelimit import send_discord_message")
    print("  send_discord_message('123456789', 'Hello!')")
    print()
    print("The guardian will enforce rate limits to prevent")
    print("your bot from getting throttled.")
