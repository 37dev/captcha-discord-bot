from bot.utils.generics import get_config, update_config
from discord.errors import HTTPException


async def send_log_message(self, event, channel, embed, message_file=None):
    """Send the message in the log channel"""

    if channel is False:
        return

    if isinstance(channel, int):
        channel = self.bot.get_channel(channel)

    if channel is None:
        try:
            channel = await event.guild.create_text_channel(f"{self.bot.user.name}-logs")

            perms = channel.overwrites_for(event.guild.default_role)
            perms.read_messages = False
            await channel.set_permissions(event.guild.default_role, overwrite=perms)

        except HTTPException as error:
            if error.code == 50013:
                return await event.channel.send(f"**Log error :** I cannot create a log channel ({error.text}).")
            return await event.channel.send(error.text)

        # Get configuration.json data
        data = get_config(channel.guild.id)
        data["log_channel"] = channel.id

        # Edit configuration.json

        update_config(channel.guild.id, data)

    # Send the message
    await channel.send(embed=embed, file=message_file)
