import re

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

'''
options = {
    0: {
        "Example button on row 1": "my_callback_data"
    },
    1: {
        "Example button on row 2": "my_callback_data",
        "Another example button on row 2": "my_callback_data"
    },
}
'''


def kb_creator(options: dict) -> InlineKeyboardMarkup:
    inline_kb_list = []

    for number, row in options.items():
        print(number, row)
        r = []
        for text, data in row.items():
            if data.startswith("http"):
                r.append(InlineKeyboardButton(text=text, url=data))
            else:
                r.append(InlineKeyboardButton(text=text, callback_data=data))

        inline_kb_list.append(r)

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def channel_management_interface(c_id: str) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="Изменить текст", callback_data=f"edit_{c_id}"),
            InlineKeyboardButton(text="Поменять настройки", callback_data=f"set_{c_id}")
        ],
        [
            InlineKeyboardButton(text="Удалить из базы", callback_data=f"del_{c_id}"),
            InlineKeyboardButton(text="Включить/Выключить канал", callback_data=f"toggle_{c_id}"),
        ],
        [
            InlineKeyboardButton(text="В главное меню(Отменить/Назад)", callback_data="cancel")
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=kb)


def my_channels(c_list: list[str], page, pages) -> InlineKeyboardMarkup:
    kb = []

    for i in c_list:
        text = re.sub(r'<[^>]+>', '', i[1])
        kb.append([InlineKeyboardButton(text=text, callback_data=f"c_{i[0]}")])

    if (page+1) < pages:
        kb.append([InlineKeyboardButton(text=f"{page+1}/{pages} >", callback_data=f"my_page_{page+1}")])

    kb.append([InlineKeyboardButton(text="В главное меню(Отменить/Назад)", callback_data="cancel")])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def settings_kb(c_id: str, settings: dict) -> InlineKeyboardMarkup:
    kb = []
    for k, v in settings.items():
        kb.append([InlineKeyboardButton(text=f"{k}: {v}", callback_data=f"setting_{c_id}_{k}")])

    kb.append([InlineKeyboardButton(text="В главное меню(Отменить/Назад)", callback_data="cancel")])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def main_kb() -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="Добавить канал", callback_data="add")
        ],
        [
            InlineKeyboardButton(text="Мои каналы", callback_data="my_page_0")
        ],
        [
            InlineKeyboardButton(text="Автор", url="https://t.me/sltmanager")
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=kb)


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data="cancel")]])


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню(Отменить/Назад)", callback_data="cancel")]])


def test():
    options = {
        0: {
            "Example button on row 1": "my_callback_data"
        },
        1: {
            "Example button on row 2": "my_callback_data",
            "Another example button on row 2": "my_callback_data"
        },
    }
    print(kb_creator(options))


if __name__ == "__main__":
    test()
