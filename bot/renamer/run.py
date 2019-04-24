from bot.renamer.selenium import RenamerSelenium
from bot.renamer.service import BusinesService


def run(*args, **kwargs):
    biz_service = BusinesService()
    object_list = biz_service.get_list()

    for obj in object_list:
        RenamerSelenium(entity=obj)
