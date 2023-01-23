from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import CallbackQuery, Message
import aiogram.utils.markdown as fmt
import datetime
from random import randint
from requests_html import HTMLSession

import config
import database as db
import keyboards as kb

# Load bot
bot = Bot(token=config.API_KEY)
dp = Dispatcher(bot)

# Parsing
session = HTMLSession()
headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'}

# user.id: [Ім’я користувача, (Час останньої дії користувача, Текст ЧОДК), слово, ост. повідом. бота]
users = {}

@dp.message_handler(commands=['start'], commands_prefix='!/')
async def start_command(message: types.Message):
    print("Start command: ", message.from_user.full_name, message.from_user.username, message.from_id)
    db.new_user(message.from_user)
    msg = await message.answer("Привітик!)\nЩо хочеш робити?", reply_markup=kb.menu)
    await message.delete()
    update_last_time(message.from_user)
    if users[message.from_id][3] is not None:
        await delete_last_msg(message.from_id)
    users[message.from_id][3] = msg.message_id
@dp.message_handler(commands=['menu'], commands_prefix='!/')
async def menu_command(message: types.Message):
    msg = await message.answer("Що хочете робити?", reply_markup=kb.menu)
    await message.delete()
    update_last_time(message.from_user)
    if users[message.from_id][3] is not None:
        await delete_last_msg(message.from_id)
    users[message.from_id][3] = msg.message_id

@dp.message_handler(commands=['sort'], commands_prefix='!/')
async def sort_command(message: types.Message):
    await next_sort(message.from_id)
    await message.delete()
    if message.from_id in users and users[message.from_id][3] is not None:
        await delete_last_msg(message.from_id)

@dp.message_handler(commands=['check'], commands_prefix='!/')
async def check_command(message: types.Message):
    await next_check(message.from_user)
    await message.delete()
    if message.from_id in users and users[message.from_id][3] is not None:
        await delete_last_msg(message.from_id)

@dp.message_handler(commands=['stats'], commands_prefix='!/')
async def stats_command(message: types.Message):
    await send_stats(message.from_id)
    await message.delete()
    if message.from_id in users and users[message.from_id][3] is not None:
        await delete_last_msg(message.from_id)

@dp.message_handler(commands=['last'], commands_prefix='!/')
async def last_command(message: types.Message):
    await send_last_actions(message.from_id)
    await message.delete()
    if message.from_id in users and users[message.from_id][3] is not None:
        await delete_last_msg(message.from_id)


async def next_sort(user_id:int):
    word = db.get_word(config.leng_sort_word)
    if word is None:
        await bot.send_message(user_id, f'❌ Помилка!\nСлова закінчилися. Тепер ви можете перевіряти, чи інші люди нормально сортували слова (/check)', reply_markup=kb.back)
        return
    users[user_id][2] = word
    msg = await bot.send_message(user_id, f'📝 <i>Режим сортування</i>\n<b>Читайте уважно!</b>\n\nЯк часто вживається слово <b>"{word}"</b>?', "HTML", reply_markup=kb.sort(word))
    users[user_id][3] = msg.message_id

async def next_check(user):
    item = db.get_check(user.full_name)
    if item is None:
        await bot.send_message(user.id, f'❌ Помилка!\nСлів для перевірки не знайдено. Можливо вони закінчилися', reply_markup=kb.check_error)
        return
    users[user.id][2] = item['word']
    freq = ['🟢 Часто', '🟠 Рідко', '🔴 Ніколи']
    msg = await bot.send_message(user.id, f'🔎 <i>Режим перевірки</i>\n<b>Читайте уважно!</b>\n\nКористувач <i>{item["user"]}</i> сказав, що\n\nслово <b>"{item["word"]}"</b>\nвживається <b>{freq[item["list"]]}</b>.\n\nЦе правда?', "HTML", reply_markup=kb.check(item["word"], item["list"]))
    users[user.id][3] = msg.message_id

async def send_stats(user_id:int):
    s = db.get_stats()
    text = f'📊 <b>Статистика\n\n📝 Кількість відсортованих слів: {s["all"]["sort"]}</b>\n — 🟢 Часто - <b>{s["all"]["s0"]}</b>\n — 🟠 Рідко - <b>{s["all"]["s1"]}</b>\n — 🔴 Ніколи - <b>{s["all"]["s2"]}</b>\n\n<b>🔎 Кількість перевірок: {s["all"]["check"]}</b>\n — ✅ К-сть слів, які пройшли перевірку - <b>{s["all"]["cy"]}</b>\n — ❌ Не пройшли - <b>{s["all"]["cn"]}</b>\n\n👥 Користувачі:'

    for i in s:
        if i == "all": continue
        u = s[i] # User
        text += f'\n — {u["name"]} ({(u["sort"] + u["check"])})\n • 📝 {u["sort"]} → 🟢 {u["s0"]} | 🟠 {u["s1"]} | 🔴 {u["s2"]}\n • 🔎 {u["check"]} → ✅ {u["cy"]} | ❌ {u["cn"]}\n'

    msg = await bot.send_message(user_id, text, "HTML", reply_markup=kb.back)
    users[user_id][2] = None
    users[user_id][3] = msg.message_id

