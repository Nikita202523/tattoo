import asyncio
import os
import re
import json
import random
import calendar
import zipfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import Message
router = Router()
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardButton, InlineKeyboardMarkup,
    CallbackQuery
)
from aiogram.filters import CommandStart, BaseFilter
from aiogram.filters.command import CommandObject, Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile


# Гарантируем, что файл слотов существует и валиден
slots_path = "available_slots.json"
if not os.path.exists(slots_path) or os.path.getsize(slots_path) == 0:
    with open(slots_path, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

class DateSelectFSM(StatesGroup):
    chosen_date = State()

class ReplyFSM(StatesGroup):
    waiting_for_text = State()  # можешь удалить, если не используешь
    index = State()
    text = State()

if not os.path.exists("referral_paid.txt"):
    with open("referral_paid.txt", "w"): pass

if not os.path.exists("purchase_limits.txt"):
    with open("purchase_limits.txt", "w", encoding="utf-8"): pass    

class QuestionFSM(StatesGroup):
    text = State()
    mode = State()

class QuestionViewFSM(StatesGroup):
    index = State()

# FSM для добавления времени
class AdminFSM(StatesGroup):
    waiting_for_time = State()    

class FilterFSM(StatesGroup):
    wait_for_date = State()    








SLOT_LIMIT_FILE = "slot_limits.txt"
BROADCAST_FLAG_FILE = "broadcast_status.txt"
LAST_RESET_FILE = "last_reset.txt"
PURCHASE_LOG_FILE = "purchase_log.txt"
ADMIN_ID = 1065790644 
CHANNEL_USERNAME = "@nikita_tattoooo"  
API_TOKEN = '7753903377:AAHZ4zEJ7gJLw6VmBpz_Q-QbkddGrY84Dig'
BARNAUL_USERS_FILE = "barnaul_users.txt"
WHEEL_LOG_FILE = "wheel_log.txt"
JACKPOT_LOG_FILE = "jackpot_log.txt"













def clear_and_collect_logs():
    files_to_clear = [
        "activity_log.txt",
        "game_log.txt",
        "purchase_log.txt",
        "referral_log.txt",
        "wheel_log.txt",
        "daily_warning_log.txt"
    ]

    today = datetime.now().strftime("%Y%m%d")
    archive_name = f"logs_backup_{today}.zip"

    with zipfile.ZipFile(archive_name, "w") as zipf:
        for filename in files_to_clear:
            if os.path.exists(filename):
                zipf.write(filename)
                open(filename, "w", encoding="utf-8").close()

    return archive_name


def has_seen_warning_today(user_id: int) -> bool:
    today = datetime.now().date().isoformat()
    if not os.path.exists("daily_warning_log.txt"):
        return False

    with open("daily_warning_log.txt", "r", encoding="utf-8") as f:
        for line in f:
            uid, date = line.strip().split(":")
            if uid == str(user_id) and date == today:
                return True
    return False

def log_warning_shown(user_id: int):
    today = datetime.now().date().isoformat()
    with open("daily_warning_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{user_id}:{today}\n")

def is_barnaul_user(user_id: int) -> bool:
    if not os.path.exists(BARNAUL_USERS_FILE):
        return False
    with open(BARNAUL_USERS_FILE, "r") as f:
        return str(user_id) in f.read()
    
def save_barnaul_user(user_id: int):
    with open(BARNAUL_USERS_FILE, "a") as f:
        f.write(f"{user_id}\n")    


async def check_subscription(user_id: int, bot: Bot) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "creator", "administrator"]
    except TelegramBadRequest:
        return False
    
class IsSubscribed(BaseFilter):
    async def __call__(self, message: types.Message, bot: Bot) -> bool:
        return await check_subscription(message.from_user.id, bot)

# Создание объектов
bot = Bot (token='7753903377:AAHZ4zEJ7gJLw6VmBpz_Q-QbkddGrY84Dig')
bot.default_parse_mode = ParseMode.HTML
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)



# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Начать")],
        [KeyboardButton(text="✍️ Записаться"), KeyboardButton(text="🖼 Портфолио")],
        [KeyboardButton(text="📚 FAQ"), KeyboardButton(text="🎮 Игры")],
        [KeyboardButton(text="🛍 Магазин"), KeyboardButton(text="📩 Пригласить друга")],
        [KeyboardButton(text="⚙️ Прочее")],[KeyboardButton(text="🛠 Админ-панель")],
        [KeyboardButton(text="⬅️ Назад в меню")],
    
    ],
    resize_keyboard=True
)

other_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏆 Лидеры")],
        [KeyboardButton(text="✍️ опубликовать вопрос или написать отзыв(анонимно или публично)")],
        [KeyboardButton(text="🧾 Все вопросы и отзывы")],
        [KeyboardButton(text="📊 Мой баланс")],
        [KeyboardButton(text="👥 Мои приглашённые")],
        [KeyboardButton(text="⬅️ Назад в меню")],
    ],
    resize_keyboard=True
)

faq_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🧴 Уход за тату", callback_data="faq_care")],
    [InlineKeyboardButton(text="⏳ Сколько заживает?", callback_data="faq_heal")],
    [InlineKeyboardButton(text="🤕 Больно ли?", callback_data="faq_pain")],
    [InlineKeyboardButton(text="💸 Сколько стоит?", callback_data="faq_price")],
    [InlineKeyboardButton(text="🏋️ Когда спорт?", callback_data="faq_sport")],
])

knb_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🪨 Камень", callback_data="knb_rock")],
    [InlineKeyboardButton(text="✂️ Ножницы", callback_data="knb_scissors")],
    [InlineKeyboardButton(text="📄 Бумага", callback_data="knb_paper")],
])\

FAQS = {
    "faq_care": "🧴 Уход за тату:\nhttps://t.me/ne_kit_a_tattoo/60",
    "faq_heal": "⏳ Сколько заживает:\nhttps://t.me/ne_kit_a_tattoo/61",
    "faq_pain": "🤕 Больно ли:\nhttps://t.me/ne_kit_a_tattoo/62",
    "faq_price": "💸 Сколько стоит:\nhttps://t.me/ne_kit_a_tattoo/63",
    "faq_sport": "🏋️ Когда спорт:\nhttps://t.me/ne_kit_a_tattoo/64",
}

SHOP_ITEMS = {
    "tattoo_300": {
        "name": "🎁 Бесплатное тату до 15см",
        "price": 300,
        "limit": "monthly"
    },
    "tattoo_125": {
        "name": "🎯 Тату до 1.500₽",
        "price": 150
    },
    "tattoo_150": {
        "name": "🔥 Тату до 2.500₽",
        "price": 125
    },
    "discount_100": {
        "name": "🧾 Скидка 30%",
        "price": 100
    }
}

class ZapisFSM(StatesGroup):
    age = State()
    area = State()
    phone = State()
    sketch = State()
    date_time = State()

@router.message(Command("Календарь"))
async def show_calendar(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    now = datetime.now()
    keyboard = generate_calendar(now.year, now.month)

    await message.answer(
        "📅 Выбери день для добавления времени:",
        reply_markup=keyboard
    )

@router.message(QuestionFSM.text)
async def choose_mode(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад в меню":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu)
        return

    await state.update_data(text=message.text)
    await state.set_state(QuestionFSM.mode)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Публично", callback_data="public")],
        [InlineKeyboardButton(text="🕶 Анонимно", callback_data="anon")]
    ])
    await message.answer("👁 Как опубликовать?", reply_markup=kb)


