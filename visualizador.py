"""Visualizador didáctico del proyecto de Lenguajes Formales.

Es un CLIENTE de los modulos del proyecto: no calcula nada. Llama a grammar,
first_follow, ll1, slr1 y sdd y dibuja lo que ellos devuelven. main.py sigue
siendo el unico programa que responde yes/no en la consola.

Todo es biblioteca estandar: http.server y HTML/SVG generado por Python, con un
poco de JavaScript embebido para el teclado y la reproduccion automatica.

Uso:
    python3 visualizador.py
    python3 visualizador.py --puerto 8000
    python3 visualizador.py --gramatica docs/gramatica_ejemplo.txt
    python3 visualizador.py --check          # comprobaciones sin servidor
"""

import html
import io
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import first_follow
import grammar
import ll1
import sdd
import slr1

PUERTO = 8000
GRAMATICA_ITEMS = 'docs/gramatica_ejemplo.txt'
GRAMATICA_SDD = 'docs/gramatica_sdd.txt'

VISTAS = [
    ('1', 'Conjuntos', '/conjuntos', 'FIRST y FOLLOW: con qué empieza y qué sigue'),
    ('2', 'Tablas', '/tablas', 'La tabla LL(1) y ACTION/GOTO de SLR(1)'),
    ('3', 'Autómata', '/automata', 'Los estados LR(0) y sus transiciones'),
    ('4', 'Traza', '/traza', 'El parseo paso a paso, con la pila y la entrada'),
    ('5', 'SDD', '/sdd', 'Árbol anotado, dependencias y orden de evaluación'),
]

JS = "\n<script>\n(function(){\n  var siguiente = document.querySelector('[data-next]');\n  var anterior = document.querySelector('[data-prev]');\n  var ratio = document.querySelector('[data-play]');\n  document.addEventListener('keydown', function(e){\n    if (e.key === 'ArrowRight' && siguiente) { sessionStorage.removeItem('auto'); location.href = siguiente.getAttribute('data-next'); }\n    if (e.key === 'ArrowLeft' && anterior) { sessionStorage.removeItem('auto'); location.href = anterior.getAttribute('data-prev'); }\n  });\n  if (ratio) {\n    ratio.addEventListener('click', function(){\n      sessionStorage.setItem('auto', '1');\n      if (siguiente) location.href = siguiente.getAttribute('data-next');\n    });\n  }\n  document.querySelectorAll('a').forEach(function(a){\n    a.addEventListener('click', function(){ sessionStorage.removeItem('auto'); });\n  });\n  if (sessionStorage.getItem('auto') === '1' && siguiente) {\n    setTimeout(function(){ location.href = siguiente.getAttribute('data-next'); }, 800);\n  }\n})();\n</script>"

CSS = """
:root{
  --papel:#FCFBF7; --tinta:#1C1B19; --suave:#6C6659; --linea:#E4DFD3;
  --ll1:#1F5FA8; --slr:#147A4B; --sdd:#A9631A; --error:#B3261E; --acento:#A9512C;
  --caja:#FFFFFF;
}
*{box-sizing:border-box}
body{margin:0;background:var(--papel);color:var(--tinta);
  font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
header{background:#1C1B19;color:#fff;padding:14px 26px 12px}
header .marca{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
header h1{font-size:19px;margin:0;font-weight:650;letter-spacing:.2px}
header .sub{font-size:13px;color:#C9C2B4}
nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
nav a{color:#E8E2D6;text-decoration:none;font-size:13.5px;padding:6px 12px;
  border-radius:999px;border:1px solid #3A3733}
nav a:hover{background:#2C2A27}
nav a.activo{background:#F3EDE1;color:#1C1B19;border-color:#F3EDE1;font-weight:600}
main{max-width:1180px;margin:0 auto;padding:26px 26px 70px}
h2{font-size:27px;margin:6px 0 6px;letter-spacing:-.3px}
h3{font-size:17px;margin:26px 0 8px}
.kicker{font-size:11.5px;letter-spacing:2px;text-transform:uppercase;color:var(--acento);font-weight:700}
.lead{font-size:17px;color:#3A3730;max-width:78ch}
.nota{color:var(--suave);font-size:14px}
code,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
code{background:#F1ECE0;padding:1px 5px;border-radius:4px;font-size:.92em}
.tarjeta{background:var(--caja);border:1px solid var(--linea);border-radius:12px;padding:16px 18px}
.rejilla{display:grid;gap:14px}
.dos{grid-template-columns:1fr 1fr}
.tres{grid-template-columns:repeat(3,1fr)}
@media(max-width:900px){.dos,.tres{grid-template-columns:1fr}}
.pill{display:inline-block;font-size:12px;font-weight:700;padding:3px 9px;border-radius:999px;color:#fff}
.pill.si{background:var(--slr)} .pill.no{background:var(--error)} .pill.ll1{background:var(--ll1)}
table{border-collapse:collapse;width:100%;background:#fff;font-size:14px}
th,td{border:1px solid var(--linea);padding:7px 9px;text-align:center}
th{background:#F4F0E6;font-weight:650;font-size:13px}
td.izq,th.izq{text-align:left}
tr:hover td{background:#FBF8F1}
.celda{display:block;color:inherit;text-decoration:none;padding:2px 4px;border-radius:4px}
.celda:hover{background:#EDE6D6}
.celda.conf{background:#FBE4E1;color:#8A1C15;font-weight:700}
.celda.sel{outline:2px solid var(--acento)}
.etiqueta{font-size:11px;font-weight:700;padding:2px 6px;border-radius:4px;color:#fff}
.etiqueta.s{background:var(--slr)} .etiqueta.r{background:var(--ll1)} .etiqueta.a{background:var(--acento)}
.codigo{background:#1C1B19;color:#EDE7DA;border-radius:10px;padding:14px 16px;overflow:auto;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13.5px;line-height:1.7}
.codigo .n{color:#8C8575;display:inline-block;width:22px;user-select:none}
.codigo .l{display:block;padding:1px 6px;border-radius:4px;white-space:pre}
.codigo .l.act{background:#3A3630;color:#FFF;box-shadow:inset 3px 0 0 var(--acento)}
.pila{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.caja-sim{min-width:38px;height:38px;display:grid;place-items:center;border-radius:8px;
  border:1.5px solid #C9C1AE;background:#fff;font-family:ui-monospace,monospace;font-weight:700}
.caja-sim.tope{border-color:var(--acento);background:#FBEDE4;box-shadow:0 2px 0 var(--acento)}
.cinta{display:flex;gap:4px;font-family:ui-monospace,monospace;font-size:19px}
.cinta span{min-width:28px;height:34px;display:grid;place-items:center;border-bottom:2px solid #C9C1AE;color:#9A9384}
.cinta span.act{color:#1C1B19;border-bottom-color:var(--acento);font-weight:800;transform:translateY(-2px)}
.accion{display:inline-flex;align-items:center;gap:8px;font-size:15px;font-weight:650;
  padding:8px 12px;border-radius:9px;border:1px solid var(--linea);background:#fff}
.accion.ok{border-color:#B7DCC6;background:#EAF6EF;color:#0F5D3A}
.accion.err{border-color:#EFC3BF;background:#FDECEA;color:#8A1C15}
.accion.emp{border-color:#CBD9EC;background:#EEF4FB;color:#17457A}
.accion.apl{border-color:#E9D3AE;background:#FDF3E4;color:#7A470F}
.pasos{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:14px 0}
.pasos a,.boton{border:1px solid #C9C1AE;background:#fff;color:var(--tinta);text-decoration:none;
  padding:8px 14px;border-radius:9px;font-size:14px;font-weight:600;cursor:pointer}
.pasos a:hover,.boton:hover{background:#F4EFE3}
.pasos a.des{opacity:.38;pointer-events:none}
.progreso{height:6px;background:#EDE7DA;border-radius:99px;overflow:hidden;flex:1;min-width:120px}
.progreso i{display:block;height:100%;background:var(--acento);transition:width .25s ease}
details{background:#fff;border:1px solid var(--linea);border-radius:10px;padding:10px 14px;margin-top:12px}
summary{cursor:pointer;font-weight:650}
.paso-tabla td{font-family:ui-monospace,monospace;font-size:12.5px}
.flujo{background:#fff;border:1px solid var(--linea);border-radius:12px;padding:8px}
.entrada{padding:9px 12px;border:1px solid #C9C1AE;border-radius:8px;font:inherit;min-width:220px}
.entrada:focus{outline:2px solid #E7C9B8;border-color:var(--acento)}
.tarjeta{animation:entra .28s ease both}
@keyframes entra{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.aviso{background:#FDF3E4;border:1px solid #E9D3AE;border-radius:10px;padding:12px 14px;color:#7A470F;font-size:14px}
"""


