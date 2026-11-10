"""Pruebas de humo en teléfonos (emulación de iPhone y Android con Chromium).
Uso:  python3 -m http.server 8765 &   python3 tests/mobile_smoke.py [url]
Termina con código 1 si algo falla, para que lo use la integración continua."""
import sys, os
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8765/index.html'
CHROME = os.environ.get('CHROME_PATH') or None
DEVICES = ['iPhone 13', 'Pixel 7', 'iPhone SE']
fails = []

def check(cond, msg):
    print(('OK   ' if cond else 'FALLA'), msg)
    if not cond: fails.append(msg)

def run(p, dev):
    d = p.devices[dev]
    kw = {'executable_path': CHROME} if CHROME else {}
    b = p.chromium.launch(args=['--no-sandbox'], **kw)
    ctx = b.new_context(**d)
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    # sin red externa: fuentes y librería de salas se bloquean (el juego solo local no las necesita)
    pg.route('**/*', lambda r: r.abort() if any(x in r.request.url for x in ('fonts.g', 'jsdelivr', 'supabase.co')) else r.continue_())
    print('\n==', dev)
    pg.goto(URL); pg.wait_for_timeout(800)
    check(pg.locator('#w-name').count() == 1, 'aparece la bienvenida con el campo de nombre')
    pg.fill('#w-name', 'Prueba'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    check('Prueba' in pg.inner_text('#modal'), 'tras el nombre aparece el menú con el saludo')
    check(pg.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'el menú no desborda horizontalmente')
    # partida rápida real: pulsar «Partida rápida» y «Empezar»
    pg.get_by_text('Partida rápida').first.click(); pg.wait_for_timeout(300)
    pg.get_by_role('button', name='Empezar').click(); pg.wait_for_timeout(1200)
    check(pg.locator('#board svg').count() >= 1, 'el tablero se dibuja')
    check(pg.evaluate("document.querySelectorAll('#board svg polygon').length") > 10, 'el tablero tiene hexágonos')
    check(pg.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'la partida no desborda horizontalmente')
    mb = pg.locator('#mbar')
    check(mb.is_visible(), 'la barra inferior (recursos y botones) está visible')
    bb = mb.bounding_box(); vh = pg.evaluate('innerHeight')
    check(bb and abs((bb['y'] + bb['height']) - vh) < 3, 'la barra queda pegada al borde inferior')
    small = pg.evaluate("[...document.querySelectorAll('#mbar button')].filter(b=>b.offsetParent&&(b.getBoundingClientRect().height<40||b.getBoundingClientRect().width<44)).length")
    check(small == 0, 'los botones de la barra miden al menos 40×44 px (aptos para el dedo)')
    check(pg.locator('#mbar .mr').count() == 5, 'se ven los 5 recursos en la barra')
    # toque real sobre un pueblo resaltado
    n0 = pg.evaluate('V.filter(v=>v.b).length')
    pg.evaluate('onBoard("v",legalSettle(0,true)[0])'); pg.wait_for_timeout(300)
    check(pg.evaluate('V.filter(v=>v.b).length') == n0 + 1, 'colocar el primer pueblo funciona')
    # personalizar y tema
    pg.evaluate('showPersonalize()'); pg.wait_for_timeout(200)
    pg.get_by_role('button', name='Nevado').click(); pg.wait_for_timeout(200)
    check(pg.evaluate("document.body.classList.contains('th-snow')"), 'el tema Nevado se aplica')
    pg.evaluate('closeModal()')
    # horizontal
    pg.set_viewport_size({'width': d['viewport']['height'], 'height': d['viewport']['width']}); pg.wait_for_timeout(300)
    check(pg.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'en horizontal tampoco hay desborde')
    # mapa grande de 6 jugadores
    pg.set_viewport_size(d['viewport'])
    pg.evaluate("closeModal();launch({name:'P',bots:5,speed:0.45,spectate:false,rules:{pts:true,target:10}},{tutorial:false})"); pg.wait_for_timeout(1200)
    check(pg.evaluate('H.length') == 37 and pg.evaluate('G.players.length') == 6, 'una partida de 6 jugadores usa el mapa grande de 37 hexágonos')
    check(pg.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'el mapa grande no desborda')
    # cifrado disponible en el navegador
    ok = pg.evaluate("""(async()=>{try{const a=await CX.ident(),h=await CX.gen(),k=await CX.key(a.priv,await CX.pub(h.publicKey));const e=await CX.enc(k,{x:1});return (await CX.dec(k,e.iv,e.c)).x===1}catch(e){return false}})()""")
    check(ok, 'el cifrado (WebCrypto) funciona en este navegador')
    real = [e for e in errs if 'supabase' not in e.lower()]
    check(not real, 'sin errores de JavaScript' + (': ' + '; '.join(real[:2]) if real else ''))
    b.close()

with sync_playwright() as p:
    for dev in DEVICES: run(p, dev)
print('\nFALLAS', len(fails))
sys.exit(1 if fails else 0)
