import os

""" Bot Configuration """


class DefaultConfig:
    """Bot Configuration"""

    APP_ID = os.environ.get("MicrosoftAppId", "9b10ea6a-4068-45b9-bbe4-1ffc2a718a6b")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "oa~8Q~euboz2HcVu2RK.b3JUh0IbIesV6OG0IcP5")
