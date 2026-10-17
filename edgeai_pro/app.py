import os
import json
import math
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title='EDGEAI PRO', page_icon='⚽', layout='wide')
LEAGUES = {39:'Premier League',140:'La Liga',135:'Serie A',78:'Bundesliga',61:'Ligue 1',88:'Eredivisie',94:'Primeira Liga',2:'Champions League',3:'Europa League',848:'Conference League'}
BASE='https://v3.football.api-sports.io'
DB=Path('edgeai_history.sqlite3')

def connect():
    c=sqlite3.connect(DB)
    c.execute('CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY, created TEXT, match_date TEXT, payload TEXT)')
    c.commit()
    return c

def api(endpoint, key, params):
    try:
        r=requests.get(BASE+endpoint,headers={'x-apisports-key':key},params=params,timeout=22)
        r.raise_for_status()
        obj=r.json()
        if obj.get('errors'):
            raise ValueError(str(obj['errors']))
        return obj.get('response',[])
    except (requests.RequestException,ValueError) as exc:
        raise RuntimeError(f'{endpoint}: {exc}') from exc

def recent(team, key, before, cache):
    k=(team,before)
    if k not in cache:
        fixtures=api('/fixtures',key,{'team':team,'last':15,'status':'FT'})
        fixtures=[f for f in fixtures if f['fixture']['date'][:10] < before]
        cache[k]=fixtures[:10]
    return cache[k]

def team_goals(fixtures, team):
    scored=[]; conceded=[]
    for f in fixtures:
        home=f['teams']['home']['id']==team
        a=f['goals']['home'] if home else f['goals']['away']
        b=f['goals']['away'] if home else f['goals']['home']
        if a is not None and b is not None:
            scored.append(a);conceded.append(b)
    return scored,conceded

def poisson_tail(lam, line):
    # Probability of at least line+1 goals.
    return 1-sum(math.exp(-lam)*lam**k/math.factorial(k) for k in range(line+1))

def candidates(f, key, cache, day):
    home=f['teams']['home']; away=f['teams']['away']
    h=team_goals(recent(home['id'],key,day,cache),home['id'])
    a=team_goals(recent(away['id'],key,day,cache),away['id'])
    if min(len(h[0]),len(a[0]))<5:
        return [],'Färre än fem verifierade tidigare matcher för något lag'
    hs,hc=h;as_,ac=a
    lh=max(.15,min(4.5,(sum(hs)/len(hs)+sum(ac)/len(ac))/2))
    la=max(.15,min(4.5,(sum(as_)/len(as_)+sum(hc)/len(hc))/2))
    markets=[]
    def add(name,p,hit,notes):
        p=max(.01,min(.99,p))
        # conservative adjustment for simple, uncalibrated model
        p=.5+(p-.5)*.70
        fair=1/p
        minodd=fair*1.06
        markets.append({'Match':home['name']+' – '+away['name'],'Tävling':LEAGUES.get(f['league']['id'],'?'),'Spel':name,'Sannolikhet %':round(p*100,1),'Sannolikhet 1–10':max(1,min(10,math.ceil(p*10))),'Minimiodds':round(minodd,2),'Aktuellt odds':'Ej verifierat','Styrka 1–10':round(5+3*abs(p-.5)+1.5*hit,1),'Underlag':notes,'Status':'KANDIDAT – odds saknas'})
    for line in [0,1,2]:
        ph=poisson_tail(lh,line)
        pa=poisson_tail(la,line)
        add(f"{home['name']} över {line+.5} lagmål",ph,sum(x>line for x in hs)/len(hs),f'10-matchform (eller färre): {len(hs)} / {len(as_)}; målmedel {lh:.2f}')
        add(f"{away['name']} över {line+.5} lagmål",pa,sum(x>line for x in as_)/len(as_),f'10-matchform (eller färre): {len(hs)} / {len(as_)}; målmedel {la:.2f}')
    for line in [1,2,3]:
        p=poisson_tail(lh+la,line)
        actual=[x+y for x,y in zip(hs,hc)]
        add(f'Över {line+.5} mål',p,sum(x>line for x in actual)/len(actual),f'Målmodell λ={lh+la:.2f}; baserad på gjorda och insläppta mål')
    add('Båda lagen gör mål', (1-math.exp(-lh))*(1-math.exp(-la)), sum(x>0 for x in hs)/len(hs), 'Oberoende Poisson-modell, endast målstatistik')
    # Do not pretend to have priced markets lacking statistics.
    return markets,None



