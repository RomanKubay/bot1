from pymongo import MongoClient
from random import randint
import datetime
import config

# load database
client = MongoClient(config.MONGODB_HOST)
all = client.sortwordsbot.all
sort = (client.sortwordsbot.often, client.sortwordsbot.rarely, client.sortwordsbot.never)
check = client.sortwordsbot.check

last_actions = []
sort_words = []
words = {}
for i in range(3, 9):
    words[i] = all.find_one({"_id": i})['words']
# checks = [ i for i in check.find() ]
# print(checks)
print("Database loaded")

def new_user(user):
    if str(user.id) in all.find_one({'_id': 0})["users"]: return
    all.update_one({'_id': 0}, {"$set": { f'users.{user.id}': {'name': user.full_name, 's0':0, 's1':0, 's2':0, 'cy':0, 'cn':0} }})

def get_word(leng:int, ban_word:str=None, _loop:int=0):
    _loop+=1
    if leng > 8 or _loop > 20:
        config.leng_sort_word = 3
        return None
    l = len(words[leng])
    if l == 0 or (l == 0 and words[leng][0] == ban_word):
        config.leng_sort_word = leng+1
        return get_word(leng+1, _loop)

    for _ in range(40):
        word = words[leng][randint(0, l-1)]
        if word != ban_word: break
    return word

def get_check(user_name:str, ban_word:str=None):
    cursor = check.find({'user':{'$ne': user_name}})
    lst = [i for i in cursor if i['word'] != ban_word]
    if len(lst) == 0: return None
    return lst[randint(0, len(lst)-1)]
# print(get_check("user_name"))

async def sort_word(word:str, lst:int, user):
    l = len(word)
    if  word in sort_words: print(f"Error sort_word | {word} - {lst} - {user.full_name}"); return
    sort_words.append(word)
    words[l].remove(word)
    all.update_one({"_id": l}, {"$pull": { "words": word }})
    all.update_one({'_id': 0}, {'$inc': {f'users.{user.id}.s{lst}': 1}})
    all.update_one({'_id': 0}, {'$set': {f"users.{user.id}.name": user.full_name}})
    check.insert_one({'word': word, 'list': lst, 'user': user.full_name})

async def check_yes(word:str, lst:int, user_id:int):
    if check.find_one({'word': word}) is None: print(f"Error check_yes | {word} - {user_id}"); return
    if word in sort_words: sort_words.remove(word)
    check.delete_one({'word': word})
    sort[lst].update_one({"_id": len(word)}, {"$push": { "words": word }})
    all.update_one({'_id': 0}, {'$inc': {"users.all.cy": 1, f'users.{user_id}.cy': 1, f"users.all.s{lst}": 1}})

async def check_no(word:str, lst:int, new_lst:int, user):
    if check.find_one({'word': word}) is None: print(f"Error check_no | {word} - {lst} - {user.id}"); return
    all.update_one({'_id': 0}, {'$inc': {"users.all.cn": 1, f'users.{user.id}.cn': 1}})
    check.update_one({'word': word}, {'$set': {"list": new_lst, 'user': user.full_name}})

def get_users():
    return all.find_one({'_id': 0})["users"]

def add_action(action:str):
    global last_actions
    today = datetime.datetime.today()
    hour = today.hour + 2
    if hour >= 24: hour =- today.hour
    action = f'\n({hour}:{today.minute}:{today.second}) {action};'
    last_actions.insert(0, action)
    if len(last_actions) > config.max_history_leng_full: last_actions.pop()

def get_last_actions(full:bool=False) -> str:
    global last_actions
    text = f'🛃 Останні дії користувачів ({len(last_actions)} записів)\n'

    if (full):
        for a in last_actions: text += a
    else:
        i = 0
        for a in last_actions:
            text += a
            i += 1
            if i > config.max_history_leng: break
    return text
