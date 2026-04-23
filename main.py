import asyncio
import math
import re

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup
from aiogram.fsm import state
from aiogram.types import CallbackQuery

from config import TOKEN, for_ili_ne_sub
from ui import *
from utils import *

bot = Bot(TOKEN)
dp = Dispatcher()
cb = ChannelsBase()
ub = UsersBase()

query = {}


class States(StatesGroup):
    title = state.State()
    text = state.State()
    query = state.State()

    remove_id = state.State()

    change_id = state.State()
    change_text = state.State()

    disable_enable_id = state.State()


class AdminStates(StatesGroup):
    grant_admin_id = state.State()
    revoke_admin_id = state.State()
    broadcast_text = state.State()


class SettingsStates(StatesGroup):
    cur_setting_id = state.State()


@dp.message(Command("grant"))
async def grant(message: types.Message, state: FSMContext):
    if not ub.is_admin(str(message.chat.id)):
        await message.answer("Вы не администратор", reply_markup=back_kb())
        return

    await message.answer("Пришлите ID пользователя", reply_markup=cancel_kb())
    await state.set_state(AdminStates.grant_admin_id)


@dp.message(AdminStates.grant_admin_id)
async def grant_admin_id(message: types.Message, state: FSMContext):
    if not message.text.replace("-", "").isdigit():
        await message.answer("Пришлите настоящий ID пользователя.", reply_markup=back_kb())
        return

    if ub.is_in_base(str(message.text)):
        ub.add_admin(str(message.text))
        await message.answer("Пользователь добавлен в список админов", reply_markup=back_kb())
    else:
        await message.answer("Пользователь не добавлен в список админов, т.к. он не является пользователем бота"
                             , reply_markup=back_kb())

    await state.clear()


@dp.message(Command("revoke"))
async def revoke(message: types.Message, state: FSMContext):
    if not ub.is_admin(str(message.chat.id)):
        await message.answer("Вы не администратор", reply_markup=back_kb())
        return

    await message.answer("Пришлите ID пользователя", reply_markup=back_kb())
    await state.set_state(AdminStates.revoke_admin_id)


@dp.message(AdminStates.revoke_admin_id)
async def revoke_admin_id(message: types.Message, state: FSMContext):
    if not message.text.replace("-", "").isdigit():
        await message.answer("Пришлите настоящий ID пользователя.")
        return

    if ub.is_in_base(str(message.text)):
        ub.remove_admin(str(message.text))
        await message.answer("Пользователь удален из списка админов")
    else:
        await message.answer("Пользователь не удален из списка админов, т.к. он не является пользователем бота")

    await state.clear()


@dp.message(Command("list"))
async def list_(message: types.Message):
    if not ub.is_admin(str(message.chat.id)):
        await message.answer("Вы не администратор", reply_markup=back_kb())
        return

    await message.answer(f"Пользователи: {ub.get_users()}")
    await message.answer(f"Админы: {ub.get_admins()}")
    await message.answer(f"Каналы: {cb.BASE}")
    await message.answer(f"Отключенные каналы: {cb.DISABLED}")
    await message.answer(f"Владельцы каналов: {cb.OWNERS}")


@dp.message(Command("broadcast"))
async def broadcast(message: types.Message, state: FSMContext):
    if not ub.is_admin(str(message.chat.id)):
        await message.answer("Вы не администратор")
        return

    await message.answer("Пришлите текст", reply_markup=cancel_kb())
    await state.set_state(AdminStates.broadcast_text)


@dp.message(AdminStates.broadcast_text)
async def broadcast_text(message: types.Message, state: FSMContext):
    await message.answer(f"Текст: {message.text}")

    for i in ub.get_users()["users"]:
        await bot.send_message(int(i), message.html_text, parse_mode="HTML")

    await state.clear()


@dp.callback_query(F.data == "add")
async def add_(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Пришлите название своего канала(точно укажите). ДО этого добавьте бота в канал и "
                                 "сделайте админом.",
                                 reply_markup=cancel_kb())
    await state.set_state(States.title)


@dp.message(Command("add"))
async def add(message: types.Message, state: FSMContext):
    await message.answer(
        "Пришлите название своего канала(точно укажите). ДО этого добавьте бота в канал и сделайте админом.",
        reply_markup=cancel_kb())
    await state.set_state(States.title)


@dp.message(Command("remove"))
async def remove(message: types.Message, state: FSMContext):
    await message.answer(
        "Пришлите ID канала, который хотите удалить из базы. Его вам написало при добавлении(это обычный ID телеграма)"
        , reply_markup=cancel_kb())
    await state.set_state(States.remove_id)


@dp.callback_query(F.data.startswith("del_"))
async def remove_(call: CallbackQuery, state: FSMContext):
    c_id = call.data.split("_")[1]

    if cb.is_in_base(str(c_id)):
        if not cb.is_owner(str(c_id), str(call.from_user.id)):
            await call.message.edit_text("Вы не владеете этим каналом", reply_markup=back_kb())
            return

        cb.remove(str(c_id))
        await bot.leave_chat(int(c_id))
        await call.message.edit_text("Канал удален", reply_markup=back_kb())
    else:
        await call.message.edit_text("Такого канала нет", reply_markup=back_kb())
    await state.clear()


