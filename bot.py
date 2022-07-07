from telegram import (
    Bot,
    Update,
    ParseMode,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
    )
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    Updater,
    Dispatcher,
    CallbackContext,
    Filters,
    CallbackQueryHandler,
    MessageHandler
    )
import logging
import re
import pytz
import json
import random
import sqlite3
import requests
import unidecode
from functools import wraps
from bs4 import BeautifulSoup
from typing import List, Tuple, cast, Dict
from datetime import datetime, timedelta
from persiantools.jdatetime import JalaliDateTime
from pk.fpl import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

### BOT CONSTANTS
admin_id = 'ADMIN_ID'
TOKEN = "TOKEN"
numtrans = str.maketrans('۱۲۳۴۵۶۷۸۹۰','1234567890')

### BOT SETTINGS
bot = Bot(TOKEN)
updater = Updater(TOKEN, use_context=True, arbitrary_callback_data=True)
dispatcher = updater.dispatcher

### DATABASE
dbcon = sqlite3.connect('bot.db', check_same_thread=False)
dbcur = dbcon.cursor()
dbcur.execute("""CREATE TABLE IF NOT EXISTS users(
   user_id TEXT PRIMARY KEY,
   name TEXT,
   username TEXT
);""")
dbcur.execute("""CREATE TABLE IF NOT EXISTS groups(
   chat_id TEXT PRIMARY KEY,
   chat_title TEXT
);""")
dbcon.commit()

def insert_to_db(table, obj):
    dbcur = dbcon.cursor()
    try:
        dbcur.execute(f"INSERT INTO {table} VALUES({','.join(['?' for i in obj])});", obj)
    except sqlite3.IntegrityError:
        tables = {'users': ['user_id', 'name', 'username'],
            'groups': ['chat_id', 'chat_title']}
        setstr = ', '.join([f'{field} = \'{obj[i+1]}\'' for i,field in enumerate(tables[table][1:])])
        dbcur.execute(f"UPDATE {table} SET {setstr} WHERE {tables[table][0]} = {obj[0]};")
    finally:
        dbcon.commit()