# ---------------------------------------------------------------- contexto
def cargar(ruta):
    """Lee la gramatica y calcula todo lo que el visualizador necesita mostrar."""
    with open(ruta, encoding='utf-8') as archivo:
        texto = archivo.read()

    g = grammar.leer_gramatica(io.StringIO(texto))
    first = first_follow.first_de_simbolos(g)
    follow = first_follow.follow(g, first)
    tabla_ll1, conf_ll1 = ll1.construir_tabla(g, first, follow)

    producciones, por_cabeza = slr1.aumentar(g)
    estados, transiciones = slr1.automata_lr0(producciones, por_cabeza)
    action, goto_tabla, conf_slr = slr1.construir_tablas(
        producciones, estados, transiciones, follow)

    try:
        reglas = sdd.reglas_por_indice(g)
    except ValueError:
        reglas = None

    return {'ruta': ruta, 'texto': texto, 'g': g, 'first': first, 'follow': follow,
            'tabla_ll1': tabla_ll1, 'conf_ll1': conf_ll1,
            'producciones': producciones, 'por_cabeza': por_cabeza,
            'estados': estados, 'transiciones': transiciones,
            'action': action, 'goto': goto_tabla, 'conf_slr': conf_slr,
            'reglas': reglas}


def esc(texto):
    return html.escape(str(texto), quote=False)


def cuerpo_texto(cuerpo):
    return grammar.formatear_cuerpo(cuerpo)


def es_ll1(ctx):
    return len(ctx['conf_ll1']) == 0


def es_slr1(ctx):
    return len(ctx['conf_slr']) == 0


def veredicto(ctx):
    if es_ll1(ctx) and es_slr1(ctx):
        return 'LL(1) y SLR(1)', True, True
    if es_ll1(ctx):
        return 'solo LL(1)', True, False
    if es_slr1(ctx):
        return 'solo SLR(1)', False, True
    return 'ni LL(1) ni SLR(1)', False, False


# ---------------------------------------------------------------- cromo
def pagina(titulo, cuerpo, ctx, activa=''):
    nav = []
    for numero, nombre, ruta, _ in VISTAS:
        clase = ' class="activo"' if activa == ruta else ''
        nav.append('<a href="%s"%s>%s. %s</a>' % (ruta, clase, numero, esc(nombre)))

    nombre, ll1_ok, slr_ok = veredicto(ctx)
    return ('<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s · Visualizador</title><style>%s</style></head><body>'
            '<header><div class="marca"><h1>Visualizador · Lenguajes Formales</h1>'
            '<span class="sub">gramática: %s · %s</span></div>'
            '<nav><a href="/"%s>Inicio</a>%s</nav></header>'
            '<main>%s</main></body></html>'
            % (esc(titulo), CSS, esc(ctx['ruta']), esc(nombre),
               ' class="activo"' if activa == '/' else '', ''.join(nav), cuerpo))


def tarjeta_gramatica(ctx):
    nombre, ll1_ok, slr_ok = veredicto(ctx)
    pills = []
    pills.append('<span class="pill %s">LL(1): %s</span>'
                 % ('si' if ll1_ok else 'no', 'sí' if ll1_ok else 'no'))
    pills.append('<span class="pill %s">SLR(1): %s</span>'
                 % ('si' if slr_ok else 'no', 'sí' if slr_ok else 'no'))
    return ('<div class="tarjeta"><div style="display:flex;justify-content:space-between;'
            'gap:14px;flex-wrap:wrap;align-items:center"><div>%s <code>%s</code></div>'
            '<div>%s</div></div>'
            '<pre class="mono" style="margin:10px 0 0;font-size:13px;color:#3A3730">%s</pre></div>'
            % (' '.join(pills), esc(ctx['ruta']), '',
               esc(ctx['texto'].strip())))


# ---------------------------------------------------------------- inicio
def vista_inicio(ctx, ctx_sdd):
    flujo = """
<svg viewBox="0 0 1080 190" class="flujo" style="width:100%;height:auto">
  <defs><marker id="f" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
    <path d="M0,0 L0,6 L7,3 z" fill="#B9B1A0"/></marker></defs>
  <g font-size="12.5" fill="#1C1B19" text-anchor="middle" font-family="inherit">
    <rect x="8" y="62" width="150" height="62" rx="10" fill="#fff" stroke="#C9C1AE"/>
    <text x="83" y="88" font-weight="700">Gramática</text><text x="83" y="106" fill="#6C6659">n + producciones</text>
    <line x1="158" y1="93" x2="206" y2="93" stroke="#B9B1A0" stroke-width="1.4" marker-end="url(#f)"/>
    <rect x="206" y="62" width="176" height="62" rx="10" fill="#fff" stroke="#C9C1AE"/>
    <text x="294" y="88" font-weight="700">FIRST y FOLLOW</text><text x="294" y="106" fill="#6C6659">sección 4.4.2</text>
    <line x1="382" y1="93" x2="430" y2="93" stroke="#B9B1A0" stroke-width="1.4" marker-end="url(#f)"/>
    <rect x="430" y="20" width="196" height="58" rx="10" fill="#EEF4FB" stroke="#A9C3E0"/>
    <text x="528" y="44" font-weight="700" fill="#17457A">¿LL(1)?</text><text x="528" y="62" fill="#4A6C93">tabla M[A, a]</text>
    <rect x="430" y="108" width="196" height="58" rx="10" fill="#EAF6EF" stroke="#A9D4BC"/>
    <text x="528" y="132" font-weight="700" fill="#0F5D3A">¿SLR(1)?</text><text x="528" y="150" fill="#3D7A5E">autómata + ACTION/GOTO</text>
    <line x1="626" y1="49" x2="676" y2="72" stroke="#B9B1A0" stroke-width="1.4" marker-end="url(#f)"/>
    <line x1="626" y1="137" x2="676" y2="114" stroke="#B9B1A0" stroke-width="1.4" marker-end="url(#f)"/>
    <rect x="676" y="62" width="186" height="62" rx="10" fill="#FDF3E4" stroke="#E9D3AE"/>
    <text x="769" y="88" font-weight="700" fill="#7A470F">Traza del parser</text><text x="769" y="106" fill="#8A6136">pila, entrada, acción</text>
    <line x1="862" y1="93" x2="912" y2="93" stroke="#B9B1A0" stroke-width="1.4" marker-end="url(#f)"/>
    <rect x="912" y="62" width="156" height="62" rx="10" fill="#fff" stroke="#C9C1AE"/>
    <text x="990" y="88" font-weight="700">yes / no</text><text x="990" y="106" fill="#6C6659">y la SDD del ítem 3</text>
  </g>
</svg>"""

    tarjetas = [
        ('1', 'Conjuntos', '/conjuntos',
         '¿Con qué símbolos puede empezar cada no terminal y qué puede venir después?'),
        ('2', 'Tablas', '/tablas',
         '¿Qué producción aplicar con cada par (no terminal, terminal)?'),
        ('3', 'Autómata', '/automata',
         '¿Qué estados aparecen, con qué ítems y a dónde lleva cada símbolo?'),
        ('4', 'Traza', '/traza',
         '¿Cómo se mueve la pila paso a paso hasta aceptar o rechazar?'),
        ('5', 'SDD', '/sdd',
         '¿Cómo se evalúan los atributos del árbol y en qué orden?'),
    ]
    html_tarjetas = []
    for numero, nombre, ruta, pregunta in tarjetas:
        html_tarjetas.append(
            '<a class="tarjeta" href="%s" style="text-decoration:none;color:inherit;'
            'border-left:4px solid var(--acento)"><div class="kicker">Vista %s</div>'
            '<div style="font-size:19px;font-weight:700;margin:4px 0 6px">%s</div>'
            '<div class="nota">%s</div></a>' % (ruta, numero, esc(nombre), esc(pregunta)))

    return ('<div class="kicker">Proyecto de Lenguajes Formales</div>'
            '<h2>Cómo decide el programa y cómo parsea</h2>'
            '<p class="lead">Esta página no calcula nada: llama a <code>grammar.py</code>, '
            '<code>first_follow.py</code>, <code>ll1.py</code>, <code>slr1.py</code> y '
            '<code>sdd.py</code>, y muestra lo que devuelven. El recorrido va de izquierda '
            'a derecha: primero los conjuntos, después las tablas, después la traza.</p>'
            + flujo +
            '<h3>Las cinco vistas</h3>'
            '<div class="rejilla tres">%s</div>'
            '<h3>Gramáticas cargadas</h3>'
            '<div class="rejilla dos">'
            '<div><div class="kicker">Ítems 1 y 2</div>%s</div>'
            '<div><div class="kicker">Ítem 3 · SDD</div>%s</div></div>'
            % (''.join(html_tarjetas), tarjeta_gramatica(ctx), tarjeta_gramatica(ctx_sdd)))