@router.callback_query(lambda c: c.data in ["public", "anon"])
async def handle_question_mode(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = data.get("text", "").strip()

    if not text:
        await callback.answer("⚠️ Вопрос не найден.", show_alert=True)
        await state.clear()
        return

    is_public = callback.data == "public"
    user = callback.from_user
    username = f"@{user.username}" if user.username else f"{user.first_name} {user.last_name or ''}".strip()
    display_name = username if is_public else "Аноним"

    # Сохраняем в файл
    with open("questions.txt", "a", encoding="utf-8") as f:
        f.write(
            f"\n---\n🗨 Вопрос: {text}\n"
            f"👤 От: {username} (ID: {user.id})\n"
            f"🕶 Статус: {'Публично' if is_public else 'Анонимно'}\n"
        )
    await bot.send_message(
    ADMIN_ID,
    f"📨 Новый вопрос или отзыв!\n"
    f"👤 От: {username}\n"
    f"🆔 ID: {user.id}\n"
    f"💬 Вопрос: {text}\n"
    f"🌐 Статус: {'Публично' if is_public else 'Анонимно'}"
    )    

    await callback.message.answer(f"✅ Спасибо! Вопрос записан как: {display_name}")
    await callback.answer()
    await state.clear() 


@router.message(lambda msg: msg.text == "🧾 Все вопросы и отзывы")
async def show_all_questions(message: types.Message, state: FSMContext):
    if not os.path.exists("questions.txt"):
        await message.answer("❌ Пока нет вопросов или отзывов.")
        return

    with open("questions.txt", "r", encoding="utf-8") as f:
        raw = f.read().strip()

    entries = [q.strip() for q in raw.split("---") if q.strip()]
    if not entries:
        await message.answer("❌ Пока нет записей.")
        return

    output = "<b>📖 Все вопросы и отзывы:</b>\n\n"

    for entry in entries:
        lines = entry.splitlines()
        question = answer = username = status = ""

        for line in lines:
            line = line.strip()
            if line.startswith("🗨 Вопрос:"):
                question = line.replace("🗨 Вопрос:", "").strip()
            elif line.startswith("✅ Ответ:"):
                answer = line.replace("✅ Ответ:", "").strip()
            elif line.startswith("👤 От:"):
                match = re.search(r"@([a-zA-Z0-9_]+)", line)
                if match:
                    username = match.group(1)
            elif line.startswith("🕶 Статус:"):
                status = line.replace("🕶 Статус:", "").strip()

        author = f"<a href='https://t.me/{username}'>{username}</a>" if status.lower() == "публично" else "Аноним"

        output = (
            f"💬 <b>Вопрос:</b> {question or '—'}\n"
            f"👤 <i>Автор:</i> {author}\n"
            f"✅ <b>Ответ:</b> {answer or '—'}"
        )

        # Только тебе покажем кнопку "Ответить"
        if message.from_user.id == ADMIN_ID:
            idx = entries.index(entry)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✍️ Ответить", callback_data=f"reply_q:{idx}")]
            ])
            await message.answer(output, reply_markup=keyboard, parse_mode="HTML")
        else:
            await message.answer(output, parse_mode="HTML")

            await state.update_data(entries=entries)

@router.callback_query(lambda c: c.data.startswith("reply_q:"))
async def handle_reply_button(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split(":")[1])

    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ Только админ может отвечать.")
        return

    await state.update_data(reply_index=index)
    await state.set_state(ReplyFSM.waiting_for_text)
    await callback.message.answer("✍️ Введи ответ на этот вопрос:")
    await callback.answer()










@router.message(ReplyFSM.waiting_for_text)
async def save_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    index = data.get("reply_index")
    answer = message.text.strip()

    with open("questions.txt", "r", encoding="utf-8") as f:
        raw = f.read().strip()

    blocks = [b.strip() for b in raw.split("---") if b.strip()]

    if index >= len(blocks):
        await message.answer("❌ Ошибка: вопрос не найден.")
        await state.clear()
        return

    entry = blocks[index].splitlines()
    new_entry = []
    answered = False

    for line in entry:
        if line.startswith("✅ Ответ:"):
            new_entry.append(f"✅ Ответ: {answer}")
            answered = True
        else:
            new_entry.append(line)

    if not answered:
        new_entry.append(f"✅ Ответ: {answer}")

    blocks[index] = "\n".join(new_entry)

    with open("questions.txt", "w", encoding="utf-8") as f:
        f.write("\n---\n".join(blocks))

    await message.answer("✅ Ответ сохранён.")
    await state.clear()

@router.message(CommandStart(deep_link=True))
@router.message(CommandStart())

@router.message(CommandStart())
async def cmd_start(message: types.Message, bot: Bot, state: FSMContext, command: CommandObject):
    await state.clear()
    user_id = message.from_user.id
    ref_id = command.args  # ID пригласившего (если есть)

    # ✅ Обрабатываем реферальную ссылку
    if ref_id and str(user_id) != ref_id:
        already_logged = False
        if os.path.exists("referral_log.txt"):
            with open("referral_log.txt", "r") as f:
                for line in f:
                    parts = line.strip().split(":")
                    if len(parts) >= 1:
                        uid = parts[0]
                        if str(user_id) == uid:
                            already_logged = True
                            break
        if not already_logged:
            with open("referral_log.txt", "a") as f:
                f.write(f"{user_id}:{ref_id}\n")
            await message.answer("✅ Ты зашёл по реферальной ссылке! Играя 7 разных дней — получишь +5 баллов, а твой друг — +12.")

    # 📍 Дальше — общая логика (всегда идёт, независимо от реферала)
    if is_barnaul_user(user_id):
        if not await check_subscription(user_id, bot):
            await message.answer("❗️ Ты отписался от канала. Подпишись снова, чтобы пользоваться ботом:\n" + CHANNEL_USERNAME)
            return

        # 👇 Инструкция + меню
        welcome_text = (
        
        "<b>Нажимай кнопку ниже,🚀 Начать!🏃🏻‍♂️</b>\n\n"
        )

        await message.answer(welcome_text, parse_mode="HTML")
        await message.answer("С возвращением! 👋", reply_markup=main_menu)
    else:
        await message.answer(
            "Привет! Ты из Барнаула?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Да"), KeyboardButton(text="Нет")]],
                resize_keyboard=True
            )
        )

@router.message(lambda msg: msg.text == "👥 Мои приглашённые")
async def show_referral_stats(message: types.Message):
    user_id = str(message.from_user.id)
    invited = 0
    activated = 0

    if os.path.exists("referral_log.txt"):
        with open("referral_log.txt", "r") as f:
            for line in f:
                uid, ref = line.strip().split(":")
                if ref == user_id:
                    invited += 1

    if os.path.exists("referral_paid.txt"):
        with open("referral_paid.txt", "r") as f:
            activated = sum(1 for line in f if line.strip())

    reward = activated * 12
    bonus = " +150 баллов!" if activated >= 10 else ""

    await message.answer(
        f"👥 Ты пригласил: {invited} человек(а)\n"
        f"✅ Активировали бонус: {activated} чел.\n"
        f"💰 Получено баллов: {reward}{bonus}"
    )