### HANDLE UPDATES
def handle_updates(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        update = args[0]
        try:
            user = update.message.from_user
            chat = update.message.chat
            
            user_id = user.id
            if int(admin_id) != user_id:
                username = user.name
                name = f"{user.first_name if user.first_name else ''} {user.last_name if user.last_name else ''}".strip()
                chat_id = chat.id
                chat_title = chat.title if chat.title != None else 'PV'
                message = update.message.text
                
                data = {'user_id': user_id, 'chat_id': chat_id, 'chat_title':     chat_title, 'username': username, 'name': name, 'message': message}
                
                insert_to_db('users',(user_id, name, username))
                if user_id != chat_id:
                    insert_to_db('groups',(chat_id, chat_title))
    
                bot.sendMessage(
                    chat_id=admin_id,
                    text='\n'.join([f'<b>{j}:</b> {data[j]}' for j in data]),
                    parse_mode=ParseMode.HTML)
                    
        except KeyError:
            bot.sendMessage(
                chat_id=admin_id,
                text=f'<b>New Error!</b>\n\n{KeyError}',
                parse_mode=ParseMode.HTML)
        
        result = func(*args, **kwargs)
        return result
        
    return wrapper


### SUPERLEAGUES
SUPERLEAGUE_MANAGEMENT, NEW_SUPERLEAGUE_NAME, NEW_SUPERLEAGUE_TEAMS, SUPERLEAGUE_ADD_TEAM, SUPERLEAGUE_DEL_TEAM, NEW_SUPERLEAGUE_DONE, EDIT_SUPERLEAGUE = range(7)
mkb_new_superleague_teams = ReplyKeyboardMarkup([['Add Team'],['Remove Team'],['Done']], resize_keyboard=True, one_time_keyboard=True)

@handle_updates
def superleague_management(update: Update, context: CallbackContext):
    update.message.reply_text(
"""☑️ <b>SUPERLEAGUES MANAGEMENT</b>

🔘 You can use this feature to create leagues where managers are organized into opposing teams which compete. Also, the robot provides the results online. if you want to cancel the task, use /cancel command.

🔘 Please choose what you want to do:

""",
        reply_markup=ReplyKeyboardMarkup([['New Superleague'],['Edit Superleague']], resize_keyboard=True, one_time_keyboard=True),parse_mode=ParseMode.HTML)
    return SUPERLEAGUE_MANAGEMENT

def new_superleague_name(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data
    user_data['superleague_creator'] = user.id
    update.message.reply_text(
"""☑️ <b>NEW SUPERLEAGUE</b>

🔘 Alright. Please choose a name for this superleague and send it:
""",
        reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
    return NEW_SUPERLEAGUE_NAME

def new_superleague_teams(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data
    user_data['superleague_name'] = update.message.text
    try:
        update.message.reply_text(
f'''☑️ <b>MANAGE SUPERLEAGUE TEAMS</b>

🏆 Name: <b>{user_data["superleague_name"]}</b>
📋 Teams:

{(chr(10)+chr(10)).join(["<b>Name: "+i+"</b>"+chr(10)+"Squad: "+" - ".join(user_data["teams"][i]) for i in user_data["teams"]])}

🔘 Please choose what you want to do:
''',
            reply_markup=mkb_new_superleague_teams,parse_mode=ParseMode.HTML)
    except:
        update.message.reply_text(
f'''☑️ <b>MANAGE SUPERLEAGUE TEAMS</b>

🏆 Name: <b>{user_data["superleague_name"]}</b>

🔘 You have not created any team yet. Please choose add team:
''',
reply_markup=ReplyKeyboardMarkup([['Add Team']], resize_keyboard=True, one_time_keyboard=True),parse_mode=ParseMode.HTML)
    return NEW_SUPERLEAGUE_TEAMS

def superleague_add_team(update: Update, context: CallbackContext):
    update.message.reply_text(
'''☑️ <b>ADD TEAM</b>

🔘 Please send a list which containing the team name and FPL ID of each team player in one line seperate by new line.

✏️ EXAMPLE:

<pre>Kings of Fantasy
12521
1498
499446
346713
</pre>
''',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML)
    return SUPERLEAGUE_ADD_TEAM


def superleague_add_team_status(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data

    try:
        teamList = [i.strip() for i in update.message.text.split("\n")]

        if 'teams' in user_data.keys():
            user_data['teams'][teamList[0]] = teamList[1:]
        else:
            user_data['teams'] = {}
            user_data['teams'][teamList[0]] = teamList[1:]
        update.message.reply_text(
            '<b>DONE!</b>',
            parse_mode=ParseMode.HTML)
        update.message.reply_text(
f'''☑️ <b>MANAGE SUPERLEAGUE TEAMS</b>

🏆 Name: <b>{user_data["superleague_name"]}</b>
📋 Teams:

{(chr(10)+chr(10)).join(["<b>Name: "+i+"</b>"+chr(10)+"Squad: "+" - ".join(user_data["teams"][i]) for i in user_data["teams"]])}

🔘 Please choose what you want to do:
''',
            reply_markup=mkb_new_superleague_teams,parse_mode=ParseMode.HTML)
        return NEW_SUPERLEAGUE_TEAMS

    except:
        update.message.reply_text(
''' <b>The entered list is not valid! Try again..</b>

🔘 Please send a list which containing the team name and FPL ID of each team player in one line seperate by new line.

✏️ EXAMPLE:

<pre>Kings of Fantasy
12521
1498
499446
346713
</pre>
''',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML))
        return SUPERLEAGUE_ADD_TEAM

def superleague_del_team(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data
    try:
        teams = [[i] for i in user_data["teams"]]
        teams.append(['🔙 Back'])
        markup = ReplyKeyboardMarkup(teams, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(
f'''☑️ <b>Remove Team</b>

Please select the name of the team you want remove.
''',    
            reply_markup=markup,
            parse_mode=ParseMode.HTML)
        return SUPERLEAGUE_DEL_TEAM
    except:
        update.message.reply_text(
            '<b>No Team Found!</b>',
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML)
        update.message.reply_text(
f'''☑️ <b>MANAGE SUPERLEAGUE TEAMS</b>

🏆 Name: <b>{user_data["superleague_name"]}</b>

🔘 You have not created any team yet. Please choose add team:
''',
            reply_markup=ReplyKeyboardMarkup([['Add Team']]),
            parse_mode=ParseMode.HTML)
        return NEW_SUPERLEAGUE_TEAMS

def superleague_del_team_status(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data
    try:
        user_data["teams"].pop(update.message.text)
        update.message.reply_text(
            '<b>DONE!</b>',
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML)
    except: 
        update.message.reply_text(
            '<b>FAILED!</b>',
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML)

    if user_data["teams"]:
        update.message.reply_text(
f'''☑️ <b>MANAGE SUPERLEAGUE TEAMS</b>

🏆 Name: <b>{user_data["superleague_name"]}</b>
📋 Teams:

{(chr(10)+chr(10)).join(["<b>Name: "+i+"</b>"+chr(10)+"Squad: "+" - ".join(user_data["teams"][i]) for i in user_data["teams"]])}

🔘 Please choose what you want to do:
''',
            reply_markup=mkb_new_superleague_teams,
            parse_mode=ParseMode.HTML)
        return NEW_SUPERLEAGUE_TEAMS
    else:
        update.message.reply_text(
f'''☑️ <b>MANAGE SUPERLEAGUE TEAMS</b>

🏆 Name: <b>{user_data["superleague_name"]}</b>

🔘 You have not created any team yet. Please choose add team:
''',
            reply_markup=ReplyKeyboardMarkup([['Add Team']],
                resize_keyboard=True,
                one_time_keyboard=True)
            ,parse_mode=ParseMode.HTML)
        return NEW_SUPERLEAGUE_TEAMS

def superleague_teams_done(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data

    try:
        update.message.reply_text(
f'''☑️ <b>CONFIRM INFORMATIONS</b>

🔘 Good! Please check the information is correct:

🏆 Name: <b>{user_data["superleague_name"]}</b>
📋 Teams:

{(chr(10)+chr(10)).join(["<b>Name: "+i+"</b>"+chr(10)+"Squad: "+" - ".join(user_data["teams"][i]) for i in user_data["teams"]])}

🔘 Please choose what you want to do:
'''
        ,reply_markup=ReplyKeyboardMarkup([['Confirm'],['Restart']], resize_keyboard=True, one_time_keyboard=True)
        ,parse_mode=ParseMode.HTML)
        return NEW_SUPERLEAGUE_DONE
    except:
        update.message.reply_text(
            '<b>No Team Found!</b>',
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML)
        update.message.reply_text(
f'''☑️ <b>MANAGE SUPERLEAGUE TEAMS</b>

🏆 Name: <b>{user_data["superleague_name"]}</b>

🔘 You have not created any team yet. Please choose add team:
''',
            reply_markup=ReplyKeyboardMarkup([['Add Team']],
                resize_keyboard=True,
                one_time_keyboard=True)
            ,parse_mode=ParseMode.HTML)
        return NEW_SUPERLEAGUE_TEAMS

def superleague_done(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data

    with open(f'data.json', 'r', encoding="utf-8") as fp:
        data = json.load(fp)
    if 'superleagues' not in data.keys():
        data['superleagues'] = []
    if 'superleague_id' not in list(user_data.keys()):
        while True:
            comid = random.randint(100, 999)
            if comid not in [i['superleague_id'] for i in data['superleagues']]:
                user_data['superleague_id'] = str(comid)
                break
    else:            
        data["superleagues"].pop(data["superleagues"].index([i for i in data["superleagues"] if i['superleague_id'] == user_data['superleague_id']][0]))
    data['superleagues'].append(user_data)
    with open(f'data.json', 'w', encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=4)

    update.message.reply_text(
f'''☑️ <b>THANK YOU</b>

🆔 Superleague ID: <b>{user_data["superleague_id"]}</b>

🔘 Use /superleague ID for check results!

🔘 Only you can edit this superleague.
''',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML)

    bot.sendMessage(chat_id=admin_id,
                    text=f'<b>New SuperLeague!</b> Check the details below:\n\nName: <b>{user_data["superleague_name"]}</b>\n\nTeams:\n\n{chr(10).join(["<b>"+i+"</b>"+chr(10)+" - ".join(user_data["teams"][i]) for i in user_data["teams"]])}\n\nId: {user_data["superleague_id"]}\nCreator: {user.name}',
                    parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    return ConversationHandler.END

def edit_superleague(update: Update, context: CallbackContext):
    user = update.message.from_user

    with open(f'data.json', 'r', encoding="utf-8") as fp:
        data = json.load(fp)
    
    global superleagues
    superleagues = []
    for i in data['superleagues']:
        if i['superleague_creator'] == user.id:
            superleagues.append(i)
    
    if superleagues:
        superleaguesnames = [[i['superleague_name']+' - '+i['superleague_id']] for i in superleagues]
        superleaguesnames.append(['Back'])
        markup = ReplyKeyboardMarkup(
            superleaguesnames,
            resize_keyboard=True,
            one_time_keyboard=True)

        update.message.reply_text(
"""☑️ <b>SELECT SUPERLEAGUE</b>

🔘 Please select the superleague you want to edit:
""",
            reply_markup=markup,
            parse_mode=ParseMode.HTML)
        return EDIT_SUPERLEAGUE
        
    else:
        update.message.reply_text('<b>You have never created a Superleague!</b>',
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML)

        update.message.reply_text(
"""☑️ <b>SUPERLEAGUES MANAGEMENT</b>

🔘 You can use this feature to create leagues where managers are organized into opposing teams which compete. Also, the robot provides the results online. if you want to cancel the task, use /cancel command.

🔘 Please choose what you want to do:

""",
            reply_markup=ReplyKeyboardMarkup([['New Superleague'],['Edit Superleague']],
                resize_keyboard=True,
                one_time_keyboard=True),
            parse_mode=ParseMode.HTML)

        return SUPERLEAGUE_MANAGEMENT

def edit_superleague_redirect(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data
    editedsuperleague = update.message.text.split('-')[-1].strip()
    for i in superleagues:
        if i['superleague_id'] == editedsuperleague:
            user_data.update(i)
            update.message.reply_text(
"""☑️ <b>EDIT SUPERLEAGUE</b>

⚠️ if you want to cancel the edit, use /cancel command.

🔘 Alright. Please edit name of this superleague and send it:

""",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode=ParseMode.HTML)
            return NEW_SUPERLEAGUE_NAME

    else:
        update.message.reply_text('<b>No Superleague Found!</b>',
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML)

        update.message.reply_text(
"""☑️ <b>SUPERLEAGUES MANAGEMENT</b>

🔘 You can use this feature to create leagues where managers are organized into opposing teams which compete. Also, the robot provides the results online. if you want to cancel the task, use /cancel command.

🔘 Please choose what you want to do:

""",
            reply_markup=ReplyKeyboardMarkup([['New Superleague'],['Edit Superleague']],
                resize_keyboard=True,
                one_time_keyboard=True),
            parse_mode=ParseMode.HTML)
        return SUPERLEAGUE_MANAGEMENT
    
    
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text('Bye! Hope to see you again next time.',
                              reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()

    return ConversationHandler.END

con_superleagues_handler = ConversationHandler(
    entry_points=[CommandHandler('superleagues', superleague_management)],
    states={
        SUPERLEAGUE_MANAGEMENT: [CommandHandler('superleagues', superleague_management), MessageHandler(Filters.regex('^New Superleague$') & (~ Filters.command), new_superleague_name),
                       MessageHandler(Filters.regex('^Edit Superleague$') & (~ Filters.command), edit_superleague)],
        NEW_SUPERLEAGUE_NAME: [CommandHandler('superleagues', superleague_management), MessageHandler(Filters.text & (~ Filters.command), new_superleague_teams),
                CommandHandler('superleagues', superleague_management)],
        NEW_SUPERLEAGUE_TEAMS: [CommandHandler('superleagues', superleague_management),MessageHandler(Filters.regex('^Add Team$') & (~ Filters.command), superleague_add_team),
                       MessageHandler(Filters.regex('^Remove Team$') & (~ Filters.command), superleague_del_team),MessageHandler(Filters.regex('^Done$') & (~ Filters.command), superleague_teams_done)],
        SUPERLEAGUE_ADD_TEAM: [CommandHandler('superleagues', superleague_management), MessageHandler(Filters.text & (~ Filters.command), superleague_add_team_status)],
        SUPERLEAGUE_DEL_TEAM: [CommandHandler('superleagues', superleague_management), MessageHandler(Filters.text & (~ Filters.command), superleague_del_team_status)],
        NEW_SUPERLEAGUE_DONE: [CommandHandler('superleagues', superleague_management), MessageHandler(Filters.regex('^Confirm$') & (~ Filters.command), superleague_done),
                       MessageHandler(Filters.regex('^Restart$') & (~ Filters.command), superleague_management)],
        EDIT_SUPERLEAGUE: [CommandHandler('superleagues', superleague_management), MessageHandler(Filters.text, edit_superleague_redirect)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

### INLINE KEYBOARDS
def static_keyboard(name, buttons, data: Dict[str, str]) -> InlineKeyboardMarkup:
    keyboard = []
    for row in buttons:
        keyboard += [[InlineKeyboardButton(button, callback_data = (name, button,data)) for button in row]]
    
    return InlineKeyboardMarkup(keyboard)
    
def dynamic_keyboard(name, data: Dict[str, str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(button, callback_data=(name, button, data)) for button in data]
        )

def moving_keyboard(name, data: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_row(
        [InlineKeyboardButton('Previous', callback_data=(name, 'Previous', data)),InlineKeyboardButton('Next', callback_data=(name, 'Next', data))]
    )

### COMMANDS
@handle_updates
def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id,
        text="Hi! I am <b>Hex FPL</b> bot. The best <b>Fantasy Premier League</b> telegram bot!\nPlease use commands to get your stats.\n\n1️⃣ Use /team with FPL id to get your team stats including live points and ranks, picks, leagues and season chart.\n2️⃣ Use /deadline to get next gameweek deadline time.\n3⃣ Use /player with his name or part of his name to get information of the player including stats, fixtures and history.\n4⃣ Use /fixtures to get current gameweek fixtures and results. If current gameweek was finished then bot return information for next gameweek.\n5⃣ Use /live to get live fixtures result, points, explain and bps ranking.\n6️⃣ Use /superleagues to create your super league and get results with /superleague online.\n\nℹ️ How to get my FPL id? /help\n\nWait for the next updates ;)\n<b>Version 2.0</b>",
         parse_mode=ParseMode.HTML)

@handle_updates
def player(update: Update, context: CallbackContext):
    try:
        results = getPlayer(" ".join([i.strip().lower() for i in context.args]))
        if not results:
            results = [['<b>Nothing Found..</b>\nPlease spell check the player name.']]
    except:
        results = [['<b>Something Went Wrong..</b>']]
    
    for result in results:
        data: Dict[str, str] = result
        keyboard = static_keyboard(
                    name= 'player',
                    buttons= [['Fixtures','History']],
                    data= data)
        try:
            update.message.reply_photo(
                photo= result['photo'],
                caption= result['Information'],
                parse_mode= ParseMode.HTML,
                reply_markup= keyboard)
        except:
            update.message.reply_text(
                text=result['information'],
                parse_mode=ParseMode.HTML,
                reply_markup= keyboard)

@handle_updates
def help(update: Update, context: CallbackContext):
    update.message.reply_photo(
        photo= 'https://t.me/HEXFPL/3',
        caption= 'Find your <b>FPL ID</b> according to this guide:\n\n1️⃣ Log into the official fantasy premier league <a href="https://fantasy.premierleague.com/">website</a>\n2️⃣ Click on the Points tab\n3️⃣ Look for the number in the URL of that webpage. That is your unique FPL ID.\n\nThen try again with /team.\n<b>More help? Use</b> /start',
        parse_mode= ParseMode.HTML)

@handle_updates
def deadline(update: Update, context: CallbackContext):
    update.message.reply_text(
        text= getDeadline(),
        parse_mode= ParseMode.HTML)

@handle_updates
def live(update: Update, context: CallbackContext):
    data = getLive()
    data: Dict[str, str] = data
    update.message.reply_text(
        text= data[next(iter(data))],
        parse_mode=ParseMode.HTML,
        reply_markup=dynamic_keyboard('live', data))

@handle_updates
def superleague(update: Update, context: CallbackContext):
    try:
        data: Dict[str, str] = getSuperLeague(context.args[0].strip().translate(numtrans))
        update.message.reply_text(
            text=data['Gameweek Standings'],
            parse_mode=ParseMode.HTML,
            reply_markup=static_keyboard(
                name='superleague',
                buttons=[['Overall Standings']],
                data= data))
    except:
        update.message.reply_text(
            text='<b>No SuperLeague Found!</b>',
            parse_mode=ParseMode.HTML)
        
@handle_updates
def stats(update: Update, context: CallbackContext):
    if context.args:
        pass
    else:
        current_list: List[str] = getStats()
        update.message.reply_text(
            text= current_list[0][0] +'\n\n'+ current_list[0][1],
            parse_mode=ParseMode.HTML,
            reply_markup=ikb_stats(current_list))
                             
@handle_updates                             
def fixtures(update: Update, context: CallbackContext):
    data: List[str] = getFixtures()
    update.message.reply_text(
        text=data[0],
        parse_mode=ParseMode.HTML,
        reply_markup=moving_keyboard('fixtures', data))

@handle_updates
def team(update: Update, context: CallbackContext):
    user_data = context.user_data
    try:
        if context.args:
            user_data['idteam'] = str(context.args[0]).strip().translate(numtrans)
        data: Dict[str, str] = getTeam(user_data['idteam'])
        keyboard = static_keyboard(
            name= 'team',
            buttons= [['Leagues','History']],
            data= data)
        update.message.reply_text(
            text=data['Informations'],
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard)
    except:
        update.message.reply_text(
            text='<b>Something went wrong!</b>\nUse /help command.',
            parse_mode=ParseMode.HTML)


### QUERIES
def queries(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    name, key, data = cast(Tuple[str, str, List[str]], query.data)

    if name in ['team','player']:
        keyboard = static_keyboard(
                    name= name,
                    buttons= [[i for i in data if i not in ['photo', key]]],
                    data= data)
        try:
            query.edit_message_caption(
                caption=data[key],
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard)
        except:
            query.edit_message_text(
                text=data[key],
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard)            

    elif name in ['live']:
        query.edit_message_text(
            text=data[key],
            parse_mode=ParseMode.HTML,
            reply_markup=dynamic_keyboard(
                name= name,
                data= data))

    elif name in ['fixtures']:
        if key == 'Next':
            data.append(data[0])
            data.pop(0)
        elif key == 'Previous':
            data.insert(0,data[-1])
            data.pop(-1)           
        query.edit_message_text(
            text=data[0],
            parse_mode=ParseMode.HTML,
            reply_markup=moving_keyboard('fixtures', data))

startHandler = CommandHandler('start', start)
playerHandler = CommandHandler('player', player)
helpHandler = CommandHandler('help', help)
deadlineHandler = CommandHandler('deadline',deadline)
teamHandler = CommandHandler('team', team)
superleagueHandler = CommandHandler('superleague', superleague)
fixturesHandler = CommandHandler('fixtures', fixtures)
liveHandler = CommandHandler('live', live)
statsHandler = CommandHandler('stats', stats)

dispatcher.add_handler(startHandler)
dispatcher.add_handler(playerHandler)
dispatcher.add_handler(helpHandler)
dispatcher.add_handler(deadlineHandler)
dispatcher.add_handler(teamHandler)
dispatcher.add_handler(superleagueHandler)
dispatcher.add_handler(fixturesHandler)
dispatcher.add_handler(liveHandler)
dispatcher.add_handler(statsHandler)

dispatcher.add_handler(CallbackQueryHandler(queries))
dispatcher.add_handler(con_superleagues_handler)

updater.start_polling()