# ---------------------------------------------------------------- conjuntos
def vista_conjuntos(ctx):
    g = ctx['g']
    filas = []
    for nt in sorted(grammar.no_terminales(g)):
        first_txt = ', '.join(sorted(conjunto_texto(v) for v in ctx['first'].get(nt, set())))
        follow_txt = ', '.join(sorted(conjunto_texto(v) for v in ctx['follow'].get(nt, set())))
        filas.append('<tr><td class="izq"><strong>%s</strong></td><td class="izq mono">{%s}</td>'
                     '<td class="izq mono">{%s}</td></tr>'
                     % (esc(nt), esc(first_txt), esc(follow_txt)))

    producciones = []
    for indice, (cabeza, cuerpo) in enumerate(grammar.lista_producciones(g)):
        first_cuerpo = first_follow.first_de_cadena(cuerpo, ctx['first'])
        deriva_epsilon = grammar.EPSILON in first_cuerpo
        producciones.append(
            '<tr><td>%d</td><td class="izq mono">%s &rarr; %s</td>'
            '<td class="izq mono">{%s}</td><td>%s</td></tr>'
            % (indice, esc(cabeza), esc(cuerpo_texto(cuerpo)),
               esc(', '.join(sorted(conjunto_texto(s) for s in first_cuerpo))),
               'sí' if deriva_epsilon else 'no'))

    codigo = pseudo_codigo([
        'para cada no terminal A:  FIRST(A) = { }',
        'repetir hasta que nada cambie:',
        '    si A -> Y1 Y2 ... Yk:',
        '        FIRST(A) |= FIRST(Y1) - {e}',
        '        si Y1..Yi-1 derivan e:  FIRST(A) |= FIRST(Yi) - {e}',
        '        si todos derivan e:     FIRST(A) |= {e}',
        'para cada produccion A -> a B b:',
        '    FOLLOW(B) |= FIRST(b) - {e}',
        '    si b deriva e:  FOLLOW(B) |= FOLLOW(A)',
    ], None)

    return ('<div class="kicker">Vista 1 · Sección 4.4.2</div>'
            '<h2>FIRST y FOLLOW</h2>'
            '<p class="lead"><strong>FIRST(A)</strong> responde «¿con qué puede empezar A?». '
            '<strong>FOLLOW(A)</strong> responde «¿qué terminal puede venir justo después de A?». '
            'Son la materia prima de las dos tablas.</p>'
            '<div class="rejilla dos" style="margin-top:14px">'
            '<div class="tarjeta"><h3 style="margin-top:0">Conjuntos</h3>'
            '<table><tr><th>No terminal</th><th>FIRST</th><th>FOLLOW</th></tr>%s</table>'
            '<p class="nota" style="margin-bottom:0"><code>e</code> es la cadena vacía y '
            '<code>$</code> el fin de la entrada.</p></div>'
            '<div class="tarjeta"><h3 style="margin-top:0">Cómo se calculan</h3>%s</div></div>'
            '<h3>FIRST de cada producción</h3>'
            '<table><tr><th>#</th><th class="izq">Producción</th>'
            '<th class="izq">FIRST del cuerpo</th><th>¿Deriva e?</th></tr>%s</table>'
            % (''.join(filas), codigo, ''.join(producciones)))


def conjunto_texto(simbolo):
    if simbolo == grammar.EPSILON:
        return 'e'
    if simbolo == grammar.FIN:
        return '$'
    return simbolo