@dp.message(States.remove_id)
async def remove_title(message: types.Message, state: FSMContext):
    if not message.text.replace("-", "").isdigit():
        await message.answer("Пришлите настоящий ID канала.", reply_markup=back_kb())
        return

    if cb.is_in_base(str(message.text)):
        if not cb.is_owner(str(message.text), str(message.from_user.id)):
            await message.answer("Вы не владеете этим каналом", reply_markup=back_kb())
            return

        cb.remove(str(message.text))
        await bot.leave_chat(int(message.text))
        await message.answer("Канал удален", reply_markup=back_kb())
    else:
        await message.answer("Такого канала нет", reply_markup=back_kb())
    await state.clear()


@dp.message(Command("change"))
async def change(message: types.Message, state: FSMContext):
    await message.answer(
        "Пришлите ID канала, текст для которого Вы хотите изменить. Его вам написало при добавлении(это обычный ID "
        "телеграма)")
    await state.set_state(States.change_id)


@dp.callback_query(F.data.startswith("edit_"))
async def edit_(call: CallbackQuery, state: FSMContext):
    c_id = call.data.split("_")[-1]
    await call.message.edit_text("Пришлите текст на который хотите изменить")
    await state.update_data(id=c_id)
    await state.set_state(States.change_text)


@dp.message(States.change_id)
async def change_title(message: types.Message, state: FSMContext):
    if not message.text.replace("-", "").isdigit():
        await message.answer("Пришлите настоящий ID канала.")
        return

    if cb.is_in_base(str(message.text)):
        if not cb.is_owner(str(message.text), str(message.from_user.id)):
            await message.answer("Вы не владеете этим каналом")
            return

        await message.answer("Пришлите текст на который изменить")
        await state.update_data(id=message.text)
        await state.set_state(States.change_text)
    else:
        await message.answer("Такого канала нет")


@dp.message(States.change_text)
async def change_text(message: types.Message, state: FSMContext):
    data = await state.get_data()

    cb.update(str(data["id"]), ("" if message.text.endswith("--no-empty-line") else "\n\n") + message.html_text
              .replace("--no-empty-line", "")
              .strip())
    await message.answer("Текст изменен на " + message.html_text, parse_mode="HTML", disable_web_page_preview=True)
    await state.clear()


@dp.callback_query(F.data.startswith("toggle_"))
async def toggle_(call: CallbackQuery, state: FSMContext):
    c_id = call.data.split("_")[1]

    if not cb.is_in_base(str(c_id)):
        await call.message.edit_text("Такого канала нет", reply_markup=back_kb())
    else:
        if not cb.is_owner(str(c_id), str(call.from_user.id)):
            await call.message.edit_text("Вы не можете отключить этот канал", reply_markup=back_kb())
            return

        if cb.is_disabled(str(c_id)):
            cb.enable(str(c_id))
            await call.message.edit_text("Канал включен", reply_markup=back_kb())
        else:
            cb.disable(str(c_id))
            await call.message.edit_text("Канал выключен", reply_markup=back_kb())
    await state.clear()


@dp.message(Command("toggle"))
async def toggle(message: types.Message, state: FSMContext):
    await message.answer(
        "Пришлите ID канала, который Вы хотите временно отключить. Его вам написало при добавлении(это обычный ID "
        "телеграма)", reply_markup=cancel_kb())
    await state.set_state(States.disable_enable_id)


@dp.message(States.disable_enable_id)
async def toggle_title(message: types.Message, state: FSMContext):
    if not message.text.replace("-", "").isdigit():
        await message.answer("Пришлите настоящий ID канала.", reply_markup=cancel_kb())
        return

    if not cb.is_in_base(str(message.text)):
        await message.answer("Такого канала нет", reply_markup=back_kb())
    else:
        if not cb.is_owner(str(message.text), str(message.from_user.id)):
            await message.answer("Вы не можете отключить этот канал", reply_markup=back_kb())
            return

        if cb.is_disabled(str(message.text)):
            cb.enable(str(message.text))
            await message.answer("Канал включен", reply_markup=back_kb())
        else:
            cb.disable(str(message.text))
            await message.answer("Канал выключен", reply_markup=back_kb())
    await state.clear()


@dp.message(States.title)
async def title(message: types.Message, state: FSMContext):
    await message.answer("""
Пришлите текст, который будет указываться в конце поста.
Можно использовать любое форматирование.

ЕСЛИ ВЫ НЕ ХОТИТЕ ПУСТУЮ СТРОКУ - ДОБАВЬТЕ В КОНЕЦ СООБЩЕНИЯ --no-empty-line
Если хотите пробел(ы) в начале - укажите вместо каждого пробела $space """, reply_markup=cancel_kb())
    await state.update_data(title=message.text)
    await state.set_state(States.text)


