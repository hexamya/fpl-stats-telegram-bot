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
import random
import sqlite3
from typing import List, Tuple, cast

from packages.fplmethods import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

admin_id = ''
TOKEN = ""

bot = Bot(TOKEN)
updater = Updater(TOKEN, use_context=True, arbitrary_callback_data=True)
dispatcher = updater.dispatcher


#
#
#

class API:
    def __init__(self, session):
        self.session = session
        self.fixtures = session.get('https://fantasy.premierleague.com/api/fixtures/').json()
        self.static = session.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
        self.element_stats = self.static['element_stats']
        self.element_types = self.static['element_types']
        self.elements = self.static['elements']
        self.events = self.static['events']
        self.teams = self.static['teams']
    
    def entry(self, id):
        return self.session.get('https://fantasy.premierleague.com/api/entry/'+id+'/').json()
        
    def history(self, id):
        return self.session.get('https://fantasy.premierleague.com/api/entry/'+id+'/history/').json()
        
    def picks(self, id, event):
        return self.session.get('https://fantasy.premierleague.com/api/entry/'+id+'/event/'+str(event)+'/picks/').json()

    def live(self, event):
        return self.session.get('https://fantasy.premierleague.com/api/event/'+str(event)+'/live/', headers={'Cache-Control': 'no-cache'}).json()
        
    def element_summary(self, id):
        return self.session.get('https://fantasy.premierleague.com/api/element-summary/'+str(id)+'/').json()
        
# CONSTANTS

understatids = {1: '181', 2: '6875', 4: '318', 5: '847', 6: '3277', 7: '204', 8: '8380', 9: '492', 10: '508', 11: '342', 12: '496', 13: '1750', 14: '1749', 15: '2328', 16: '8089', 17: '5656', 18: '1227', 19: '6630', 20: '6482', 21: '7230', 22: '7322', 23: '5613', 24: '6722', 25: '5759', 26: '7752', 27: '6888', 28: '4475', 29: '7721', 30: '4401', 31: '7152', 32: '695', 33: '675', 34: '3696', 35: '7723', 36: '6859', 37: '7722', 38: '1024', 39: '884', 40: '8865', 41: '8040', 42: '5612', 43: '2203', 44: '8864', 45: '7726', 46: '3253', 47: '7724', 48: '8287', 49: '1053', 50: '6122', 51: '8941', 52: '631', 53: '486', 54: '7235', 55: '239', 56: '6047', 57: '6050', 58: '7382', 59: '6048', 60: '6049', 61: '7699', 62: '8780', 63: '3621', 64: '7698', 66: '6842', 67: '7298', 69: '9098', 70: '5609', 71: '8226', 72: '7991', 73: '8020', 74: '8379', 75: '9284', 76: '1801', 77: '7083', 78: '998', 80: '9676', 81: '1078', 82: '10405', 83: '9679', 84: '9680', 85: '7069', 86: '7166', 87: '9687', 88: '9684', 89: '9685', 90: '9683', 91: '9678', 96: '6552', 97: '9682', 98: '1665', 99: '857', 100: '887', 101: '712', 102: '6051', 103: '1747', 104: '844', 105: '4422', 106: '1654', 107: '669', 108: '1663', 109: '4456', 110: '1652', 111: '1017', 112: '5552', 113: '6044', 114: '7459', 115: '8323', 116: '7383', 117: '8482', 118: '6756', 119: '681', 120: '502', 121: '3288', 122: '1621', 123: '1389', 124: '592', 125: '2254', 126: '1678', 127: '1822', 128: '935', 129: '5061', 130: '751', 131: '8992', 132: '688', 133: '200', 134: '65', 135: '782', 136: '702', 137: '2662', 138: '7768', 139: '6369', 140: '6456', 141: '5220', 142: '8067', 143: '6880', 144: '9040', 145: '7988', 146: '2190', 147: '530', 148: '633', 149: '606', 150: '532', 151: '525', 152: '5549', 153: '672', 154: '522', 155: '757', 156: '856', 157: '6027', 159: '5735', 160: '8706', 161: '6451', 162: '8214', 163: '876', 164: '714', 165: '585', 166: '2249', 167: '7063', 168: '1823', 169: '1653', 170: '741', 171: '1379', 172: '2383', 173: '1726', 174: '500', 175: '6521', 176: '1042', 177: '5555', 178: '985', 179: '7689', 180: '6026', 181: '8366', 182: '2164', 183: '2259', 184: '8816', 185: '8716', 186: '4381', 187: '2381', 188: '8718', 189: '822', 190: '2163', 191: '8719', 192: '3428', 193: '1014', 194: '6273', 195: '8723', 196: '8026', 197: '8721', 198: '8717', 199: '8715', 200: '745', 201: '807', 202: '753', 203: '1785', 205: '755', 206: '1234', 207: '3303', 208: '759', 209: '6157', 210: '5956', 211: '770', 212: '6818', 213: '620', 214: '6418', 215: '6681', 216: '5545', 217: '5264', 218: '7753', 219: '8562', 220: '7589', 221: '489', 222: '605', 223: '527', 224: '332', 225: '229', 226: '888', 227: '966', 228: '482', 229: '833', 230: '838', 231: '1257', 232: '3420', 233: '1250', 234: '1688', 235: '484', 236: '8239', 237: '1791', 238: '987', 239: '5247', 240: '6854', 241: '8228', 242: '7904', 243: '6326', 244: '6665', 245: '8852', 246: '8204', 247: '9086', 249: '638', 250: '314', 251: '447', 252: '586', 253: '3389', 254: '750', 255: '618', 256: '2379', 257: '6054', 258: '579', 259: '2498', 260: '7817', 261: '3635', 262: '8961', 263: '5543', 264: '2958', 265: '6055', 266: '2496', 267: '8720', 268: '6441', 269: '3294', 270: '546', 271: '697', 272: '1740', 273: '1687', 274: '6817', 275: '1006', 276: '558', 277: '1228', 278: '553', 279: '1828', 280: '7702', 281: '556', 282: '8821', 283: '934', 284: '6080', 285: '5560', 286: '1739', 287: '5595', 288: '5584', 289: '7490', 290: '8075', 291: '769', 292: '461', 293: '875', 294: '780', 295: '6532', 296: '468', 297: '1746', 298: '1683', 299: '766', 300: '743', 301: '853', 302: '1719', 303: '1545', 304: '6063', 305: '76', 306: '6062', 307: '101', 308: '7420', 309: '7078', 310: '87', 311: '7691', 312: '8016', 313: '8022', 314: '982', 315: '7696', 316: '7694', 317: '62', 318: '7693', 319: '7690', 320: '7697', 321: '902', 322: '6526', 323: '1032', 324: '7990', 325: '7695', 326: '7688', 327: '9748', 328: '10097', 329: '8021', 330: '8455', 331: '9833', 332: '503', 333: '831', 334: '635', 335: '842', 336: '790', 337: '986', 338: '1735', 339: '6893', 340: '111', 341: '843', 342: '885', 343: '6042', 345: '7700', 346: '8456', 347: '8224', 348: '6504', 349: '6736', 350: '7701', 351: '6923', 352: '609', 353: '637', 354: '772', 355: '639', 356: '644', 357: '647', 358: '3600', 359: '453', 360: '6852', 361: '643', 362: '3293', 363: '645', 364: '660', 365: '343', 366: '971', 367: '6249', 368: '6837', 369: '8300', 370: '7187', 371: '8222', 372: '5681', 373: '7198', 374: '6377', 375: '5962', 376: '803', 377: '641', 378: '462', 379: '581', 380: '574', 381: '596', 382: '5043', 383: '1660', 384: '1725', 385: '1677', 386: '6104', 387: '6996', 388: '1154', 389: '1025', 390: '1441', 391: '6841', 395: '1675', 396: '7081', 397: '5573', 398: '5085', 399: '5675', 400: '8235', 401: '7216', 403: '7278', 404: '8272', 406: '533', 407: '540', 408: '706', 409: '528', 410: '529', 411: '534', 412: '6274', 413: '531', 414: '804', 415: '6891', 416: '535', 417: '1760', 418: '8965', 419: '3585', 420: '1776', 421: '5553', 422: '8288', 423: '2335', 424: '3203', 425: '6424', 426: '3422', 427: '6849', 428: '6850', 429: '6851', 430: '4105', 431: '3491', 432: '5708', 433: '2280', 434: '7236', 435: '900', 436: '6853', 437: '6163', 438: '8291', 439: '7332', 440: '6857', 441: '6382', 442: '8180', 443: '8351', 445: '8778', 447: '501', 448: '5544', 449: '6523', 450: '9301', 451: '9733', 452: '785', 453: '614', 455: '9738', 456: '1707', 457: '9745', 458: '6310', 459: '554', 460: '6500', 461: '8934', 462: '9734', 463: '6485', 464: '9948', 465: '708', 466: '9691', 467: '6538', 468: '465', 470: '6674', 471: '5619', 472: '6954', 473: '835', 474: '510', 475: '9740', 477: '7603', 478: '9689', 479: '9681', 480: '509', 481: '694', 482: '775', 483: '9677', 484: '762', 485: '6345', 486: '1841', 487: '7338', 488: '6314', 489: '2310', 491: '9512', 492: '5221', 493: '603', 494: '7218', 495: '1123', 497: '9415', 498: '9915', 499: '9914', 500: '4068', 501: '5648', 502: '1084', 503: '8150', 504: '4764', 505: '9739', 506: '7546', 507: '8497', 510: '7281', 511: '922', 512: '9524', 513: '852', 515: '9747', 516: '7295', 517: '6894', 518: '8384', 519: '839', 520: '9332', 523: '4918', 524: '5786', 525: '4419', 526: '9356', 527: '6615', 528: '9746', 529: '594', 530: '9690', 531: '6492', 533: '9082', 535: '9099', 537: '9735', 539: '7430', 541: '9461', 544: '8476', 545: '9406', 546: '7280', 547: '8179', 550: '9493', 551: '9492', 552: '1711', 553: '5557', 555: '2245', 556: '5191', 557: '9957', 558: '2517', 559: '5603', 562: '9499', 563: '9220', 564: '1304', 566: '8496', 567: '6252', 568: '9912', 569: '9916', 570: '8109', 573: '1697', 574: '763', 575: '593', 576: '9933', 577: '9339', 578: '3278', 579: '2371', 580: '7376', 581: '7470', 582: '6276', 583: '8845', 584: '7134', 585: '5568', 586: '3697', 587: '5556', 588: '7430', 589: '8017', 590: '7931', 591: '813', 592: '2266', 593: '8158', 594: '6030', 595: '6542', 601: '10001', 602: '8582', 606: '7076', 607: '10027', 608: '10028', 609: '9154', 612: '10036', 617: '10061', 620: '10091', 622: '6477', 624: '8544', 625: '10118', 629: '10126', 630: '9287', 632: '951', 634: '10141', 636: '8127', 641: '624', 647: '10166', 648: '10172', 661: '6336', 673: '3468', 675: '10291', 676: '3729', 677: '1142', 678: '652', 679: '10290', 681: '488', 685: '10293', 690: '689', 691: '6962', 697: '8327', 698: '6947', 699: '646', 700: '7052', 701: '6691', 702: '6108', 704: '8868'
}
element_stats = {
        "minutes": "Minutes played",
        "goals_scored": "Goals scored",
        "assists": "Assists",
        "clean_sheets": "Clean sheets",
        "goals_conceded": "Goals conceded",
        "own_goals": "Own goals",
        "penalties_saved": "Penalties saved",
        "penalties_missed": "Penalties missed",
        "yellow_cards": "Yellow cards",
        "red_cards": "Red cards",
        "saves": "Saves",
        "bonus": "Bonus",
        "bps": "Bonus Points System",
        "influence": "Influence",
        "creativity": "Creativity",
        "threat": "Threat",
        "ict_index": "ICT Index"
}
emo= {
    'goals_scored':'⚽️',
    'assists':'🅰️',
    'yellow_cards':'🟨',
    'red_cards':'🟥',
    'own_goals': '🤡',
    'penalties_missed': '❌',
    'penalties_saved': '⛔️',
    'saves': '🧤',
    'bonus': '🎖'
}
fdrcolor = {
    2:'🟩',
    3:'⬜️',
    4:'🟧',
    5:'🟥',
}
fdricon = str.maketrans({'2':'🟩','3':'⬜️','4':'🟧','5':'🟥'})
statusicon = str.maketrans({"a": "","s": "❌", "i": "🚑", "d": "⚠️","u": "⛔️","n": "⛔️"})

