import asyncio,subprocess,time,sys
sys.path.insert(0,'/home/claude/tierra-austral/tests')
from playwright.async_api import async_playwright
STUB=open('/home/claude/tierra-austral/tests/landing_auth.py').read().split('STUB=open')[1].split('r"""')[1].split('"""')[0]
async def main():
    srv=subprocess.Popen(['python3','-m','http.server','8773','-d','/home/claude/tierra-austral'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for name,vp in [('pc',{'width':1280,'height':900}),('mv',{'width':390,'height':844})]:
            c=await b.new_context(viewport=vp,locale='es-CL');pg=await c.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.route('**/supabase-js@2/**',lambda r:r.fulfill(body=STUB,content_type='application/javascript'))
            await pg.route('**/*.supabase.co/**',lambda r:r.abort())
            await pg.goto('http://localhost:8773/');await pg.wait_for_timeout(1200)
            await pg.evaluate("AUTH.setSession({access_token:'t',user:{id:'u1',email:'vilarcristianms@gmail.com'}})")
            await pg.fill('#l-name','BALDOR');await pg.click('#l-go');await pg.wait_for_timeout(600)
            print(name,'hub',await pg.evaluate("[document.getElementById('land').classList.contains('on'),LANDM,document.querySelectorAll('.htile').length]"))
            await pg.screenshot(path=f'/tmp/hub_{name}.png')
            await pg.click('text=Multijugador en línea');await pg.wait_for_timeout(500)
            await pg.screenshot(path=f'/tmp/net_{name}.png')
            await pg.evaluate("closeModal()")
            await pg.click('text=Tutorial guiado');await pg.wait_for_timeout(1500)
            print(name,'juego',await pg.evaluate("[document.getElementById('land').classList.contains('on'),G.phase]"),errs)
            await pg.screenshot(path=f'/tmp/game_{name}.png')
            await c.close()
        await b.close()
    srv.kill()
asyncio.run(main())