async def send_last_actions(user_id:int):
    msg = await bot.send_message(user_id, db.get_last_actions(), reply_markup=kb.back)
    users[user_id][2] = None
    users[user_id][3] = msg.message_id

@dp.message_handler()
async def msg_handler(message: types.Message):
    print("Get Message")
    if not " " in message.text and not message.text.isnumeric():
        await message.answer(get_info(message.text), reply_markup=kb.close)
    await message.delete()

@dp.callback_query_handler(lambda callback_query: True)
async def callback(call: types.CallbackQuery):
    update_last_time(call.from_user)
    match (call.data):
        case 'back':
            msg = await call.message.answer("Що хочете робити?", reply_markup=kb.menu)
            users[call.from_user.id][3] = msg.message_id
            
        case 'close': pass
        case 'stats': await send_stats(call.from_user.id)
        case 'last': await send_last_actions(call.from_user.id)

        case "start_sort": await next_sort(call.from_user.id)
        case "start_check": await next_check(call.from_user)

        case _:
            data = call.data.split("_")
            match data[0]:
                case "often":
                    await next_sort(call.from_user.id)
                    await call.message.delete()
                    await call.answer(f"{data[1]} - 🟢 Часто")
                    await db.sort_word(data[1], 0, call.from_user)
                case "rarely":
                    await next_sort(call.from_user.id)
                    await call.message.delete()
                    await call.answer(f"{data[1]} - 🟠 Рідко")
                    await db.sort_word(data[1], 1, call.from_user)
                case "never":
                    await next_sort(call.from_user.id)
                    await call.message.delete()
                    await call.answer(f"{data[1]} - 🔴 Ніколи")
                    await db.sort_word(data[1], 2, call.from_user)
                    
                case "yes":
                    await call.message.delete()
                    await call.answer(f"✅ Слово {data[1]} записано!")
                    await db.check_yes(data[1], call.from_user.id)
                    await next_check(call.from_user)
                case "no":
                    await call.message.delete()
                    await call.answer(f'❌ Слово {data[1]} повернуто назад для сортування!')
                    await db.check_no(data[1], data[2], call.from_user.id)
                    await next_check(call.from_user)

                case "info":
                    await call.message.answer(get_info(data[1]), reply_markup=kb.close)
                    await call.answer()
            return
    
    await call.message.delete()

# Получити визначення слова зі сайту       
def get_info(word:str):
    print(f"- https://slova.com.ua/word/{word}")
    r = session.get(f"https://slova.com.ua/word/{word}", headers=headers)
    defenition = r.html.find(".defenition", first=True)

    if defenition is None: text = f'Я не знаю що означає слово "{word}"'
    else: 
        text = f'Визначення слова "{word}"\n'
        i = 0
        for el in defenition.find("p", first=False):
            i += 1
            if i == 4: break
            text += f"{el.text}\n\n"
    return text

# Admin Commands
@dp.message_handler(commands=['setmaxleng'], commands_prefix='!/')
async def setmaxleng_command(message: types.Message):
    if message.get_args().isdigit():
        config.leng_sort_word = int(message.get_args())
        await message.answer(f"Розмір слів для сортування змінено на {config.leng_sort_word}", reply_markup=kb.close)
    else: 
        await message.answer(f"пиши нормально, будь ласка", reply_markup=kb.close)
    await message.delete()
@dp.message_handler(commands=['maxleng'], commands_prefix='!/')
async def maxleng_command(message: types.Message):
    await message.answer(f"Розмір слів для сортування: {config.leng_sort_word}", reply_markup=kb.close)
    await message.delete()
@dp.message_handler(commands=['getusers'], commands_prefix='!/')
async def getusers_command(message: types.Message):
    await message.answer(users.__str__(), reply_markup=kb.close)
    await message.delete()

def get_time(): 
    today = datetime.datetime.today()
    return ((today.hour*60)+today.minute, f"{today.day}.{today.month} {today.hour}:{today.minute}:{today.second}")
def update_last_time(user):
    if user.id in users: users[user.id][1] = get_time()
    else: users[user.id] = [user.full_name, get_time(), None, None]
async def delete_last_msg(user_id:int):
    try: await bot.delete_message(user_id, users[user_id][3])
    except: pass

async def on_startup(_): 
    pass

if __name__ == "__main__":
    print("Bot is running")
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