# Обработка /start
@router.message(lambda msg: msg.text in ["Да", "Нет"])
async def handle_city_answer(message: types.Message, bot: Bot):
    user_id = message.from_user.id

    if message.text == "Да":
        if not await check_subscription(user_id, bot):
            await message.answer(
                "❗️ Подпишись на канал, чтобы продолжить:\n" + CHANNEL_USERNAME
            )
            return

        save_barnaul_user(user_id)
        await message.answer(
            "Отлично! Подписка подтверждена. Можешь выбирать действие 👇",
            reply_markup=main_menu
        )
    else:
        await message.answer(
            "Извини, я работаю только по Барнаулу. Если что-то изменится — буду рад помочь!"
        )

@router.callback_query(lambda c: c.data.startswith("admin_date:"))
async def choose_date_admin(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    date = callback.data.replace("admin_date:", "")
    await state.update_data(selected_date=date)

    # Варианты времени (или можно заменить на кастомные)
    times = ["12:00", "14:00", "16:00", "18:00"]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=time, callback_data=f"admin_time:{time}")]
            for time in times
        ] + [[InlineKeyboardButton(text="➕ Ввести своё", callback_data="admin_custom_time")]]
    )

    await callback.message.answer(
        f"🕐 Выбери или введи время для <b>{date}</b>:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(IsSubscribed(), lambda msg: msg.text == "🎰 Тату-Джекпот")
async def jackpot_game(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    is_admin = user_id == ADMIN_ID
    balance = get_balance(user_id)

    now = datetime.now().time()
    start_time = datetime.strptime("00:00", "%H:%M").time()
    end_time = datetime.strptime("03:00", "%H:%M").time()

    # Только ночью (если не админ)
    if not is_admin and not (start_time <= now <= end_time):
        await message.answer("⏳ Джекпот доступен только ночью — с 00:00 до 03:00 по МСК.")
        return

    # Выбор: обычная или VIP-крутка
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Обычная — 10 баллов", callback_data="jackpot_normal")],
        [InlineKeyboardButton(text="💎 VIP — 50 баллов (+1 шанс)", callback_data="jackpot_vip")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
    await message.answer("Выбери режим игры:", reply_markup=keyboard)

@router.callback_query(lambda c: c.data in ["jackpot_normal", "jackpot_vip"])
async def handle_jackpot(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_admin = user_id == ADMIN_ID
    balance = get_balance(user_id)
    mode = callback.data

    cost = 10 if mode == "jackpot_normal" else 50

    if balance < cost:
        await callback.message.answer("❌ Недостаточно баллов для этой попытки.")
        await callback.answer()
        return

    add_balance(user_id, -cost)

    # Анимация
    msg = await callback.message.answer("🎰 Крутим барабан...")
    symbols = ["🟢", "🔴", "🟠", "🟣", "🟡", "🔵", "⚪️"]
    for i in range(10):
        await asyncio.sleep(0.3)
        await msg.edit_text(f"🎯 Барабан: {symbols[i % len(symbols)]}")

    await asyncio.sleep(1)
    weights = [35, 25, 20, 12, 6, 2]

    reward = random.choices(
        [0, 5, 10, 30, 50, 200],  # награды
        weights=weights,
        k=1
    )[0]
    # Джекпот: проверка, получал ли уже
    if reward == 200:
        if has_received_jackpot(user_id):
            reward = 0
        else:
            log_jackpot_received(user_id)
    add_balance(user_id, reward)

    # Итог
    if reward == 0:
        text = "😢 Ничего не выпало. Не в этот раз..."
    elif reward == 200:
        text = "💎 ДЖЕКПОТ! +200 баллов! ТЫ ЛЕГЕНДА!"
    else:
        text = f"🎉 Поздравляем! Ты получил +{reward} баллов!"

    await msg.edit_text(f"🎰 Джекпот завершён!\n\n{text}")
    await callback.answer()    

@router.callback_query(lambda c: c.data == "admin_custom_time")
async def ask_custom_time(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Введи своё время в формате ЧЧ:ММ, например 13:45:")
    await state.set_state(AdminFSM.waiting_for_time)
    await callback.answer()

@router.message(AdminFSM.waiting_for_time)
async def save_custom_time(message: types.Message, state: FSMContext):
    time = message.text.strip()
    if not re.fullmatch(r"\d{2}:\d{2}", time):
        await message.answer("⚠️ Введи время в формате ЧЧ:ММ, например 13:45")
        return

    data = await state.get_data()
    date = data.get("selected_date")
    if not date:
        await message.answer("⚠️ Ошибка: дата не выбрана.")
        await state.clear()
        return

    # Загружаем слоты
    path = "available_slots.json"
    slots = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            slots = json.load(f)

    slots.setdefault(date, [])
    if time in slots[date]:
        await message.answer("⛔️ Это время уже добавлено.")
        await state.clear()
        return

    slots[date].append(time)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(slots, f, ensure_ascii=False, indent=2)

    await message.answer(f"✅ Добавлено: {date} — {time}")
    await state.clear()



@router.message(IsSubscribed(), lambda msg: msg.text == "✍️ Записаться")
async def select_date(message: types.Message, state: FSMContext):
    path = "available_slots.json"
    if not os.path.exists(path):
        await message.answer("❌ Пока нет свободных дат.")
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            slots = json.load(f)
    except json.JSONDecodeError:
        await message.answer("⚠️ Ошибка чтения файла свободных дат.")
        return

    if not slots:
        await message.answer("❌ Пока нет свободных дат.")
        return

    buttons = [
        [InlineKeyboardButton(text=date, callback_data=f"user_date:{date}")]
        for date in sorted(slots.keys())
    ]

    await message.answer(
        "📅 Выбери дату для записи:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(DateSelectFSM.chosen_date)
    
    
@router.message(IsSubscribed(), lambda msg: msg.text == "🖼 Портфолио")
async def show_portfolio(message: types.Message, state: FSMContext):
    await state.set_state(None)
    await message.answer("🖼 Моё портфолио здесь:\n👉 https://t.me/ne_kit_a_tattoo/14")

@router.message(IsSubscribed(), lambda msg: msg.text == "📚 FAQ")
async def show_faq_menu(message: types.Message, state: FSMContext):
    await state.set_state(None)
    await message.answer("Выбери интересующий вопрос:", reply_markup=faq_keyboard) 

@router.message(lambda msg: msg.text == "⬅️ Назад в меню")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()  # Сброс FSM состояния
    await message.answer("⬅️ Главное меню", reply_markup=main_menu)

@router.message(lambda msg: msg.text == "🚀 Начать")
async def handle_launch_button(message: types.Message, bot: Bot):
    await message.answer(
    "👋 Привет! Бот работает,для чего он? Вот что с помощью него можно сделать:\n\n"
    "🗓 Записаться на сеанс\n"
    "🖼 Посмотреть портфолио\n"
    "📚 Почитать ответы на частые вопросы\n"
    "🎲 Играть и получать баллы,их тратим в магазине\n"
    "👥Также баллы можно получать приглашая друзей\n"
    "🛍 Совершать покупки в магазине за баллы,получи бесплатное тату!🙀\n"   
    "🗣 Можно оставить отзыв или задать вопрос в разделе  -прочее-, позже я на него отвечу\n\n"
    )

@router.message(IsSubscribed(), lambda msg: msg.text == "📩 Пригласить друга")
async def invite_friend(message: types.Message, state: FSMContext):
    await state.clear()  # очищаем прошлый state, если есть
    user_id = message.from_user.id
    username = (await bot.get_me()).username
    invite_link = f"https://t.me/{username}?start={user_id}"

    await message.answer(
        f"🔗 Приглашай друзей и получай баллы!\n"
        f"Они должны играть 7 дней — тогда ты получишь +12 баллов.\n\n"
        f"Твоя ссылка:\n<code>{invite_link}</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📤 Поделиться", url=f"https://t.me/share/url?url={invite_link}")]
        ])
    )

@router.message(IsSubscribed(), lambda msg: msg.text == "🎮 Игры")
async def show_games_menu(message: types.Message, state: FSMContext):
    reset_balances_if_needed()
    await state.set_state(None)

    now = datetime.now().time()
    start_time = datetime.strptime("00:00", "%H:%M").time()
    end_time = datetime.strptime("03:00", "%H:%M").time()
    is_night = start_time <= now <= end_time or message.from_user.id == ADMIN_ID

    keyboard = [
        [KeyboardButton(text="🪨 Камень-ножницы-бумага")],
        [KeyboardButton(text="🎡 Колесо Фортуны")]
    ]
    if is_night:
        keyboard.append([KeyboardButton(text="🎰 Тату-Джекпот")])

    keyboard.append([KeyboardButton(text="⬅️ Назад в меню")])

    await message.answer(
        "🎮 Выбери игру:\n\n"
        "🪨 Камень-ножницы-бумага — сыграй с ботом\n"
        "🎡 Колесо Фортуны — 1 раз в день шанс на халявные баллы\n\n"
        + ("🎰 Тату-Джекпот доступен сейчас!" if is_night else "⏳ Джекпот доступен только ночью (00:00–03:00)"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True
        )
    )

@router.callback_query(lambda c: c.data.startswith("choose_time:"))
async def start_zapis_fsm(callback: CallbackQuery, state: FSMContext):
    time = callback.data.replace("choose_time:", "")
    data = await state.get_data()
    selected_date = data.get("selected_date") or data.get("chosen_date")

    if not selected_date:
        await callback.message.answer("⚠️ Ошибка: дата не выбрана.")
        await state.clear()
        return

    await state.update_data(date_time=f"{selected_date} {time}")
        # Удаляем выбранное время из available_slots.json
    await callback.message.answer("Ты хочешь записаться на сеанс. Сколько тебе лет? (Напиши цифрами)")
    await state.set_state(ZapisFSM.age)
    await callback.answer()
    
def get_total_slot_limit(user_id: int) -> int:
    base_limit = 10
    bonus = 0
    today = datetime.now().date().isoformat()
    if os.path.exists("vip_slots.txt"):
        with open("vip_slots.txt", "r", encoding="utf-8") as f:
            for line in f:
                uid, date = line.strip().split(":")
                if uid == str(user_id) and date == today:
                    bonus += 5
    return base_limit + bonus

@router.message(IsSubscribed(), lambda msg: msg.text == "🪨 Камень-ножницы-бумага")
async def start_knb_game(message: types.Message):
    if not has_seen_warning_today(message.from_user.id):
        await message.answer(
        "⚠️ Будь осторожен. Никогда не переходи по подозрительным ссылкам,бот иногда рассылает разного характера сообщения,перехватить их невозможно❗️❗️❗️",
        disable_notification=True
    )
    log_warning_shown(message.from_user.id)
    user_id = message.from_user.id
    if not can_play_knb(user_id):
        await message.answer("⏳ Ты уже играл. Попробуй снова через час.")
        return
    await message.answer("Выбери ход:", reply_markup=knb_keyboard)
    log_game_activity(user_id)
    check_and_reward_referral(user_id)


@router.message(IsSubscribed(), lambda msg: msg.text == "🎡 Колесо Фортуны")
async def spin_wheel(message: types.Message):
    user_id = message.from_user.id

    # ✅ Проверяем лимит до блокировки
    if not can_spin_wheel(user_id):
        await message.answer("⏳ Ты уже крутил колесо сегодня. Приходи завтра!")
        return

    lock_file = f"wheel_lock_{user_id}.lock"
    if os.path.exists(lock_file):
        await message.answer("🔄 Подожди, колесо ещё крутится!")
        return
    open(lock_file, "w").close()

    try:
        await message.answer(
            "🎡 Колесо Фортуны — что может выпасть:\n\n"
            "❌ 0 баллов\n"
            "➕ 1 балл\n"
            "➕ 2 балла\n"
            "➕ 3 балла\n"
            "🎁 5 баллов (редкость!)\n\n"
            "Начинаем вращение..."
        )

        symbols = ["🟢", "🟡", "🟠", "🟣", "🔴", "🔵"]
        msg = await message.answer("🎯 Крутится...")

        for i in range(12):
            await asyncio.sleep(0.25 + i * 0.02)
            await msg.edit_text(f"🎯 Крутится... {symbols[i % len(symbols)]}")

        await asyncio.sleep(0.5)

        reward = random.choice([0, 1, 2, 3, 5])
        add_balance(user_id, reward)
        update_wheel_log(user_id)

        if reward == 0:
            result = "😢 Сегодня не повезло. Ты не получил баллов."
        else:
            result = f"🎉 Поздравляю! Ты выиграл +{reward} балл(ов)!"

        await msg.edit_text(f"🎡 Колесо остановилось!\n\n{result}")  

        log_game_activity(user_id)
        check_and_reward_referral(user_id)

    finally:
        if os.path.exists(lock_file):
            os.remove(lock_file)

@router.message(IsSubscribed(), lambda msg: msg.text == "⚙️ Прочее")
async def show_other_menu(message: types.Message, state: FSMContext):
    await state.set_state(None)
    await message.answer("📂 Дополнительные функции:", reply_markup=other_menu)  

@router.message(IsSubscribed(), lambda msg: msg.text == "🛍 Магазин")
async def show_shop(message: types.Message, state: FSMContext):
    reset_balances_if_needed()
    await state.clear()
    user_id = message.from_user.id
    points = get_balance(user_id)
    keyboard = []

    for code, item in SHOP_ITEMS.items():
        price = item["price"]
        name = item["name"]

        if points >= price and (item.get("limit") != "monthly" or can_buy_limited_item(user_id, code)):
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{name} — {price} баллов",
                    callback_data=f"confirm_{code}"
                )
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"🔒 {name} — {price} баллов",
                    callback_data="unavailable"
                )
            ])

    await message.answer(
        f"🛍 Магазин (у тебя {points} баллов):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.message(ZapisFSM.age)
async def get_age(message: types.Message, state: FSMContext):
    

    try:
        age = int(message.text)
        if age < 18:
            await message.answer("🚫 Мне жаль, но я не могу набить тату лицам младше 18 лет.")
            return

        await state.update_data(age=age)
        await message.answer(
            "Куда хочешь набить?\n" 
            "Опиши словами: рука, грудь, шея и т.п.\n"
            "Если есть шрам или старая татуировка — укажи обязательно!."
        )
        await state.set_state(ZapisFSM.area)

    except ValueError:
        await message.answer("Напиши возраст цифрами, например: 23")

@router.message(ZapisFSM.area)
async def get_area(message: types.Message, state: FSMContext):
    await state.update_data(area=message.text)
    await message.answer("Оставь свой номер телефона 📱")
    await state.set_state(ZapisFSM.phone)

@router.message(ZapisFSM.phone)
async def get_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    if not re.fullmatch(r"\+7\d{10}", phone):
        await message.answer("❗️ Введи номер в формате +7XXXXXXXXXX")
        return
    await state.update_data(phone=phone)
    await message.answer("Пришли фото эскиза:")
    await state.set_state(ZapisFSM.sketch)

@router.message(ZapisFSM.sketch)
async def get_sketch(message: types.Message, state: FSMContext, bot: Bot):
    if not message.photo:
        await message.answer("Пожалуйста, отправь именно фото эскиза 📸")
        return

    photo = message.photo[-1]
    user = message.from_user
    username = f"@{user.username}" if user.username else f"{user.first_name} {user.last_name or ''}".strip()

    # Отправляем тебе (мастеру)
    await bot.send_photo(
        ADMIN_ID,
        photo.file_id,
        caption=f"🖼 Эскиз от {username} (ID: {user.id})"
    )

    # Сохраняем file_id в состояние (вместо пути)
    await state.update_data(sketch_path=photo.file_id)

    await finish_zapis(message, state)


@router.message(ZapisFSM.date_time)
async def get_date_time(message: types.Message, state: FSMContext):
    # Сохраняем дату и время, которое ввёл пользователь
    await state.update_data(date_time=message.text)

    # Получаем все данные пользователя
    user_data = await state.get_data()

    # Проверяем, что все нужные поля есть
    required_fields = ["age", "area", "phone", "date_time"]
    missing = [field for field in required_fields if field not in user_data]

    if missing:
        await message.answer(
            "⚠️ Ошибка — ты не прошёл все шаги записи.\n"
            "Попробуй сначала нажать «✍️ Записаться» и пройти до конца."
        )
        await state.clear()
        return

    # Получаем данные с безопасным доступом
    age = user_data.get("age", "не указано")
    area = user_data.get("area", "не указано")
    phone = user_data.get("phone", "не указано")
    date_time = user_data.get("date_time", "не указано")
    sketch_path = user_data.get("sketch_path", "—")

    # Сохраняем в файл
    username = format_user(message.from_user)
    with open("zayavki.txt", "a", encoding="utf-8") as f:
        f.write(
            f"\n---\n📌 Заявка от {username}:\n"
            f"Возраст: {age}\n"
            f"Зона: {area}\n"
            f"Телефон: {phone}\n"
            f"Эскиз: {sketch_path}\n"
            f"Когда удобно: {date_time}\n"
        )

    await message.answer(
    f"✅ Заявка записана, {username}!\n\n")
    # Уведомляем администратора
    admin_id = ADMIN_ID  # из твоей переменной вверху файла
    text = (
        f"🆕 Новая заявка от {username}:\n"
        f"Возраст: {age}\n"
        f"Зона: {area}\n"
        f"Телефон: {phone}\n"
        f"Эскиз: {sketch_path}\n"
        f"Когда удобно: {date_time}"
    )
    await message.bot.send_message(admin_id, text)
    await state.clear()
    


async def finish_zapis(message: types.Message, state: FSMContext):
    user_data = await state.get_data()

    age = user_data.get("age", "—")
    area = user_data.get("area", "—")
    phone = user_data.get("phone", "—")
    date_time = user_data.get("date_time", "—")
    sketch = user_data.get("sketch_path", "—")
    username = format_user(message.from_user)

    # Логируем
    with open("zayavki.txt", "a", encoding="utf-8") as f:
        f.write(
            f"\n---\n📌 Заявка от {username}:\n"
            f"Возраст: {age}\n"
            f"Зона: {area}\n"
            f"Телефон: {phone}\n"
            f"Эскиз: {sketch}\n"
            f"Когда удобно: {date_time}\n"
        )

    await message.answer("✅ Заявка записана. Я свяжусь с тобой 🙌")
    # ⛔️ Удаляем время из available_slots.json
    try:
        date, time = date_time.strip().split()
        path = "available_slots.json"

        with open(path, "r", encoding="utf-8") as f:
            slots = json.load(f)

        if date in slots and time in slots[date]:
            slots[date].remove(time)
            if not slots[date]:  # если список стал пустой — удаляем день
                del slots[date]

        with open(path, "w", encoding="utf-8") as f:
            json.dump(slots, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"❌ Ошибка при удалении времени из слотов: {e}")
    await state.clear()

    # Уведомление мастеру
    await message.bot.send_message(
        ADMIN_ID,
        f"🆕 Заявка от {username}:\nВозраст: {age}\nЗона: {area}\nТел: {phone}\nКогда: {date_time}"
    )
     


@router.callback_query(lambda c: c.data in FAQS)
async def handle_faq_callback(callback: CallbackQuery):
    await callback.message.answer(FAQS[callback.data])
    await callback.answer()  # чтобы убрать "часики"

def can_play_knb(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True  # админ всегда может играть
    now = datetime.now()
    if not os.path.exists("game_log.txt"):
        return True
    with open("game_log.txt", "r") as f:
        for line in f:
            uid, ts = line.strip().split(":", 1)
            if str(user_id) == uid:
                last_time = datetime.fromisoformat(ts)
                return now - last_time >= timedelta(hours=1)
    return True

def update_knb_time(user_id: int):
    now = datetime.now()
    logs = {}
    if os.path.exists("game_log.txt"):
        with open("game_log.txt", "r") as f:
            for line in f:
                uid, ts = line.strip().split(":", 1)
                logs[int(uid)] = ts
    logs[user_id] = now.isoformat()
    with open("game_log.txt", "w") as f:
        for uid, ts in logs.items():
            f.write(f"{uid}:{ts}\n")

@router.callback_query(lambda c: c.data.startswith("knb_"))
async def handle_knb_choice(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not can_play_knb(user_id):
        await callback.message.answer("⏳ Ты уже играл. Попробуй снова через час.")
        await callback.answer()
        return

    user_choice = callback.data.split("_")[1]
    choices = ["rock", "scissors", "paper"]
    bot_choice = random.choice(choices)

    results = {
        ("rock", "scissors"): "win",
        ("rock", "paper"): "lose",
        ("scissors", "paper"): "win",
        ("scissors", "rock"): "lose",
        ("paper", "rock"): "win",
        ("paper", "scissors"): "lose",
    }

    if user_choice == bot_choice:
        outcome = "draw"
        reward = 1
    else:
        outcome = results.get((user_choice, bot_choice), "lose")
        reward = 3 if outcome == "win" else 0

    add_balance(user_id, reward)
    update_knb_time(user_id)

    emojis = {
        "rock": "🪨",
        "scissors": "✂️",
        "paper": "📄"
    }

    text = f"Ты выбрал: {emojis[user_choice]}\nБот выбрал: {emojis[bot_choice]}\n"

    if outcome == "win":
        text += "✅ Ты победил! +3 балла!"
    elif outcome == "draw":
        text += "🤝 Ничья. +1 балл."
    else:
        text += "❌ Ты проиграл. 0 баллов."

    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("user_date:"))
async def se_time_for_user(callback: CallbackQuery, state: FSMContext):
    date = callback.data.replace("user_date:", "")
    await state.update_data(selected_date=date)

    try:
        with open("available_slots.json", "r", encoding="utf-8") as f:
            slots = json.load(f)
    except json.JSONDecodeError:
        await callback.message.answer("⚠️ Ошибка при чтении времён.")
        await callback.answer()
        return

    times = slots.get(date, [])
    if not times:
        await callback.message.answer("⛔️ Нет доступных времён на эту дату.")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t, callback_data=f"choose_time:{t}")]
            for t in times
        ]
    )

    await callback.message.answer(
        f"🕐 Выбери удобное время на <b>{date}</b>:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("choose_time:"))
async def select_time(callback: CallbackQuery, state: FSMContext):
    time = callback.data.replace("choose_time:", "")
    data = await state.get_data()
    date = data.get("selected_date") or data.get("chosen_date")

    if not date:
        await callback.message.answer("⚠️ Ошибка: дата не выбрана.")
        return

    full_datetime = f"{date} {time}"
    await state.update_data(date_time=full_datetime)

    # Запуск FSM записи
    await callback.message.answer("Ты хочешь записаться на сеанс. Сколько тебе лет?(Строго🔞)")
    await state.set_state(ZapisFSM.age)
    await callback.answer()

def can_spin_wheel(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True  # админ всегда может крутить
    today = datetime.now().date()
    if not os.path.exists(WHEEL_LOG_FILE):
        return True
    with open(WHEEL_LOG_FILE, "r") as f:
        for line in f:
            uid, datestr = line.strip().split(":")
            if str(user_id) == uid:
                last_date = datetime.fromisoformat(datestr).date()
                return last_date < today
    return True

def update_wheel_log(user_id: int):
    today = datetime.now().date()
    logs = {}
    if os.path.exists(WHEEL_LOG_FILE):
        with open(WHEEL_LOG_FILE, "r") as f:
            for line in f:
                uid, datestr = line.strip().split(":")
                logs[int(uid)] = datestr
    logs[user_id] = today.isoformat()
    with open(WHEEL_LOG_FILE, "w") as f:
        for uid, datestr in logs.items():
            f.write(f"{uid}:{datestr}\n")

BALANCE_FILE = "user_balances.txt"

def get_balance(user_id: int) -> int:
    if not os.path.exists(BALANCE_FILE):
        return 0
    with open(BALANCE_FILE, "r") as f:
        for line in f:
            uid, balance = line.strip().split(":")
            if str(user_id) == uid:
                return int(balance)
    return 0

def add_balance(user_id: int, amount: int = 1):
    balances = {}
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r") as f:
            for line in f:
                uid, balance = line.strip().split(":")
                balances[int(uid)] = int(balance)

    balances[user_id] = balances.get(user_id, 0) + amount

    with open(BALANCE_FILE, "w") as f:
        for uid, balance in balances.items():
            f.write(f"{uid}:{balance}\n")

def can_buy_limited_item(user_id: int, item_code: str) -> bool:
    path = "purchase_limits.txt"
    if not os.path.exists(path):
        return True

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(":", 2)
            if len(parts) != 3:
                continue  # пропускаем битые строки
            uid, code, date_str = parts
            if str(user_id) == uid and code == item_code:
                try:
                    last_date = datetime.fromisoformat(date_str).date()
                    return (datetime.now().date() - last_date).days >= 30
                except:
                    continue  # если дата кривая — пропускаем
    return True

@router.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_purchase(callback: CallbackQuery):
    code = callback.data.replace("confirm_", "")
    item = SHOP_ITEMS.get(code)
    if not item:
        await callback.answer("Ошибка: товар не найден", show_alert=True)
        return

    await callback.message.answer(
    f"Подтвердить покупку: {item['name']} за {item['price']} баллов?",
    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"buy_{code}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
)
    await callback.answer()

def log_purchase(user_id: int, item_code: str):
    path = "purchase_limits.txt"
    lines = []

    # Загружаем старые строки
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    # Удаляем дубликаты (по user_id и товару)
    lines = [line for line in lines if not line.startswith(f"{user_id}:{item_code}:")]

    # Добавляем новую строку
    lines.append(f"{user_id}:{item_code}:{datetime.now().isoformat()}\n")

    # Перезаписываем файл
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    # Пишем в основной лог покупок (можно оставить)
    with open("purchase_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{user_id}:{item_code}:{datetime.now().isoformat()}\n")

@router.callback_query(lambda c: c.data.startswith("buy_"))
async def handle_purchase(callback: CallbackQuery):
    print("ПОЛУЧЕНО:", callback.data)
    user_id = callback.from_user.id
    code = callback.data.replace("buy_", "")
    item = SHOP_ITEMS.get(code)
    if not item:
        await callback.answer("❌ Ошибка", show_alert=True)
        return

    if item.get("limit") == "monthly" and not can_buy_limited_item(user_id, code):
        await callback.answer("⏳ Этот товар можно получить только раз в месяц", show_alert=True)
        return

    balance = get_balance(user_id)
    if balance < item["price"]:
        await callback.answer("❌ Недостаточно баллов", show_alert=True)
        return

    add_balance(user_id, -item["price"])
    log_purchase(user_id, code)

    await callback.message.answer(f"✅ Ты купил: {item['name']}\nТекущий баланс: {get_balance(user_id)} баллов")
            # Удаляем старую клавиатуру с кнопками
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass  # Если сообщение уже было удалено или недоступно
    
    # Уведомление мастеру
    username = format_user(callback.from_user)
    await bot.send_message(
    ADMIN_ID,
    f"🛍 Покупка в магазине:\n"
    f"👤 {username} (ID: {user_id})\n"
    f"🎁 {item['name']}\n"
    f"Баланс после: {get_balance(user_id)}"
)

@router.callback_query(lambda c: c.data == "cancel")
async def cancel_purchase(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("Отменено")

def reset_balances_if_needed():
    today = datetime.now().date()
    month_key = today.strftime("%Y-%m")

    if os.path.exists(LAST_RESET_FILE):
        with open(LAST_RESET_FILE, "r") as f:
            last = f.read().strip()
            if last == month_key:
                return  # Уже сбрасывали в этом месяце

    if today.day != 1:
        return  # Только 1-го числа

    if os.path.exists("user_data.json"):
        with open("user_data.json", "r", encoding="utf-8") as f:
            user_data = json.load(f)
    else:
        user_data = {}

    for user_id, data in user_data.items():
        points = int(data.get("points", 0))
        if points > 50:
            new_points = round(points * 0.1)
            user_data[user_id]["points"] = new_points

    with open("user_data.json", "w", encoding="utf-8") as f:
        json.dump(user_data, f, indent=2, ensure_ascii=False)

    with open(LAST_RESET_FILE, "w") as f:
        f.write(month_key)

async def get_display_name(user: types.User = None, user_id: int = None) -> str:
    if user:
        if user.username:
            return f"@{user.username}"
        else:
            return f"{user.first_name} {user.last_name or ''}".strip()

    if user_id:
        try:
            bot_instance = Bot.get_current()
            user_info = await bot_instance.get_chat(user_id)
            if user_info.username:
                return f"@{user_info.username}"
            return f"{user_info.first_name} {user_info.last_name or ''}".strip()
        except:
            return f"ID {user_id}"

    return "Неизвестный"

@router.message(lambda msg: msg.text == "🏆 Лидеры")
async def show_leaders(message: types.Message):
    if not os.path.exists(BALANCE_FILE):
        await message.answer("Пока нет данных.")
        return

    balances = []
    with open(BALANCE_FILE, "r") as f:
        for line in f:
            uid, bal = line.strip().split(":")
            balances.append((int(uid), int(bal)))

    top = sorted(balances, key=lambda x: x[1], reverse=True)[:3]
    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 <b>Топ 3 участников по баллам:</b>\n\n"

    for i, (uid, bal) in enumerate(top):
        try:
            user_info = await bot.get_chat(uid)
            name = f"@{user_info.username}" if user_info.username else user_info.full_name
        except:
            name = f"ID {uid}"

        text += f"{medals[i]} {name}: {bal} баллов\n"

    await message.answer(text, parse_mode="HTML")

@router.message(lambda msg: msg.text == "📆 Заявки по дате" and msg.from_user.id == ADMIN_ID)
async def ask_for_date(message: types.Message, state: FSMContext):
    await message.answer("🗓 Напиши дату в формате: 27.06.2025")
    await state.set_state(FilterFSM.wait_for_date)

@router.message(FilterFSM.wait_for_date)
async def show_filtered_zayavki(message: types.Message, state: FSMContext):
    date_str = message.text.strip()
    await state.clear()

    if not re.match(r"\d{2}\.\d{2}\.\d{4}", date_str):
        await message.answer("⚠️ Неверный формат. Введи дату как: 27.06.2025")
        return

    path = "zayavki.txt"
    if not os.path.exists(path):
        await message.answer("❌ Заявок нет.")
        return

    with open(path, "r", encoding="utf-8") as f:
        entries = f.read().split("---")

    found = []
    for entry in entries:
        if date_str in entry:
            found.append(entry.strip())

    if not found:
        await message.answer(f"🫤 Заявок на {date_str} не найдено.")
    else:
        for item in found:
            await message.answer(f"📌 Заявка:\n{item}")    

@router.message(lambda msg: msg.text == "📊 Мой баланс")
async def show_my_balance(message: types.Message):
    balance = get_balance(message.from_user.id)
    await message.answer(f"📊 У тебя сейчас: {balance} баллов")

    



def check_and_reward_referral(user_id: int):
    import asyncio

    invited_by = None
    log_path = "referral_log.txt"
    paid_path = "referral_paid.txt"
    activity_path = "activity_log.txt"

    # 1. Ищем пригласившего
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) != 2:
                    continue
                uid, ref = parts
                if str(user_id) == uid:
                    invited_by = int(ref)
                    break

    if not invited_by:
        return  # не по реферальной ссылке

    # 2. Проверка: уже начисляли?
    if os.path.exists(paid_path):
        with open(paid_path, "r", encoding="utf-8") as f:
            already_paid = set(line.strip() for line in f if line.strip())
        if str(user_id) in already_paid:
            return  # уже начисляли

    # 3. Проверка: играл ли 3 дня (или 7 — на выбор)
    days = set()
    if os.path.exists(activity_path):
        with open(activity_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) != 2:
                    continue
                uid, date = parts
                if str(user_id) == uid:
                    days.add(date)

    if len(days) < 3:  # ← можешь поставить 7 если хочешь
        return

    # 4. Начисляем бонус
    add_balance(user_id, 5)
    add_balance(invited_by, 12)

    with open(paid_path, "a", encoding="utf-8") as f:
        f.write(f"{user_id}\n")

    # 5. Уведомляем пригласившего
    asyncio.create_task(bot.send_message(
        invited_by,
        f"🎉 Твой друг активен 3 дня! Ты получил +12 баллов 🎯"
    ))

def log_game_activity(user_id: int):
    today = datetime.now().date().isoformat()
    path = "activity_log.txt"
    lines = []

    if os.path.exists(path):
        with open(path, "r") as f:
            lines = f.readlines()

    # Уникальный ключ по юзеру и дате
    entry = f"{user_id}:{today}\n"
    if entry not in lines:
        lines.append(entry)
        with open(path, "w") as f:
            f.writelines(lines)

def format_user(user: types.User) -> str:
    if user.username:
        return f"@{user.username}"
    else:
        return f"{user.first_name} {user.last_name or ''}".strip()
    
@router.channel_post()
async def handle_channel_post(message: types.Message):
    # Проверка, что сообщение из нужного канала
    if message.chat.id != -1002651916205 or not is_broadcast_enabled():  # заменишь на свой ID
        return

    for user_id in get_all_user_ids():  # функция читает из users.txt
        try:
            await message.copy_to(chat_id=user_id)
        except:
            pass  # пользователь заблокировал бота или ошибка

def get_all_user_ids():
    with open("barnaul_users.txt", "r", encoding="utf-8") as f:
        return [int(line.strip()) for line in f if line.strip().isdigit()]
    
@router.message(lambda msg: msg.text == "🛠 Админ-панель" and msg.from_user.id == ADMIN_ID)
async def show_admin_panel(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/Календарь"), KeyboardButton(text="📖 Заявки")],
            [KeyboardButton(text="🔁 Рассылка: вкл/выкл")],
            [KeyboardButton(text="🛒 Покупки")],
            [KeyboardButton(text="🧹 Очистить логи")],
            [KeyboardButton(text="/сброс адми")],
            [KeyboardButton(text="/вопросы")],
            [KeyboardButton(text="⬅️ Назад в меню")]
        ],
        resize_keyboard=True
    )
    await message.answer("🔧 Админ-панель. Выбери действие:", reply_markup=keyboard)

@router.message(lambda msg: msg.text == "🧹 Очистить логи" and msg.from_user.id == ADMIN_ID)
async def clean_logs_button(message: Message):
    await message.answer("♻️ Логи очищаются, отправляю архив...")
    archive_name = clear_and_collect_logs()  # создаёт zip или txt
    try:
        await bot.send_document(ADMIN_ID, FSInputFile(archive_name))
    except Exception as e:
        await message.answer(f"❗️ Ошибка при отправке: {e}")
    else:
        await message.answer("✅ Логи отправлены и очищены.")
    finally:
        os.remove(archive_name)  # удалим архив после отправки    
 
 

@router.message(lambda msg: msg.text == "🔁 Рассылка: вкл/выкл" and msg.from_user.id == ADMIN_ID)
async def toggle_broadcast_command(message: types.Message):
    new_status = toggle_broadcast()
    await message.answer(f"🔁 Рассылка теперь {'включена ✅' if new_status else 'выключена ⛔️'}")    



def is_broadcast_enabled() -> bool:
    if not os.path.exists(BROADCAST_FLAG_FILE):
        return True  # по умолчанию включено
    with open(BROADCAST_FLAG_FILE, "r") as f:
        return f.read().strip() == "on"

def toggle_broadcast():
    current = is_broadcast_enabled()
    with open(BROADCAST_FLAG_FILE, "w") as f:
        f.write("off" if current else "on")
    return not current        

@router.callback_query(lambda c: c.data.startswith("nav_month:"))
async def navigate_month(callback: CallbackQuery):
    _, direction, year, month = callback.data.split(":")
    year, month = int(year), int(month)

    if direction == "prev":
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    elif direction == "next":
        month += 1
        if month == 13:
            month = 1
            year += 1

    keyboard = generate_calendar(year, month)
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except TelegramBadRequest:
        await callback.message.answer("⚠️ Ошибка при обновлении календаря.")
    await callback.answer()

def generate_calendar(year: int, month: int) -> InlineKeyboardMarkup:
    cal = calendar.monthcalendar(year, month)
    buttons = []

    # Название месяца и стрелки
    month_name = calendar.month_name[month]
    buttons.append([
    InlineKeyboardButton(text="←", callback_data=f"nav_month:prev:{year}:{month}"),
    InlineKeyboardButton(text=f"{month_name} {year}", callback_data="ignore"),
    InlineKeyboardButton(text="→", callback_data=f"nav_month:next:{year}:{month}")
    ])

    # Дни недели
    buttons.append([
        InlineKeyboardButton(text="Пн", callback_data="ignore"),
        InlineKeyboardButton(text="Вт", callback_data="ignore"),
        InlineKeyboardButton(text="Ср", callback_data="ignore"),
        InlineKeyboardButton(text="Чт", callback_data="ignore"),
        InlineKeyboardButton(text="Пт", callback_data="ignore"),
        InlineKeyboardButton(text="Сб", callback_data="ignore"),
        InlineKeyboardButton(text="Вс", callback_data="ignore")
    ])

    # Календарь дней
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                date_str = f"{day:02}.{month:02}.{year}"
                row.append(InlineKeyboardButton(text=str(day), callback_data=f"admin_date:{date_str}"))
        buttons.append(row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(lambda c: c.data.startswith("nav_month:"))
async def navigate_month(callback: CallbackQuery):
    try:
        _, direction, year, month = callback.data.split(":")
        year = int(year)
        month = int(month)

        if direction == "prev":
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        elif direction == "next":
            month += 1
            if month == 13:
                month = 1
                year += 1

        keyboard = generate_calendar(year, month)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer()
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при переключении месяца: {e}")

@router.message(lambda msg: msg.text == "📖 Заявки" and msg.from_user.id == ADMIN_ID)
async def show_zayavki(message: types.Message):
    path = "zayavki.txt"
    if not os.path.exists(path):
        await message.answer("📭 Пока нет заявок.")
        return

    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        await message.answer("📭 Пока нет заявок.")
        return

    # Если заявок много — отправим несколькими сообщениями
    for block in text.split("---"):
        block = block.strip()
        if block:
            await message.answer(f"📌 Заявка:\n{block}")            


@router.message(lambda msg: msg.text == "🛒 Покупки")
async def show_purchase_log(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return  # Только админ видит

    path = "purchase_log.txt"
    if not os.path.exists(path):
        await message.answer("⛔️ Нет записей о покупках.")
        return

    with open(path, "r", encoding="utf-8") as f:
        logs = f.read().strip()

    if not logs:
        await message.answer("⛔️ Лог пуст.")
        return

    # Если лог слишком длинный — режем
    MAX_CHARS = 4000
    for chunk in [logs[i:i+MAX_CHARS] for i in range(0, len(logs), MAX_CHARS)]:
        await message.answer(f"🛒 Покупки:\n\n{chunk}")



async def get_username_from_id(user_id: int) -> str:
    try:
        bot_instance = Bot.get_current()
        user = await bot_instance.get_chat(user_id)
        if user.username:
            return f"@{user.username}"
        elif user.first_name:
            return f"{user.first_name} {user.last_name or ''}".strip()
    except:
        pass
    return f"@user_{user_id}"

class QuestionAdminFSM(StatesGroup):
    current_index = State()

@router.message(lambda msg: msg.text == "/вопросы" and msg.from_user.id == ADMIN_ID)
async def view_questions(message: types.Message, state: FSMContext):
    if not os.path.exists("questions.txt"):
        await message.answer("❌ Нет вопросов.")
        return

    with open("questions.txt", "r", encoding="utf-8") as f:
        raw = f.read()

    blocks = [b.strip() for b in raw.split("---") if b.strip()]
    if not blocks:
        await message.answer("❌ Нет записей.")
        return

    await state.update_data(blocks=blocks)
    await state.update_data(current_index=0)
    await show_question_block(message, blocks, 0)
    await state.set_state(QuestionAdminFSM.current_index)

async def show_question_block(message: types.Message, blocks: list, index: int):
    block = blocks[index]
    text = f"<b>Вопрос #{index + 1}</b>\n\n{block}"

    keyboard = [
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_q:{index}")]
    ]
    if index < len(blocks) - 1:
        keyboard.append([InlineKeyboardButton(text="➡️ Далее", callback_data="next_q")])

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")

@router.callback_query(lambda c: c.data == "next_q")
async def next_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    blocks = data.get("blocks", [])
    index = data.get("current_index", 0) + 1

    if index >= len(blocks):
        await callback.message.answer("✅ Это был последний вопрос.")
        await state.clear()
        await callback.answer()
        return

    await state.update_data(current_index=index)
    await show_question_block(callback.message, blocks, index)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("delete_q:"))
async def delete_question(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split(":")[1])

    data = await state.get_data()
    blocks = data.get("blocks", [])
    
    if index >= len(blocks):
        await callback.message.answer("❌ Ошибка: индекс вне диапазона.")
        await state.clear()
        return

    deleted = blocks.pop(index)

    # Обновляем файл
    with open("questions.txt", "w", encoding="utf-8") as f:
        for block in blocks:
            f.write(f"---\n{block.strip()}\n")

    if not blocks:
        await callback.message.answer("🗑 Вопрос удалён. Больше вопросов нет.")
        await state.clear()
        await callback.answer()
        return

    new_index = min(index, len(blocks) - 1)
    await state.update_data(blocks=blocks, current_index=new_index)
    await callback.message.answer("🗑 Вопрос удалён.")
    await show_question_block(callback.message, blocks, new_index)
    await callback.answer()

@router.message(Command("clean_logs"))  # или свою кнопку
async def clean_logs_command(message: Message):
    archive_file = archive_and_clear_logs()
    await message.answer("✅ Логи очищены. Архив отправляю:")
    with open(archive_file, "rb") as f:
        await bot.send_document(ADMIN_ID, f)

@router.message(lambda msg: msg.text == "❌ Отменить отзыв")
async def cancel_question(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отзыв отменён. Ты в главном меню.", reply_markup=main_menu)

@router.message(lambda msg: msg.text == "✍️ опубликовать вопрос или написать отзыв(анонимно или публично)")
async def ask_question(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(QuestionFSM.text)
    cancel_question_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отменить отзыв")]],
        resize_keyboard=True
    )
    await message.answer("✏️ Напиши свой вопрос или отзыв:", reply_markup=cancel_question_kb)

@router.message(lambda msg: msg.text.startswith("/сброс адми"))
async def manual_reset_command(message: types.Message):
    user_id = message.from_user.id
    is_admin = user_id == ADMIN_ID  # замени на свою переменную

    if not is_admin:
        await message.answer("🚫 У тебя нет доступа к этой команде.")
        return

    try:
        parts = message.text.strip().split()
        password = parts[1] if len(parts) > 1 else ""
    except:
        password = ""

    if password != "админ":  # ❗️ Задай свой пароль здесь
        await message.answer("❌ Неверный пароль для сброса.")
        return

    # Выполняем ручной сброс
    today = datetime.now().date()
    month_key = today.strftime("%Y-%m")

    if os.path.exists("user_data.json"):
        with open("user_data.json", "r", encoding="utf-8") as f:
            user_data = json.load(f)
    else:
        user_data = {}

    count = 0
    for user_id, data in user_data.items():
        points = int(data.get("points", 0))
        if points > 100:
            new_points = round(points * 0.1)
            user_data[user_id]["points"] = new_points
            count += 1

    with open("user_data.json", "w", encoding="utf-8") as f:
        json.dump(user_data, f, indent=2, ensure_ascii=False)

    # обновляем лог
    with open("last_reset.txt", "w") as f:
        f.write(month_key)

    await message.answer(f"✅ Баллы сброшены вручную у {count} пользователей.")
























# Запуск бота
async def main():
    reset_balances_if_needed()
    await bot.delete_webhook(drop_pending_updates=True)
    # Убираем все команды, оставляем только /start
    await bot.set_my_commands([
    types.BotCommand(command="start", description="Запуск бота")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    print(" Бот запущен и ждёт команды в Telegram...")
    asyncio.run(main())
    
