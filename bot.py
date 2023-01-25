from aiogram import Bot, Dispatcher, executor, types
from requests_html import HTMLSession

import asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import config
import keyboards as kb
import database as db

# Load bot
bot = Bot(token=config.API_KEY)
dp = Dispatcher(bot)

# Parsing
session = HTMLSession()
headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'}

# user.id: [Ім’я користувача, слово, ост. повідом. бота]
temp = {}

@dp.message_handler(commands=['start'], commands_prefix='!/')
async def start_command(message: types.Message):
    print("Start command: ", message.from_user.full_name, message.from_user.username, message.from_id)
    db.new_user(message.from_user)
    msg = await message.answer("Привітик!)\nЩо хочеш робити?", reply_markup=kb.menu)
    await message.delete()
    new_temp_data(message.from_user)
    if temp[message.from_id]['msg'] is not None:
        await delete_last_msg(message.from_id)
    temp[message.from_id]['msg'] = msg.message_id
@dp.message_handler(commands=['menu'], commands_prefix='!/')
async def menu_command(message: types.Message):
    msg = await message.answer("Що хочете робити?", reply_markup=kb.menu)
    await message.delete()
    new_temp_data(message.from_user)
    if temp[message.from_id]['msg'] is not None:
        await delete_last_msg(message.from_id)
    temp[message.from_id]['msg'] = msg.message_id


async def next_sort(user_id:int):
    word = db.get_word(config.leng_sort_word)
    if word is None:
        await bot.send_message(user_id, f'❌ Помилка!\nСлова закінчилися. Тепер ви можете перевіряти, чи інші люди нормально сортували слова (/check)', reply_markup=kb.back)
        return
    temp[user_id]['word'] = word
    msg = await bot.send_message(user_id, f'📝 <i>Режим сортування</i>\n<b>Читайте уважно!</b>\n\nЯк часто вживається слово <b>"{word}"</b>?', "HTML", reply_markup=kb.sort(word))
    temp[user_id]['msg'] = msg.message_id

async def next_check(user):
    item = db.get_check(user.full_name, temp[user.id]['word'])
    if item is None:
        await bot.send_message(user.id, f'❌ Помилка!\nСлів для перевірки не знайдено. Можливо вони закінчилися', reply_markup=kb.check_error)
        return
    temp[user.id]['word'] = item['word']
    freq = ['🟢 Часто', '🟠 Рідко', '🔴 Ніколи']
    msg = await bot.send_message(user.id, f'🔎 <i>Режим перевірки</i>\n<b>Читайте уважно!</b>\n\nКористувач <i>{item["user"]}</i> сказав, що\n\nслово <b>"{item["word"]}"</b>\nвживається <b>{freq[item["list"]]}</b>.\n\nЦе правда? <i>Якщо ні, то виберіть інший варіант</i>', "HTML", reply_markup=kb.check(item["word"], item["list"]))
    temp[user.id]['msg'] = msg.message_id

async def send_stats(user_id:int):
    users = db.get_users()
    all_sort = users["all"]["s0"] + users["all"]["s1"] + users["all"]["s2"]
    all_check = users["all"]["cy"] + users["all"]["cn"]
    text = f'📊 <b>Статистика\n\n📝 Кількість відсортованих слів: {all_sort}</b>\n — 🟢 Часто - <b>{users["all"]["s0"]}</b>\n — 🟠 Рідко - <b>{users["all"]["s1"]}</b>\n — 🔴 Ніколи - <b>{users["all"]["s2"]}</b>\n\n<b>🔎 Кількість перевірок: {all_check}</b>\n — ✅ К-сть схвалених слів - <b>{users["all"]["cy"]}</b>\n — ❌ Не схвалено <b>{users["all"]["cn"]}</b> разів\n\n👥 Користувачі:'

    for i in users:
        if i == "all": continue
        u = users[i] # User
        text += f'\n — {u["name"]} ({(u["sort"] + u["check"])})\n • 📝 {u["sort"]} → 🟢 {u["s0"]} | 🟠 {u["s1"]} | 🔴 {u["s2"]}\n • 🔎 {u["check"]} → ✅ {u["cy"]} | ❌ {u["cn"]}\n'

    msg = await bot.send_message(user_id, text, "HTML", reply_markup=kb.reload("stats"))
    temp[user_id]['word'] = None
    temp[user_id]['msg'] = msg.message_id

