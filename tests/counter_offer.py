import asyncio,subprocess,time
from playwright.async_api import async_playwright
STUB=open('/home/claude/tierra-austral/tests/landing_auth.py').read().split('STUB=open')[1].split('r"""')[1].split('"""')[0]
async def main():
    srv=subprocess.Popen(['python3','-m','http.server','8781','-d','/home/claude/tierra-austral'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':1100,'height':800},locale='es-CL')).new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.route('**/supabase-js@2/**',lambda r:r.fulfill(body=STUB,content_type='application/javascript'))
        await pg.route('**/*.supabase.co/**',lambda r:r.abort())
        await pg.goto('http://localhost:8781/');await pg.wait_for_timeout(800)
        await pg.fill('#l-name','Cris');await pg.click('#l-go');await pg.wait_for_timeout(300)
        await pg.click('text=Tutorial guiado');await pg.wait_for_timeout(1200)
        r=await pg.evaluate("""async()=>{
          const me=G.cfg.humanSeat,bot=G.players.find(p=>p.id!==me).id;
          for(const r of RES){G.players[me].res[r]=3;G.players[bot].res[r]=3;}
          G.players[bot].res.wood=0;G.players[bot].res.brick=0;
          const o={from:me,to:bot,give:{wool:1},get:{ore:1}};
          const c=botCounter(bot,o);
          return {ok:tradeValid(o),dec:botDecides(bot,o),counter:c?JSON.stringify(c.give):null,fn:typeof counterModal};
        }""")
        print(r)
        await pg.evaluate("()=>{G.paused=false;window.__p=counterModal({from:G.cfg.humanSeat,to:1,give:{wool:2},get:{ore:1}});return 1}");await pg.wait_for_timeout(300)
        await pg.screenshot(path='/tmp/counter.png')
        await pg.click('#co-ok');print('acepta',await pg.evaluate("window.__p"),errs)
        await b.close()
    srv.kill()
asyncio.run(main())
