"""Offline regression checks for odds market matching; run: python test_market_matching.py"""
import ast
from pathlib import Path
src=ast.parse(Path(__file__).with_name('app.py').read_text())
functions=[n for n in src.body if isinstance(n,ast.FunctionDef) and n.name in ('norm','_selection','match_offer','_recent_timestamp')]
import datetime
ns={'datetime':datetime.datetime,'timedelta':datetime.timedelta,'timezone':datetime.timezone}
exec(compile(ast.Module(body=functions,type_ignores=[]),'app.py','exec'),ns)
fixture={'teams':{'home':{'name':'Manchester City'},'away':{'name':'AEK Athens'}}}
def check(candidate,market,selection,expected):
    result=ns['match_offer']({'Spel':candidate},{'market':market,'selection':selection},fixture)
    assert result==expected,(candidate,market,selection,result,expected)
check('Båda lagen gör mål','Both Teams to Score','Yes',True)
check('Båda lagen gör mål','Both Teams to Score','No',False)
check('Båda lagen gör mål','Both Teams to Score - 1st Half','Yes',False)
check('Över 2.5 mål','Goals Over/Under','Over 2.5',True)
check('Över 2.5 mål','Goals Over/Under','Over 3.5',False)
check('Manchester City över 5.5 hörnor','Home Corners Over/Under','Over 5.5',True)
check('Manchester City över 5.5 hörnor','Away Corners Over/Under','Over 5.5',False)
check('Manchester City över 1.5 lagmål','Home Team Goals Over/Under','Over 1.5',True)
check('Manchester City över 1.5 lagmål','Home Team Goals Over/Under - 1st Half','Over 1.5',False)
check('1X2 1','Match Winner','Home',True)
check('1X2 X','Match Winner','Draw',True)
check('1X2 2','Match Winner','Home',False)
print('12 market matching regression checks passed')

check('Manchester City AH -0.5','Asian Handicap','Home -0.5',True)
check('Manchester City AH -0.5','Asian Handicap','Home +0.5',False)
check('Manchester City AH -0.5','European Handicap','Home -0.5',False)
print('3 Asian handicap checks passed')
