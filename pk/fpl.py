from datetime import datetime, timedelta
from persiantools.jdatetime import JalaliDateTime
import requests
import unidecode
from bs4 import BeautifulSoup
import re
import pytz
import json

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
        try:
            return self.session.get('https://fantasy.premierleague.com/api/entry/'+id+'/event/'+str(event)+'/picks/').json()
        except:
            pass

    def live(self, event):
        try:
            return self.session.get('https://fantasy.premierleague.com/api/event/'+str(event)+'/live/', headers={'Cache-Control': 'no-cache'}).json()
        except:
            pass
        
    def element_summary(self, id):
        return self.session.get('https://fantasy.premierleague.com/api/element-summary/'+str(id)+'/').json()
        
# CONSTANTS

understatids = {}
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
fdricon = str.maketrans({
    '2':'🟩',
    '3':'⬜️',
    '4':'🟧',
    '5':'🟥'
})
statusicon = str.maketrans({
    "a": "",
    "s": "❌", 
    "i": "🚑",
    "d": "⚠️",
    "u": "⛔️",
    "n": "⛔️"
})

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

    s = lambda e,t : str(e)+t+'s' if e!=1 else str(e)+t
    deadline = f"🔒 <b>GW{event['id']} DEADLINE:</b>\n\n{date.strftime('%H:%M 🇬🇧 %A %d %B')}\n{jdate.strftime('%H:%M 🇮🇷 %A %d %B')}\n\n<b>⏳ {s(diff.days,'</b><i> day')} </i><b>: {s(diff.seconds//3600,'</b><i> hour')} </i><b>: {s(diff.seconds%3600//60, '</b><i> min')}</i>"
    
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
    
    try:
        chip = f"\n<b>Active Chip: </b>{picksevent['active_chip']}" if picksevent['active_chip'] else ''
    except:
        chip = ''
        
    if chip:
        chip = chip.replace('wildcard','Wildcard').replace('freehit','Freehit').replace('3xc','Triple captain').replace('bboost','Bench boost')
        
    star = lambda x : f'<pre>{x:3} </pre>'+''.join(['•' for i in range(x//4)])
    chart = '\n'.join([star(j['points']) for j in history['current']])
    
    past = '\n'.join([f"<b>{i['season_name']}</b> | <b>Total Pts:</b> <pre>{i['total_points']:>4}</pre> | <b>Rank:</b> <pre>{i['rank']}</pre>" for i in history['past']])
    
    leagues = '\n'.join([f"{'🔺' if i['entry_rank']<i['entry_last_rank'] else '➖' if i['entry_rank']==i['entry_last_rank'] else '🔻'} {i['entry_rank']}  <i>x</i> <b>{i['name'] if len(i['name'])<23 else i['name'][:21]+'..'}</b>   " for i in entry['leagues']['classic']])
    
    try:
        value = f"\n<b>Total Value: </b>£{entry['last_deadline_value']/10}m\n<b>Bank: </b>£{entry['last_deadline_bank']/10}m"
    except:
        value = f"\n<b>Total Value: </b>£100.0m"
        
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

        teamstats['More'] = header + value + chip + "\n\n"+ points +"\n\n"+ ranks +"\n\n"+ lineupstr['more'] + benchstr['more']
        teamstats['Fewer'] = header + value + chip + "\n\n"+ points +"\n\n"+ ranks +"\n\n"+ lineupstr['fewer'] + benchstr['fewer']
        
    except:
        try:
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
            
            teamstats['Fewer'] = header + value + chip + '\n\n' + stats + lineupstr['fewer'] + benchstr['fewer'] + "\n\n<i>Live server is currently unavailable..</i>"
            teamstats['More'] = header + value + chip + '\n\n' + stats + lineupstr['more'] + benchstr['more'] + "\n\n<i>Live server is currently unavailable..</i>"
        except:
            teamstats['Informations'] = header + value + chip

    teamstats['Leagues'] = header + '\n\n<b>Classic Leagues:</b>\n\n' + leagues
    if chart:
        teamstats['History'] = header + '\n\n<b>Chart of Season Points:</b>\n\n' + chart
    else:
        teamstats['History'] = header + '\n\n<b>Past Seasons:</b>\n\n' + past

    
    return teamstats

def getPlayer(name):
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

    name0 = name.split()
    if len(name0) > 1:
        name1 = name0[0]
        name2 = name0[1]
    else:
        name1 = 'none'
        name2 = 'none'
        
    resultsList = []
    for element in api.elements:
        fname = unidecode.unidecode(element['first_name']).lower()
        sname = unidecode.unidecode(element['second_name']).lower()
        wname = unidecode.unidecode(element['web_name']).lower()
        
        if ((len(name) in [2,3] and any((name==fname, name==sname, name==wname))) or (len(name)>3 and any((name in f"{fname} {sname}", name in wname, name1 in fname and name2 in sname)))):
            
            # try:
            if element['status'] in ['n','u']:
                continue
            # player = players[understatids[element['id']]]
            
            information = f"<b>{element['first_name'].upper()} {element['second_name'].upper()}</b>\n{types[element['element_type']]} - {teams[element['team']]}\n\n<b>Price:</b> £{element['now_cost']/10}m\n<b>Form:</b> {element['form']}\n<b>Selected:</b> {element['selected_by_percent']}%\n<b>Top10k EO:</b> {round(top10k[str(element['id'])]*100,2)}%\n<b>Event Transfers:</b> +{element['transfers_in_event']} -{element['transfers_out_event']}\n\n<b>STATS</b>\n<b>Total Points:</b> {element['total_points']}  <b>Per Game:</b> {element['points_per_game']}\n<b>Value Season:</b> {element['value_season']}\n<b>Minutes:</b> {element['minutes']}\n"
            
            if element['element_type'] in [3,4]:
                information += f"<b>Goals:</b> {element['goals_scored']}\n<b>Assists:</b> {element['assists']}\n<b>Bonus:</b> {element['bonus']} <b>BPS:</b> {element['bps']}\n\n"
                
            elif element['element_type']==2:
                information += f"<b>Goals:</b> {element['goals_scored']}\n<b>Assists:</b> {element['assists']}\n<b>Clean Sheets:</b> {element['clean_sheets']}\n<b>Goals Conceded:</b> {element['goals_conceded']}\n<b>Bonus:</b> {element['bonus']} <b>BPS:</b> {element['bps']}\n\n"                                     
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
            
            fixturesstr= f"<b>{element['first_name'].upper()} {element['second_name'].upper()}</b>\n{types[element['element_type']]} - {teams[element['team']]}\n\n<b>Next Fixtures:</b>\n"+'\n'.join([f"GW{j:02} | "+"  ".join([f"{fdrcolor[k['difficulty']]+' '+shortteams[k['team_h']]+' (A)' if k['team_h']!=element['team'] else ''}{fdrcolor[k['difficulty']]+' '+shortteams[k['team_a']]+' (H)' if k['team_a']!=element['team'] else '' }" if k['team_h']!=None else '⬛️ -' for k in fixtures if j==k['event']]) for j in gameweeks])


            result = {'Information': information, 'Fixtures': fixturesstr,'History': historystr, 'photo': f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{element['photo']}".replace('jpg','png')}
            
            resultsList.append(result)
                
    return resultsList

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
        
        STR = {f"{list(fixs[i].keys())[0]} {livefixtures[i]['team_h_score'] if livefixtures[i]['team_h_score']!= None else ''} - {livefixtures[i]['team_a_score'] if livefixtures[i]['team_a_score']!= None else ''} {list(fixs[i].keys())[1]}":f"<b>{list(fixs[i].keys())[0]}</b> {livefixtures[i]['team_h_score'] if livefixtures[i]['team_h_score']!= None else ''} - {livefixtures[i]['team_a_score'] if livefixtures[i]['team_a_score']!= None else ''} <b>{list(fixs[i].keys())[1]}</b>"+'\n\n'+'\n\n'.join([fixs[i][j] for j in fixs[i]]) + '\n\n'+'\n'.join([f"<b>{element_stats[k]}:</b>\n{dict2bps(stats[i][k])}" for k in stats[i] if k == 'bps']) for i in fixs}
        
    else:
        now = datetime.utcnow().astimezone(pytz.timezone("UTC"))
        
        fixsns = {pytz.timezone("UTC").localize(datetime.strptime(i['kickoff_time'], '%Y-%m-%dT%H:%M:%SZ'), is_dst=True): i for i in api.fixtures if not(i['finished']) and not (i['finished_provisional']) and i['kickoff_time']}
        fixsns = dict(sorted(fixsns.items()))
        
        for i in fixsns:
           if i > now:
                nextfix = {i: fixsns[i]}
                break
        
        STR = {f"{teams[list(nextfix.values())[0]['team_h']]['name']} - {teams[list(nextfix.values())[0]['team_a']]['name']}": '<b>Next Fixture on\n'+list(nextfix.keys())[0].astimezone(pytz.timezone("Asia/Tehran")).strftime('%a %d %B at %H:%M')+"</b>\nSee fixtures with /fixtures"}
            
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
    STR['Gameweek Standings'] = f'{superleague["superleague_name"]}\n<b>Current GW Standings</b>\n\n'+'\n'.join([f'<b>#{j+1:0{digits}}</b>  {i.replace("_","")} : <b>{sumsgw[i]}</b>' for j,i in enumerate(sumsgw)])
    
    sumsoa = dict(sorted({i: sum([j['oa'] for j in points[i]]) for i in points}.items(), key=lambda item: item[1], reverse=True))
    
    STR['Overall Standings'] = f'{superleague["superleague_name"]}\n<b>Overall Standings</b>\n\n'+'\n'.join([f'<b>#{j+1:0{digits}}</b>  {i.replace("_","")} : <b>{sumsoa[i]}</b>' for j,i in enumerate(sumsoa)])

    return STR