async def send_last_actions(user_id:int, full:bool=False):
    if full: keyboard = kb.reload("last")
    else: keyboard = kb.last
    msg = await bot.send_message(user_id, db.get_last_actions(full), reply_markup=keyboard)
    temp[user_id]['word'] = None
    temp[user_id]['msg'] = msg.message_id

@dp.callback_query_handler(lambda callback_query: True)
async def callback(call: types.CallbackQuery):
    new_temp_data(call.from_user)
    match (call.data):
        case 'back':
            msg = await call.message.answer("Що хочете робити?", reply_markup=kb.menu)
            temp[call.from_user.id]['msg'] = msg.message_id
            temp[call.from_user.id]['word'] = None
            
        case 'close': pass
        case 'stats': await send_stats(call.from_user.id)
        case 'last': await send_last_actions(call.from_user.id)
        case 'last_full': await send_last_actions(call.from_user.id, True)

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
                    db.add_action(f'📝 {call.from_user.full_name} → слово "{data[1]}" до 🟢 Часто')
                case "rarely":
                    await next_sort(call.from_user.id)
                    await call.message.delete()
                    await call.answer(f"{data[1]} - 🟠 Рідко")
                    await db.sort_word(data[1], 1, call.from_user)
                    db.add_action(f'📝 {call.from_user.full_name} → слово "{data[1]}" до 🟠 Рідко')
                case "never":
                    await next_sort(call.from_user.id)
                    await call.message.delete()
                    await call.answer(f"{data[1]} - 🔴 Ніколи")
                    await db.sort_word(data[1], 2, call.from_user)
                    db.add_action(f'📝 {call.from_user.full_name} → слово "{data[1]}" до 🔴 Ніколи')
                    
                case "yes":
                    await call.message.delete()
                    await call.answer(f"✅ Слово {data[1]} записано!")
                    await db.check_yes(data[1], int(data[2]), call.from_user.id)
                    await next_check(call.from_user)
                    db.add_action(f'🔎 {call.from_user.full_name} схвалив слово "{data[1]}" у {("🟢 Часто", "🟠 Рідко", "🔴 Ніколи")[int(data[2])]}')
                case "no":
                    await call.message.delete()
                    await call.answer(f'{data[1]} - {("🟢 Часто", "🟠 Рідко", "🔴 Ніколи")[int(data[3])]}')
                    await db.check_no(data[1], int(data[2]), int(data[3]), call.from_user)
                    await next_check(call.from_user)
                    db.add_action(f'🔎 {call.from_user.full_name} вважає, що слову "{data[1]}" місце у {("🟢 Часто", "🟠 Рідко", "🔴 Ніколи")[int(data[3])]}, а не в {("🟢 Часто", "🟠 Рідко", "🔴 Ніколи")[int(data[2])]}')

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
    await message.answer(temp.__str__(), reply_markup=kb.close)
    await message.delete()


@dp.message_handler()
async def msg_handler(message: types.Message):
    print("Get Message")
    if not " " in message.text and not message.text.isnumeric():
        await message.answer(get_info(message.text), reply_markup=kb.close)
    await message.delete()


def new_temp_data(user):
    if not user.id in temp: temp[user.id] = {'name':user.full_name, 'word':None, 'msg':None}

async def delete_last_msg(user_id:int):
    try: await bot.delete_message(user_id, temp[user_id]['msg'])
    except: pass

if __name__ == "__main__":
    print("Bot is running")
    executor.start_polling(dp, skip_updates=True)