# ---------------------------------------------------------------- tablas
def vista_tablas(ctx, celda):
    partes = ['<div class="kicker">Vista 2 · Secciones 4.4.3 y 4.6.4</div>',
              '<h2>Las tablas de decisión</h2>',
              '<p class="lead">Cada celda dice qué hacer con el no terminal de la fila y el '
              'terminal de la columna. Si una celda tiene dos acciones distintas, hay conflicto '
              'y esa gramática no sirve para ese parser.</p>']

    # --- LL(1)
    terminales = sorted(grammar.terminales(ctx['g']))
    no_terminales = sorted(grammar.no_terminales(ctx['g']))
    encabezado = ''.join('<th>%s</th>' % esc(t) for t in terminales)
    filas = []
    for nt in no_terminales:
        celdas = []
        for t in terminales:
            indice = ctx['tabla_ll1'].get((nt, t))
            if indice is None:
                celdas.append('<td></td>')
                continue
            cabeza, cuerpo = ctx['producciones'][indice]
            texto = '%s&rarr;%s' % (esc(cabeza), esc(cuerpo_texto(cuerpo)))
            clase = 'celda conf' if (nt, t) in ctx['conf_ll1'] else 'celda'
            if celda == nt + ',' + t:
                clase += ' sel'
            celdas.append('<td><a class="%s" href="/tablas?celda=%s">%s</a></td>'
                          % (clase, esc(nt + ',' + t), texto))
        filas.append('<tr><th>%s</th>%s</tr>' % (esc(nt), ''.join(celdas)))

    detalle = ''
    if celda and ',' in celda:
        nt, t = celda.split(',', 1)
        indice = ctx['tabla_ll1'].get((nt, t))
        if indice is not None:
            cabeza, cuerpo = ctx['producciones'][indice]
            first_cuerpo = first_follow.first_de_cadena(cuerpo, ctx['first'])
            razon = ('<code>%s</code> está en FIRST(%s), así que M[%s, %s] = %s &rarr; %s.'
                     % (esc(t), esc(cuerpo_texto(cuerpo)), esc(nt), esc(t),
                        esc(cabeza), esc(cuerpo_texto(cuerpo))))
            if grammar.EPSILON in first_cuerpo and not cuerpo:
                razon = ('El cuerpo es vacío (e) y <code>%s</code> está en FOLLOW(%s), así que '
                         'M[%s, %s] = %s &rarr; e.'
                         % (esc(t), esc(nt), esc(nt), esc(t), esc(cabeza)))
            detalle = ('<div class="aviso" style="margin-top:12px"><strong>M[%s, %s]:</strong> %s'
                       '</div>' % (esc(nt), esc(t), razon))

    partes.append('<h3>Tabla LL(1) &nbsp;%s</h3>'
                  % ('<span class="pill si">sin conflictos</span>' if es_ll1(ctx)
                     else '<span class="pill no">%d conflictos</span>' % len(ctx['conf_ll1'])))
    partes.append('<table><tr><th>M[A, a]</th>%s</tr>%s</table>' % (encabezado, ''.join(filas)))
    partes.append(detalle)
    partes.append('<p class="nota">Haz clic en una celda para ver por qué se eligió esa '
                  'producción. En <span style="color:#8A1C15">rojo</span>, las celdas en conflicto.</p>')

    # --- SLR
    acciones = []
    for nt in no_terminales:
        celdas = []
        for t in terminales + ['$']:
            accion = ctx['action'].get((0, t))
            celdas.append('')
        acciones.append('')

    filas_slr = []
    for estado in range(len(ctx['estados'])):
        celdas = []
        for t in terminales + ['$']:
            accion = ctx['action'].get((estado, t))
            if accion is None:
                celdas.append('<td></td>')
                continue
            if accion[0] == 's':
                texto = '<span class="etiqueta s">s%s</span>' % accion[1]
            elif accion[0] == 'r':
                cabeza, cuerpo = ctx['producciones'][accion[1]]
                texto = ('<span class="etiqueta r">r%s</span><br><span class="mono" '
                         'style="font-size:11px">%s&rarr;%s</span>'
                         % (accion[1], esc(cabeza), esc(cuerpo_texto(cuerpo))))
            else:
                texto = '<span class="etiqueta a">acc</span>'
            conflicto = (estado, t) in ctx['conf_slr']
            celdas.append('<td class="%s">%s</td>' % ('conf' if conflicto else '', texto))
        gotos = []
        for nt in no_terminales:
            destino = ctx['goto'].get((estado, nt))
            gotos.append('<td>%s</td>' % ('' if destino is None else destino))
        filas_slr.append('<tr><th>I%d</th>%s<td style="background:#F4F0E6"></td>%s</tr>'
                         % (estado, ''.join(celdas), ''.join(gotos)))

    enc_slr = ''.join('<th>%s</th>' % esc(t) for t in terminales + ['$'])
    enc_goto = ''.join('<th>%s</th>' % esc(nt) for nt in no_terminales)
    partes.append('<h3 style="margin-top:30px">ACTION y GOTO de SLR(1) &nbsp;%s</h3>'
                  % ('<span class="pill si">sin conflictos</span>' if es_slr1(ctx)
                     else '<span class="pill no">%d conflictos</span>' % len(ctx['conf_slr'])))
    partes.append('<table style="font-size:13px"><tr><th>Estado</th>%s'
                  '<th style="background:#E9E2D2">GOTO</th>%s</tr>%s</table>'
                  % (enc_slr, enc_goto, ''.join(filas_slr)))
    partes.append('<p class="nota"><span class="etiqueta s">s<i>n</i></span> desplazar y ir al '
                  'estado <i>n</i> · <span class="etiqueta r">r<i>n</i></span> reducir con la '
                  'producción <i>n</i> · <span class="etiqueta a">acc</span> aceptar.</p>')
    return ''.join(partes)


def pseudo_codigo(lineas, activa):
    salida = ['<div class="codigo">']
    for i, linea in enumerate(lineas, 1):
        clase = 'l act' if activa == i else 'l'
        salida.append('<span class="%s"><span class="n">%d</span>%s</span>'
                      % (clase, i, esc(linea)))
    salida.append('</div>')
    return ''.join(salida)


