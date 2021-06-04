import json

import requests

__all__ = ('Message')


class Message:
    """GET messaages from a channel, or, POST a message
    to a channel.

    In oder to send a message as a bot, there are several
    prerequisites. Review the readme for the details.
    """

    def __init__(self, auth_token, channel_id, logger):
        """args:
            - auth_token: The token used to ID a user
            - channel_id: The ID of the discord channel
            - logger: Implement Logger using singleton pattern
        """
        self.__AUTH_TOKEN = auth_token
        self.__CHANNEL_ID = channel_id
        self.url = f"https://discord.com/api/channels/{self.__CHANNEL_ID}/messages"
        self.__logger = logger
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': self.__AUTH_TOKEN
        }

    def post_message_to_channel(self, payload):
        """POST a message to a discord channel
        args:
            - data: The data received from the lambda function
        """

        try:
            r = requests.post(self.url, headers=self.headers, data=payload)
        except Exception as e:
            self.__logger.error(f"Message.post_message_to_channel: {e}")
            return {
                'status': 500,
                'message': 'There was a problem posting your message to Discord.',
                'error_payload': e
            }
        self.__logger.info(
            f"Message.post_message_to_channel: {r.text}")
        return r.json()

    def get_messages_from_channel(self):
        """Get messages from a discord channel"""

        try:
            r = requests.get(self.url, headers=self.headers)
        except Exception as e:
            self.__logger.error(f"Message.get_messages_from_channel: {e}")
            return {
                'status': 500,
                'message': 'There was a problem getting your messages from Discord.',
                'error_payload': e
            }
        self.__logger.info(
            f"Message.post_message_to_channel: {r.text}")
        return r.json()
