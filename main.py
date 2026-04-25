import asyncio
import math
import random
import re

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup
from aiogram.fsm import state
from aiogram.types import CallbackQuery

from config import TOKEN, for_ili_ne_sub, format_rules, HELP
from ui import *
from utils import *

import sys


class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("console.log", "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        pass


sys.stdout = Logger()
sys.stderr = sys.stdout

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


def repl_ch_id_into_title_if_can(ch_id: str) -> str:
    if ch_id in cb.TITLES:
        return cb.TITLES[ch_id]
    else:
        return ch_id


@dp.message(Command("log"))
async def log(message: types.Message):
    if not ub.is_admin(str(message.chat.id)):
        await message.answer("Вы не администратор", reply_markup=back_kb())
        return

    log_file = FSInputFile("console.log")
    try:
        await message.answer_document(log_file, caption="📄 Актуальный лог консоли")
    except Exception as e:
        await message.answer(f"Ошибка при отправке: {e}")


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

        # Собираем основной отчет
    report = ["<b>📊 ОТЧЕТ ПО БАЗЕ ДАННЫХ</b>\n", "<b>📢 Каналы и подписи:</b>"]

    # 1. Каналы и их подписи
    for ch_id, text in cb.BASE.items():
        clean_text = text.replace('\n', ' ')[:50]  # Короткое превью
        report.append(
            f"• <code>{repl_ch_id_into_title_if_can(ch_id)}</code>: <blockquote expandable>{text.strip()}</blockquote> • <a href='tg://user?id={cb.OWNERS[ch_id]}'>Админ</a>")

    # 2. Настройки (с фиксом юникода в вариациях)
    report.append("\n<b>⚙️ Настройки и вариации:</b>")
    for ch_id, settings in cb.CHANNEL_SETTINGS.items():
        var_info = "нет"
        if 'variations' in settings:
            try:
                # Декодируем ту самую "залупу" из JSON
                v_data = json.loads(settings['variations'])
                var_info = ", ".join(v_data.get('variations', []))
            except:
                var_info = "ошибка парсинга"

        report.append(f"• <code>{repl_ch_id_into_title_if_can(ch_id)}</code>:")
        report.append(
            f"<blockquote expandable>Мин. символов: {settings.get('min_symbols')}\nМедиа: {settings.get('apply_to_media')}\nВариации: {var_info}</blockquote>")

    # 3. Юзеры и Админы
    report.append("\n<b>👥 Пользователи:</b>")
    admins = []

    for adm in ub.get_admins():
        admins.append("tg://user?id=" + adm)

    users = []

    for user in ub.get_users().get('users', []):
        users.append("tg://user?id=" + user)

    report.append(f"• Пользователи: {', '.join(users)}")
    report.append(f"• Админы: {', '.join(admins)}")

    report.append(f"• Всего юзеров: <code>{len(ub.get_users().get('users', []))}</code>")

    # 4. Прочее
    disabled = cb.DISABLED.get('disabled', [])
    report.append(f"\n<b>🚫 Отключено:</b> {len(disabled)} каналов")
    if disabled:
        report.append(f"<blockquote>{', '.join(disabled)}</blockquote>")

    # Отправляем одним или несколькими сообщениями (если отчет слишком длинный)
    final_text = "\n".join(report)

    # Разбиваем на части по 4000 символов, если база разрослась
    if len(final_text) > 4096:
        for x in range(0, len(final_text), 4000):
            await message.answer(final_text[x:x + 4000], parse_mode="HTML", reply_markup=back_kb(),
                                 disable_web_page_preview=True)
    else:
        await message.answer(final_text, parse_mode="HTML", reply_markup=back_kb(), disable_web_page_preview=True)


@dp.message(Command("broadcast"))
async def broadcast(message: types.Message, state: FSMContext):
    if not ub.is_admin(str(message.chat.id)):
        await message.answer("Вы не администратор", reply_markup=back_kb())
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
        "телеграма)", reply_markup=cancel_kb())
    await state.set_state(States.change_id)


