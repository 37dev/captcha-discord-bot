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
            "captcha_channel": False,
            "captcha_images_channel": False,
            "log_channel": 1,
            "temporary_role": 1,
            "role_given_after_captcha": False,
            "min_account_date": 86400
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
