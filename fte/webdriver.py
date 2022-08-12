from os import devnull, environ
from typing import Union

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as F_Options
from selenium.webdriver.chrome.options import Options as C_Options
from selenium.webdriver.firefox.webdriver import WebDriver as FF_WebDriver
from selenium.webdriver.chrome.webdriver import WebDriver as C_WebDriver
from selenium.webdriver.firefox.service import Service as FF_Service
from selenium.webdriver.chrome.service import Service as C_Service


def get_webdriver(
    log_dest=devnull, browser="firefox"
) -> Union[FF_WebDriver, C_WebDriver]:
    """Return a webdriver for webscraping"""
    if "LOG_DEST" in environ:
        log_dest = environ["LOG_DEST"]

    if "WEB_DRIVER" in environ:
        browser = environ["WEB_DRIVER"]

    if browser == "firefox":
        options = F_Options()
        options.headless = True

        service = FF_Service(log_path=log_dest)

        driver = webdriver.Firefox(service=service, options=options)
    elif browser == "chrome":
        options = C_Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        chrome_prefs = {}
        chrome_prefs["profile.default_content_settings"] = {"images": 2}

        service = C_Service(log_path=log_dest)

        options.experimental_options["prefs"] = chrome_prefs
        driver = webdriver.Chrome(service=service, options=options)

    return driver
