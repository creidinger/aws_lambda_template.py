class Settings:
    """Misc settings neede for lambda"""

    def __init__(self):
        self.company_name = ""
        self.company_url = ""
        # discord
        self.discord_channel_id = ""
        self.discord_auth_token = ""
        # mailgun
        self.mailgun_domain = None
        self.mailgun_api_key = None
        # DynamoDB
        self.dynamodb_table = None