@dp.message(States.text)
async def text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.html_text)
    data = await state.get_data()

    json_data = {
        data["title"]: {
            "text": ("" if data["text"].endswith("--no-empty-line") else "\n\n") + data["text"]
            .replace("--no-empty-line", "")
            .replace("$space", " ")
            .strip(),
            "u_id": message.chat.id
        }
    }

    query.update(json_data)
    await message.answer("Напишите что-либо в канал и он добавится(Напишите 2 сообщения. второе для проверки)")
    await state.clear()


@dp.channel_post()
async def channel_post_handler(message: types.Message):
    if cb.is_in_base(str(message.chat.id)) and cb.apply_to_message(message):
        await edit_me(message, cb.BASE[str(message.chat.id)])

    elif message.chat.title in query:
        q_out = query[message.chat.title]

        cb.add(str(message.chat.id), str(q_out["text"]), str(q_out["u_id"]))
        await bot.send_message(
            q_out["u_id"],
            f"Канал {message.chat.title} добавлен в базу.\n"
            f"ID вашего канала(понадобится при удалении из базы/изменении текста): {str(message.chat.id)}\n"
            f"Текст: {q_out['text']}",
            parse_mode="HTML",
            reply_markup=back_kb(),
            disable_web_page_preview=True
        )
        # print(cb.BASE)
        query.pop(message.chat.title)


async def edit_me(message: types.Message, to: str):
    find = to
    if to.__contains__("<a>") or to.__contains__("</a>"):
        find = re.sub(r'<[^>]+>', '', to)
    content = message.html_text or message.caption or ""

    if not content.endswith(find):
        new_text = content + to

        try:
            if message.text:
                await message.edit_text(
                    text=new_text,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    entities=message.entities
                )
            else:
                await message.edit_caption(
                    caption=new_text,
                    parse_mode="HTML",
                    entities=message.caption_entities
                )
        except Exception as e:
            pass


@dp.callback_query(F.data.startswith("my_page_"))
async def fetch_my_channels(call: CallbackQuery):
    page = int(call.data.split("_")[-1])

    channels = cb.get_all_users_channels(str(call.from_user.id))

    if not channels:
        return await call.message.edit_text("У вас нет каналов", reply_markup=back_kb())

    pages = math.ceil(len(channels) / 5)

    if page >= pages or page < 0:
        page = 0

    items_per_page = 5
    start_index = page * items_per_page
    end_index = start_index + items_per_page

    channels_in_page = channels[start_index:end_index]

    if not channels:
        await call.message.edit_text("У вас нет каналов", reply_markup=back_kb())
    elif not channels_in_page:
        await call.message.edit_text("На этой странице пусто", reply_markup=back_kb())
    else:
        await call.message.edit_text(
            f"Ваши каналы (страница {page + 1} из {pages}):",
            reply_markup=my_channels(channels_in_page, page, pages)
        )


@dp.callback_query(F.data.startswith("set_"))
async def view_settings(call: CallbackQuery, state: FSMContext):
    c_id = call.data.split("_")[-1]

    await call.message.edit_text(
        "Настройки канала:",
        reply_markup=settings_kb(c_id, cb.get_settings(c_id))
    )


@dp.callback_query(F.data.startswith("setting_"))
async def change_setting(call: CallbackQuery, state: FSMContext):
    c_id = call.data.split("_")[1]
    setting = call.data.replace(f"setting_{c_id}_", "")

    await call.message.edit_text(
        f"Изменение настройки {setting} со значением {cb.get_settings(c_id)[setting]}. Напишите новое значение. "
        f"\nОписание настройки: {Settings.DESCRIPTIONS[setting]}",
    )
    await state.set_state(SettingsStates.cur_setting_id)
    await state.update_data(c_id=c_id, setting=setting)


@dp.message(SettingsStates.cur_setting_id)
async def change_setting_value(message: types.Message, state: FSMContext):
    if not message.text.isnumeric():
        return await message.answer("Нужно ввести число!")

    c_id = (await state.get_data())["c_id"]
    setting = (await state.get_data())["setting"]

    cb.set_setting(c_id, setting, int(message.text))

    await message.answer("Настройка изменена!", reply_markup=settings_kb(c_id, cb.get_settings(c_id)))
    await state.clear()


@dp.callback_query(F.data.startswith("c_"))
async def manage(call: CallbackQuery):
    c_id = call.data.split("_")[-1]

    await call.message.edit_text(
        "Канал: " + cb.BASE[c_id],
        reply_markup=channel_management_interface(c_id)
    )


@dp.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Главное меню!", reply_markup=main_kb())


@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()

    # await message.answer("Чтобы добавить свой канал /add\nУдалить - /remove\nИзменить текст - /change\nВременно "
    #                      "отключить/включить - /toggle")

    await message.answer("Главное меню!", reply_markup=main_kb())

    if not ub.is_in_base(str(message.chat.id)):
        ub.add(str(message.chat.id))


if __name__ == "__main__":
    cb.from_file()
    ub.from_file()
    asyncio.run(dp.start_polling(bot))
