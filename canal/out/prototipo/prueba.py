import base64, json, subprocess, sys, time, re
from playwright.sync_api import sync_playwright

import os
RAIZ = os.path.dirname(os.path.abspath(__file__))
OUT = RAIZ
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8765', '--bind', '127.0.0.1'], cwd=RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
URL = 'http://127.0.0.1:8765/index.html'
fallos = []
def ok(cond, msg):
    print(('OK   ' if cond else 'FALLO ') + msg)
    if not cond: fallos.append(msg)

def descifra(s):
    return base64.b64decode(s[::-1]).decode('utf-8')

LET = 'ABCDEFGHIJ'
def a_codigo(nivel):
    toks = []
    piezas = [t.split(',') for t in descifra(nivel['s']).split(';') if t]
    piezas.sort(key=lambda t: int(t[0]) * nivel['C'] + int(t[1]))
    for f, c, cl, o in piezas:
        casilla = f"{LET[int(c)]}{int(f) + 1}"
        tipo, _, col = cl.partition(':')
        if tipo in ('espejo', 'divisor'): toks.append(casilla + tipo[0] + ('s' if o == '/' else 'b'))
        elif tipo == 'piedra': toks.append(casilla + 'p')
        else: toks.append(casilla + tipo[0] + col)
    return '.'.join(['EA1', nivel['id']] + toks), piezas

