"""Dependency-free meal planner. Python 3.10+."""
import json, os, math
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen

# Ingredient quantities are per person, for one dinner.
def recipe(name, category, ingredients, steps):
    return dict(name=name, category=category, ingredients=[dict(name=n, quantity=q, unit=u) for n,q,u in ingredients], steps=steps)
RECIPES = [
recipe('Lemon chicken & broccoli','Keto',[('Chicken breast',200,'g'),('Broccoli',150,'g'),('Olive oil',15,'ml'),('Lemon',0.25,'whole')],['Heat oven to 400°F / 200°C.','Put chicken and broccoli on a baking tray. Toss with oil and lemon juice.','Roast 20–30 minutes, until chicken reaches 165°F / 74°C internally.']),
recipe('Spinach feta omelet','Keto',[('Eggs',3,'whole'),('Spinach',60,'g'),('Feta',40,'g'),('Olive oil',5,'ml')],['Warm oil in a skillet over medium heat; wilt spinach.','Beat eggs and pour into the skillet. Sprinkle with feta.','Cook until eggs are fully set; fold and serve.']),
recipe('Chickpea tomato skillet','Vegan',[('Canned chickpeas, drained',180,'g'),('Canned tomatoes',200,'g'),('Spinach',60,'g'),('Olive oil',10,'ml'),('Rice, dry',60,'g')],['Cook rice according to package directions.','Warm oil in a pan; add tomatoes and chickpeas. Simmer 12 minutes.','Stir in spinach until wilted; serve over rice.']),
recipe('Tofu vegetable rice bowl','Vegan',[('Firm tofu',200,'g'),('Broccoli',150,'g'),('Rice, dry',60,'g'),('Soy sauce',15,'ml'),('Olive oil',10,'ml')],['Cook rice according to package directions.','Drain and cube tofu. Pan-fry in oil for 8–10 minutes, turning occasionally.','Add broccoli and a splash of water; cover for 5 minutes. Add soy sauce and serve over rice.']),
recipe('Turkey bean bowl','High Protein',[('Ground turkey',200,'g'),('Canned black beans, drained',100,'g'),('Canned tomatoes',150,'g'),('Rice, dry',50,'g')],['Cook rice according to package directions.','Brown turkey in a nonstick skillet, breaking it up, until it reaches 165°F / 74°C.','Add beans and tomatoes. Simmer 10 minutes; serve over rice.']),
recipe('Chicken lentil stew','High Protein',[('Chicken breast',200,'g'),('Lentils, dry',60,'g'),('Carrot',100,'g'),('Canned tomatoes',150,'g')],['Dice chicken and carrot. Rinse lentils.','Combine in a pot with tomatoes and enough water to cover by 1 inch.','Simmer 25–35 minutes until lentils are tender and chicken reaches 165°F / 74°C. Add water as needed.']),
recipe('Lentil rice pot','Affordable',[('Lentils, dry',80,'g'),('Rice, dry',60,'g'),('Carrot',100,'g'),('Canned tomatoes',150,'g')],['Rinse lentils and rice. Dice carrot.','Simmer lentils and carrot in water for 15 minutes.','Add rice and tomatoes; add water as needed and simmer until rice and lentils are tender, about 20 minutes.']),
recipe('Bean & egg rice bowl','Affordable',[('Eggs',2,'whole'),('Canned black beans, drained',150,'g'),('Rice, dry',60,'g'),('Olive oil',5,'ml')],['Cook rice according to package directions.','Warm drained beans in a saucepan with a little water.','Scramble eggs in oil until fully set. Serve with beans over rice.'])]

def plan(data):
    category = data.get('category')
    if category not in {r['category'] for r in RECIPES}: raise ValueError('Select a valid recipe type.')
    people, days = data.get('people'), data.get('days')
    if type(people) is not int or not 1 <= people <= 20: raise ValueError('People must be an integer from 1 to 20.')
    if type(days) is not int or not 1 <= days <= 31: raise ValueError('Days must be an integer from 1 to 31.')
    location = data.get('location','')
    if not isinstance(location,str) or not location.strip() or len(location)>200: raise ValueError('Enter a ZIP code or address (up to 200 characters).')
    pool=[r for r in RECIPES if r['category']==category]
    meals=[]; totals={}
    for day in range(days):
        r=pool[day % len(pool)]; ingredients=[]
        for i in r['ingredients']:
            item={**i,'quantity':round(i['quantity']*people,2)}; ingredients.append(item)
            key=(i['name'],i['unit']); totals[key]=totals.get(key,0)+item['quantity']
        meals.append(dict(day=day+1,name=r['name'],ingredients=ingredients,steps=r['steps']))
    shopping=[dict(name=n,unit=u,quantity=round(q,2)) for (n,u),q in sorted(totals.items())]
    result=dict(meals=meals,shopping=shopping,people=people,days=days,location=location.strip(),scope='One dinner per day')
    endpoint=os.getenv('GROCERY_PROVIDER_URL','')
    if not endpoint:
        result.update(mode='demo',notice='Demo only: these are fictional stores, not the closest stores. Stock, prices and availability are not verified.',stores=[dict(name=f'Demo grocery {i}',items=[dict(**item,availability='Not verified') for item in shopping]) for i in range(1,4)])
    else:
        if not endpoint.startswith('https://'): raise RuntimeError('Grocery provider must use HTTPS.')
        headers={'Content-Type':'application/json'}
        token=os.getenv('GROCERY_PROVIDER_TOKEN','')
        if token: headers['Authorization']='Bearer '+token
        req=Request(endpoint,data=json.dumps(dict(location=location.strip(),ingredients=shopping,limit=3)).encode(),headers=headers,method='POST')
        with urlopen(req,timeout=15) as response: provider=json.load(response)
        stores=provider.get('stores')
        if not isinstance(stores,list): raise RuntimeError('Invalid provider response.')
        for s in stores:
            if not isinstance(s,dict) or not isinstance(s.get('name'),str) or not isinstance(s.get('items'),list): raise RuntimeError('Invalid store response.')
            distance=s.get('distanceKm')
            if type(distance) not in (int,float) or not math.isfinite(distance) or distance<0: raise RuntimeError('Invalid store distance.')
        result.update(mode='live',notice='Store information supplied by the configured provider. Check item status and freshness before shopping.',stores=sorted(stores,key=lambda s:s['distanceKm'])[:3])
    return result

class Handler(BaseHTTPRequestHandler):
    def send(self,status,body,kind='application/json'):
        raw=body.encode(); self.send_response(status); self.send_header('Content-Type',kind+'; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path=='/': self.send(200,Path(__file__).with_name('index.html').read_text(), 'text/html')
        else: self.send(404,json.dumps({'error':'Not found'}))
    def do_POST(self):
        if self.path!='/api/plan': return self.send(404,json.dumps({'error':'Not found'}))
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=8192: raise ValueError('Invalid request size.')
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict): raise ValueError('Expected a JSON object.')
            self.send(200,json.dumps(plan(data)))
        except (ValueError,TypeError) as exc: self.send(400,json.dumps({'error':str(exc)}))
        except Exception: self.send(502,json.dumps({'error':'Grocery provider unavailable or misconfigured. Try again or check server configuration.'}))

if __name__=='__main__':
    print('Meal planner: http://localhost:8000')
    ThreadingHTTPServer(('127.0.0.1',8000),Handler).serve_forever()
