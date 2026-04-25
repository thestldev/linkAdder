import json
from aiogram.types import Message


class Settings:
    DEFAULT_SETTINGS = {
        "min_symbols": -1,
        "apply_to_media": 1,
        "variations": ""
    }

    DESCRIPTIONS = {
        "min_symbols": "Минимальное количество символов в сообщении для добавления текста",
        "apply_to_media": "Добавлять ли текст к медиафайлам. 0 - нет, 1 - да.",
        "variations": "Вариации текста для добавления. Пишите их каждую на отдельной строке. "
                      "!! Чтобы убрать вариации - $NO-VARIATIONS"
    }

    TYPES = {
        "min_symbols": int,
        "apply_to_media": int,
        "variations": str
    }


class ChannelsBase:
    # id(str): text(str)
    BASE = {}
    DISABLED = {"disabled": []}
    # id(str): title(str)
    TITLES = {}

    # id(str): user_id(str)
    OWNERS = {}

    # id(str): settings(dict)
    CHANNEL_SETTINGS = {}

    def apply_to_message(self, message: Message) -> bool:
        c_id = str(message.chat.id)

        if c_id not in self.TITLES:
            self.TITLES.update({c_id: message.chat.title})

        for k, v in Settings.DEFAULT_SETTINGS.items():
            if k not in self.CHANNEL_SETTINGS[c_id]:
                self.CHANNEL_SETTINGS[c_id].update({k: v})
        self.to_file()

        try:
            if self.is_disabled(c_id):
                return False
            if message.caption is not None:
                if self.CHANNEL_SETTINGS[c_id]["apply_to_media"] == 0:
                    return False
                return len(message.caption) >= self.CHANNEL_SETTINGS[c_id]["min_symbols"]
            if self.CHANNEL_SETTINGS[c_id]["min_symbols"] > -1:
                return len(message.text) >= self.CHANNEL_SETTINGS[c_id]["min_symbols"]
        except Exception as e:
            pass

        return True

    def set_default_settings(self, id: str) -> None:
        self.CHANNEL_SETTINGS.update({id: Settings.DEFAULT_SETTINGS})
        self.to_file()

    def is_in_base(self, id: str) -> bool:
        return id in self.BASE

    def is_disabled(self, id: str) -> bool:
        return id in self.DISABLED["disabled"]

    def is_owner(self, id: str, user_id: str) -> bool:
        return self.OWNERS.get(id) == user_id

    def disable(self, id: str) -> None:
        if id not in self.DISABLED["disabled"]:
            self.DISABLED["disabled"].append(id)
        self.to_file()

    def enable(self, id: str) -> None:
        if id in self.DISABLED["disabled"]:
            self.DISABLED["disabled"].remove(id)
        self.to_file()

    def add(self, id: str, text: str, user_id: str) -> None:
        self.BASE.update({id: text})
        self.set_default_settings(id)
        self.OWNERS.update({id: user_id})
        self.to_file()

    def update(self, id: str, text: str) -> None:
        self.BASE.update({id: text})
        self.to_file()

    def get(self, id: str) -> str:
        return self.BASE.get(id)

    def get_settings(self, c_id: str) -> dict:
        return self.CHANNEL_SETTINGS.get(c_id)

    def remove(self, id: str) -> None:
        self.BASE.pop(id)
        self.OWNERS.pop(id)
        self.to_file()

    def set_setting(self, c_id, setting, value):
        self.CHANNEL_SETTINGS[c_id][setting] = value
        self.to_file()

    def get_all_users_channels(self, u_id: str) -> list:
        return [[k, v] for k, v in self.BASE.items() if self.OWNERS.get(k) == u_id]

    def from_file(self) -> None:
        try:
            with open("./channels.json", "r", encoding='utf-8') as f:
                self.BASE = json.load(f)
        except FileNotFoundError as e:
            self.BASE = {}
            with open("./channels.json", "w", encoding='utf-8') as f:
                json.dump(self.BASE, f)

        try:
            with open("./disabled.json", "r", encoding='utf-8') as f:
                self.DISABLED = json.load(f)
        except FileNotFoundError as e:
            self.DISABLED = {"disabled": []}
            with open("./disabled.json", "w", encoding='utf-8') as f:
                json.dump(self.DISABLED, f)

        try:
            with open("./owners.json", "r", encoding='utf-8') as f:
                self.OWNERS = json.load(f)
        except FileNotFoundError as e:
            self.OWNERS = {}
            with open("./owners.json", "w", encoding='utf-8') as f:
                json.dump(self.OWNERS, f)

        try:
            with open("./settings.json", "r", encoding='utf-8') as f:
                self.CHANNEL_SETTINGS = json.load(f)
        except FileNotFoundError as e:
            self.CHANNEL_SETTINGS = {}
            with open("./settings.json", "w", encoding='utf-8') as f:
                json.dump(self.CHANNEL_SETTINGS, f)

        try:
            with open("./titles.json", "r", encoding='utf-8') as f:
                self.TITLES = json.load(f)
        except FileNotFoundError as e:
            self.TITLES = {}
            with open("./titles.json", "w", encoding='utf-8') as f:
                json.dump(self.TITLES, f)

        for i in self.BASE:
            if i not in self.CHANNEL_SETTINGS:
                self.CHANNEL_SETTINGS[i] = Settings.DEFAULT_SETTINGS

    def to_file(self) -> None:
        with open("./channels.json", "w", encoding='utf-8') as f:
            json.dump(self.BASE, f)

        with open("./disabled.json", "w", encoding='utf-8') as f:
            json.dump(self.DISABLED, f)

        with open("./owners.json", "w", encoding='utf-8') as f:
            json.dump(self.OWNERS, f)

        with open("./settings.json", "w", encoding='utf-8') as f:
            json.dump(self.CHANNEL_SETTINGS, f)

        with open("./titles.json", "w", encoding='utf-8') as f:
            json.dump(self.TITLES, f)


class UsersBase:
    # id(str)
    USERS = {"users": [], "admins": ["5325723189"]}

    def add_admin(self, id: str) -> None:
        self.USERS["admins"].append(id)
        self.to_file()

    def remove_admin(self, id: str) -> None:
        self.USERS["admins"].remove(id)
        self.to_file()

    def get_users(self):
        return self.USERS

    def get_admins(self):
        return self.USERS["admins"]

    def is_in_base(self, id: str) -> bool:
        return id in self.USERS["users"]

    def is_admin(self, id: str) -> bool:
        return id in self.USERS["admins"]

    def add(self, id: str) -> None:
        self.USERS["users"].append(id)
        self.to_file()

    def remove(self, id: str) -> None:
        self.USERS["users"].remove(id)
        self.to_file()

    def from_file(self) -> None:
        try:
            with open("./users.json", "r", encoding='utf-8') as f:
                self.USERS = json.load(f)
        except FileNotFoundError as e:
            self.USERS = {"users": [], "admins": []}
            with open("./users.json", "w", encoding='utf-8') as f:
                json.dump(self.USERS, f)

    def to_file(self) -> None:
        with open("./users.json", "w", encoding='utf-8') as f:
            json.dump(self.USERS, f)


def process_text(text: str) -> str:
    return (("" if text.__contains__("--no-empty-line") else "\n\n") + text
            .replace("--no-empty-line", "")
            .replace("$space", " ")
            .strip())
