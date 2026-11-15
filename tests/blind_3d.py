import asyncio,subprocess,time
from playwright.async_api import async_playwright
async def m():
    srv=subprocess.Popen(['python3','-m','http.server','8779','-d','/home/claude/tierra-austral'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    res=[]
    def ok(c,msg):res.append(bool(c));print('OK  ' if c else 'FALLA',msg)
    async with async_playwright() as p:
        b=await p.chromium.launch();c=await b.new_context(viewport={'width':1280,'height':900},locale='es-CL')
        pg=await c.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.route('**/*.supabase.co/**',lambda r:r.abort())
        await pg.goto('http://localhost:8779/');await pg.wait_for_timeout(1200)
        await pg.evaluate("localStorage.setItem('ta-view','3d');PNAME='Cris';closeModal();landHide()")
        # partida ciega
        await pg.evaluate("launch({name:'Tú',bots:2,speed:1,spectate:false,map:'blind',rules:{},diff:['normal','easy','easy']})");await pg.wait_for_timeout(1500)
        ok(await pg.evaluate("G.hidden")==True,'la partida parte con el mapa oculto')
        ok(await pg.evaluate("document.querySelector('#v3d').classList.contains('on')")==False,'el 3D no se abre solo con mapa oculto')
        await pg.evaluate("open3d(true)");await pg.wait_for_timeout(600)
        ok(await pg.evaluate("document.querySelector('#v3d').classList.contains('on')")==False,'pedir 3D a mano queda bloqueado')
        t=await pg.evaluate("document.querySelector('#toast')?document.querySelector('#toast').innerText:''")
        ok('oculto' in t.lower(),'avisa por que: '+t.replace('\n',' ')[:60])
        # el 2D sigue con niebla
        ok(await pg.evaluate("document.querySelector('#board').innerHTML.includes('g-fog')")==True,'el tablero 2D muestra niebla')
        # al revelar, vuelve el 3D
        await pg.evaluate("G.hidden=false;G.revealAt=Date.now();auto3d()");await pg.wait_for_timeout(900)
        ok(await pg.evaluate("document.querySelector('#v3d').classList.contains('on')")==True,'al revelarse el mapa, el 3D se abre solo')
        print('pageerrors',errs)
        await b.close()
    srv.terminate();print('PASS' if all(res) and not errs else 'HAY FALLAS')
asyncio.run(m())