@dp.callback_query(F.data.startswith("edit_"))
async def edit_(call: CallbackQuery, state: FSMContext):
    c_id = call.data.split("_")[-1]

    await call.message.edit_text("Пришлите текст на который изменить."
                                 "\nПравила форматирования:"
                                 f"<blockquote expandable>{format_rules}</blockquote>",
                                 parse_mode="HTML",
                                 reply_markup=InlineKeyboardMarkup(
                                     inline_keyboard=[
                                         [
                                             InlineKeyboardButton(text="< К каналу", callback_data=f"c_{c_id}")
                                         ]
                                     ]
                                 ))
    await state.update_data(id=c_id)
    await state.set_state(States.change_text)


@dp.message(States.change_id)
async def change_title(message: types.Message, state: FSMContext):
    if not message.text.replace("-", "").isdigit():
        await message.answer("Пришлите настоящий ID канала.", reply_markup=back_kb())
        return

    if cb.is_in_base(str(message.text)):
        if not cb.is_owner(str(message.text), str(message.from_user.id)):
            await message.answer("Вы не владеете этим каналом", reply_markup=back_kb())
            return

        await message.answer("Пришлите текст на который изменить."
                             "\nПравила форматирования:"
                             f"<blockquote expandable>{format_rules}</blockquote>",
                             parse_mode="HTML")
        await state.update_data(id=message.text)
        await state.set_state(States.change_text)
    else:
        await message.answer("Такого канала нет", reply_markup=back_kb())


@dp.message(States.change_text)
async def change_text(message: types.Message, state: FSMContext):
    data = await state.get_data()

    cb.update(str(data["id"]), ("" if message.text.endswith("--no-empty-line") else "\n\n") + message.html_text
              .replace("--no-empty-line", "")
              .strip())
    await message.answer("Текст изменен на " + message.html_text, parse_mode="HTML", disable_web_page_preview=True,
                         reply_markup=back_kb())
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
    await message.answer(f"""
Пришлите текст, который будет указываться в конце поста.
Можно использовать любое форматирование.

{format_rules}""", reply_markup=cancel_kb())
    await state.update_data(title=message.text)
    await state.set_state(States.text)


@dp.message(States.text)
async def text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.html_text)
    data = await state.get_data()

    json_data = {
        data["title"]: {
            "text": process_text(data["text"]),
            "u_id": message.chat.id
        }
    }

    query.update(json_data)
    await message.answer("Напишите что-либо в канал и он добавится.")
    await state.clear()


@dp.channel_post()
async def channel_post_handler(message: types.Message):
    if cb.is_in_base(str(message.chat.id)) and cb.apply_to_message(message):
        to = cb.BASE[str(message.chat.id)]

        if cb.get_settings(str(message.chat.id))["variations"] != "":
            variations = json.loads(cb.get_settings(str(message.chat.id))["variations"])["variations"]
            variations.append(to)

            to = random.choice(variations)

            await edit_me(message, to)
        else:
            await edit_me(message, to)

    elif message.chat.title in query:
        q_out = query[message.chat.title]

        cb.add(str(message.chat.id), str(q_out["text"]), str(q_out["u_id"]))
        await bot.send_message(
            q_out["u_id"],
            f"Канал <code>{message.chat.title}</code> добавлен в базу.\n"
            f"ID вашего канала(понадобится при удалении из базы/изменении текста): <code>{str(message.chat.id)}</code>\n"
            f"Текст: {q_out['text']}",
            parse_mode="HTML",
            reply_markup=back_kb(),
            disable_web_page_preview=True
        )
        # print(cb.BASE)
        query.pop(message.chat.title)
        await edit_me(message, cb.BASE[str(message.chat.id)])