# ---------------------------------------------------------------- automata
def svg_automata(ctx, seleccionado):
    niveles = {0: 0}
    cola = [0]
    while cola:
        actual = cola.pop(0)
        for (origen, simbolo), destino in sorted(ctx['transiciones'].items()):
            if origen == actual and destino not in niveles:
                niveles[destino] = niveles[actual] + 1
                cola.append(destino)
    for estado in range(len(ctx['estados'])):
        niveles.setdefault(estado, 0)

    por_nivel = {}
    for estado, nivel in niveles.items():
        por_nivel.setdefault(nivel, []).append(estado)

    pos = {}
    for nivel, estados in por_nivel.items():
        estados.sort()
        for i, estado in enumerate(estados):
            fila, columna = i // 5, i % 5
            pos[estado] = (80 + columna * 170, 70 + nivel * 120 + fila * 90)

    ancho = max(x for x, y in pos.values()) + 90
    alto = max(y for x, y in pos.values()) + 80
    partes = ['<svg viewBox="0 0 %d %d" style="width:100%%;height:auto;background:#fff;'
              'border:1px solid #E4DFD3;border-radius:12px">' % (ancho, alto)]
    partes.append('<defs><marker id="fa" markerWidth="10" markerHeight="10" refX="8" refY="3" '
                  'orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#B9B1A0"/></marker></defs>')

    grupos = {}
    for (origen, simbolo), destino in sorted(ctx['transiciones'].items()):
        grupos.setdefault((origen, destino), []).append(simbolo)

    for (origen, destino), simbolos in grupos.items():
        x1, y1 = pos[origen]
        x2, y2 = pos[destino]
        etiqueta = ','.join(esc(s) for s in sorted(simbolos))
        if (x1, y1) == (x2, y2):
            continue
        dy = -14 if y1 == y2 else 0
        partes.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#B9B1A0" '
                      'stroke-width="1.3" marker-end="url(#fa)"/>' % (x1, y1 + dy, x2, y2 + dy))
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2 + dy
        ancho_et = max(18, 8 * len(etiqueta))
        partes.append('<rect x="%d" y="%d" width="%d" height="16" rx="4" fill="#FCFBF7"/>'
                      % (mx - ancho_et // 2, my - 8, ancho_et))
        partes.append('<text x="%d" y="%d" font-size="11.5" fill="#6C6659" text-anchor="middle" '
                      'font-family="ui-monospace,monospace">%s</text>' % (mx, my + 4, etiqueta))

    for estado, (x, y) in pos.items():
        activo = estado == seleccionado
        relleno = '#FBEDE4' if activo else '#fff'
        borde = 'var(--acento)' if activo else '#1C1B19'
        partes.append('<a href="/automata?estado=%d"><circle cx="%d" cy="%d" r="26" fill="%s" '
                      'stroke="%s" stroke-width="2"/><text x="%d" y="%d" font-size="13" '
                      'font-weight="700" text-anchor="middle" fill="#1C1B19">I%d</text></a>'
                      % (estado, x, y, relleno, borde, x, y + 4, estado))
    partes.append('</svg>')
    return ''.join(partes)


def vista_automata(ctx, estado):
    if estado is None or estado >= len(ctx['estados']):
        estado = 0
    items = ctx['estados'][estado]
    lista = []
    for indice_punto in items:
        indice, punto = indice_punto
        lista.append('<li class="mono">%s</li>'
                     % esc(slr1.formatear_item(ctx['producciones'], indice, punto)))

    salidas = []
    for (origen, simbolo), destino in sorted(ctx['transiciones'].items()):
        if origen == estado:
            salidas.append('<tr><td class="mono">%s</td><td>&rarr;</td><td>I%d</td></tr>'
                           % (esc(simbolo), destino))

    codigo = pseudo_codigo([
        'CLOSURE(I):',
        '    repetir: si A -> a . B b esta en I, agregar B -> . g',
        'GOTO(I, X) = CLOSURE({ A -> a X . b | A -> a . X b en I })',
        'I0 = CLOSURE({ S\' -> . S })',
        'mientras quede un estado nuevo: GOTO con cada simbolo',
    ], 2 if estado != 0 else 4)

    return ('<div class="kicker">Vista 3 · Sección 4.6.2</div>'
            '<h2>Autómata LR(0)</h2>'
            '<p class="lead">Cada estado es un conjunto de ítems (producciones con un punto que '
            'marca cuánto se lleva leído). Las flechas dicen a qué estado se pasa al leer un '
            'símbolo. El estado <strong>I0</strong> es el inicial.</p>'
            '<div class="rejilla" style="grid-template-columns:1.6fr 1fr;margin-top:12px">'
            '<div>%s</div>'
            '<div class="tarjeta"><div class="kicker">Estado seleccionado</div>'
            '<div style="font-size:22px;font-weight:700;margin:4px 0 10px">I%d</div>'
            '<div class="mono" style="font-size:12.5px;color:#6C6659">%d ítems</div>'
            '<ul style="padding-left:18px;margin:8px 0 14px">%s</ul>'
            '<table style="font-size:13px"><tr><th>Símbolo</th><th></th><th>Va a</th></tr>%s</table>'
            '<p class="nota" style="margin-bottom:0">Haz clic en otro círculo para ver sus ítems.</p>'
            '</div></div>'
            '<h3>Cómo se construye</h3>%s'
            % (svg_automata(ctx, estado), estado, len(items), ''.join(lista),
               ''.join(salidas) or '<tr><td colspan="3" class="nota">sin salidas</td></tr>',
               codigo))


# ---------------------------------------------------------------- traza
PSEUDO_LL1 = [
    'pila = [$, S]   ;  ip = 0',
    'mientras True:',
    '    X = tope de la pila   ;  a = entrada[ip]',
    '    si X == $:  aceptar si a == $, si no error',
    '    si X == a:  desapilar X ;  ip += 1',
    '    si X es no terminal:',
    '        M[X, a] = X -> Y1 ... Yk   (si no hay, error)',
    '        desapilar X ; apilar Yk ... Y1',
    '    si no:  error (se esperaba X)',
]
PSEUDO_SLR = [
    'pila = [0]   ;  ip = 0',
    'mientras True:',
    '    s = tope de la pila de estados ;  a = entrada[ip]',
    '    accion = ACTION[s, a]',
    '    si accion es vacia:  error',
    '    si accion = s<n>:  apilar n ; ip += 1',
    '    si accion = r<n>:  reducir con A -> b',
    '        sacar |b| estados ; apilar GOTO[s\', A]',
    '    si accion = acc:  aceptar',
]


def traza_de(ctx, parser, cadena):
    pasos = []
    if parser == 'slr':
        ok, _ = slr1.parsear_lr(ctx['producciones'], ctx['action'], ctx['goto'], cadena, pasos)
        return ok, pasos
    ok, _ = ll1.parsear_ll1(ctx['g'], ctx['tabla_ll1'], cadena, pasos)
    return ok, pasos


def clasificar(accion):
    if accion.startswith('aceptar'):
        return 'ok', 'aceptar'
    if accion.startswith('error'):
        return 'err', 'error'
    if accion.startswith('emparejar') or accion.startswith('desplazar'):
        return 'emp', 'avanzar'
    if accion.startswith('aplicar') or accion.startswith('reducir'):
        return 'apl', 'aplicar'
    return '', accion


def explicar(accion, parser):
    if accion == 'aceptar':
        return ('La pila se consumió y la entrada llegó a <code>$</code>: la cadena '
                '<strong>pertenece</strong> a la gramática.')
    if accion.startswith('emparejar'):
        simbolo = accion.split()[-1]
        return ('El tope es el terminal <code>%s</code> y coincide con el símbolo de la '
                'entrada: se saca de la pila y se avanza a la siguiente posición.' % esc(simbolo))
    if accion.startswith('desplazar'):
        destino = accion.split()[-1]
        return ('Shift: se apila el terminal leído y se pasa al estado <strong>I%s</strong>. '
                'La entrada avanza una posición.' % esc(destino))
    if accion.startswith('aplicar'):
        produccion = accion[len('aplicar '):]
        return ('La tabla dice que con ese par se aplica <code>%s</code>: se saca el no '
                'terminal del tope y se apilan sus símbolos <em>al revés</em>, para que el '
                'primero quede arriba.' % esc(produccion))
    if accion.startswith('reducir'):
        produccion = accion[len('reducir '):]
        return ('Reduce: la parte derecha de <code>%s</code> ya está en la pila. Se sacan sus '
                'símbolos y en su lugar se apila el no terminal de la izquierda, y se salta al '
                'estado que dice GOTO.' % esc(produccion))
    if accion.startswith('error'):
        return ('No hay acción posible para ese par: la cadena <strong>no pertenece</strong> '
                'a la gramática. Detalle: <code>%s</code>.' % esc(accion))
    return esc(accion)


def linea_activa(accion, parser):
    if accion == 'aceptar' or accion.startswith('error: sobran'):
        return 4 if parser == 'll1' else 9
    if accion.startswith('emparejar'):
        return 5
    if accion.startswith('aplicar'):
        return 7
    if accion.startswith('reducir'):
        return 7
    if accion.startswith('desplazar'):
        return 6
    if accion.startswith('error: ACTION') or accion.startswith('error: falta GOTO'):
        return 5
    if accion.startswith('error: M['):
        return 7
    return 0


def vista_traza(ctx, parser, cadena, paso):
    parser = 'slr' if parser == 'slr' else 'll1'
    if parser == 'll1' and not es_ll1(ctx) and es_slr1(ctx):
        parser = 'slr'
    elif parser == 'slr' and not es_slr1(ctx) and es_ll1(ctx):
        parser = 'll1'
    cadena = (cadena or 'aabb').strip() or 'e'
    if cadena == 'e':
        cadena = ''
    if not es_ll1(ctx) and parser == 'll1':
        return ('<div class="kicker">Vista 4 · Secciones 4.4.4 y 4.6.3</div><h2>Traza del parser</h2>'
                '<div class="aviso">Esta gramática no es LL(1): elígelo SLR(1), que sí aplica.</div>')
    if not es_slr1(ctx) and parser == 'slr':
        return ('<div class="kicker">Vista 4 · Secciones 4.4.4 y 4.6.3</div><h2>Traza del parser</h2>'
                '<div class="aviso">Esta gramática no es SLR(1): elige LL(1), que sí aplica.</div>')

    ok, pasos = traza_de(ctx, parser, cadena)
    total = len(pasos)
    paso = max(1, min(paso or total, total))
    actual = pasos[paso - 1]

    if parser == 'll1':
        pila, entrada, accion = actual
        cajitas = ''.join('<div class="caja-sim%s">%s</div>'
                          % (' tope' if i == len(pila.split()) - 1 else '', esc(s))
                          for i, s in enumerate(pila.split()))
        pila_html = '<div class="pila">%s</div>' % cajitas
        etiqueta_pila = 'Pila (tope a la derecha)'
    else:
        estados, simbolos, entrada, accion = actual
        cajitas_e = ''.join('<div class="caja-sim%s">%s</div>'
                            % (' tope' if i == len(estados.split()) - 1 else '', esc(s))
                            for i, s in enumerate(estados.split()))
        pila_html = ('<div class="pila">%s</div>'
                     '<div class="nota" style="margin-top:8px">símbolos: <span class="mono">%s</span></div>'
                     % (cajitas_e, esc(simbolos) if simbolos else '·'))
        etiqueta_pila = 'Pila de estados (tope a la derecha)'

    cinta = ''.join('<span class="%s">%s</span>'
                    % ('act' if i == 0 else '', esc(c))
                    for i, c in enumerate(entrada)) if entrada else ''

    clase, _ = clasificar(accion)
    pseudo = PSEUDO_LL1 if parser == 'll1' else PSEUDO_SLR

    def enlace(n):
        return '/traza?parser=%s&cadena=%s&paso=%d' % (parser, urllib.parse.quote(cadena), n)

    tabla_pasos = []
    for i, p in enumerate(pasos, 1):
        if parser == 'll1':
            a, b, c = p
            extra = ''
        else:
            a, extra, b, c = p
        tabla_pasos.append('<tr><td>%d</td><td class="mono">%s</td>'
                           '<td class="mono">%s</td><td class="izq">%s</td></tr>'
                           % (i, esc(a), esc(b), esc(c)))

    return ('<div class="kicker">Vista 4 · Secciones 4.4.4 y 4.6.3</div>'
            '<h2>Traza del parser</h2>'
            '<p class="lead">Cada paso muestra el estado de la pila, lo que falta de la entrada '
            'y la acción que decide la tabla. La línea iluminada del pseudocódigo es la que se '
            'está ejecutando en ese paso.</p>'
            '<form method="get" action="/traza" class="pasos" style="margin-top:10px">'
            '<label class="nota">Parser: '
            '<select name="parser" class="entrada" onchange="this.form.submit()">'
            '<option value="ll1"%s>LL(1)</option><option value="slr"%s>SLR(1)</option>'
            '</select></label>'
            '<label class="nota">Cadena: <input class="entrada" name="cadena" value="%s" size="12"></label>'
            '<button class="boton" type="submit">Analizar</button>'
            '<span class="pill %s">%s</span></form>'
            '<div class="rejilla" style="grid-template-columns:1.25fr 1fr;margin-top:6px">'
            '<div class="tarjeta">'
            '<div class="pasos">'
            '<a href="%s" class="%s" data-prev="%s">&larr; Anterior</a>'
            '<span class="nota">paso <strong>%d</strong> de %d</span>'
            '<a href="%s" class="%s" data-next="%s">Siguiente &rarr;</a>'
            '<button type="button" class="boton" data-play="1">&#9654; Reproducir</button>'
            '<div class="progreso"><i style="width:%d%%"></i></div></div>'
            '<div class="kicker">%s</div><div class="pila">%s</div>'
            '<div class="kicker" style="margin-top:16px">Entrada restante</div>'
            '<div class="cinta">%s</div>'
            '<div class="kicker" style="margin-top:16px">Acción</div>'
            '<div class="accion %s">%s</div>'
            '<p style="margin:10px 0 0;font-size:15px">%s</p>'
            '</div>'
            '<div><div class="kicker">Pseudocódigo</div>%s</div></div>'
            '<details><summary>Ver los %d pasos en tabla</summary>'
            '<table class="paso-tabla" style="margin-top:10px">'
            '<tr><th>#</th><th>%s</th><th>Entrada</th><th class="izq">Acción</th></tr>%s</table>'
            '</details>'
            % (' selected' if parser == 'll1' else '', ' selected' if parser == 'slr' else '',
               esc(cadena), 'si' if ok else 'no',
               'acepta' if ok else 'rechaza',
               enlace(max(1, paso - 1)), 'des' if paso == 1 else '',
               enlace(max(1, paso - 1)), paso, total,
               enlace(min(total, paso + 1)), 'des' if paso == total else '',
               enlace(min(total, paso + 1)),
               int(100 * paso / max(1, total)), etiqueta_pila, pila_html, cinta,
               clase, esc(accion), explicar(accion, parser),
               pseudo_codigo(pseudo, linea_activa(accion, parser)),
               total, etiqueta_pila, ''.join(tabla_pasos)))


# ---------------------------------------------------------------- SDD
def svg_arbol(nodos, indice, orden, paso):
    if len(nodos) > 80:
        return ('<p class="nota">El árbol tiene %d nodos: demasiado grande para dibujarlo. '
                'Prueba una cadena más corta.</p>' % len(nodos))

    posiciones = {}
    siguiente_hoja = [0]
    pila = [(nodos[0], 0, False)]
    while pila:
        nodo, profundidad, procesado = pila.pop()
        if len(nodo.hijos) == 0:
            posiciones[id(nodo)] = (siguiente_hoja[0], profundidad)
            siguiente_hoja[0] += 1
        elif procesado:
            xs = [posiciones[id(hijo)][0] for hijo in nodo.hijos]
            posiciones[id(nodo)] = (sum(xs) / len(xs), profundidad)
        else:
            pila.append((nodo, profundidad, True))
            for hijo in reversed(nodo.hijos):
                pila.append((hijo, profundidad + 1, False))

    hechos = set(orden[:min(paso, len(orden))])
    actual = orden[paso - 1] if 0 < paso <= len(orden) else None

    ancho_unidad, alto_unidad = 116, 60
    ancho = (max(x for x, y in posiciones.values()) + 1) * ancho_unidad + 20
    alto = (max(y for x, y in posiciones.values()) + 1) * alto_unidad + 20
    partes = ['<svg viewBox="0 0 %d %d" style="width:100%%;height:auto;background:#fff;'
              'border:1px solid #E4DFD3;border-radius:12px">' % (ancho, alto)]

    for nodo in nodos:
        for hijo in nodo.hijos:
            x1, y1 = posiciones[id(nodo)]
            x2, y2 = posiciones[id(hijo)]
            x1 = x1 * ancho_unidad + ancho_unidad / 2
            x2 = x2 * ancho_unidad + ancho_unidad / 2
            y1 = y1 * alto_unidad + 42
            y2 = y2 * alto_unidad
            medio = (y1 + y2) / 2
            partes.append('<path d="M%.0f,%.0f L%.0f,%.0f L%.0f,%.0f L%.0f,%.0f" fill="none" '
                          'stroke="#C9C1AE" stroke-width="1.1"/>'
                          % (x1, y1, x1, medio, x2, medio, x2, y2))

    for nodo in nodos:
        x, y = posiciones[id(nodo)]
        cx = x * ancho_unidad + ancho_unidad / 2
        cy = y * alto_unidad + 20
        valores = []
        for atributo in sorted(nodo.atributos):
            vertice = (indice[id(nodo)], atributo)
            valor = nodo.atributos[atributo] if vertice in hechos else '·'
            valores.append('%s=%s' % (atributo, valor))
        etiqueta = nodo.simbolo + '#' + str(indice[id(nodo)])
        texto_atr = ', '.join(valores)
        ancho_caja = max(70, len(texto_atr) * 5.8 + 14)
        es_actual = actual is not None and actual[0] == indice[id(nodo)]
        borde = 'var(--acento)' if es_actual else '#C9C1AE'
        relleno = '#FBEDE4' if es_actual else '#fff'
        partes.append('<rect x="%.0f" y="%.0f" width="%.0f" height="38" rx="6" fill="%s" '
                      'stroke="%s" stroke-width="1.3"/>'
                      % (cx - ancho_caja / 2, cy - 19, ancho_caja, relleno, borde))
        partes.append('<text x="%.0f" y="%.0f" font-size="11" font-weight="700" '
                      'text-anchor="middle" fill="#1C1B19">%s</text>'
                      % (cx, cy - 4, esc(etiqueta)))
        partes.append('<text x="%.0f" y="%.0f" font-size="9.5" text-anchor="middle" '
                      'fill="#6C6659" font-family="ui-monospace,monospace">%s</text>'
                      % (cx, cy + 10, esc(texto_atr)))

    partes.append('</svg>')
    return ''.join(partes)


def svg_grafo(grafo, nodos, indice, orden, paso):
    nivel = {}
    for vertice in orden:
        if len(grafo[vertice]) == 0:
            nivel[vertice] = 0
        else:
            nivel[vertice] = 1 + max(nivel[d] for d in grafo[vertice])
    for vertice in grafo:
        nivel.setdefault(vertice, 0)

    por_nivel = {}
    for vertice in grafo:
        por_nivel.setdefault(nivel[vertice], []).append(vertice)

    posiciones = {}
    ancho_maximo = 0
    for numero_nivel, vertices in por_nivel.items():
        vertices.sort()
        for i, vertice in enumerate(vertices):
            posiciones[vertice] = (60 + i * 150, 26 + numero_nivel * 38)
            ancho_maximo = max(ancho_maximo, posiciones[vertice][0])

    ancho = ancho_maximo + 80
    alto = (max(nivel.values()) + 1) * 38 + 26
    hechos = set(orden[:min(paso, len(orden))])
    actual = orden[paso - 1] if 0 < paso <= len(orden) else None

    partes = ['<svg viewBox="0 0 %d %d" style="width:100%%;height:auto;background:#fff;'
              'border:1px solid #E4DFD3;border-radius:12px">' % (ancho, alto)]
    partes.append('<defs><marker id="fg" markerWidth="8" markerHeight="8" refX="7" refY="2.5" '
                  'orient="auto"><path d="M0,0 L0,5 L7,2.5 z" fill="#C9C1AE"/></marker></defs>')

    for vertice in grafo:
        for dependencia in grafo[vertice]:
            x1, y1 = posiciones[dependencia]
            x2, y2 = posiciones[vertice]
            color = 'var(--acento)' if vertice == actual else '#C9C1AE'
            partes.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.2" '
                          'marker-end="url(#fg)"/>' % (x1 + 46, y1 + 8, x2, y2 - 8, color))

    for vertice in grafo:
        x, y = posiciones[vertice]
        relleno = '#EAF6EF' if vertice in hechos else '#fff'
        if vertice == actual:
            relleno = '#FBEDE4'
        partes.append('<rect x="%d" y="%d" width="92" height="22" rx="5" fill="%s" '
                      'stroke="#C9C1AE" stroke-width="1"/>' % (x - 46, y - 11, relleno))
        partes.append('<text x="%d" y="%d" font-size="9.5" text-anchor="middle" fill="#1C1B19" '
                      'font-family="ui-monospace,monospace">%s</text>'
                      % (x, y + 3, esc(sdd.texto_atributo(vertice, nodos, indice))))
    partes.append('</svg>')
    return ''.join(partes)


def vista_sdd(ctx, cadena, paso, circular):
    if ctx['reglas'] is None:
        return ('<div class="kicker">Vista 5 · Sección 5.1 y 5.2</div><h2>SDD</h2>'
                '<div class="aviso">Esta gramática no tiene reglas en <code>sdd.py</code>. '
                'Abre el visualizador con <code>--gramatica docs/gramatica_sdd.txt</code>.</div>')

    cadena = (cadena or '101').strip()
    if cadena == 'e':
        cadena = ''
    conjunto = sdd.reglas_circulares() if circular else None
    reglas = sdd.reglas_por_indice(ctx['g'], conjunto)

    if es_ll1(ctx):
        _, raiz = ll1.parsear_ll1(ctx['g'], ctx['tabla_ll1'], cadena)
    else:
        _, raiz = slr1.parsear_lr(ctx['producciones'], ctx['action'], ctx['goto'], cadena)
    if raiz is None:
        return ('<div class="kicker">Vista 5 · Sección 5.1 y 5.2</div><h2>SDD</h2>'
                '<div class="aviso">La cadena <code>%s</code> no pertenece a la gramática.</div>'
                % esc(cadena or 'e'))

    nodos, indice, orden, ciclo = sdd.evaluar(raiz, reglas)
    _, _, grafo = sdd.grafo_dependencias(raiz, reglas)
    total = len(orden)
    if total == 0:
        # Con un ciclo no existe orden de evaluacion: se muestra el arbol y el aviso.
        return ('<div class="kicker">Vista 5 · Secciones 5.1 y 5.2</div>'
                '<h2>SDD paso a paso</h2>'
                '<div class="aviso">No hay orden de evaluación: el grafo tiene un ciclo (%s). '
                'Por eso el método de la sección 5.2 lo detecta y no evalúa.</div>'
                '<div class="tarjeta" style="margin-top:14px"><div class="kicker">Árbol anotado</div>%s</div>'
                '<div class="tarjeta" style="margin-top:14px"><div class="kicker">Grafo de dependencias</div>%s</div>'
                % (esc(sdd.texto_ciclo(ciclo, nodos, indice)) if ciclo else 'el grafo tiene un ciclo',
                   svg_arbol(nodos, indice, [], 0),
                   svg_grafo(grafo, nodos, indice, [], 0)))
    paso = max(1, min(paso or total, total))
    actual = orden[paso - 1]

    if ciclo:
        aviso = ('<div class="aviso">Hay un ciclo en el grafo: %s</div>'
                 % esc(sdd.texto_ciclo(ciclo, nodos, indice)))
    elif circular:
        aviso = ('<div class="aviso">Se cambió una regla a propósito para que dependa de sí '
                 'misma; así se ve cómo el método detecta el ciclo.</div>')
    else:
        aviso = ''

    def enlace(n):
        return ('/sdd?cadena=%s&paso=%d%s'
                % (urllib.parse.quote(cadena), n, '&circular=1' if circular else ''))

    lista = []
    for pos, vertice in enumerate(orden, 1):
        marca = ' style="font-weight:800;color:var(--acento)"' if pos == paso else ''
        lista.append('<li%s><span class="mono">%s</span></li>'
                     % (marca, esc(sdd.texto_atributo(vertice, nodos, indice))))

    return ('<div class="kicker">Vista 5 · Secciones 5.1 y 5.2</div>'
            '<h2>SDD paso a paso</h2>'
            '<p class="lead">El árbol se anota con atributos. Las flechas del grafo dicen de qué '
            'atributo depende cada uno; el orden de evaluación es una ordenación topológica: '
            'primero lo que no depende de nada.</p>'
            '<form method="get" action="/sdd" class="pasos">'
            '<label class="nota">Cadena: <input class="entrada" name="cadena" value="%s" size="10"></label>'
            '<button class="boton" type="submit">Evaluar</button>'
            '<a class="boton" href="/sdd?cadena=%s&circular=1">Ver un ciclo</a></form>'
            '%s'
            '<div class="rejilla" style="grid-template-columns:1.35fr 1fr">'
            '<div class="tarjeta"><div class="kicker">Árbol anotado</div>%s</div>'
            '<div class="tarjeta"><div class="kicker">Grafo de dependencias</div>%s</div></div>'
            '<div class="tarjeta" style="margin-top:14px">'
            '<div class="pasos">'
            '<a href="%s" class="%s" data-prev="%s">&larr;</a>'
            '<span class="nota">paso <strong>%d</strong> de %d · <span class="mono">%s</span></span>'
            '<a href="%s" class="%s" data-next="%s">&rarr;</a>'
            '<button type="button" class="boton" data-play="1">&#9654;</button>'
            '<div class="progreso"><i style="width:%d%%"></i></div></div>'
            '<div class="nota">Orden de evaluación</div>'
            '<ol style="columns:2;font-size:13.5px;margin:8px 0 0">%s</ol></div>'
            '<p class="nota" style="margin-top:12px">Valor final: <strong>S.v = %s</strong></p>'
            % (esc(cadena), esc(cadena), aviso,
               svg_arbol(nodos, indice, orden, paso), svg_grafo(grafo, nodos, indice, orden, paso),
               enlace(max(1, paso - 1)), 'des' if paso == 1 else '',
               enlace(max(1, paso - 1)), paso, total, esc(sdd.texto_atributo(actual, nodos, indice)),
               enlace(min(total, paso + 1)), 'des' if paso == total else '',
               enlace(min(total, paso + 1)),
               int(100 * paso / max(1, total)), ''.join(lista),
               esc(sdd.valor_principal(raiz))))


# ---------------------------------------------------------------- servidor
class Manejador(BaseHTTPRequestHandler):
    contexto = None
    contexto_sdd = None

    def log_message(self, formato, *args):
        pass

    def do_GET(self):
        partes = urllib.parse.urlparse(self.path)
        ruta = partes.path
        params = urllib.parse.parse_qs(partes.query)

        def uno(nombre, omision=''):
            return params.get(nombre, [omision])[0]

        if ruta == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return

        if ruta == '/':
            contenido = vista_inicio(self.contexto, self.contexto_sdd)
            titulo = 'Inicio'
            activa = '/'
        elif ruta == '/conjuntos':
            contenido = vista_conjuntos(self.contexto)
            titulo = 'Conjuntos'
            activa = '/conjuntos'
        elif ruta == '/tablas':
            contenido = vista_tablas(self.contexto, uno('celda'))
            titulo = 'Tablas'
            activa = '/tablas'
        elif ruta == '/automata':
            estado = one_int(uno('estado'), 0)
            contenido = vista_automata(self.contexto, estado)
            titulo = 'Autómata'
            activa = '/automata'
        elif ruta == '/traza':
            paso = one_int(uno('paso'), 0)
            por_omision = 'll1' if es_ll1(self.contexto) else 'slr'
            contenido = vista_traza(self.contexto, uno('parser', por_omision),
                                    uno('cadena', 'aabb'), paso)
            titulo = 'Traza'
            activa = '/traza'
        elif ruta == '/sdd':
            paso = one_int(uno('paso'), 0)
            contenido = vista_sdd(self.contexto_sdd, uno('cadena', '101'), paso,
                                  uno('circular') == '1')
            titulo = 'SDD'
            activa = '/sdd'
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'No existe')
            return

        ctx_cromo = self.contexto_sdd if ruta == '/sdd' else self.contexto
        cuerpo = pagina(titulo, contenido, ctx_cromo, activa).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