def odds_diagnostics(key, fixture_id):
    """Small, explicit odds probe; never persist keys or raw API responses."""
    report={'bookmakers': [], 'bet_types': [], 'fixture_markets': [], 'errors': []}
    for endpoint, target in [('/odds/bookmakers','bookmakers'),('/odds/bets','bet_types')]:
        try:
            report[target]=api(endpoint,key,{})
        except RuntimeError as exc:
            report['errors'].append(f'{endpoint}: {exc}')
    if fixture_id:
        try:
            report['fixture_markets']=api('/odds',key,{'fixture':fixture_id,'page':1})
        except RuntimeError as exc:
            report['errors'].append(f'/odds: {exc}')
    return report

def bet365_rows(report):
    bookmakers=report['bookmakers']
    matching=[b for b in bookmakers if 'bet365' in str(b.get('name','')).lower().replace(' ','')]
    rows=[]
    for event in report['fixture_markets']:
        for book in event.get('bookmakers',[]):
            if 'bet365' not in str(book.get('name','')).lower().replace(' ',''):
                continue
            for bet in book.get('bets',[]):
                vals=bet.get('values',[])
                rows.append({'Marknad':bet.get('name',''), 'Marknads-ID':bet.get('id',''), 'Antal utfall':len(vals), 'Exempel på utfall':', '.join(str(v.get('value','')) for v in vals[:4])})
    return matching,rows

st.title('⚽ EDGEAI PRO 1.2')
st.caption('Datadriven matchscreening • inga påhittade odds • samma sparade analys kan öppnas igen')
with st.sidebar:
    st.header('Inställningar')
    key=st.text_input('API-Football nyckel',value=st.secrets.get('API_FOOTBALL_KEY',os.getenv('API_FOOTBALL_KEY','')),type='password',help='Nyckeln används bara för API-anrop och sparas inte i historiken.')
    day=st.date_input('Matchdatum',date.today())
    selected=st.multiselect('Godkända tävlingar',options=list(LEAGUES),default=list(LEAGUES),format_func=lambda i:LEAGUES[i])
    st.info('Gratis-API: begränsad anropskvot och säsongstäckning. Vissa anrop kräver betald API-Football-plan.')

st.divider()
with st.expander('🔎 Bet365 – kontrollera API-täckning innan köp', expanded=False):
    st.write('Testar vilka spelbolag och marknader API-Football faktiskt lämnar ut för din nyckel. Detta är **inte** en garanti för Bet365 Sverige eller alla matcher.')
    st.caption('Kontrollen använder upp till tre API-anrop per klick. Ange ett fixture-ID för att även kontrollera odds för en specifik match. Nyckeln sparas inte.')
    fixture_text=st.text_input('Fixture-ID (valfritt)',placeholder='Exempel: 1234567',help='Ett numeriskt match-ID från API-Football, inte lagets ID.')
    fixture_ok=not fixture_text.strip() or (fixture_text.strip().isdigit() and int(fixture_text.strip())>0)
    if not fixture_ok: st.error('Fixture-ID måste vara ett positivt heltal.')
    if st.button('KONTROLLERA BET365 OCH MARKNADER',disabled=not bool(key) or not fixture_ok):
        with st.spinner('Kontrollerar API-Footballs bookmakerlista, marknader och eventuella matchodds…'):
            result=odds_diagnostics(key,int(fixture_text.strip()) if fixture_text.strip() else None)
        st.session_state['odds_diagnostics']=result
        st.session_state['odds_fixture_id']=fixture_text.strip()
    report=st.session_state.get('odds_diagnostics')
    if report is not None:
        matching,market_rows=bet365_rows(report)
        if report['bookmakers']:
            if matching:
                st.success('Bet365 finns i bookmakerlistan för detta API-svar.')
                st.dataframe(pd.DataFrame([{'ID':b.get('id'),'Namn':b.get('name')} for b in matching]),hide_index=True)
            else:
                st.warning('Bet365 hittades inte i bookmakerlistan. Det bevisar inte att Bet365 saknas i alla produkter eller abonnemang.')
        else:
            st.info('Ingen bookmakerlista kunde verifieras. Se eventuella API-fel nedan.')
        if report['bet_types']:
            st.write(f"**{len(report['bet_types'])} marknadstyper** returnerades av /odds/bets. Det betyder inte att de erbjuds för en viss match eller hos Bet365.")
            terms=['corner','card','shot','assist','goal','handicap','winner','over','under']
            listed=[{'ID':b.get('id'),'Marknad':b.get('name')} for b in report['bet_types'] if any(t in str(b.get('name','')).lower() for t in terms)]
            if listed:st.dataframe(pd.DataFrame(listed),hide_index=True,use_container_width=True)
        if st.session_state.get('odds_fixture_id'):
            if market_rows:
                st.success(f'{len(market_rows)} Bet365-marknader hittades för vald match.')
                st.dataframe(pd.DataFrame(market_rows),hide_index=True,use_container_width=True)
            else:
                st.warning('Inga Bet365-marknader kunde verifieras för vald match. Det kan bero på täckning, tidpunkt, abonnemang eller att match-ID saknar odds.')
        if report['errors']:
            st.error('API-begränsningar eller fel:\n'+'\n'.join(report['errors']))
        st.caption('Observera: Endast en ögonblicksbild. Kontrollera även pris, marknadstäckning och geografisk tillgänglighet hos leverantören före köp.')

