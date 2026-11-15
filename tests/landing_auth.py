import asyncio,subprocess,time
from playwright.async_api import async_playwright
STUB=open('stub.js').read() if False else r"""
window.supabase={createClient:(u,k,o)=>{
 const L=[];let S=JSON.parse(localStorage.getItem('sb-test-auth-token')||'null');
 const db=()=>JSON.parse(localStorage.getItem('zz-db')||'{}'),sv=d=>localStorage.setItem('zz-db',JSON.stringify(d));
 const auth={async getSession(){return{data:{session:S}}},onAuthStateChange(cb){L.push(cb);setTimeout(()=>cb('INITIAL_SESSION',S),0);return{data:{subscription:{unsubscribe(){}}}}},
  async signInWithOtp({email}){window.__sent=email;return{error:null}},
  async signInWithOAuth(o){window.__oauth=o;return{error:null}},
  async verifyOtp({email,token}){if(token!=='123456')return{error:{message:'Token has expired or is invalid'}};S={access_token:'tok',user:{id:'u1',email,app_metadata:{provider:'google'}}};localStorage.setItem('sb-test-auth-token',JSON.stringify(S));L.forEach(f=>f('SIGNED_IN',S));return{data:{session:S},error:null}},
  async signOut(){S=null;localStorage.removeItem('sb-test-auth-token');L.forEach(f=>f('SIGNED_OUT',null));return{error:null}}};
 return{auth,realtime:{setAuth(){}},channel(){return{on(){return this},subscribe(cb){setTimeout(()=>cb('SUBSCRIBED'),0)},send(){}}},removeChannel(){},
  rpc(n){window.__rpc=n;return Promise.resolve({error:null})},
  from(t){return{select(){return Promise.resolve({data:Object.values(db()),error:null})},
   upsert(rows){const d=db();rows.forEach(r=>d[r.k]=r);sv(d);return Promise.resolve({error:null})},
   delete(){return{in(c,ks){const d=db();ks.forEach(x=>delete d[x]);sv(d);return Promise.resolve({error:null})}}}}}}}};
"""
async def main():
    srv=subprocess.Popen(['python3','-m','http.server','8772','-d','/home/claude/tierra-austral'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    res=[]
    def ok(c,m):res.append((bool(c),m));print('OK  ' if c else 'FALLA',m)
    async with async_playwright() as p:
        b=await p.chromium.launch()
        c=await b.new_context(viewport={'width':390,'height':844},locale='es-CL')
        pg=await c.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.route('**/supabase-js@2/**',lambda r:r.fulfill(body=STUB,content_type='application/javascript'))
        await pg.route('**/*.supabase.co/**',lambda r:r.abort())
        await pg.goto('http://localhost:8772/');await pg.wait_for_timeout(1200)
        ok(await pg.locator('#land.on').count()==1,'la portada aparece al abrir')
        ok(await pg.locator('#modal.open').count()==0,'no hay modal encima')
        ok(await pg.evaluate("getComputedStyle(document.body).overflow")=='hidden','no se hace scroll al fondo')
        ok(await pg.evaluate("document.activeElement.id!=='l-name'"),'en telefono no abre el teclado solo')
        # idioma
        await pg.click('.llang button[data-l="en"]');await pg.wait_for_timeout(400)
        ok('Play as guest' in await pg.inner_text('#l-go'),'cambia a ingles')
        await pg.click('.llang button[data-l="es"]');await pg.wait_for_timeout(400)
        ok('invitado' in (await pg.inner_text('#l-go')).lower(),'vuelve a espanol')
        # ajustes
        await pg.click('#l-gear');await pg.wait_for_timeout(300)
        ok(await pg.locator('#modal.open').count()==1,'el engranaje abre ajustes')
        await pg.click('#modal .mact .btn.primary');await pg.wait_for_timeout(300)
        ok(await pg.locator('#modal.open').count()==0 and await pg.locator('#land.on').count()==1,'Listo vuelve a la portada')
        # login por correo desde la portada
        await pg.click('#l-mail');await pg.wait_for_timeout(300)
        ok(await pg.locator('#lg-mail').count()==1,'abre el acceso por correo')
        await pg.click('#lg-guest');await pg.wait_for_timeout(300)
        ok(await pg.locator('#modal.open').count()==0 and await pg.locator('#land.on').count()==1,'Volver regresa a la portada')
        # google: ahora armamos la URL de autorizacion nosotros
        nav=[]
        await pg.route('**/*.supabase.co/auth/v1/authorize**',lambda r:(nav.append(r.request.url),asyncio.ensure_future(r.abort()))[0])
        await pg.click('#l-goog');await pg.wait_for_timeout(1200)
        ok(any('provider=google' in u and 'code_challenge_method=s256' in u for u in nav),'Google parte con reto S256 propio')
        await pg.goto('http://localhost:8772/');await pg.wait_for_timeout(900)
        # invitado
        await pg.fill('#l-name','Cris<>');await pg.click('#l-go');await pg.wait_for_timeout(500)
        ok(await pg.evaluate('LANDM')=='hub','invitado: pasa al menú principal')
        ok(await pg.locator('.htile').count()>=8 and await pg.locator('#modal.open').count()==0,'invitado: el menú es una pantalla con fichas')
        ok(await pg.evaluate("PNAME")=='Cris','el nombre se limpia y se guarda')
        pass
        ok('invitado' in (await pg.inner_text('#acct')).lower(),'el menu muestra modo invitado')
        # volver a la portada con "Cambiar nombre"
        await pg.click('.hubhead a');await pg.wait_for_timeout(400)
        ok(await pg.locator('#land.on').count()==1,'Cambiar nombre vuelve a la portada')
        ok(await pg.input_value('#l-name')=='Cris','trae el nombre guardado')
        # entrar con cuenta por correo y confirmar que pasa al menu
        await pg.click('#l-mail');await pg.fill('#lg-mail','cris@test.cl');await pg.click('#lg-send')
        await pg.wait_for_selector('#lg-code');await pg.fill('#lg-code','123456');await pg.click('#lg-ok');await pg.wait_for_timeout(1500)
        ok(await pg.evaluate('LANDM')=='hub','tras entrar pasa al menu')
        # portada con sesion
        await pg.evaluate("showWelcome()");await pg.wait_for_timeout(400)
        ok('cris@test.cl' in await pg.inner_text('#landin'),'la portada muestra la cuenta')
        ok((await pg.inner_text('#l-go')).strip().lower()=='entrar','el boton dice Entrar')
        ok(await pg.locator('#l-goog').count()==0,'con sesion no ofrece Google de nuevo')
        await pg.click('#l-out');await pg.wait_for_timeout(900)
        ok(await pg.locator('#l-goog').count()==1,'cerrar sesion vuelve al estado invitado')
        ok(await pg.locator('#land.on').count()==1,'y sigue en la portada')
        # sala por enlace sin cuenta
        await pg.goto('http://localhost:8772/?sala=ABCDE');await pg.wait_for_timeout(1500)
        ok(await pg.locator('#lg-mail').count()==1,'enlace de sala sigue pidiendo cuenta')
        # escritorio: foco en el nombre
        c2=await b.new_context(viewport={'width':1280,'height':800},locale='es-CL');p2=await c2.new_page()
        p2.on('pageerror',lambda e:errs.append('pc:'+str(e)))
        await p2.route('**/supabase-js@2/**',lambda r:r.fulfill(body=STUB,content_type='application/javascript'))
        await p2.route('**/*.supabase.co/**',lambda r:r.abort())
        await p2.goto('http://localhost:8772/');await p2.wait_for_timeout(1200)
        ok(await p2.evaluate("document.activeElement.id")=='l-name','en PC el foco va al nombre')
        await p2.keyboard.type('Ana');await p2.keyboard.press('Enter');await p2.wait_for_timeout(500)
        ok(await p2.evaluate('LANDM')=='hub','Enter entra al menú')
        print('pageerrors',errs)
        await b.close()
    srv.terminate()
    print('PASS' if all(r[0] for r in res) and not errs else 'HAY FALLAS')
asyncio.run(main())
