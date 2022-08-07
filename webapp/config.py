import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "test_secret_key")