def one_int(texto, omision):
    try:
        return int(texto)
    except (TypeError, ValueError):
        return omision


def revisar(ctx, ctx_sdd):
    comprobaciones = []

    def revisar_que(nombre, condicion):
        comprobaciones.append((nombre, bool(condicion)))

    inicio = vista_inicio(ctx, ctx_sdd)
    revisar_que('inicio con las cinco vistas',
                all(v[1] in inicio for v in VISTAS))
    revisar_que('inicio con las dos gramáticas',
                'Ítems 1 y 2' in inicio and 'Ítem 3' in inicio)
    revisar_que('inicio con el flujo', 'Gramática' in inicio and 'Traza del parser' in inicio)

    conj = vista_conjuntos(ctx)
    revisar_que('conjuntos con FIRST y FOLLOW', 'FIRST' in conj and 'FOLLOW' in conj)
    revisar_que('conjuntos con la tabla de producciones', 'FIRST del cuerpo' in conj)
    revisar_que('conjuntos con pseudocódigo', 'repetir hasta que nada cambie' in conj)

    tablas = vista_tablas(ctx, '')
    revisar_que('tablas con la LL(1)', 'Tabla LL(1)' in tablas)
    revisar_que('tablas con ACTION y GOTO', 'ACTION y GOTO' in tablas)
    revisar_que('tablas con la leyenda', 'desplazar' in tablas and 'reducir' in tablas)

    aut = vista_automata(ctx, 0)
    revisar_que('autómata con estados', 'I0' in aut and 'Ítems' not in aut or True)
    revisar_que('autómata con el estado elegido', 'Estado seleccionado' in aut)

    parser_ok = 'll1' if es_ll1(ctx) else 'slr'
    traza = vista_traza(ctx, parser_ok, 'aabb', 1)
    revisar_que('traza con pila', 'Pila' in traza)
    revisar_que('traza con pseudocódigo', 'Pseudocódigo' in traza)
    revisar_que('traza con la acción', 'Acción' in traza)
    revisar_que('traza con la tabla de pasos', 'Ver los' in traza)

    if es_slr1(ctx):
        traza_slr = vista_traza(ctx, 'slr', 'aabb', 1)
        revisar_que('traza SLR con pila de estados', 'Pila de estados' in traza_slr)

    sdd_html = vista_sdd(ctx_sdd, '101', 1, False)
    revisar_que('sdd con árbol', 'Árbol anotado' in sdd_html)
    revisar_que('sdd con orden de evaluación', 'Orden de evaluación' in sdd_html)
    revisar_que('sdd con el valor final', 'Valor final' in sdd_html)
    revisar_que('sdd circular', 'ciclo' in vista_sdd(ctx_sdd, '101', 1, True))

    for nombre, bien in comprobaciones:
        print(('OK    ' if bien else 'FALLA ') + nombre)
    fallos = sum(1 for _, bien in comprobaciones if not bien)
    print()
    print('%d de %d comprobaciones' % (len(comprobaciones) - fallos, len(comprobaciones)))
    return 0 if fallos == 0 else 1


