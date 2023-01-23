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
words = {}
for i in range(3, 9):
    words[i] = all.find_one({"_id": i})['words']
# checks = [ i for i in check.find() ]
# print(checks)
print("Database loaded")

def new_user(user):
    if str(user.id) in all.find_one({'_id': 0})["stats"]: return
    all.update_one({'_id': 0}, {"$set": { f'stats.{user.id}': {'name': user.full_name, 'sort':0, 's0':0, 's1':0, 's2':0, 'check':0, 'cy':0, 'cn':0} }})

def get_word(leng:int, _loop:int=0):
    _loop+=1
    if leng > 8 or _loop > 100:
        config.leng_sort_word = 3
        return None
    l = len(words[leng])
    if l == 0:
        config.leng_sort_word = leng+1
        return get_word(leng+1, _loop)
    return words[leng][randint(0, l-1)]

def get_check(user_name:str):
    cursor = check.find({'user':{'$ne': user_name}})
    lst = [ i for i in cursor ]
    if len(lst) == 0: return None
    return lst[randint(0, len(lst)-1)]

async def sort_word(word:str, lst:int, user):
    l = len(word)
    if not word in all.find_one({'_id': l})["words"]: print(f"Error sort_word | {word} - {lst} - {user.full_name}"); return
    words[l].remove(word)
    all.update_one({"_id": l}, {"$pull": { "words": word }})
    all.update_one({'_id': 0}, {'$inc': {"stats.all.sort": 1, f"stats.all.s{lst}": 1, f'stats.{user.id}.sort': 1, f'stats.{user.id}.s{lst}': 1}})
    all.update_one({'_id': 0}, {'$set': {f"stats.{user.id}.name": user.full_name}})
    sort[lst].update_one({"_id": l}, {"$push": { "words": word }})
    check.insert_one({'word': word, 'list': lst, 'user': user.full_name})

async def check_yes(word:str, user_id:int):
    l = len(word)
    if check.find_one({'word': word}) is None: print(f"Error check_yes | {word} - {user_id}"); return
    check.delete_one({'word': word})
    all.update_one({'_id': 0}, {'$inc': {"stats.all.check": 1, f"stats.all.cy": 1, f'stats.{user_id}.check': 1, f'stats.{user_id}.cy': 1}})

async def check_no(word:str, lst:int, user_id:int):
    l = len(word)
    if check.find_one({'word': word}) is None: print(f"Error check_no | {word} - {lst} - {user_id}"); return
    words[l].append(word)
    all.update_one({"_id": l}, {"$push": { "words": word }})
    all.update_one({'_id': 0}, {'$inc': {"stats.all.check": 1, f"stats.all.cn": 1, f'stats.{user_id}.check': 1, f'stats.{user_id}.cn': 1, "stats.all.sort": -1, f"stats.all.s{lst}": -1}})
    sort[lst].update_one({"_id": l}, {"$pull": { "words": word }})
    check.delete_one({'word': word})

def get_stats():
    return all.find_one({'_id': 0})["stats"]

def add_action(action:str):
    global last_actions
    today = datetime.datetime.today()
    action = f'\n({today.hour}:{today.minute}:{today.second}) {action};'
    last_actions.insert(0, action)
    if len(last_actions) >= config.max_history_leng: last_actions.pop()

def get_last_actions() -> str:
    global last_actions
    text = f'🛃 Останні дії користувачів ({len(last_actions)} записів)\n'
    for a in last_actions: text += a
    return text
