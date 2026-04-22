import json


class ChannelsBase:
    # id(str): text(str)
    BASE = {}
    DISABLED = {"disabled": []}

    # id(str): user_id(str)
    OWNERS = {}

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
        self.OWNERS.update({id: user_id})
        self.to_file()

    def update(self, id: str, text: str) -> None:
        self.BASE.update({id: text})
        self.to_file()

    def get(self, id: str) -> str:
        return self.BASE.get(id)

    def remove(self, id: str) -> None:
        self.BASE.pop(id)
        self.OWNERS.pop(id)
        self.DISABLED["disabled"].remove(id)
        self.to_file()

    def from_file(self) -> None:
        with open("./channels.json", "r", encoding='utf-8') as f:
            self.BASE = json.load(f)

        with open("./disabled.json", "r", encoding='utf-8') as f:
            self.DISABLED = json.load(f)

        with open("./owners.json", "r", encoding='utf-8') as f:
            self.OWNERS = json.load(f)

    def to_file(self) -> None:
        with open("./channels.json", "w", encoding='utf-8') as f:
            json.dump(self.BASE, f)

        with open("./disabled.json", "w", encoding='utf-8') as f:
            json.dump(self.DISABLED, f)

        with open("./owners.json", "w", encoding='utf-8') as f:
            json.dump(self.OWNERS, f)


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
        with open("./users.json", "r", encoding='utf-8') as f:
            self.USERS = json.load(f)

    def to_file(self) -> None:
        with open("./users.json", "w", encoding='utf-8') as f:
            json.dump(self.USERS, f)