try:
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        ctx = nav.new_context(viewport={'width': 1200, 'height': 900})
        ctx.route(re.compile(r'fonts\.(googleapis|gstatic)\.com'), lambda r: r.abort())
        pag = ctx.new_page()
        errores = []
        pag.on('pageerror', lambda e: errores.append(str(e)))
        pag.on('console', lambda m: errores.append(m.text) if m.type == 'error' and 'fonts' not in m.text and 'ERR_FAILED' not in m.text else None)
        pag.goto(URL); pag.wait_for_function('window.LISTO')
        niveles = pag.evaluate('window.NIVELES')
        ok(len(niveles) == 16, f'16 niveles cargados ({len(niveles)})')

        # 1) la solución de cada nivel, pegada como código: enciende todo, no suma progreso
        for n in niveles:
            cod, _ = a_codigo(n)
            r = pag.evaluate('(c) => { const ok = ESPEJOS_UI.pegaPos(c, true); const st = ESPEJOS_UI.estado(); const r = Espejos.comprobar(Espejos.nivel(NIVELES[st.idx]), ESPEJOS_UI.leeCodigoPos(c).col); return { ok, st, sol: r.ok, vuelta: ESPEJOS_UI.codigoPos(), aviso: document.querySelector("#aviso").textContent, modal: !document.querySelector("#victoria").hidden }; }', cod)
            ok(r['ok'] and r['sol'] and r['st']['ganado'] and r['st']['prestado'] and not r['modal'] and r['vuelta'] == cod, f"{n['id']}: código {cod} → solución encendida, sin felicitar, ida y vuelta igual")
        prog = pag.evaluate('localStorage.getItem("espejos_del_alba_v1")')
        ok(prog in (None, '{}'), f'pegar soluciones no suma progreso ({prog})')

        # 2) códigos malos: mensaje claro y el tablero no cambia
        malos = {'hola': 'no parece', 'EA1.n99.A1es': 'No conozco', 'EA1.n01.B1es': 'muro', 'EA1.n01.A1es': 'fija', 'EA1.n01.A3es': 'fija', 'EA1.n01.A2es.A2eb': 'dos veces',
                 'EA1.n01.A2ds': 'no tiene', 'EA1.n01.A2es.A4es.A5es.B5es': 'solo tiene', 'EA1.n01.F1es': 'no está', 'EA1.n13.A1fRR': 'no vale', 'EA1.n13.A1fAR.B2fR': 'no tiene', 'EA1.n01.A2zz': 'No entiendo'}
        for cod, trozo in malos.items():
            msg = pag.evaluate('(c) => { try { ESPEJOS_UI.leeCodigoPos(c); return "SIN ERROR"; } catch (e) { return e.message; } }', cod)
            ok(trozo in msg, f'código malo {cod!r} → «{msg}»')
        enlace = pag.evaluate('(c) => ESPEJOS_UI.leeCodigoPos(c).i', 'https://x.github.io/espejos-del-alba/#EA1.n05.' + a_codigo(niveles[4])[0].split('.', 2)[2])
        ok(enlace == 4, 'un enlace completo con el código detrás de # también se lee')

        # 3) jugar el nivel 1 con el ratón: colocar, girar, deshacer, R, ganar
        pag.evaluate('localStorage.clear()'); pag.goto(URL + '#n01'); pag.reload(); pag.wait_for_function('window.LISTO')
        n1 = niveles[0]; C = n1['C']
        _, sol = a_codigo(n1)
        def toca(f, c): pag.click(f'.toque[data-k="{int(f) * C + int(c)}"]')
        f0, c0 = sol[0][0], sol[0][1]
        toca(f0, c0)
        ok(pag.evaluate('ESPEJOS_UI.estado().piezas') == 1, 'tocar casilla coloca un espejo')
        pag.keyboard.press('z')
        ok(pag.evaluate('ESPEJOS_UI.estado().piezas') == 0, 'Z deshace la colocación')
        for f, c, cl, o in sol:
            toca(f, c)
            if o == '\\': toca(f, c)   # se coloca «/» y un toque lo gira
        st = pag.evaluate('ESPEJOS_UI.estado()')
        ok(st['ganado'] and not st['prestado'] and pag.is_visible('#victoria'), f'n01 resuelto a mano: sale la tarjeta de victoria ({st})')
        prog = json.loads(pag.evaluate('localStorage.getItem("espejos_del_alba_v1")'))
        ok(prog.get('n01', {}).get('pistas') == 0, f'progreso guardado sin pistas ({prog})')
        pag.click('#cerrar')
        pag.keyboard.press('r')
        ok(pag.evaluate('ESPEJOS_UI.estado().piezas') == 0, 'R reinicia el nivel')
        pag.keyboard.press('z')
        st = pag.evaluate('ESPEJOS_UI.estado()')
        ok(st['piezas'] == len(sol), 'Z deshace el reinicio (vuelven las piezas)')

        # 4) partida a medias: se recupera al recargar; el nivel resuelto se ve encendido sin felicitar
        pag.goto(URL + '#n05'); pag.reload(); pag.wait_for_function('window.LISTO')
        n5 = niveles[4]; C = n5['C']; _, sol5 = a_codigo(n5)
        pag.click(f'.toque[data-k="{int(sol5[0][0]) * C + int(sol5[0][1])}"]')
        pag.reload(); pag.wait_for_function('window.LISTO')
        ok(pag.evaluate('ESPEJOS_UI.estado().piezas') == 1, 'n05 a medias se recupera tras recargar')
        pag.goto(URL + '#n01'); pag.reload(); pag.wait_for_function('window.LISTO')
        st = pag.evaluate('ESPEJOS_UI.estado()')
        ok(st['ganado'] and not pag.is_visible('#victoria') and 'ya lo tienes resuelto' in pag.text_content('#aviso'), 'n01 resuelto: al volver se ve encendido y sin tarjeta')
        ok(pag.text_content('.escalon button.nivel[data-i="0"]') == '✔', 'n01 marcado con ✔ en la lista')

        # 5) pista: cuenta aunque se deshaga
        pag.goto(URL + '#n02'); pag.reload(); pag.wait_for_function('window.LISTO')
        pag.click('#pista'); pag.keyboard.press('z')
        st = pag.evaluate('ESPEJOS_UI.estado()')
        ok(st['usadasPistas'] == 1 and st['pistas'] == 0, f'deshacer quita la pieza de la pista, pero la pista cuenta ({st})')

        # 6) teclas 1-9 y X
        pag.goto(URL + '#n13'); pag.reload(); pag.wait_for_function('window.LISTO')
        pag.keyboard.press('3'); sel3 = pag.get_attribute('.bandeja .pieza.sel', 'data-clase')
        pag.keyboard.press('x'); goma = pag.get_attribute('.bandeja .pieza.sel', 'data-goma')
        ok(sel3 == 'filtro:R' and goma == '1', f'tecla 3 elige la 3.ª pieza ({sel3}) y X activa «Quitar»')
        pag.keyboard.press('x')

        # 7) progreso: exportar y cargar en otro aparato (contexto limpio)
        codprog = pag.evaluate('ESPEJOS_UI.codigoProg()')
        ok(codprog == 'EAP1.n01', f'código de progreso: {codprog}')
        ctx2 = nav.new_context(); ctx2.route(re.compile(r'fonts\.(googleapis|gstatic)\.com'), lambda r: r.abort())
        p2 = ctx2.new_page(); p2.goto(URL); p2.wait_for_function('window.LISTO')
        p2.click('#compartir-boton'); p2.fill('#pega-prog', codprog + '.n07h2.nzz'); p2.click('#cargar-prog')
        ok('2 niveles nuevos' in p2.text_content('#compartir-estado'), 'progreso cargado en otro aparato: ' + p2.text_content('#compartir-estado'))
        prog2 = json.loads(p2.evaluate('localStorage.getItem("espejos_del_alba_v1")'))
        ok(prog2 == {'n01': {'hecho': True, 'pistas': 0}, 'n07': {'hecho': True, 'pistas': 2}}, f'progreso fundido ({prog2})')
        p2.fill('#pega-prog', 'EAP1.n07'); p2.click('#cargar-prog')
        prog2 = json.loads(p2.evaluate('localStorage.getItem("espejos_del_alba_v1")'))
        ok(prog2['n07']['pistas'] == 0, 'al fundir se queda la marca con menos pistas')

        # 8) enlace con tablero
        cod9, _ = a_codigo(niveles[8])
        p2.goto(URL + '#' + cod9); p2.reload(); p2.wait_for_function('window.LISTO')
        st = p2.evaluate('ESPEJOS_UI.estado()')
        ok(st['idx'] == 8 and st['ganado'] and st['prestado'], 'un enlace #EA1… abre su nivel con ese tablero')

        # 9) Ctrl+C / Ctrl+V del portapapeles (Chromatron)
        ctx3 = nav.new_context(permissions=['clipboard-read', 'clipboard-write']); ctx3.route(re.compile(r'fonts\.(googleapis|gstatic)\.com'), lambda r: r.abort())
        p3 = ctx3.new_page(); p3.goto(URL + '#n03'); p3.wait_for_function('window.LISTO')
        n3 = niveles[2]; C = n3['C']; _, s3 = a_codigo(n3)
        p3.click(f'.toque[data-k="{int(s3[0][0]) * C + int(s3[0][1])}"]')
        p3.click('h1')  # foco fuera de botones
        p3.keyboard.press('Control+c')
        copiado = p3.evaluate('navigator.clipboard.readText()')
        ok(copiado == p3.evaluate('ESPEJOS_UI.codigoPos()') and copiado.startswith('EA1.n03.'), f'Ctrl+C copia el código del tablero ({copiado})')
        cod4, _ = a_codigo(niveles[3])
        p3.evaluate('(t) => navigator.clipboard.writeText(t)', cod4)
        p3.keyboard.press('Control+v')
        ok(p3.evaluate('ESPEJOS_UI.estado().idx') == 3, 'Ctrl+V con un código de otro nivel lleva a ese nivel')
        p3.click('#compartir-boton'); p3.click('#copiar-pos')
        ok(p3.evaluate('navigator.clipboard.readText()') == cod4 and 'copiado' in p3.text_content('#compartir-estado'), 'botón «Copiar código» funciona')

        # 10) capturas en móvil
        ctx4 = nav.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        ctx4.route(re.compile(r'fonts\.(googleapis|gstatic)\.com'), lambda r: r.abort())
        p4 = ctx4.new_page(); p4.goto(URL + '#' + a_codigo(niveles[12])[0]); p4.wait_for_function('window.LISTO')
        p4.screenshot(path=OUT + '/movil_tablero.png', full_page=True)
        p4.click('#compartir-boton'); p4.screenshot(path=OUT + '/movil_compartir.png')
        ancho = p4.evaluate('document.documentElement.scrollWidth')
        ok(ancho <= 390, f'sin scroll horizontal en móvil ({ancho}px)')
        ok(not errores, f'sin errores de consola ({errores})')
        nav.close()
finally:
    srv.terminate()
print('\nFALLOS:', len(fallos))
for f in fallos: print(' -', f)