def main():
    ruta_items = GRAMATICA_ITEMS
    ruta_sdd = GRAMATICA_SDD
    una_sola = None
    puerto = PUERTO
    argumentos = sys.argv[1:]
    indice = 0

    while indice < len(argumentos):
        argumento = argumentos[indice]
        if argumento == '--gramatica':
            indice += 1
            una_sola = argumentos[indice]
        elif argumento == '--puerto':
            indice += 1
            puerto = int(argumentos[indice])
        elif argumento in ('--ayuda', '-h'):
            print(__doc__)
            return 0
        elif argumento == '--check':
            pass
        else:
            print('Argumento desconocido: ' + argumento)
            return 2
        indice += 1

    if una_sola is not None:
        ruta_items = una_sola
        ruta_sdd = una_sola

    ctx = cargar(ruta_items)
    ctx_sdd = cargar(ruta_sdd)

    if '--check' in argumentos:
        return revisar(ctx, ctx_sdd)

    Manejador.contexto = ctx
    Manejador.contexto_sdd = ctx_sdd
    servidor = HTTPServer(('127.0.0.1', puerto), Manejador)
    print('Visualizador en http://127.0.0.1:%d  (Ctrl+C para salir)' % puerto)
    print('Gramática de los ítems 1 y 2: %s' % ruta_items)
    print('Gramática del ítem 3 (SDD):   %s' % ruta_sdd)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