def getDeadline():
    session = requests.Session()
    api = API(session)
    EVENTS = api.events
    now = datetime.utcnow()
    
    for i in EVENTS:
        next_deadline = datetime.strptime(i['deadline_time'], '%Y-%m-%dT%H:%M:%SZ')
        if next_deadline > now:
            event = i
            break

    date = pytz.timezone("Etc/Greenwich").localize(datetime.strptime(i['deadline_time'], '%Y-%m-%dT%H:%M:%SZ'), is_dst=True)
    diff = date - pytz.timezone("Asia/Tehran").localize(datetime.now(), is_dst=True)
    jdate = JalaliDateTime(date).astimezone(pytz.timezone("Asia/Tehran"))
    qdate = date.astimezone(pytz.timezone("Asia/Baghdad"))
    udate = date.astimezone(pytz.timezone("Asia/Tashkent"))

    s = lambda e,t : str(e)+t+'s' if e!=1 else str(e)+t
    deadline = f"🔒 <b>GW{event['id']} DEADLINE:</b>\n\n{date.strftime('%H:%M 🇬🇧 %A %d %B')}\n{qdate.strftime('%H:%M 🇮🇶 %A %d %B')}\n{jdate.strftime('%H:%M 🇮🇷 %A %d %B')}\n{udate.strftime('%H:%M 🇺🇿 %A %d %B')}\n\n<b>⏳ {s(diff.days,'</b><i> day')} </i><b>: {s(diff.seconds//3600,'</b><i> hour')} </i><b>: {s(diff.seconds%3600//60, '</b><i> min')}</i>"
    
    return deadline
    

def getFixtures():
    session = requests.Session()
    api = API(session)
    teams = {i['id']: i['name'].replace('Crystal Palace', 'Palace').replace('Southampton','Soton') for i in api.teams}

    now = datetime.utcnow()
    for j,i in enumerate(api.events):
        if (i['is_current'] and not(i['finished'])) or i['is_next']:
            current_event = i
            break
    
    fixtures = []
    for eventid in list(range(current_event['id'],39))+list(range(1,current_event['id'])):
        current_event_fixtures = [fixture for fixture in api.fixtures if fixture['event']==eventid]
        
        for j in current_event_fixtures:
            date = datetime.strptime(j['kickoff_time'], '%Y-%m-%dT%H:%M:%SZ')
            jdate = JalaliDateTime(pytz.timezone("UTC").localize(date, is_dst=True)).astimezone(pytz.timezone("Asia/Tehran"))
            j['jdate'] = jdate.strftime('%A %d %B')
            j['jtime'] = jdate.strftime("%H:%M")
            j['date'] = date.strftime("%A %d %B")
            j['time'] = date.strftime("%H:%M")
        
        fixture = f"<b>GW{str(eventid)} Fixtures:</b> (Asia/Tehran)\n"+'\n'.join([('' if j['date']==current_event_fixtures[i-1]['date'] else f"\n<b>{j['date']}</b>\n") + f"{'⏹ ' if j['finished_provisional'] else '⏸ ' if j['started'] else '▶️ '}<b>{j['jtime']}</b>  {teams[j['team_h']]} <b>{'' if j['team_h_score']==None else j['team_h_score']}-{'' if j['team_a_score']==None else j['team_a_score']}</b> {teams[j['team_a']]}" for i,j in enumerate(current_event_fixtures)])
        
        fixtures.append(fixture)
    
    return fixtures    
    
