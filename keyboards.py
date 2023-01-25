from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('◄ Назад', callback_data="back")]])
close = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('❌ Закрити', callback_data="close")]])
check_error = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('Cпробувати ще раз', callback_data="start_check")], [InlineKeyboardButton('◄ Назад', callback_data="back")]])

menu = InlineKeyboardMarkup(inline_keyboard=
        [
            [InlineKeyboardButton('📝 Сортувати слова', callback_data="start_sort")],
            [InlineKeyboardButton('🔎 Перевіряти слова', callback_data="start_check")],
            [InlineKeyboardButton('📊 Статистика', callback_data="stats")],
            [InlineKeyboardButton('🛃 Останні дії користувачів', callback_data="last")],
        ])

def check(word:str, lst:int): # lst - id списку слів (often, rarely, never)
    kb = InlineKeyboardMarkup(inline_keyboard=
        [
            [InlineKeyboardButton('✅ Так', callback_data=f"yes_{word}_{lst}")],
            [
                InlineKeyboardButton('🟢 Часто', callback_data=f"no_{word}_{lst}_0"),
                InlineKeyboardButton('🟠 Рідко', callback_data=f"no_{word}_{lst}_1"),
                InlineKeyboardButton('🔴 Ніколи', callback_data=f"no_{word}_{lst}_2"),
            ],
            [
                InlineKeyboardButton('🤷🏼‍♀️ Не знаю', callback_data="start_check"),
                InlineKeyboardButton('❔ Про слово', callback_data=f"info_{word}"),
            ],
            [InlineKeyboardButton('◄ Назад', callback_data="back")]
        ])
    kb.inline_keyboard[1].pop(lst)
    return kb

def sort(word:str):
    return InlineKeyboardMarkup(inline_keyboard=
        [
            [InlineKeyboardButton('🟢 Часто / Слово всі знають', callback_data=f"often_{word}")],
            [
                InlineKeyboardButton('🟠 Рідко', callback_data=f"rarely_{word}"),
                InlineKeyboardButton('🔴 Ніколи', callback_data=f"never_{word}"),
            ],
            [
                InlineKeyboardButton('🤷🏼‍♀️ Не знаю', callback_data="start_sort"),
                InlineKeyboardButton('❔ Про слово', callback_data=f"info_{word}"),
            ],
            [InlineKeyboardButton('◄ Назад', callback_data="back")]
        ])

def reload(reload_data:str):
    return InlineKeyboardMarkup(inline_keyboard=
        [
            [
                InlineKeyboardButton('🔁 Оновити', callback_data=reload_data),
                InlineKeyboardButton('◄ Назад', callback_data="back")
            ]
        ])

last = InlineKeyboardMarkup(inline_keyboard=
        [
            [
                InlineKeyboardButton('🔁 Оновити', callback_data="last"),
                InlineKeyboardButton('↕️ Більше', callback_data="last_full")
            ],
            [InlineKeyboardButton('◄ Назад', callback_data="back")]
        ])
