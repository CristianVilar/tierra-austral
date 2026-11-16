import asyncio,subprocess,time
from playwright.async_api import async_playwright
STUB=open('/home/claude/tierra-austral/tests/landing_auth.py').read().split('STUB=open')[1].split('r"""')[1].split('"""')[0]
async def main():
    srv=subprocess.Popen(['python3','-m','http.server','8791','-d','/home/claude/tierra-austral'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':1100,'height':800},locale='es-CL')).new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.route('**/supabase-js@2/**',lambda r:r.fulfill(body=STUB,content_type='application/javascript'))
        await pg.route('**/*.supabase.co/**',lambda r:r.abort())
        await pg.goto('http://localhost:8791/');await pg.wait_for_timeout(700)
        await pg.fill('#l-name','Cris');await pg.click('#l-go');await pg.wait_for_timeout(300)
        await pg.click('text=Tutorial guiado');await pg.wait_for_timeout(1200)
        await pg.evaluate("""()=>{const me=G.cfg.humanSeat,bot=G.players.find(p=>p.id!==me).id;
          for(const r of RES){G.players[me].res[r]=3;G.players[bot].res[r]=3;}
          window.__r=askTrade({from:bot,to:me,give:{brick:1},get:{grain:1}});window.__bot=bot;window.__me=me;}""")
        await pg.wait_for_timeout(500)
        await pg.click('#tr-ct');await pg.wait_for_timeout(200)
        await pg.click('#modal .tpbtn[data-w="give"][data-r="wool"][data-d="1"]');await pg.wait_for_timeout(100)
        await pg.screenshot(path='/tmp/ct.png')
        await pg.click('#ct-send');await pg.wait_for_timeout(300)
        print('res',await pg.evaluate("window.__r.then(v=>v)"),'cnt',await pg.evaluate("JSON.stringify(G.cnt)"),errs)
        await pg.evaluate("openUpg&&(G.upg[G.cfg.humanSeat]||0,0)")
        await b.close()
    srv.kill()
asyncio.run(main())