def getTeam(id):
    session = requests.Session()
    api = API(session)
    
    static = api.static
    entry = api.entry(id)
    history = api.history(id)
    picksevent = api.picks(id,entry['current_event'])
    names = {str(i['id']): i['web_name'] for i in api.elements}
    element_type = {i['id']: i['element_type'] for i in api.elements}
    
    chip = f"\n<b>Active Chip: </b>{picksevent['active_chip']}" if picksevent['active_chip'] else ''
    if chip:
        chip = chip.replace('wildcard','Wildcard').replace('freehit','Freehit').replace('3xc','Triple captain').replace('bboost','Bench boost')
        
    star = lambda x : f'<pre>{x:3} </pre>'+''.join(['•' for i in range(x//4)])
    chart = '\n'.join([star(j['points']) for j in history['current']])
    
    leagues = '\n'.join([f"{'🔺' if i['entry_rank']<i['entry_last_rank'] else '➖' if i['entry_rank']==i['entry_last_rank'] else '🔻'} {i['entry_rank']}  <i>x</i> <b>{i['name'] if len(i['name'])<23 else i['name'][:21]+'..'}</b>   " for i in entry['leagues']['classic']])
    
    value = f"\n<b>Total Value: </b>£{entry['last_deadline_value']/10}m\n<b>Bank: </b>£{entry['last_deadline_bank']/10}m"
    header = f"<b>{entry['name'].upper()}</b>\n"+"<b>Manager: </b>"+ entry['player_first_name']+" "+entry['player_last_name']    
    
    teamstats = {}
    armband = ' ©️'
    cp = 2
    try:
        response = session.get('https://www.livefpl.net/'+id, timeout=3)
        lineup = re.findall(r'var eo = \(\[(.*)\]\)',response.text)[0].split(', ')
        bench = re.findall(r'b = \[(.*)\]',response.text)[0].split(', ')
    
        points = json.loads(re.findall(r'var pts = \((.*)\)',response.text)[0])
        status = json.loads(re.findall(r'var status = \((.*)\)',response.text.replace('y','▶️').replace('d','☑️').replace('l','⏸').replace('m','🅾️'))[0])
        explain = json.loads(re.findall(r'var explaind = \((.*)\)',response.text.replace('_',' '))[0])
        vice = re.findall(r'var vice = (.*);',response.text)[0]
        try:
            autosubs = json.loads('['+re.findall(r'a = \[(.*)\];',response.text)[0]+']')
        except:
            autosubs = []
        
        if len(lineup) in [13, 17]:
            lineup = lineup[:-1]
            cp = 3
        if status[lineup[-1]] == '🅾️':
            lineup[-1] = vice
            
        lineupstr, benchstr = [{},{}]
        if len(lineup) == 12:
            lineupstr['more'] = "<b>LINEUP</b>\n"+"\n".join([f'{status[i]} <b>{names[i].upper()+armband if i==lineup[-1] else names[i].upper()} [ {points[i]*cp if i==lineup[-1] else points[i]} ]</b>{chr(10)}{chr(10).join([f"<i> {j[1]} {j[0].strip()}</i>" for j in explain[i]])}' for i in lineup[:-1]])
            lineupstr['fewer'] = "<b>LINEUP</b>\n"+"\n".join([f'{status[i]} <b>{names[i].upper()+armband if i==lineup[-1] else names[i].upper()} [ {points[i]*cp if i==lineup[-1] else points[i]} ]</b>' for i in lineup[:-1]])
    
            try:
                benchstr['more'] = "\n\n<b>BENCH</b>\n"+"\n".join([f'{status[i]} <b>{names[i].upper()} [ {points[i]} ]</b>{" 🔁" if int(i) in autosubs else ""}{chr(10)}{chr(10).join([f"<i> {j[1]} {j[0].strip()}</i>" for j in explain[i]])}' for i in bench])
                benchstr['fewer'] = "\n\n<b>BENCH</b>\n"+"\n".join([f'{status[i]} <b>{names[i].upper()} [ {points[i]} ]</b>{" 🔁" if int(i) in autosubs else ""}' for i in bench])
    
            except:
                benchstr['more'] = ""
                benchstr['fewer'] = ""
                
        else:
            lineupstr['more'] = "<b>LINEUP</b>\n"+"\n".join([f'{status[i]} <b>{names[i].upper()+armband if i==lineup[-1] else names[i].upper()} [ {points[i]*cp if i==lineup[-1] else points[i]} ]</b>{chr(10).join([f"<i> {j[1]} {j[0].strip()}</i>" for j in explain[i]])}' for i in lineup[:-5]])
            lineupstr['fewer'] = "<b>LINEUP</b>\n"+"\n".join([f'{status[i]} <b>{names[i].upper()+armband if i==lineup[-1] else names[i].upper()} [ {points[i]*cp if i==lineup[-1] else points[i]} ]</b>' for i in lineup[:-5]])
            
            benchstr['more'] = "\n\n<b>BENCH</b>\n"+"\n".join([f'{status[i]} <b>{names[i].upper()+armband if i==lineup[-1] else names[i].upper()} [ {points[i]} ]</b>{" 🔁" if int(i) in autosubs else ""}{chr(10)}{chr(10).join([f"<i> {j[1]} {j[0].strip()}</i>" for j in explain[i]])}' for i in lineup[-5:-1]])
            benchstr['fewer'] = "\n\n<b>BENCH</b>\n"+"\n".join([f'{status[i]} <b>{names[i].upper()+armband if i==lineup[-1] else names[i].upper()} [ {points[i]} ]</b>{" 🔁" if int(i) in autosubs else ""}' for i in lineup[-5:-1]])
    
        soup = BeautifulSoup(response.content,'html5lib')
        tables = soup.select('div.gameweek-points')
        
        try:
            table3 = [f"<b>{th.h7.getText().strip()}</b>: {th.p.getText().strip()}" for th in tables[0].findAll('div')]
            points = "<b>POINTS</b>\n"+"\n".join(table3)
        except:
            points = ""

        try:
            table5 = [f"<b>{th.h7.getText().strip()}</b>: {th.p.getText().strip()}{'↑' if 'up' in str(th) else '↓' if 'down' in str(th) else ''}" for th in  tables[1].findAll('div')]
            ranks = "<b>RANKS</b>\n"+"\n".join(table5)
        except:
            ranks = ""

        teamstats['more'] = header + value + chip + "\n\n"+ points +"\n\n"+ ranks +"\n\n"+ lineupstr['more'] + benchstr['more']
        teamstats['fewer'] = header + value + chip + "\n\n"+ points +"\n\n"+ ranks +"\n\n"+ lineupstr['fewer'] + benchstr['fewer']
        
    except:
        eventlive = api.live(entry['current_event'])
        
        lineup = {i['element']: i for i in picksevent['picks'][:-4]}
        bench = {i['element']: i for i in picksevent['picks'][-4:]}
        elements = {i['id']:i for i in eventlive['elements']}

        moredetails = lambda x : '\n'.join([f'<i>{elements[x]["stats"][i]} {i.replace("_"," ")}</i>' for i in elements[x]['stats'] if i in ["minutes","goals_scored","assists","clean_sheets","goals_conceded","own_goals","penalties_saved","penalties_missed","yellow_cards","red_cards","saves","bonus","bps"] and ((elements[x]["stats"][i] != 0) or (i=='minutes')) and (i != "goals_conceded" or element_type[x] in [1,2])])
        
        stats = f"<b>STATS</b>\n<b>GW{entry['current_event']} Points: </b>{entry['summary_event_points']} - {history['current'][-1]['event_transfers_cost']}\n<b>Total Points: </b>{entry['summary_overall_points']}\n<b>GW{entry['current_event']} Rank: </b>{entry['summary_event_rank']}\n<b>Overall Rank: </b>{entry['summary_overall_rank']}\n\n"
        
        if picksevent['active_chip'] == '3xc':
            cp = 3
            
        lineupstr, benchstr = [{},{}]
        lineupstr['fewer'] = "<b>LINEUP</b>\n"+"\n".join([f'⏺ <b>{names[str(i)].upper()+armband if lineup[i]["is_captain"] else names[str(i)].upper()} [ {elements[i]["stats"]["total_points"]*cp if lineup[i]["is_captain"] else elements[i]["stats"]["total_points"]} ]</b>' for i in lineup])
        lineupstr['more'] = "<b>LINEUP</b>\n"+"\n".join([f'⏺ <b>{names[str(i)].upper()+armband if lineup[i]["is_captain"] else names[str(i)].upper()} [ {elements[i]["stats"]["total_points"]*cp if lineup[i]["is_captain"] else elements[i]["stats"]["total_points"]} ]</b>\n{moredetails(i)}' for i in lineup])
        
        benchstr['fewer'] = "\n\n<b>BENCH</b>\n"+"\n".join([f'⏺ <b>{names[str(i)].upper()} [ {elements[i]["stats"]["total_points"]} ]</b>' for i in bench])
        benchstr['more'] = "\n\n<b>BENCH</b>\n"+"\n".join([f'⏺ <b>{names[str(i)].upper()} [ {elements[i]["stats"]["total_points"]} ]</b>\n{moredetails(i)}' for i in bench])
        
        teamstats['fewer'] = header + value + chip + '\n\n' + stats + lineupstr['fewer'] + benchstr['fewer'] + "\n\n<i>Live server is currently unavailable..</i>"
        teamstats['more'] = header + value + chip + '\n\n' + stats + lineupstr['more'] + benchstr['more'] + "\n\n<i>Live server is currently unavailable..</i>"
        
        
    teamstats['leagues'] = header + '\n\n<b>Classic Leagues:</b>\n\n' + leagues
    teamstats['chart'] = header + '\n\n<b>Chart of Season Points:</b>\n\n' + chart
    
    return teamstats

def getPlayer(name, name1='none', name2='none'):
    session = requests.Session()
    api = API(session)
    top10k = session.get('https://www.livefpl.net/static3/top10k.json').json()
    try:
        understat = session.get('https://understat.com/main/league/EPL', timeout=3)
        if understat:
            understatjsons = re.findall(r'JSON\.parse\(\'(.*)\'\)',understat.text)
            understatdata = [json.loads(bytes(i, 'utf-8').decode('unicode-escape')) for i in [understatjsons[0],understatjsons[2]]]
            with open('understat.json', 'w', encoding="utf-8") as fp:
                json.dump(understatdata, fp, ensure_ascii=False, indent=4)
    except:
        with open('understat.json', 'r', encoding="utf-8") as fp:
            understatdata = json.load(fp)

    players = {i['id']:i for i in understatdata[1]}
    
    for i in api.events:
        if i['is_next']:
            event = i['id']
            break

    teams = {i['id']: i['name'] for i in api.teams}
    shortteams = {i['id']: i['short_name'] for i in api.teams}
    types = {i['id']: i['singular_name'] for i in api.element_types}

    LIST = []

    for element in api.elements:
        fname = unidecode.unidecode(element['first_name']).lower()
        sname = unidecode.unidecode(element['second_name']).lower()
        wname = unidecode.unidecode(element['web_name']).lower()
        
        if ((len(name) in [2,3] and any((name==fname, name==sname, name==wname))) or (len(name)>3 and any((name in f"{fname} {sname}", name in wname, name1 in fname and name2 in sname)))):

            try:
                if element['status'] in ['n','u']:
                    continue
                player = players[understatids[element['id']]]
                
                information = f"<b>{element['first_name'].upper()} {element['second_name'].upper()}</b>\n{types[element['element_type']]} - {teams[element['team']]}\n\n<b>Price:</b> £{element['now_cost']/10}m\n<b>Form:</b> {element['form']}\n<b>Selected:</b> {element['selected_by_percent']}%\n<b>Top10k EO:</b> {round(top10k[str(element['id'])]*100,2)}%\n<b>Event Transfers:</b> +{element['transfers_in_event']} -{element['transfers_out_event']}\n\n<b>STATS</b>\n<b>Total Points:</b> {element['total_points']}  <b>Per Game:</b> {element['points_per_game']}\n<b>Value Season:</b> {element['value_season']}\n<b>Minutes:</b> {element['minutes']}\n"
                
                if element['element_type'] in [3,4]:
                    information += f"<b>Goals:</b> {element['goals_scored']}  <b>xG:</b> {round(float(player['xG']),2)}\n<b>Assists:</b> {element['assists']}  <b>xA:</b> {round(float(player['xA']),2)}\n<b>Key Passes:</b> {player['key_passes']}  <b>Shots:</b> {player['shots']}\n<b>Bonus:</b> {element['bonus']} <b>BPS:</b> {element['bps']}\n\n"
                    
                elif element['element_type']==2:
                    information += f"<b>Goals:</b> {element['goals_scored']}  <b>xG:</b> {round(float(player['xG']),2)}\n<b>Assists:</b> {element['assists']}  <b>xA:</b> {round(float(player['xA']),2)}\n<b>Clean Sheets:</b> {element['clean_sheets']}\n<b>Goals Conceded:</b> {element['goals_conceded']}\n<b>Bonus:</b> {element['bonus']} <b>BPS:</b> {element['bps']}\n\n"                                     
                else:    
                    information += f"<b>Goals:</b> {element['goals_scored']} <b>Assists:</b> {element['assists']}\n<b>Clean Sheets:</b> {element['clean_sheets']}\n<b>Saves:</b> {element['saves']}\n<b>Goals Conceded:</b> {element['goals_conceded']}\n<b>Bonus:</b> {element['bonus']} <b>BPS:</b> {element['bps']}\n\n"             
                status = f"<b>{element['status'].translate(statusicon)} Status:</b> {element['news']}" if element['status'] != "a" else ""
                information += status
                
                summaryres = api.element_summary(element['id'])
                history = sorted(summaryres['history'], key=lambda item: item['round'])

                if element['element_type'] != 1:
                    historystr = f"<b>{element['first_name'].upper()} {element['second_name'].upper()}</b>\n{types[element['element_type']]} - {teams[element['team']]}\n\n<b>This Season History:</b>\n<pre> H   -   A  |TP|MP|G|A|B|</pre>\n"+"\n".join([f"<pre>" +(f"{shortteams[element['team']]} {p['team_h_score'] if p['team_h_score']!=None else '–'}-{p['team_a_score'] if p['team_a_score']!=None else '–'} {shortteams[p['opponent_team']]}" if p['was_home'] else f"{shortteams[p['opponent_team']]} {p['team_h_score'] if p['team_h_score']!=None else '–'}-{p['team_a_score'] if p['team_a_score']!=None else '–'} {shortteams[element['team']]}") +f" |{p['total_points']:>2}|{p['minutes']:>2}|{p['goals_scored'] if p['goals_scored'] else ' '}|{p['assists'] if p['assists'] else ' '}|{p['bonus'] if p['bonus'] else ' '}|</pre>" for p in history])
                else:
                    historystr = f"<b>{element['first_name'].upper()} {element['second_name'].upper()}</b>\n{types[element['element_type']]} - {teams[element['team']]}\n\n<b>This Season History:</b>\n<pre> H   -   A  |TP|MP|S|B|</pre>\n"+"\n".join([f"<pre>" +(f"{shortteams[element['team']]} {p['team_h_score'] if p['team_h_score']!=None else '–'}-{p['team_a_score'] if p['team_a_score']!=None else '–'} {shortteams[p['opponent_team']]}" if p['was_home'] else f"{shortteams[p['opponent_team']]} {p['team_h_score'] if p['team_h_score']!=None else '–'}-{p['team_a_score'] if p['team_a_score']!=None else '–'} {shortteams[element['team']]}") +f" |{p['total_points']:>2}|{p['minutes']:>2}|{p['saves'] if p['saves'] else ' '}|{p['bonus'] if p['bonus'] else ' '}|</pre>" for p in history])

                fixtures = sorted([j for j in summaryres['fixtures'] if j['event']!=None], key=lambda item: item['event'])
                
                gameweeks = [i for i in range(event,39)]
                for k in gameweeks:
                    if k not in [j['event'] for j in fixtures]:
                        fixtures.append({'id': None, 'code': None, 'team_h': None, 'team_h_score': None, 'team_a': None, 'team_a_score': None, 'event': k, 'finished': None, 'minutes': None, 'provisional_start_time': None, 'kickoff_time': None ,'event_name': f'Gameweek {k}', 'is_home': False, 'difficulty': None})
                
                fixtures = sorted(fixtures, key=lambda item: item['event'])
                
                fixturesstr= f"<b>{element['first_name'].upper()} {element['second_name'].upper()}</b>\n{types[element['element_type']]} - {teams[element['team']]}\n\n<b>Next Fixtures:</b>\n"+'\n'.join([f"GW{j:2} | "+"  ".join([f"{fdrcolor[k['difficulty']]+' '+shortteams[k['team_h']]+' (A)' if k['team_h']!=element['team'] else ''}{fdrcolor[k['difficulty']]+' '+shortteams[k['team_a']]+' (H)' if k['team_a']!=element['team'] else '' }" if k['team_h']!=None else '⬛️ -' for k in fixtures if j==k['event']]) for j in gameweeks])


                information = information + 'splitor' + historystr + 'splitor' + fixturesstr
                
                LIST.append([information,f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{element['photo']}".replace('jpg','png')])
                
            except:
                pass

    return LIST

def getStats():
    session = requests.Session()
    figsres = session.get('https://www.livefpl.net/figs')
    liveres = session.get('https://www.livefpl.net/')
    soupf = BeautifulSoup(figsres.content,'html.parser')
    
    figs = soupf.select('body .container .column')
    figslist = [[i.h4.string,session.get('https://www.livefpl.net/'+i.img['src'], timeout=10).content] for i in figs if all([j not in i.h4.string for j in ['Freehit','Wildcards','Wildcard','Chips']])]

    soupl = BeautifulSoup(liveres.content,'html.parser')
    livestr = '</b>\n'.join([':\n<b>'.join(sorted(list(i.stripped_strings)[:2], reverse=True)) for i in soupl.select_one('.table-team-statistic').findAll('td')])+'</b>'
    
    STR = [['<b>'+soupl.select_one('.heading-component-title').string.strip().replace('[','(').replace(']',')')+'</b>',livestr]] + figslist
    
    return STR
  
def getLive():
    session = requests.Session()
    api = API(session)

    teams = {i['id']: i for i in api.teams}
    elementsid = {i['id']: i for i in api.elements}
    names = {i['id']: i['web_name'] for i in api.elements}

    for j,i in enumerate(api.events):
        if (i['is_current'] and not(i['finished'])) or i['is_next']:
            event = i
            break
    
    session.headers.update({'x-test': 'true'})
    liveres = session.get('https://fantasy.premierleague.com/api/event/'+str(event['id'])+'/live/', stream=True ,  ).json()['elements']
    live = {i['id']:i for i in liveres}
    
    livefixtures = {i['id']:i for i in api.fixtures if (i['provisional_start_time'] or i['started']) and not(i['finished']) and not (i['finished_provisional'])}

    if livefixtures:
        livefixtureslist = [livefixtures[i] for i in livefixtures]
    
        statslivefixs = { fixture['id']: {team:dict(sorted(sorted({i['id']: {e['fixture']:(e['stats'][0]['value'],elementsid[i['id']]['element_type']) for e in i['explain']}[fixture['id']] for i in liveres if (fixture['id'] in [j['fixture'] for j in i['explain']]) if (0!={j['fixture']:j['stats'][0]['value'] for j in i['explain']}[fixture['id']]) and elementsid[i['id']]['team']==team}.items(), key=lambda item: item[1][1]),key=lambda item: item[1][0], reverse=True)) for team in [fixture['team_h'],fixture['team_a']]} for fixture in livefixtureslist}
    
        
        dict2str = lambda x: sum([i['points'] for i in x])
        dict2emo = lambda x: ''.join([''.join([emo[i['identifier']] for j in range(i['value'])]) for i in x[1:] if i['identifier'] in ['goals_scored', 'assists', 'yellow_cards', 'red_cards','own_goals', 'penalties_saved', 'penalties_missed', 'saves']])
        
        dict2bps = lambda x: '\n'.join(k[0] for k in sorted([("<pre>{:2}".format(i['value'])+f"</pre> {names[i['element']]}",i['value']) for i in x], key=lambda item: item[1], reverse=True)[:7])
        fixs = {fix: {teams[team]['name']: '\n'.join([f"<pre>{statslivefixs[fix][team][i][0]:2}'|{dict2str({j['fixture']: j for j in live[i]['explain']}[fix]['stats']):2}p {elementsid[i]['web_name']} "+ dict2emo({j['fixture']: j for j in live[i]['explain']}[fix]['stats']) + '</pre>' for i in statslivefixs[fix][team]]) for team in statslivefixs[fix]} for fix in statslivefixs}
        
        stats = {k:{j['identifier']: j['h']+j['a'] for j in livefixtures[k]['stats'] if j['h']+j['a']} for k in livefixtures}
        
        STR = {f"{list(fixs[i].keys())[0]} {livefixtures[i]['team_h_score'] if livefixtures[i]['team_h_score']!= None else ''} - {livefixtures[i]['team_a_score'] if livefixtures[i]['team_a_score']!= None else ''} {list(fixs[i].keys())[1]}splitor":f"<b>{list(fixs[i].keys())[0]}</b> {livefixtures[i]['team_h_score'] if livefixtures[i]['team_h_score']!= None else ''} - {livefixtures[i]['team_a_score'] if livefixtures[i]['team_a_score']!= None else ''} <b>{list(fixs[i].keys())[1]}</b>"+'\n\n'+'\n\n'.join([fixs[i][j] for j in fixs[i]]) + '\n\n'+'\n'.join([f"<b>{element_stats[k]}:</b>\n{dict2bps(stats[i][k])}" for k in stats[i] if k == 'bps']) for i in fixs}
        
    else:
        now = datetime.utcnow().astimezone(pytz.timezone("UTC"))
        
        fixsns = {pytz.timezone("UTC").localize(datetime.strptime(i['kickoff_time'], '%Y-%m-%dT%H:%M:%SZ'), is_dst=True): i for i in api.fixtures if not(i['finished']) and not (i['finished_provisional']) and i['kickoff_time']}
        fixsns = dict(sorted(fixsns.items()))
        
        for i in fixsns:
           if i > now:
                nextfix = {i: fixsns[i]}
                break
        
        STR = {f"{teams[list(nextfix.values())[0]['team_h']]['name']} - {teams[list(nextfix.values())[0]['team_a']]['name']}" +'splitor': '<b>Next Fixture on\n'+list(nextfix.keys())[0].astimezone(pytz.timezone("Asia/Tehran")).strftime('%a %d %B at %H:%M')+"</b>\nSee fixtures with /fixtures"}
            
    return STR

def getSuperLeague(id):
    
    session = requests.Session()
    with open(f'data.json', 'r', encoding="utf-8") as fp:
        data = json.load(fp)
    
    for i in data['superleagues']:
        if i['superleague_id'] == id:
            superleague = i
            break
    
    STR = {}
    pts = lambda current : {'gw': current['points'] - current['event_transfers_cost'], 'oa': current['total_points']}
    
    points = {i : [pts(session.get('https://fantasy.premierleague.com/api/entry/'+j+'/history/').json()['current'][-1]) for j in superleague['teams'][i]] for i in superleague['teams']}
    
    sumsgw = dict(sorted({i: sum([j['gw'] for j in points[i]]) for i in points}.items(), key=lambda item: item[1], reverse=True))
    
    digits = len(str(len(sumsgw)))
    STR['gw'] = f'{superleague["superleague_name"]}\n<b>Current GW Standings</b>\n\n'+'\n'.join([f'<b>#{j+1:0{digits}}</b>  {i.replace("_","")} : <b>{sumsgw[i]}</b>' for j,i in enumerate(sumsgw)])
    
    sumsoa = dict(sorted({i: sum([j['oa'] for j in points[i]]) for i in points}.items(), key=lambda item: item[1], reverse=True))
    
    STR['oa'] = f'{superleague["superleague_name"]}\n<b>Overall Standings</b>\n\n'+'\n'.join([f'<b>#{j+1:0{digits}}</b>  {i.replace("_","")} : <b>{sumsoa[i]}</b>' for j,i in enumerate(sumsoa)])

    return STR

#
#
#


dbcon = sqlite3.connect('bot.db', check_same_thread=False)
dbcur = dbcon.cursor()
dbcur.execute("""CREATE TABLE IF NOT EXISTS users(
   user_id TEXT PRIMARY KEY,
   name TEXT,
   username TEXT);
""")
dbcur.execute("""CREATE TABLE IF NOT EXISTS groups(
   chat_id TEXT PRIMARY KEY,
   chat_title TEXT);
""")
dbcon.commit()

def insert_to_db(table, obj):
    try:
        dbcur = dbcon.cursor()
        dbcur.execute(f"INSERT INTO {table} VALUES({','.join(['?' for i in obj])});", obj)
        dbcon.commit()
    except:
        pass

def handle_updates(update):
    try:
        user = update.message.from_user
        chat = update.message.chat
        
        user_id = user.id
        if int(admin_id) != user_id:
            username = user.name
            name = f"{chat.first_name if chat.first_name else ''} {chat.last_name if chat.last_name else ''}".strip()
            chat_id = chat.id
            chat_title = chat.title
            message = update.message.text
            
            data = {'user_id': user_id, 'chat_id': chat_id, 'chat_title':     chat_title, 'username': username, 'name': name, 'message': message}
            
            insert_to_db('users',(user_id, name, username))
            if user_id != chat_id:
                insert_to_db('groups',(chat_id, chat_title))

            bot.sendMessage(chat_id=admin_id,
                    text='\n'.join([f'<b>{j}:</b> {data[j]}' for j in data]),
                    parse_mode=ParseMode.HTML)
    except KeyError:
        pass

numtrans = str.maketrans('۱۲۳۴۵۶۷۸۹۰','1234567890')

SUPERLEAGUE_MANAGEMENT, NEW_SUPERLEAGUE_NAME, NEW_SUPERLEAGUE_TEAMS, SUPERLEAGUE_ADD_TEAM, SUPERLEAGUE_DEL_TEAM, NEW_SUPERLEAGUE_DONE, EDIT_SUPERLEAGUE = range(7)
mkb_new_superleague_teams = ReplyKeyboardMarkup([['Add Team'],['Remove Team'],['Done']], resize_keyboard=True, one_time_keyboard=True)

def superleague_management(update: Update, context: CallbackContext):
    handle_updates(update)
    update.message.reply_text(
        "<b>SUPERLEAGUES MANAGEMENT</b>\n\nYou can use this feature to create leagues "
        "where managers are organized into opposing teams which compete. Also, the robot provides the results online.\n\nPlease choose what you want to do:",
        reply_markup=ReplyKeyboardMarkup([['New SuperLeague'],['Edit SuperLeague']], resize_keyboard=True, one_time_keyboard=True),parse_mode=ParseMode.HTML)
    return SUPERLEAGUE_MANAGEMENT

def new_superleague_name(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data
    user_data['superleague_creator'] = user.id
    update.message.reply_text('<b>NEW SUPERLEAGUE</b>\n\nAlright. Please choose a name for this superleague and send it:',reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
    return NEW_SUPERLEAGUE_NAME

def new_superleague_teams(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data
    user_data['superleague_name'] = update.message.text
    try:
        update.message.reply_text(f'<b>MANAGE SUPERLEAGUE TEAMS</b>\n\nName: <b>{user_data["superleague_name"]}</b>\n\nTeams:\n{chr(10).join(["<b>"+i+"</b>"+chr(10)+" - ".join(user_data["teams"][i]) for i in user_data["teams"]])}\n\nPlease choose what you want to do:',reply_markup=mkb_new_superleague_teams,parse_mode=ParseMode.HTML)
    except:
        update.message.reply_text(f'<b>MANAGE SUPERLEAGUE TEAMS</b>\n\nName: <b>{user_data["superleague_name"]}</b>\n\nPlease choose what you want to do:',reply_markup=mkb_new_superleague_teams,parse_mode=ParseMode.HTML)
    return NEW_SUPERLEAGUE_TEAMS

def superleague_add_team(update: Update, context: CallbackContext):
    update.message.reply_text('Please send a list which containing the team name and FPL ID of each team player in one line seperate by two semicolon.\n\nExample:\nKings of Fantasy ;; 12521 ;; 1498 ;; 499446 ;; 346713',reply_markup=ReplyKeyboardRemove())
    return SUPERLEAGUE_ADD_TEAM


def superleague_add_team_status(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data

    try:
        teamList = [i.strip() for i in update.message.text.split(";;")]

        if 'teams' in user_data.keys():
            user_data['teams'][teamList[0]] = teamList[1:]
        else:
            user_data['teams'] = {}
            user_data['teams'][teamList[0]] = teamList[1:]
        update.message.reply_text('<b>Done!</b>',parse_mode=ParseMode.HTML)
        update.message.reply_text(f'<b>MANAGE SUPERLEAGUE TEAMS</b>\n\nName: <b>{user_data["superleague_name"]}</b>\n\nTeams:\n{chr(10).join(["<b>"+i+"</b>"+chr(10)+" - ".join(user_data["teams"][i]) for i in user_data["teams"]])}\n\nPlease choose what you want to do:',reply_markup=mkb_new_superleague_teams,parse_mode=ParseMode.HTML)
        return NEW_SUPERLEAGUE_TEAMS
    except:
        update.message.reply_text('The entered list is not valid! Try again..\nPlease send a list which containing the team name and FPL ID of each team player in one line seperate by two semicolon.\n\nExample:\nKings of Fantasy ;; 12521 ;; 1498 ;; 499446 ;; 346713')
        return SUPERLEAGUE_ADD_TEAM

def superleague_del_team(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data
    try:
        teams = [[i] for i in user_data["teams"]]
        teams.append(['Back'])
        markup = ReplyKeyboardMarkup(teams, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text('Please select the name of the team you want remove.',reply_markup=markup)
        return SUPERLEAGUE_DEL_TEAM
    except:
        update.message.reply_text('<b>No Team Found.</b>',reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
        update.message.reply_text(f'<b>MANAGE SUPERLEAGUE TEAMS</b>\n\nName: <b>{user_data["superleague_name"]}</b>\n\nTeams:\n{chr(10).join(["<b>"+i+"</b>"+chr(10)+" - ".join(user_data["teams"][i]) for i in user_data["teams"]])}\n\nPlease choose what you want to do:',reply_markup=mkb_new_superleague_teams,parse_mode=ParseMode.HTML)
        return NEW_SUPERLEAGUE_TEAMS

def superleague_del_team_status(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data
    try:
        user_data["teams"].pop(update.message.text)
        update.message.reply_text('Done!',reply_markup=ReplyKeyboardRemove())
        update.message.reply_text(f'<b>MANAGE SUPERLEAGUE TEAMS</b>\n\nName: <b>{user_data["superleague_name"]}</b>\n\nTeams:\n{chr(10).join(["<b>"+i+"</b>"+chr(10)+" - ".join(user_data["teams"][i]) for i in user_data["teams"]])}\n\nPlease choose what you want to do:',reply_markup=mkb_new_superleague_teams,parse_mode=ParseMode.HTML)
        return NEW_SUPERLEAGUE_TEAMS

    except:
        update.message.reply_text('No Team Found!',reply_markup=ReplyKeyboardRemove())
        update.message.reply_text(f'<b>MANAGE SUPERLEAGUE TEAMS</b>\n\nName: <b>{user_data["superleague_name"]}</b>\n\nTeams:\n{chr(10).join(["<b>"+i+"</b>"+chr(10)+" - ".join(user_data["teams"][i]) for i in user_data["teams"]])}\n\nPlease choose what you want to do:',reply_markup=mkb_new_superleague_teams,parse_mode=ParseMode.HTML)
        return NEW_SUPERLEAGUE_TEAMS

def superleague_teams_done(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data

    try:
        update.message.reply_text(f'Good! Please check the information is correct:\n\nName: <b>{user_data["superleague_name"]}</b>\n\nTeams:\n{chr(10).join(["<b>"+i+"</b>"+chr(10)+" - ".join(user_data["teams"][i]) for i in user_data["teams"]])}'
        ,reply_markup=ReplyKeyboardMarkup([['Confirm'],['Restart']], resize_keyboard=True, one_time_keyboard=True)
        ,parse_mode=ParseMode.HTML)
        return NEW_SUPERLEAGUE_DONE
    except:
        update.message.reply_text('No Team Found! Try again and add teams in superleague.\n')
        update.message.reply_text(f'<b>MANAGE SUPERLEAGUE TEAMS</b>\n\nName: <b>{user_data["superleague_name"]}</b>\n\nTeams:\n{chr(10).join(["<b>"+i+"</b>"+chr(10)+" - ".join(user_data["teams"][i]) for i in user_data["teams"]])}\n\nPlease choose what you want to do:',reply_markup=mkb_new_superleague_teams,parse_mode=ParseMode.HTML)
        return NEW_SUPERLEAGUE_TEAMS

def superleague_done(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data

    with open(f'data.json', 'r', encoding="utf-8") as fp:
        data = json.load(fp)
    if 'superleagues' not in data.keys():
        data['superleagues'] = []
    while True:
        comid = random.randint(100, 999)
        if comid not in [i['superleague_id'] for i in data['superleagues']]:
            user_data['superleague_id'] = str(comid)
            break                

    data['superleagues'].append(user_data)
    with open(f'data.json', 'w', encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=4)
    
    update.message.reply_text(f'Thank you!\n\nSuperLeague ID: <b>{user_data["superleague_id"]}</b>\nUse ID for check results!\nOnly you can edit this superleague.', reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)

    bot.sendMessage(chat_id=admin_id,
                    text=f'<b>New SuperLeague!</b> Check the details below:\n\nName: <b>{user_data["superleague_name"]}</b>\n\nTeams:\n{chr(10).join(["<b>"+i+"</b>"+chr(10)+" - ".join(user_data["teams"][i]) for i in user_data["teams"]])}\n\nId: {user_data["superleague_id"]}\nCreator: {user.name}',
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
        superleaguesnames = [[i['superleague_name']] for i in superleagues]
        superleaguesnames.append(['Back'])
        markup = ReplyKeyboardMarkup(superleaguesnames, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text('Please select the superleague you want to edit:',reply_markup=markup)
        return EDIT_SUPERLEAGUE
        
    else:
        update.message.reply_text('You have never created a Super League!',
                              reply_markup=ReplyKeyboardRemove())
        update.message.reply_text(
            "<b>SUPERLEAGUES MANAGEMENT</b>\n\nYou can use this feature to create leagues "
            "where managers are organized into opposing teams which compete. Also, the robot provides the results online.\n\nPlease choose what you want to do:",
            reply_markup=ReplyKeyboardMarkup([['New SuperLeague'],['Edit SuperLeague']], resize_keyboard=True, one_time_keyboard=True),parse_mode=ParseMode.HTML)
        return SUPERLEAGUE_MANAGEMENT

def edit_superleague_redirect(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data
    for i in superleagues:
        if i['superleague_name'] == update.message.text:
            user_data.update(i)
            with open(f'data.json', 'r', encoding="utf-8") as fp:
                data = json.load(fp)
            data["superleagues"].pop(data["superleagues"].index(i))
            with open(f'data.json', 'w', encoding="utf-8") as fp:
                json.dump(data, fp, ensure_ascii=False, indent=4)
            update.message.reply_text('<b>EDIT SUPERLEAGUE</b>\n\nAttention! The previous Super League has been <b>deleted</b> from the database. So if you do not want to edit, save the Super League again by continuing the steps.\n\nAlright. Please edit name of this superleague and send it:',reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
            return NEW_SUPERLEAGUE_NAME
    else:
        update.message.reply_text(
            "<b>SUPERLEAGUES MANAGEMENT</b>\n\nYou can use this feature to create leagues "
            "where managers are organized into opposing teams which compete. Also, the robot provides the results online.\n\nPlease choose what you want to do:",
            reply_markup=ReplyKeyboardMarkup([['New SuperLeague'],['Edit SuperLeague']], resize_keyboard=True, one_time_keyboard=True),parse_mode=ParseMode.HTML)
        return SUPERLEAGUE_MANAGEMENT
    
    
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text('Bye! Hope to see you again next time.',
                              reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

#
#
#

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hi! I am <b>Hex FPL</b> bot. The best <b>Fantasy Premier League</b> telegram bot!\nPlease use commands to get your stats.\n\n1️⃣ Use /team with FPL id to get your team stats including live points and ranks, picks, leagues and season chart.\n2️⃣ Use /deadline to get next gameweek deadline time.\n3⃣ Use /player with his name or part of his name to get information of the player including stats, fixtures and history.\n4⃣ Use /fixtures to get current gameweek fixtures and results. If current gameweek was finished then bot return information for next gameweek.\n5⃣ Use /live to get live fixtures result, points, explain and bps ranking.\n6️⃣ Use /superleagues to create your super league and get results with /superleague online.\n\nℹ️ How to get my FPL id? /help\n\nWait for the next updates ;)\n<b>Version 2.0</b>",
                             parse_mode=ParseMode.HTML)
    handle_updates(update)

def ikb_inform(current_list: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_row(
        [InlineKeyboardButton('Fixtures', callback_data=('fixs', current_list)),InlineKeyboardButton('History', callback_data=('history', current_list))]
    )
def ikb_history(current_list: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_row(
        [InlineKeyboardButton('Fixtures', callback_data=('fixs', current_list)),InlineKeyboardButton('Information', callback_data=('inform', current_list))]
    )
def ikb_fixs(current_list: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_row(
        [InlineKeyboardButton('Information', callback_data=('inform', current_list)),InlineKeyboardButton('History', callback_data=('history', current_list))]
    )
def ikb_live(current_list: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(i.split('splitor')[0], callback_data=(i, current_list)) for i in current_list]
        )
def ikb_oa(current_list: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton('Overall Standings', callback_data=('oa', current_list))]
    )
def ikb_gw(current_list: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton('Current GW Standings', callback_data=('gw', current_list))]
    )        
def ikb_stats(current_list: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton('Live Averages', callback_data=(current_list[0], current_list))]]+[[InlineKeyboardButton(i[0], callback_data=(i, current_list))] for i in current_list[1:]]
        )
def ikb_fixtures(current_list: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_row(
        [InlineKeyboardButton('Previous', callback_data=('previous', current_list)),InlineKeyboardButton('Next', callback_data=('next', current_list))]
    )
    
def ikb_more(current_list: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton('More Details', callback_data=('more', current_list))],[InlineKeyboardButton('Leagues', callback_data=('leagues', current_list)),InlineKeyboardButton('Season Chart', callback_data=('chart', current_list))]]
    )
def ikb_fewer(current_list: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton('Fewer Details', callback_data=('fewer', current_list))],[InlineKeyboardButton('Leagues', callback_data=('leagues', current_list)),InlineKeyboardButton('Season Chart', callback_data=('chart', current_list))]]
    )
def ikb_league(current_list: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton('Live Points & Ranks', callback_data=('fewer', current_list)),InlineKeyboardButton('Season Chart', callback_data=('chart', current_list))]
    )    
def ikb_chart(current_list: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton('Live Points & Ranks', callback_data=('fewer', current_list)), InlineKeyboardButton('Leagues', callback_data=('leagues', current_list)) ]
    )   
    
            
def player(update: Update, context: CallbackContext):
    try:
        if len(context.args) >= 2:
            LIST = getPlayer(" ".join([i.strip().lower() for i in context.args]),name1=context.args[0].lower(), name2=context.args[1].lower())
            if LIST==[]: LIST = [['<b>Nothing Found..</b>\nPlease spell check the player name.']] 
        else:
            LIST = getPlayer(" ".join([i.strip() for i in context.args]))
            if LIST==[]: LIST = [['<b>Nothing Found..</b>\nPlease spell check the player name.']] 
    except:
        LIST = [['<b>Something Went Wrong..</b>']]
    
    for i in LIST:
        current_list: List[str] = i[0].split('splitor')
        try:
            update.message.reply_photo(photo=i[1],caption=current_list[0],parse_mode=ParseMode.HTML, reply_markup=ikb_inform(current_list))
        except:
            if 'Nothing Found' in current_list[0]:
                update.message.reply_text(text=current_list[0],parse_mode=ParseMode.HTML)
            else:
                update.message.reply_text(text=current_list[0],parse_mode=ParseMode.HTML)
    handle_updates(update)


def help(update: Update, context: CallbackContext):
    update.message.reply_photo(photo='https://t.me/HEXFPL/3',
                   caption='Find your <b>FPL ID</b> according to this guide:\n\n1️⃣ Log into the official fantasy premier league <a href="https://fantasy.premierleague.com/">website</a>\n2️⃣ Click on the Points tab\n3️⃣ Look for the number in the URL of that webpage. That is your unique FPL ID.\n\nThen try again with /team.\n<b>More help? Use</b> /start'
                           , parse_mode=ParseMode.HTML)
    handle_updates(update)
    
    
def deadline(update: Update, context: CallbackContext):
    update.message.reply_text(text= getDeadline(),
                             parse_mode=ParseMode.HTML)
    handle_updates(update)    


def live(update: Update, context: CallbackContext):
    handle_updates(update)
    data = getLive()
    current_list: List[str] = [i+data[i] for i in data]
    update.message.reply_text(text= current_list[0].split('splitor')[1],
                             parse_mode=ParseMode.HTML,
                             reply_markup=ikb_live(current_list))

    
def superleague(update: Update, context: CallbackContext):
    handle_updates(update)
    try:
        data = getSuperLeague(str(context.args[0]).strip().translate(numtrans))
        league_list: List[str] = [data['gw'], data['oa']]
        update.message.reply_text(text=league_list[0], parse_mode=ParseMode.HTML,reply_markup=ikb_oa(league_list))

    except:
        comptext = '<b>No SuperLeague Found!</b>'
        update.message.reply_text(text=comptext, parse_mode=ParseMode.HTML)     
        

def stats(update: Update, context: CallbackContext):
    if context.args:
        pass
    else:
        handle_updates(update)
        current_list: List[str] = getStats()
        update.message.reply_text(text= current_list[0][0] +'\n\n'+ current_list[0][1],
                             parse_mode=ParseMode.HTML,
                             reply_markup=ikb_stats(current_list))
                             
                             
def fixtures(update: Update, context: CallbackContext):
    current_list: List[str] = getFixtures()
    update.message.reply_text(text=current_list[0],
                             parse_mode=ParseMode.HTML,reply_markup=ikb_fixtures(current_list))
    handle_updates(update)


def team(update: Update, context: CallbackContext):
    handle_updates(update)
    user_data = context.user_data
    
    try:
        if len(context.args) != 0:
            user_data['idteam'] = str(context.args[0]).strip().translate(numtrans)
        data = getTeam(user_data['idteam'])
        team_list: List[str] = [data['fewer'], data['more'], data['leagues'], data['chart']]
        update.message.reply_text(text=team_list[0],parse_mode=ParseMode.HTML,reply_markup=ikb_more(team_list))
    
    except:
        update.message.reply_text(text='<b>Something went wrong!</b>\nUse /help command.',parse_mode=ParseMode.HTML)
   
###
                    
def query_edit(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    detail, current_list = cast(Tuple[str, List[str]], query.data)

    if detail == 'gw':
        query.edit_message_text(text=current_list[0],
                    parse_mode=ParseMode.HTML,reply_markup=ikb_oa(current_list))
    elif detail == 'oa':
        query.edit_message_text(text=current_list[1],
                    parse_mode=ParseMode.HTML,reply_markup=ikb_gw(current_list))
                    
    elif detail == 'more':
        query.edit_message_text(text=current_list[1],
                            parse_mode=ParseMode.HTML,reply_markup=ikb_fewer(current_list))
    elif detail == 'fewer':
        query.edit_message_text(text=current_list[0],
                            parse_mode=ParseMode.HTML,reply_markup=ikb_more(current_list))
    elif detail == 'leagues':
        query.edit_message_text(text=current_list[2],
                            parse_mode=ParseMode.HTML,reply_markup=ikb_league(current_list))
    elif detail == 'chart':
        query.edit_message_text(text=current_list[3],
                            parse_mode=ParseMode.HTML,reply_markup=ikb_chart(current_list))
    elif detail == 'next':
        current_list.append(current_list[0])
        current_list.pop(0)
        query.edit_message_text(text=current_list[0],
                            parse_mode=ParseMode.HTML,reply_markup=ikb_fixtures(current_list))
    elif detail == 'previous':
        current_list.insert(0,current_list[-1])
        current_list.pop(-1)
        query.edit_message_text(text=current_list[0],
                            parse_mode=ParseMode.HTML,reply_markup=ikb_fixtures(current_list))
    elif 'Bonus Points System:' in detail:
        query.edit_message_text(text=detail.split('splitor')[1],
                            parse_mode=ParseMode.HTML,reply_markup=ikb_live(current_list))
    elif detail == 'history':
        query.edit_message_caption(caption=current_list[1],
                            parse_mode=ParseMode.HTML,reply_markup=ikb_history(current_list))
    elif detail == 'inform':
        query.edit_message_caption(caption=current_list[0],
                            parse_mode=ParseMode.HTML,reply_markup=ikb_inform(current_list))
    elif detail == 'fixs':
        query.edit_message_caption(caption=current_list[2],
                            parse_mode=ParseMode.HTML,reply_markup=ikb_fixs(current_list))
    elif 'Averages' in current_list[0][0]:
        try:
            ID = query.message.reply_to_message.message_id
        except:
            pass
        query.delete_message()
        if current_list[0][0] != detail[0]:
            try:
                query.message.reply_photo(reply_to_message_id=ID,photo=detail[1],caption=detail[0], protect_content=True, parse_mode=ParseMode.HTML, reply_markup=ikb_stats(current_list))
            except:
                query.message.reply_photo(photo=detail[1],caption=detail[0],parse_mode=ParseMode.HTML, protect_content=True, reply_markup=ikb_stats(current_list))
        else:
            try:
                query.message.reply_text(reply_to_message_id=ID,text=detail[0]+'\n\n'+detail[1],parse_mode=ParseMode.HTML, reply_markup=ikb_stats(current_list))
            except:
                query.message.reply_text(text=detail[0]+'\n\n'+detail[1],parse_mode=ParseMode.HTML, reply_markup=ikb_stats(current_list))
            
con_hexamya_handler = ConversationHandler(
    entry_points=[CommandHandler('sendhexamya', getlisthexamya)],
    states={
        SEND_HEXAMYA_LIST: [CommandHandler('sendhexamya', getlisthexamya), MessageHandler(Filters.text, messagehexamya)],
        SEND_HEXAMYA_MESSAGE: [CommandHandler('sendhexamya', getlisthexamya), MessageHandler(~ Filters.regex('/cancel'), sendhexamya)]
    },
    fallbacks=[CommandHandler('cancel', cancel)])


con_superleagues_handler = ConversationHandler(
    entry_points=[CommandHandler('superleagues', superleague_management)],
    states={
        SUPERLEAGUE_MANAGEMENT: [CommandHandler('superleagues', superleague_management), MessageHandler(Filters.regex('^New SuperLeague$'), new_superleague_name),
                       MessageHandler(Filters.regex('^Edit SuperLeague$'), edit_superleague)],
        NEW_SUPERLEAGUE_NAME: [CommandHandler('superleagues', superleague_management), MessageHandler(Filters.text, new_superleague_teams),
                CommandHandler('superleagues', superleague_management)],
        NEW_SUPERLEAGUE_TEAMS: [CommandHandler('superleagues', superleague_management),MessageHandler(Filters.regex('^Add Team$'), superleague_add_team),
                       MessageHandler(Filters.regex('^Remove Team$'), superleague_del_team),MessageHandler(Filters.regex('^Done$'), superleague_teams_done)],
        SUPERLEAGUE_ADD_TEAM: [CommandHandler('superleagues', superleague_management), MessageHandler(Filters.text, superleague_add_team_status)],
        SUPERLEAGUE_DEL_TEAM: [CommandHandler('superleagues', superleague_management), MessageHandler(Filters.text, superleague_del_team_status)],
        NEW_SUPERLEAGUE_DONE: [CommandHandler('superleagues', superleague_management), MessageHandler(Filters.regex('^Confirm$'), superleague_done),
                       MessageHandler(Filters.regex('^Restart$'), superleague_management)],
        EDIT_SUPERLEAGUE: [CommandHandler('superleagues', superleague_management), MessageHandler(Filters.text, edit_superleague_redirect)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

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

dispatcher.add_handler(CallbackQueryHandler(query_edit))

dispatcher.add_handler(con_superleagues_handler)
dispatcher.add_handler(con_hexamya_handler)

updater.start_polling()