async def edit_me(message: types.Message, to: str):
    btn_match = re.search(r'--button:(\S+)', to)
    button_link = btn_match.group(1) if btn_match else ""

    to_clean = re.sub(r'--button:\S+', '', to)
    do_text = "--no-text" not in to_clean
    to_clean = to_clean.replace("--no-text", "")

    find = re.sub(r'<[^>]+>', '', to_clean).strip()

    content_html = message.html_text or message.caption or ""

    new_text_html = (content_html + to_clean) if do_text else content_html
    if content_html.endswith(to_clean) and not button_link:
        return

    try:
        kb = None
        if button_link:
            btn_text = to_clean  # if not do_text else "Перейти"
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=btn_text, url=button_link)]
            ])

        if message.text:
            await message.edit_text(
                text=new_text_html,
                parse_mode="HTML",
                reply_markup=kb,
                disable_web_page_preview=True
            )
        else:
            await message.edit_caption(
                caption=new_text_html,
                parse_mode="HTML",
                reply_markup=kb
            )

    except Exception as e:
        print(f"Error: {e}")


@dp.callback_query(F.data.startswith("my_page_"))
async def fetch_my_channels(call: CallbackQuery):
    page = int(call.data.split("_")[-1])

    channels_id = cb.get_all_users_channels(str(call.from_user.id))

    channels = []
    for i in channels_id:
        if i[0] in cb.TITLES:
            channels.append([i[0], cb.TITLES[i[0]]])
        else:
            channels.append(i)

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
    value = cb.get_settings(c_id)[setting]
    c_v = value

    try:
        value = json.loads(value)
    except:
        value = c_v

    await call.message.edit_text(
        f"Изменение настройки {setting} со значением {value}. Напишите новое значение. "
        f"\nОписание настройки: {Settings.DESCRIPTIONS[setting]}",
        reply_markup=back_kb()
    )
    await state.set_state(SettingsStates.cur_setting_id)
    await state.update_data(c_id=c_id, setting=setting)


@dp.message(SettingsStates.cur_setting_id)
async def change_setting_value(message: types.Message, state: FSMContext):
    c_id = (await state.get_data())["c_id"]
    setting = (await state.get_data())["setting"]

    try:
        typed = Settings.TYPES[setting](message.html_text)

        end = typed

        if setting == "variations" and message.html_text != "$NO-VARIATIONS":
            lines = message.html_text.split("\n")

            end = {
                "variations": []
            }

            for i in lines:
                if not i:
                    continue
                end["variations"].append(process_text(i))

            end = json.dumps(end)
        elif setting == "variations" and message.html_text == "$NO-VARIATIONS":
            end = ""

        cb.set_setting(c_id, setting, end)

        # print(f"all settings: {cb.get_settings(c_id)}")
        # print(f"typed: {typed}")
        # print(f"end: {end}")

        await message.answer("Настройка изменена!", reply_markup=settings_kb(c_id, cb.get_settings(c_id)))
        await state.clear()

    except TypeError:
        return await message.answer("Некорректное значение! Введите еще раз.", reply_markup=back_kb())


@dp.callback_query(F.data.startswith("c_"))
async def manage(call: CallbackQuery):
    c_id = call.data.split("_")[-1]

    await call.message.edit_text(
        "Канал: \n\n" + repl_ch_id_into_title_if_can(c_id).strip(),
        parse_mode="HTML",
        reply_markup=channel_management_interface(c_id)
    )


@dp.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Главное меню!", reply_markup=main_kb())


@dp.callback_query(F.data == "help")
async def help(call: CallbackQuery):
    await call.message.edit_text("Помощь", reply_markup=help_kb())


@dp.callback_query(F.data.startswith("help_"))
async def help_page(call: CallbackQuery):
    help_text = HELP[call.data.split("_")[1]]

    await call.message.edit_text(help_text, parse_mode="HTML", reply_markup=back_to_help_kb())


@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()

    # await message.answer("Чтобы добавить свой канал /add\nУдалить - /remove\nИзменить текст - /change\nВременно "
    #                      "отключить/включить - /toggle")

    if not ub.is_in_base(str(message.chat.id)):
        ub.add(str(message.chat.id))

        return await message.answer("Главное меню!"
                                    "\n\nЭто будет написано один раз:"
                                    "используя бот, вы даете согласие на сбор "
                                    "данных для аналитики и отладки(иначе бот будет баганным)", reply_markup=main_kb())

    await message.answer("Главное меню!", reply_markup=main_kb())


if __name__ == "__main__":
    cb.from_file()
    ub.from_file()

    asyncio.run(dp.start_polling(bot))