# Public web odds discovery: search results are leads, never treated as verified prices.
# Brave Search API is optional; its free allowance and terms may change.
def web_odds_leads(query, token):
    if not token:
        return [], 'Ingen söknyckel: använd öppna söklänkar eller fyll i kontrollerat odds manuellt.'
    try:
        r=requests.get('https://api.search.brave.com/res/v1/web/search',
            headers={'Accept':'application/json','X-Subscription-Token':token},
            params={'q':query,'count':6,'search_lang':'en'},timeout=18)
        r.raise_for_status()
        data=r.json()
        return [{'Titel':x.get('title',''), 'URL':x.get('url',''),
                 'Utdrag (ej verifierat odds)':x.get('description','')}
                for x in data.get('web',{}).get('results',[])], None
    except (requests.RequestException,ValueError) as exc:
        return [],f'Sökningen misslyckades: {exc}'

with st.expander('🌐 Hitta odds online – flera spelbolag',expanded=False):
    st.write('Sök efter odds på valfri marknad hos offentliga oddswebbplatser. Sökresultat är **ledtrådar**, inte verifierade aktuella odds. Kontrollera alltid exakt marknad, lina, datum och spelbolag.')
    search_key=st.text_input('Brave Search API-nyckel (valfri)',type='password',
        value=st.secrets.get('BRAVE_SEARCH_API_KEY',os.getenv('BRAVE_SEARCH_API_KEY','')),
        help='Separat söktjänst. Nyckeln lagras inte i analyshistoriken. Gratisnivå kan finnas, kontrollera leverantörens aktuella villkor.')
    match_query=st.text_input('Match',placeholder='Arsenal Chelsea')
    market_query=st.text_input('Spelmarknad',placeholder='Arsenal over 5.5 corners')
    if st.button('SÖK ODDS PÅ WEBBEN',disabled=not bool(match_query.strip() and market_query.strip())):
        query=f'{match_query.strip()} {market_query.strip()} odds bookmaker betting'
        leads,error=web_odds_leads(query,search_key)
        st.session_state['web_leads']=(leads,error,query)
    if st.session_state.get('web_leads'):
        leads,error,query=st.session_state['web_leads']
        if error:st.info(error)
        if leads:
            for lead in leads:
                if lead['URL'].startswith(('https://','http://')):
                    st.markdown(f"[{lead['Titel']}]({lead['URL']})")
                    st.caption(lead['Utdrag (ej verifierat odds)'])
        st.link_button('Sök samma odds på Google', 'https://www.google.com/search?q='+requests.utils.quote(query))
    st.caption('Sökningen är inte begränsad till Bet365. Automatisk och tillförlitlig avläsning av aktuella odds kräver oftast en licensierad datakälla.')

with st.expander('✍️ Kontrollera odds och jämför med minimiodds',expanded=False):
    st.write('Ange ett odds du själv har kontrollerat på ett spelbolags webbplats. Detta påverkar inte originalanalysen och är inte ett automatiskt verifierat odds.')
    if st.session_state.get('analysis',{}).get('rows'):
        rows=st.session_state['analysis']['rows']
        names=[f"{r['Match']} | {r['Spel']} | min {r['Minimiodds']}" for r in rows]
        idx=st.selectbox('Spelkandidat',range(len(names)),format_func=lambda i:names[i])
        price=st.number_input('Hittat decimalodds',min_value=1.01,max_value=1000.0,value=1.80,step=.05)
        bookmaker=st.text_input('Spelbolag / källa',placeholder='Bet365, Betsson, Unibet ...')
        if st.button('JÄMFÖR ODDS'):
            row=rows[idx]
            edge=100*(price*row['Sannolikhet %']/100-1)
            st.write(f"**{row['Spel']}** – ditt odds {price:.2f}; minimiodds {row['Minimiodds']:.2f}.")
            if price>=row['Minimiodds']:
                st.success('Oddset når modellens preliminära minimigräns.')
            else:st.warning('Oddset ligger under modellens preliminära minimigräns.')
            st.caption(f'Indikativt EV enligt okalibrerad modell: {edge:+.1f} %. Källa: {bookmaker or "ej angiven"}. Kontrollera att marknaden och linan är identiska. Inte ett säkerställt spelvärde.')
    else:st.info('Kör eller öppna en tidigare analys först.')

