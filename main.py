import asyncio
import re

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup
from aiogram.fsm import state
from config import TOKEN, for_ili_ne_sub
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


@dp.message(Command("grant"))
async def grant(message: types.Message, state: FSMContext):
    if not ub.is_admin(str(message.chat.id)):
        await message.answer("Вы не администратор")
        return

    await message.answer("Пришлите ID пользователя")
    await state.set_state(AdminStates.grant_admin_id)


@dp.message(AdminStates.grant_admin_id)
async def grant_admin_id(message: types.Message, state: FSMContext):
    if not message.text.replace("-", "").isdigit():
        await message.answer("Пришлите настоящий ID пользователя.")
        return

    if ub.is_in_base(str(message.text)):
        ub.add_admin(str(message.text))
        await message.answer("Пользователь добавлен в список админов")
    else:
        await message.answer("Пользователь не добавлен в список админов, т.к. он не является пользователем бота")

    await state.clear()


@dp.message(Command("revoke"))
async def revoke(message: types.Message, state: FSMContext):
    if not ub.is_admin(str(message.chat.id)):
        await message.answer("Вы не администратор")
        return

    await message.answer("Пришлите ID пользователя")
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
        await message.answer("Вы не администратор")
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

    await message.answer("Пришлите текст")
    await state.set_state(AdminStates.broadcast_text)


@dp.message(AdminStates.broadcast_text)
async def broadcast_text(message: types.Message, state: FSMContext):
    await message.answer(f"Текст: {message.text}")

    for i in ub.get_users()["users"]:
        await bot.send_message(int(i), message.html_text, parse_mode="HTML")

    await state.clear()


@dp.message(Command("add"))
async def add(message: types.Message, state: FSMContext):
    await message.answer(
        "Пришлите название своего канала(точно укажите). ДО этого добавьте бота в канал и сделайте админом.")
    await state.set_state(States.title)


@dp.message(Command("remove"))
async def remove(message: types.Message, state: FSMContext):
    await message.answer(
        "Пришлите ID канала, который хотите удалить из базы. Его вам написало при добавлении(это обычный ID телеграма)")
    await state.set_state(States.remove_id)


@dp.message(States.remove_id)
async def remove_title(message: types.Message, state: FSMContext):
    if not message.text.replace("-", "").isdigit():
        await message.answer("Пришлите настоящий ID канала.")
        return

    if cb.is_in_base(str(message.text)):
        if not cb.is_owner(str(message.text), str(message.from_user.id)):
            await message.answer("Вы не владеете этим каналом")
            return

        cb.remove(str(message.text))
        await bot.leave_chat(int(message.text))
        await message.answer("Канал удален")
    else:
        await message.answer("Такого канала нет")
    await state.clear()


@dp.message(Command("change"))
async def change(message: types.Message, state: FSMContext):
    await message.answer(
        "Пришлите ID канала, текст для которого Вы хотите изменить. Его вам написало при добавлении(это обычный ID "
        "телеграма)")
    await state.set_state(States.change_id)


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
    await message.answer("Текст изменен на " + message.html_text, parse_mode="HTML")
    await state.clear()


@dp.message(Command("toggle"))
async def toggle(message: types.Message, state: FSMContext):
    await message.answer(
        "Пришлите ID канала, который Вы хотите временно отключить. Его вам написало при добавлении(это обычный ID "
        "телеграма)")
    await state.set_state(States.disable_enable_id)


@dp.message(States.disable_enable_id)
async def toggle_title(message: types.Message, state: FSMContext):
    if not message.text.replace("-", "").isdigit():
        await message.answer("Пришлите настоящий ID канала.")
        return

    if not cb.is_in_base(str(message.text)):
        await message.answer("Такого канала нет")
    else:
        if not cb.is_owner(str(message.text), str(message.from_user.id)):
            await message.answer("Вы не можете отключить этот канал")
            return

        if cb.is_disabled(str(message.text)):
            cb.enable(str(message.text))
            await message.answer("Канал включен")
        else:
            cb.disable(str(message.text))
            await message.answer("Канал выключен")
    await state.clear()


@dp.message(States.title)
async def title(message: types.Message, state: FSMContext):
    await message.answer("""Пришлите текст, который будет указываться в конце поста.
    Можно использовать любое форматирование.
    (ЕСЛИ ВЫ НЕ ХОТИТЕ ПУСТУЮ СТРОКУ - ДОБАВЬТЕ В КОНЕЦ СООБЩЕНИЯ --no-empty-line)""")
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
            .strip(),
            "u_id": message.chat.id
        }
    }

    query.update(json_data)
    await message.answer("Напишите что-либо в канал и он добавится(Напишите 2 сообщения. второе для проверки)")
    await state.clear()


@dp.channel_post()
async def channel_post_handler(message: types.Message):
    # if message.chat.title == "фор или не?":
    #     await edit_me(message, for_ili_ne_sub)
    #       content = message.text or message.caption or ""

    #       if not content.endswith("фор или не?. подписаться."):
    #           new_text = content + for_ili_ne_sub

    #           try:
    #               if message.text:
    #                   await message.edit_text(
    #                       text=new_text,
    #                       parse_mode="HTML",
    #                       disable_web_page_preview=True
    #                   )
    #               else:
    #                   await message.edit_caption(
    #                       caption=new_text,
    #                       parse_mode="HTML"
    #                   )
    #           except Exception as e:
    #               pass

    if cb.is_in_base(str(message.chat.id)) and not cb.is_disabled(str(message.chat.id)):
        await edit_me(message, cb.BASE[str(message.chat.id)])

    elif message.chat.title in query:
        q_out = query[message.chat.title]

        # print(message.chat.title)
        cb.add(str(message.chat.id), str(q_out["text"]), str(q_out["u_id"]))
        await bot.send_message(
            q_out["u_id"],
            f"Канал {message.chat.title} добавлен в базу.\n"
            f"ID вашего канала(понадобится при удалении из базы/изменении текста): {str(message.chat.id)}\n"
            f"Текст: {q_out['text']}",
            parse_mode="HTML"
        )
        # print(cb.BASE)
        query.pop(message.chat.title)


async def edit_me(message: types.Message, to: str):
    find = to
    if to.__contains__("<a>") or to.__contains__("</a>"):
        find = re.sub(r'<[^>]+>', '', to)
    content = message.text or message.caption or ""

    if not content.endswith(find):
        new_text = content + to

        try:
            if message.text:
                await message.edit_text(
                    text=new_text,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
            else:
                await message.edit_caption(
                    caption=new_text,
                    parse_mode="HTML"
                )
        except Exception as e:
            pass


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Чтобы добавить свой канал /add\nУдалить - /remove\nИзменить текст - /change\nВременно "
                         "отключить/включить - /toggle")

    if not ub.is_in_base(str(message.chat.id)):
        ub.add(str(message.chat.id))


if __name__ == "__main__":
    cb.from_file()
    ub.from_file()
    asyncio.run(dp.start_polling(bot))
