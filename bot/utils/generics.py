import asyncio
import json
import secrets


def get_guild_prefix(bot, message):
    if not message.guild:
        return "?"
    else:
        config = get_config(message.guild.id)
        return config["prefix"]


def get_token_from_config():
    with open("config.json", "r") as config:
        data = json.load(config)

    token = data.get("token")
    if not token:
        raise ValueError("Token must be provided in config.json")

    return token


def get_config(guild_id):
    with open("config.json", "r") as config:
        data = json.load(config)

    guild_id = str(guild_id)
    registered_guilds = data["guilds"]

    if guild_id not in registered_guilds:
        default_guild_config = {
            "prefix": "?",
            "language": "english",
            "captcha": False,
            "captcha_channel": "",
            "captcha_logs": "",
            "log_channel": 1,
            "captcha_settings": {
                "title": "**Server Verification**",
                "description": "To prevent bot abuse, new members are required to verify in this server. \n\n__Please "
                               "complete the verification promptly, or you risk being kicked from the "
                               "server.__\n\nPress the button below to begin the verification process",
                "author_name": "",
                "verified_role": "",
                "unverified_role": "",
                "author_icon": "",
                "thumb": ""
            }
        }
        update_config(guild_id, default_guild_config)
        return default_guild_config
    return data["guilds"][guild_id]


def update_config(guild_id, guild_config):
    with open("config.json", "r") as config:
        data = json.load(config)

    guild_id = str(guild_id)

    data["guilds"][guild_id] = guild_config
    new_data = json.dumps(data, indent=4, ensure_ascii=False)
    with open("config.json", "w") as config:
        config.write(new_data)


def system_rng():
    rng = secrets.SystemRandom()
    return rng


async def get_member_roles(member):
    member_role_ids = [role.id for role in member.roles]
    return member_role_ids


async def auto_kick(guild, member, message_after_minutes=2, kick_after_minutes=2):
    message_after_minutes *= 60
    kick_after_minutes *= 60

    task_started_time = member.joined_at

    config = get_config(guild.id)

    verified_role_id = config["captcha_settings"].get("verified_role")

    await asyncio.sleep(message_after_minutes)

    member = guild.get_member(member.id)

    if not member or member.joined_at > task_started_time:
        return

    member_role_ids = await get_member_roles(member)

    if verified_role_id in member_role_ids:
        return

    await member.send(
        f"{member.mention} - You will be kicked from the server in {kick_after_minutes} seconds.\n"
        f"Please, solve the captcha."
    )

    await asyncio.sleep(kick_after_minutes)

    # need to refresh member as it may change and old instance wont have new role
    member = guild.get_member(member.id)

    if not member or member.joined_at > task_started_time:
        return

    member_role_ids = await get_member_roles(member)

    if verified_role_id in member_role_ids:
        return

    await member.kick()


async def audit_captcha_tries(guild, member, captcha_state):
    config = get_config(guild.id)
    captcha_logs_channel = guild.get_channel(config["captcha_logs"])
    await captcha_logs_channel.send(
        f"Captcha Audit: User {member.mention} has {captcha_state.name} the captcha."
    )