run=st.button('▶ KÖR ANALYS',type='primary',disabled=not bool(key and selected))
if run:
    try:
        with st.spinner('Hämtar matchschema och granskar målmarknader…'):
            games=api('/fixtures',key,{'date':day.isoformat()})
            games=[g for g in games if g['league']['id'] in selected and g['fixture']['status']['short'] in ('NS','TBD')]
            games.sort(key=lambda g:g['fixture']['date'])
            cache={}; rows=[]; missing=[]
            progress=st.progress(0)
            for i,g in enumerate(games):
                try:
                    found,reason=candidates(g,key,cache,day.isoformat())
                    rows.extend(found)
                    if reason: missing.append(f"{g['teams']['home']['name']}–{g['teams']['away']['name']}: {reason}")
                except RuntimeError as e:
                    missing.append(f"{g['teams']['home']['name']}–{g['teams']['away']['name']}: {e}")
                progress.progress((i+1)/len(games))
            rows.sort(key=lambda x:(-x['Styrka 1–10'],-x['Sannolikhet %'],x['Match'],x['Spel']))
            for i,r in enumerate(rows):r['Rank']=i+1
            payload={'matches':len(games),'rows':rows,'missing':missing,'date':day.isoformat(),'created':datetime.now(timezone.utc).isoformat()}
            c=connect();c.execute('INSERT INTO runs(created,match_date,payload) VALUES(?,?,?)',(payload['created'],day.isoformat(),json.dumps(payload,ensure_ascii=False)));c.commit();c.close()
            st.session_state['analysis']=payload
    except RuntimeError as e:
        st.error(f'API-anrop misslyckades: {e}')

with st.expander('Tidigare analyser (sparade på servern)',expanded=False):
    c=connect();history=c.execute('SELECT id,created,match_date FROM runs ORDER BY id DESC LIMIT 30').fetchall();c.close()
    if history:
        choice=st.selectbox('Välj körning',history,format_func=lambda r:f'#{r[0]} | {r[2]} | {r[1][:16]} UTC')
        if st.button('Öppna sparad analys'):
            c=connect();data=c.execute('SELECT payload FROM runs WHERE id=?',(choice[0],)).fetchone();c.close()
            if data:st.session_state['analysis']=json.loads(data[0])
    else:st.write('Ingen historik ännu.')

p=st.session_state.get('analysis')
if p:
    st.subheader(f"Analys {p['date']}")
    st.write(f"**{p['matches']} matcher**, **{len(p['rows'])} målmarknadskandidater**. Analysen sparades {p['created'][:16]} UTC.")
    st.warning('Version 1.2 analyserar fortfarande ENDAST mål och båda lagen gör mål. Hörnor, kort, 1X2, skott och automatisk inhämtning av verifierade odds är ännu inte implementerade. Ingen kandidat är ett verifierat spelvärde utan marknadsodds. Sannolikheter är förenklade, ej kalibrerade modellskattningar.')
    if p['rows']:
        df=pd.DataFrame(p['rows'])
        cols=['Rank','Match','Tävling','Spel','Sannolikhet %','Sannolikhet 1–10','Minimiodds','Aktuellt odds','Styrka 1–10','Status']
        st.dataframe(df[cols].head(30),hide_index=True,use_container_width=True)
        with st.expander('Metod och underlag'):
            st.dataframe(df[['Match','Spel','Underlag']],hide_index=True,use_container_width=True)
        st.download_button('Ladda ner kandidater (CSV)',df.to_csv(index=False).encode('utf-8-sig'),file_name=f'edgeai_{p["date"]}.csv',mime='text/csv')
    else:st.info('Inga kandidater kunde beräknas från tillgänglig data.')
    if p['missing']:
        with st.expander(f'Ofullständiga matcher / API-fel ({len(p["missing"])})'):
            for msg in p['missing']:st.write('• '+msg)
else:
    st.info('Ange din API-nyckel och tryck KÖR ANALYS. Historik finns under sidomenyn i appen.')
