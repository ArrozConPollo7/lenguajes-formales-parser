"""
Visualizador del proyecto (opcional, Item 3 del enunciado).

Es un CLIENTE de los modulos del proyecto: no calcula nada. Llama a grammar,
first_follow, ll1, slr1 y sdd y dibuja lo que ellos devuelven. Por eso no hay
logica duplicada y `main.py` sigue siendo el unico programa que responde con
"yes"/"no" y con la salida del Item 3 en la consola.

Todo es biblioteca estandar: un http.server y paginas HTML con SVG generado por
Python. No hay JavaScript, ni archivos de imagen, ni dependencias que instalar.

Uso:
    python3 visualizador.py                          # gramatica del Item 3
    python3 visualizador.py --gramatica docs/gramatica_ejemplo.txt
    python3 visualizador.py --puerto 8000 --abrir
    python3 visualizador.py --check                  # prueba sin levantar el servidor
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
CSS = """
body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif; margin: 0;
       background: #f6f7fa; color: #1b1f27; }
header { background: #1f3864; color: #fff; padding: 12px 22px; }
header h1 { font-size: 17px; margin: 0; font-weight: 600; }
header nav a { color: #cdd7ee; text-decoration: none; margin-right: 16px;
               font-size: 13px; }
header nav a:hover, header nav .activo { color: #fff; border-bottom: 2px solid #fff; }
main { padding: 22px; max-width: 840px; }
h2 { font-size: 16px; color: #1f3864; margin: 0 0 4px 0; }
p.nota { color: #55607a; font-size: 13px; margin: 2px 0 14px 0; }
table { border-collapse: collapse; background: #fff; font-size: 13px;
        box-shadow: 0 1px 2px rgba(0,0,0,.08); margin-bottom: 16px; }
th, td { border: 1px solid #dde1ea; padding: 5px 9px; text-align: center; }
th { background: #1f3864; color: #fff; font-weight: 600; }
td.izq, th.izq { text-align: left; }
tr:nth-child(even) td { background: #fbfcfe; }
td.conflicto { background: #ffe1e1 !important; color: #9b1c1c; font-weight: 600; }
td.actual { background: #fff3cd !important; font-weight: 700; }
td.hecho { background: #e6f4ea !important; }
code, .mono { font-family: "SFMono-Regular", Consolas, Menlo, monospace; }
.tarjetas { display: flex; gap: 14px; flex-wrap: wrap; }
.tarjeta { background: #fff; border: 1px solid #dde1ea; border-radius: 8px;
           padding: 14px 16px; width: 255px; box-shadow: 0 1px 2px rgba(0,0,0,.06); }
.tarjeta h3 { margin: 0 0 6px 0; font-size: 14px; color: #1f3864; }
.tarjeta p { margin: 0 0 10px 0; font-size: 12.5px; color: #55607a; }
.tarjeta a.boton { display: inline-block; background: #1f3864; color: #fff;
                   padding: 5px 11px; border-radius: 5px; text-decoration: none;
                   font-size: 12.5px; }
.navegacion { margin: 12px 0 16px 0; }
.navegacion a, .navegacion span { display: inline-block; padding: 5px 11px;
        border: 1px solid #c9d0de; border-radius: 5px; margin-right: 6px;
        text-decoration: none; color: #1f3864; background: #fff; font-size: 13px; }
.navegacion span { color: #8d95a8; border-color: #e3e7ef; }
.navegacion a:hover { background: #eef2fa; }
.estado { display: inline-block; padding: 3px 9px; border-radius: 12px;
          font-size: 12px; font-weight: 600; }
.ok { background: #e6f4ea; color: #1e6b3a; }
.no { background: #ffe1e1; color: #9b1c1c; }
form { margin: 0 0 14px 0; font-size: 13px; }
input[type=text] { padding: 5px 8px; border: 1px solid #c9d0de; border-radius: 5px;
                   font-family: monospace; }
input[type=submit] { background: #1f3864; color: #fff; border: 0; padding: 6px 12px;
                     border-radius: 5px; cursor: pointer; }
.leyenda { font-size: 12px; color: #55607a; }
"""

VISTAS = [('1', 'Conjuntos FIRST / FOLLOW', '/conjuntos',
           'De dónde sale cada celda de la tabla: FIRST del cuerpo y FOLLOW de la cabeza.'),
          ('2', 'Tablas y autómata', '/tablas',
           'La tabla predictiva con sus conflictos y, si es SLR(1), ACTION/GOTO.'),
          ('3', 'Traza del parser', '/traza',
           'Pila, entrada y acción, paso a paso, con el parser que elija.'),
          ('4', 'SDD paso a paso', '/sdd',
           'El árbol anotado, el grafo de dependencias y el orden de evaluación.')]


# --------------------------------------------------------------------- modelo
def cargar(ruta):
    """Lee la gramatica y calcula todo lo que el visualizador necesita mostrar.

    Recibe: la ruta del archivo de gramatica (formato de la Seccion 2.2).
    Devuelve: un diccionario con la gramatica, los conjuntos, la tabla LL(1), el
    automata y las tablas SLR(1). No calcula nada por su cuenta: todo viene de
    los modulos del proyecto.
    """
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

    # La SDD solo aplica a su propia gramatica (las reglas van por produccion).
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


def producir(ctx):
    """Texto de una produccion numerada: '3: E -> x'."""
    return ctx['producciones']


def texto_cuerpo(cuerpo):
    """Cuerpo legible: 'S+T' o 'e' si es vacio."""
    return grammar.formatear_cuerpo(cuerpo)


def es_ll1(ctx):
    return len(ctx['conf_ll1']) == 0


def es_slr1(ctx):
    return len(ctx['conf_slr']) == 0


# ------------------------------------------------------------------ utilidades
def esc(texto):
    return html.escape(str(texto), quote=False)


def pagina(titulo, cuerpo, ctx, activa=''):
    """Envuelve el contenido de una vista con el encabezado y el menu."""
    menu = []
    for numero, nombre, ruta, _ in VISTAS:
        clase = ' class="activo"' if activa == ruta else ''
        menu.append('<a href="%s"%s>%s. %s</a>' % (ruta, clase, numero, esc(nombre)))

    if es_ll1(ctx) and es_slr1(ctx):
        veredicto = 'LL(1) y SLR(1)'
    elif es_ll1(ctx):
        veredicto = 'LL(1), no SLR(1)'
    elif es_slr1(ctx):
        veredicto = 'SLR(1), no LL(1)'
    else:
        veredicto = 'ni LL(1) ni SLR(1)'

    return ('<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">'
            '<title>%s</title><style>%s</style></head><body>'
            '<header><h1>Visualizador &mdash; %s &nbsp;<span style="font-weight:400;'
            'font-size:12px;color:#cdd7ee">(%s)</span></h1>'
            '<nav style="margin-top:8px"><a href="/"%s>Inicio</a>%s</nav></header>'
            '<main>%s</main></body></html>'
            % (esc(titulo), CSS, esc(titulo), esc(veredicto),
               ' class="activo"' if activa == '/' else '', ''.join(menu), cuerpo))


def tarjeta_estado(ctx):
    """Bloque con la gramatica de entrada y su veredicto."""
    lineas = ['<p class="nota">Gramática: <code>%s</code></p>' % esc(ctx['ruta'])]
    lineas.append('<pre class="mono" style="background:#fff;border:1px solid #dde1ea;'
                  'padding:10px;display:inline-block;font-size:12.5px">%s</pre>'
                  % esc(ctx['texto'].strip()))
    return ''.join(lineas)


# ------------------------------------------------------------------- vista 1
def vista_conjuntos(ctx):
    """FIRST y FOLLOW por no terminal, y por produccion FIRST del cuerpo."""
    partes = ['<h2>1. FIRST y FOLLOW</h2>',
              '<p class="nota">Esto es la Sección 4.4.2: los conjuntos se calculan '
              'por punto fijo. La segunda tabla explica la tabla predictiva: para cada '
              'producción, FIRST del cuerpo son las columnas donde se puede usar, y si '
              'el cuerpo puede desaparecer se usan las de FOLLOW de la cabeza.</p>']

    partes.append('<table><tr><th>No terminal</th><th>FIRST</th><th>FOLLOW</th></tr>')
    for nt in grammar.no_terminales(ctx['g']):
        partes.append('<tr><td><b>%s</b></td><td class="izq mono">%s</td>'
                      '<td class="izq mono">%s</td></tr>'
                      % (esc(nt), esc(conjunto_texto(ctx['first'][nt])),
                         esc(conjunto_texto(ctx['follow'][nt]))))
    partes.append('</table>')

    partes.append('<table><tr><th>#</th><th>Producción</th><th>FIRST(cuerpo)</th>'
                  '<th>¿Puede desaparecer?</th><th>Celdas que llena</th></tr>')
    for indice, (cabeza, cuerpo) in enumerate(grammar.lista_producciones(ctx['g'])):
        first_cuerpo = first_follow.first_de_cadena(cuerpo, ctx['first'])
        celdas = []
        for terminal in sorted(first_cuerpo - {'e'}):
            celdas.append('M[%s, %s]' % (cabeza, terminal))
        if 'e' in first_cuerpo:
            for terminal in sorted(ctx['follow'][cabeza]):
                celdas.append('M[%s, %s]' % (cabeza, terminal))
        partes.append('<tr><td>%d</td><td class="izq mono">%s</td>'
                      '<td class="izq mono">%s</td><td>%s</td>'
                      '<td class="izq mono">%s</td></tr>'
                      % (indice, esc(cabeza + ' -> ' + texto_cuerpo(cuerpo)),
                         esc(conjunto_texto(first_cuerpo)),
                         'sí' if 'e' in first_cuerpo else 'no',
                         esc(', '.join(celdas))))
    partes.append('</table>')
    return ''.join(partes)


def conjunto_texto(conjunto):
    """Conjunto en el formato del enunciado: ASCII, luego e, luego $."""
    orden = []
    for simbolo in sorted(conjunto):
        if simbolo not in ('e', '$'):
            orden.append(simbolo)
    if 'e' in conjunto:
        orden.append('e')
    if '$' in conjunto:
        orden.append('$')
    return '{' + ', '.join(orden) + '}'


# ------------------------------------------------------------------- vista 2
def vista_tablas(ctx, parser):
    """Tabla LL(1) con conflictos y, si aplica, ACTION/GOTO del SLR(1)."""
    partes = ['<h2>2. Tablas</h2>',
              '<p class="nota">Tabla predictiva de la Sección 4.4.3 (celdas en rojo = '
              'dos producciones distintas: la gramática no sería LL(1)) y tablas '
              'ACTION/GOTO de la Sección 4.6.4.</p>']

    terminales = grammar.terminales(ctx['g'])
    no_terminales = grammar.no_terminales(ctx['g'])

    partes.append('<h3 style="margin:14px 0 6px;font-size:14px;color:#1f3864">'
                  'Tabla predictiva M[A, a]</h3>')
    partes.append('<table><tr><th class="izq">M</th>')
    for terminal in terminales:
        partes.append('<th class="mono">%s</th>' % esc(terminal))
    partes.append('</tr>')
    for nt in no_terminales:
        partes.append('<tr><td class="izq"><b>%s</b></td>' % esc(nt))
        for terminal in terminales:
            clave = (nt, terminal)
            if clave in ctx['tabla_ll1']:
                indice = ctx['tabla_ll1'][clave]
                cabeza, cuerpo = ctx['producciones'][indice]
                clase = ' class="conflicto"' if clave in ctx['conf_ll1'] else ''
                partes.append('<td%s class="mono">%s</td>'
                              % (clase, esc(texto_cuerpo(cuerpo))))
            else:
                partes.append('<td style="color:#b6bcc9">—</td>')
        partes.append('</tr>')
    partes.append('</table>')

    if ctx['conf_ll1']:
        partes.append('<p class="nota">Celdas en conflicto: <code>%s</code>. Por eso la '
                      'gramática no es LL(1).</p>'
                      % esc(', '.join('M[%s, %s]' % celda for celda in ctx['conf_ll1'])))
    else:
        partes.append('<p class="nota">Sin celdas en conflicto: la gramática es LL(1).</p>')

    if not es_slr1(ctx):
        partes.append('<p class="nota">La gramática no es SLR(1): conflictos en <code>%s</code>'
                      '; las tablas ACTION/GOTO no se muestran.</p>'
                      % esc(str(ctx['conf_slr'])))
        return ''.join(partes)

    partes.append('<h3 style="margin:20px 0 6px;font-size:14px;color:#1f3864">'
                  'ACTION y GOTO (SLR(1))</h3>')
    partes.append('<table><tr><th>Estado</th>')
    for terminal in terminales + ['$']:
        partes.append('<th class="mono">%s</th>' % esc(terminal))
    for nt in no_terminales:
        partes.append('<th class="mono" style="background:#31507f">%s</th>' % esc(nt))
    partes.append('</tr>')

    for estado in range(len(ctx['estados'])):
        partes.append('<tr><td><b>I%d</b></td>' % estado)
        for terminal in terminales + ['$']:
            accion = ctx['action'].get((estado, terminal))
            if accion is None:
                partes.append('<td style="color:#b6bcc9">—</td>')
                continue
            if accion[0] == 's':
                partes.append('<td class="mono">s%d</td>' % accion[1])
            elif accion[0] == 'r':
                partes.append('<td class="mono">r%d</td>' % accion[1])
            else:
                partes.append('<td class="mono">acc</td>')
        for nt in no_terminales:
            destino = ctx['goto'].get((estado, nt))
            partes.append('<td class="mono">%s</td>'
                          % ('I%d' % destino if destino is not None else '—'))
        partes.append('</tr>')
    partes.append('</table>')

    leyenda = ['<p class="leyenda">s<i>j</i> = desplazar al estado <i>j</i>; '
               'r<i>i</i> = reducir la producción <i>i</i>; acc = aceptar; '
               '— = celda de error.<br>']
    for indice in range(len(ctx['producciones']) - 1):
        cabeza, cuerpo = ctx['producciones'][indice]
        leyenda.append('r%d = %s &rarr; %s &nbsp;&nbsp;'
                       % (indice, esc(cabeza), esc(texto_cuerpo(cuerpo))))
    leyenda.append('</p>')
    partes.append(''.join(leyenda))
    partes.append('<p class="nota">El autómata completo está en '
                  '<a href="/automata">la vista del autómata</a>.</p>')
    return ''.join(partes)


# ------------------------------------------------------------------- vista 4
def vista_automata(ctx, estado):
    """Grafo de los estados LR(0) y, si se elige uno, sus items."""
    partes = ['<h2>El autómata LR(0)</h2>',
              '<p class="nota">Diez estados, sus ítems y las transiciones GOTO '
              '(Sección 4.6.2). Haga clic en un estado para ver sus ítems.</p>']
    partes.append(svg_automata(ctx, estado))

    if estado is None:
        estado = 0
    if estado < len(ctx['estados']):
        partes.append('<h3 style="margin:16px 0 6px;font-size:14px;color:#1f3864">'
                      'Ítems de I%d</h3>' % estado)
        partes.append('<table><tr><th>Ítem</th></tr>')
        for indice, punto in sorted(ctx['estados'][estado]):
            partes.append('<tr><td class="izq mono">%s</td></tr>'
                          % esc(slr1.formatear_item(ctx['producciones'], indice, punto)))
        partes.append('</table>')
        acciones = []
        for (estado_accion, terminal), accion in sorted(ctx['action'].items()):
            if estado_accion != estado:
                continue
            if accion[0] == 's':
                acciones.append('ACTION[I%d, %s] = s%d' % (estado, terminal, accion[1]))
            elif accion[0] == 'r':
                cabeza, cuerpo = ctx['producciones'][accion[1]]
                acciones.append('ACTION[I%d, %s] = r%d (%s -> %s)'
                                % (estado, terminal, accion[1], cabeza,
                                   texto_cuerpo(cuerpo)))
            else:
                acciones.append('ACTION[I%d, %s] = acc' % (estado, terminal))
        for (estado_goto, nt), destino in sorted(ctx['goto'].items()):
            if estado_goto == estado:
                acciones.append('GOTO[I%d, %s] = I%d' % (estado, nt, destino))
        if acciones:
            partes.append('<p class="leyenda mono">%s</p>' % '<br>'.join(esc(a) for a in acciones))
    return ''.join(partes)


def svg_automata(ctx, seleccionado):
    """Dibuja el autómata con capas segun la distancia desde I0."""
    niveles = {0: 0}
    cola = [0]
    while cola:
        actual = cola.pop(0)
        for (origen, simbolo), destino in sorted(ctx['transiciones'].items()):
            if origen == actual and destino not in niveles:
                niveles[destino] = niveles[actual] + 1
                cola.append(destino)

    for estado in range(len(ctx['estados'])):
        if estado not in niveles:
            niveles[estado] = 0

    por_nivel = {}
    for estado, nivel in niveles.items():
        por_nivel.setdefault(nivel, []).append(estado)

    posiciones = {}
    for nivel, estados in por_nivel.items():
        estados.sort()
        # Los niveles con muchos estados se reparten en filas de 6 para que el
        # dibujo no se vuelva una linea larguisima.
        for i, estado in enumerate(estados):
            fila = i // 6
            columna = i % 6
            posiciones[estado] = (60 + columna * 132, 60 + nivel * 110 + fila * 66)

    ancho = max(x for x, y in posiciones.values()) + 70
    alto = max(y for x, y in posiciones.values()) + 70
    partes = ['<svg viewBox="0 0 %d %d" style="width:100%%;max-width:%dpx;height:auto;'
              'background:#fff;border:1px solid #dde1ea">' % (ancho, alto, ancho)]
    partes.append('<defs><marker id="flecha" markerWidth="9" markerHeight="9" refX="8" '
                  'refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8a93a8"/>'
                  '</marker></defs>')

    for (origen, simbolo), destino in sorted(ctx['transiciones'].items()):
        x1, y1 = posiciones[origen]
        x2, y2 = posiciones[destino]
        if (x1, y1) == (x2, y2):
            continue
        partes.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#8a93a8" '
                      'stroke-width="1.2" marker-end="url(#flecha)"/>' % (x1, y1, x2, y2))
        medio_x = (x1 + x2) // 2
        medio_y = (y1 + y2) // 2
        partes.append('<rect x="%d" y="%d" width="%d" height="14" fill="#fff"/>'
                      % (medio_x - 9, medio_y - 7, 18))
        partes.append('<text x="%d" y="%d" font-size="11" fill="#55607a" '
                      'text-anchor="middle">%s</text>'
                      % (medio_x, medio_y + 3, esc(simbolo)))

    for estado, (x, y) in posiciones.items():
        color = '#fff3cd' if estado == seleccionado else '#fff'
        borde = '#c9a227' if estado == seleccionado else '#1f3864'
        partes.append('<a href="/automata?estado=%d">' % estado)
        partes.append('<circle cx="%d" cy="%d" r="21" fill="%s" stroke="%s" '
                      'stroke-width="2"/>' % (x, y, color, borde))
        partes.append('<text x="%d" y="%d" font-size="12" font-weight="600" fill="#1b1f27" '
                      'text-anchor="middle">I%d</text></a>' % (x, y + 4, estado))

    partes.append('</svg>')
    return ''.join(partes)


# ------------------------------------------------------------------- vista 3
def vista_traza(ctx, parser, cadena, paso):
    """Traza del parser LL(1) o SLR(1) sobre una cadena, paso a paso."""
    # Igual que main.py: el parser solo se usa si la gramatica paso su prueba.
    # (Llamar al LL(1) con una tabla en conflicto y recursion por la izquierda no
    # termina nunca: la pila crece sin fin.)
    if parser == 'll1' and not es_ll1(ctx):
        return ('<h2>3. Traza del parser</h2><p class="nota">Esta gramática no es LL(1), '
                'así que el parser predictivo no sirve para ella. '
                '<a href="/traza?parser=lr&amp;cadena=%s">Use el SLR(1)</a>.</p>'
                % esc(cadena))
    if parser == 'lr' and not es_slr1(ctx):
        return ('<h2>3. Traza del parser</h2><p class="nota">Esta gramática no es SLR(1), '
                'así que el parser LR no sirve para ella. '
                '<a href="/traza?parser=ll1&amp;cadena=%s">Use el LL(1)</a>.</p>'
                % esc(cadena))

    traza = []
    if parser == 'lr':
        _, arbol = slr1.parsear_lr(ctx['producciones'], ctx['action'], ctx['goto'],
                                   cadena, traza)
        columnas = ('Pila de estados', 'Entrada', 'Acción')
    else:
        _, arbol = ll1.parsear_ll1(ctx['g'], ctx['tabla_ll1'], cadena, traza)
        columnas = ('Pila', 'Entrada', 'Acción')

    aceptada = len(traza) > 0 and traza[-1][3] in ('aceptar',)
    total = len(traza)
    paso = max(0, min(paso, total))

    partes = ['<h2>3. Traza del parser</h2>',
              '<p class="nota">Cada fila es una configuración del parser '
              '(Sección 4.4.4 para LL(1), 4.6.3 para SLR(1)). Se avanza con las '
              'flechas; la fila resaltada es la que se está explicando.</p>']

    partes.append('<form method="get" action="/traza">'
                  '<input type="hidden" name="parser" value="%s">'
                  'Cadena: <input type="text" name="cadena" value="%s" size="22"> '
                  '<input type="submit" value="Analizar"> '
                  '<span class="leyenda">(<code>e</code> = cadena vacía; parsers: '
                  '<a href="/traza?parser=ll1&amp;cadena=%s">LL(1)</a> · '
                  '<a href="/traza?parser=lr&amp;cadena=%s">SLR(1)</a>)</span></form>'
                  % (esc(parser), esc(cadena), esc(cadena), esc(cadena)))

    if paso < total:
        partes.append('<p><span class="estado">en curso: paso %d de %d</span></p>'
                      % (paso, total))
    elif not aceptada:
        partes.append('<p><span class="estado no">la cadena no pertenece al lenguaje</span></p>')
    else:
        partes.append('<p><span class="estado ok">la cadena pertenece al lenguaje</span></p>')

    enlace = '/traza?parser=%s&amp;cadena=%s&amp;paso=%%d' % (esc(parser), esc(cadena))
    partes.append('<div class="navegacion">'
                  '<a href="%s">|&lt;</a><a href="%s">&lt; anterior</a>'
                  '<span>paso %d de %d</span>'
                  '<a href="%s">siguiente &gt;</a><a href="%s">&gt;|</a></div>'
                  % (enlace % 0, enlace % max(0, paso - 1), paso, total,
                     enlace % min(total, paso + 1), enlace % total))

    partes.append('<table><tr><th>%s</th><th>%s</th><th>%s</th></tr>'
                  % tuple(esc(c) for c in columnas))
    for indice, (pila, consumido, resto, accion) in enumerate(traza):
        numero_fila = indice + 1
        if numero_fila > paso:
            break
        clase = ' class="actual"' if numero_fila == paso else ''
        partes.append('<tr%s><td class="izq mono">%s</td>'
                      '<td class="izq mono">%s | %s</td><td class="izq mono">%s</td></tr>'
                      % (clase, esc(pila), esc(consumido), esc(resto), esc(accion)))
    partes.append('</table>')

    if paso == total and aceptada:
        partes.append('<p class="nota">El árbol que construyó el parser está en la '
                      '<a href="/sdd">vista del SDD</a>.</p>')
    return ''.join(partes)


# ------------------------------------------------------------------- vista 4b
def vista_sdd(ctx, cadena, paso, circular):
    """Arbol anotado y grafo de dependencias, evaluando hasta el paso N."""
    if ctx['reglas'] is None:
        return ('<h2>4. SDD paso a paso</h2><p class="nota">La gramática cargada no es '
                'la del Item 3 (no tiene reglas en <code>sdd.py</code>). Arranque con '
                '<code>--gramatica docs/gramatica_sdd.txt</code>.</p>')

    if es_ll1(ctx):
        _, raiz = ll1.parsear_ll1(ctx['g'], ctx['tabla_ll1'], cadena)
    else:
        _, raiz = slr1.parsear_lr(ctx['producciones'], ctx['action'], ctx['goto'], cadena)

    conjunto = sdd.reglas_circulares() if circular else None
    reglas = sdd.reglas_por_indice(ctx['g'], conjunto)
    nodos, indice, orden, ciclo = sdd.evaluar(raiz, reglas)
    _, _, grafo = sdd.grafo_dependencias(raiz, reglas)

    partes = ['<h2>4. La SDD, paso a paso</h2>',
              '<p class="nota">Cada paso es un atributo del orden topológico del grafo '
              '(Secciones 5.2.1 y 5.2.2). El árbol muestra lo calculado hasta ahora y el '
              'grafo marca en amarillo el atributo del paso actual.</p>']

    partes.append('<form method="get" action="/sdd">'
                  'Cadena: <input type="text" name="cadena" value="%s" size="16"> '
                  '<input type="hidden" name="paso" value="0">'
                  '<input type="submit" value="Empezar"> '
                  '<span class="leyenda">(<code>e</code> = número vacío)</span></form>'
                  % esc(cadena))

    if ciclo is not None:
        partes.append('<p><span class="estado no">SDD circular</span> '
                      'El grafo tiene un ciclo, así que no existe orden de evaluación:'
                      '<br><code>%s</code></p>'
                      % esc(sdd.texto_ciclo(ciclo, nodos, indice)))
        partes.append(svg_grafo(grafo, nodos, indice, [], 0))
        return ''.join(partes)

    total = len(orden)
    paso = max(0, min(paso, total))
    enlace = '/sdd?cadena=%s&amp;paso=%%d' % esc(cadena)
    if circular:
        enlace = enlace + '&amp;circular=1'

    actual = ''
    if 0 < paso <= total:
        actual = sdd.texto_atributo(orden[paso - 1], nodos, indice)

    partes.append('<div class="navegacion">'
                  '<a href="%s">|&lt;</a><a href="%s">&lt; anterior</a>'
                  '<span>paso %d de %d%s</span>'
                  '<a href="%s">siguiente &gt;</a><a href="%s">&gt;|</a></div>'
                  % (enlace % 0, enlace % max(0, paso - 1), paso, total,
                     ' &middot; ' + esc(actual) if actual else '',
                     enlace % min(total, paso + 1), enlace % total))

    partes.append('<table style="margin-bottom:12px"><tr><th>Cadena</th><th>Valor de '
                  'S.v</th><th>Nodos</th><th>Atributos</th></tr>'
                  '<tr><td class="mono">%s</td><td class="mono">%s</td><td>%d</td>'
                  '<td>%d</td></tr></table>'
                  % (esc(cadena if cadena else 'e'),
                     esc(sdd.valor_principal(raiz)) if paso == total else '…',
                     len(nodos), total))

    partes.append('<h3 style="font-size:13px;color:#1f3864;margin:4px 0 6px">'
                  'Árbol anotado (· = atributo todavía sin calcular)</h3>')
    partes.append(svg_arbol(nodos, indice, orden, paso))
    partes.append('<h3 style="font-size:13px;color:#1f3864;margin:14px 0 6px">'
                  'Grafo de dependencias (verde = calculado, amarillo = paso actual)</h3>')
    partes.append(svg_grafo(grafo, nodos, indice, orden, paso))

    partes.append('<h3 style="margin:16px 0 6px;font-size:14px;color:#1f3864">'
                  'Orden de evaluación</h3><table><tr>')
    for columna in range(4):
        partes.append('<th>#</th><th>Atributo</th>')
    partes.append('</tr>')
    for inicio in range(0, total, 4):
        partes.append('<tr>')
        for posicion in range(inicio, inicio + 4):
            if posicion < total:
                numero = posicion + 1
                clase = ''
                if numero < paso:
                    clase = ' class="hecho"'
                elif numero == paso:
                    clase = ' class="actual"'
                partes.append('<td%s>%d</td><td class="izq mono"%s>%s</td>'
                              % (clase, numero, clase,
                                 esc(sdd.texto_atributo(orden[posicion], nodos, indice))))
            else:
                partes.append('<td></td><td></td>')
        partes.append('</tr>')
    partes.append('</table>')

    partes.append('<p class="leyenda">SDD circular: <a href="/sdd?cadena=%s&amp;circular=1">'
                  'ver la versión con una regla cambiada</a> · '
                  'SDD normal: <a href="/sdd?cadena=%s">volver</a></p>'
                  % (esc(cadena), esc(cadena)))
    return ''.join(partes)


def svg_arbol(nodos, indice, orden, paso):
    """Arbol anotado en SVG; los atributos posteriores al paso se dibujan como '·'."""
    if len(nodos) > 80:
        return ('<p class="nota">El árbol tiene %d nodos: demasiado grande para '
                'dibujarlo. Use una cadena de hasta 12 dígitos.</p>' % len(nodos))

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

    # Que atributos ya se calcularon: los primeros 'paso' del orden.
    hechos = set()
    for posicion in range(min(paso, len(orden))):
        hechos.add(orden[posicion])
    actual = orden[paso - 1] if 0 < paso <= len(orden) else None

    ancho_unidad = 108
    alto_unidad = 58
    ancho = (max(x for x, y in posiciones.values()) + 1) * ancho_unidad + 20
    alto = (max(y for x, y in posiciones.values()) + 1) * alto_unidad + 20
    partes = ['<svg viewBox="0 0 %d %d" style="width:100%%;max-width:%dpx;height:auto;'
              'background:#fff;border:1px solid #dde1ea">' % (ancho, alto, ancho)]

    for nodo in nodos:
        for hijo in nodo.hijos:
            x1, y1 = posiciones[id(nodo)]
            x2, y2 = posiciones[id(hijo)]
            x1 = x1 * ancho_unidad + ancho_unidad / 2
            x2 = x2 * ancho_unidad + ancho_unidad / 2
            y1 = y1 * alto_unidad + 40
            y2 = y2 * alto_unidad
            medio = (y1 + y2) / 2
            partes.append('<path d="M%.0f,%.0f L%.0f,%.0f L%.0f,%.0f L%.0f,%.0f" fill="none" '
                          'stroke="#aab1c0" stroke-width="1.1"/>'
                          % (x1, y1, x1, medio, x2, medio, x2, y2))

    for nodo in nodos:
        x, y = posiciones[id(nodo)]
        centro_x = x * ancho_unidad + ancho_unidad / 2
        centro_y = y * alto_unidad + 18

        valores = []
        for atributo in sorted(nodo.atributos):
            vertice = (indice[id(nodo)], atributo)
            if vertice in hechos:
                valor = nodo.atributos[atributo]
            else:
                valor = '·'
            valores.append('%s=%s' % (atributo, valor))

        etiqueta = nodo.simbolo + '#' + str(indice[id(nodo)])
        texto_atributos = ', '.join(valores)
        ancho_caja = max(64, len(texto_atributos) * 5.6 + 12)
        borde = '#c9a227' if actual is not None and actual[0] == indice[id(nodo)] else '#9aa3b5'
        relleno = '#fff8e1' if borde == '#c9a227' else '#fff'
        partes.append('<rect x="%.0f" y="%.0f" width="%.0f" height="34" rx="5" '
                      'fill="%s" stroke="%s" stroke-width="1.2"/>'
                      % (centro_x - ancho_caja / 2, centro_y - 17, ancho_caja, relleno, borde))
        partes.append('<text x="%.0f" y="%.0f" font-size="10.5" font-weight="700" '
                      'text-anchor="middle" fill="#1b1f27">%s</text>'
                      % (centro_x, centro_y - 3, esc(etiqueta)))
        partes.append('<text x="%.0f" y="%.0f" font-size="9" text-anchor="middle" '
                      'fill="#4a5468">%s</text>'
                      % (centro_x, centro_y + 10, esc(texto_atributos)))

    partes.append('</svg>')
    return ''.join(partes)


def svg_grafo(grafo, nodos, indice, orden, paso):
    """Grafo de dependencias en capas; verde = calculado, amarillo = paso actual."""
    """Dibuja el grafo ya construido (vertices (numero, atributo))."""
    nivel = {}
    for vertice in orden:
        if len(grafo[vertice]) == 0:
            nivel[vertice] = 0
        else:
            nivel[vertice] = 1 + max(nivel[dependencia] for dependencia in grafo[vertice])

    for vertice in grafo:
        if vertice not in nivel:
            nivel[vertice] = 0

    por_nivel = {}
    for vertice in grafo:
        por_nivel.setdefault(nivel[vertice], []).append(vertice)

    # x empieza en 46 para que la primera caja (que se dibuja a x-34) no se corte.
    posiciones = {}
    ancho_maximo = 0
    for numero_nivel, vertices in por_nivel.items():
        vertices.sort()
        for i, vertice in enumerate(vertices):
            posiciones[vertice] = (46 + i * 132, 20 + numero_nivel * 34)
            ancho_maximo = max(ancho_maximo, posiciones[vertice][0])

    ancho = ancho_maximo + 60
    alto = (max(nivel.values()) + 1) * 34 + 20
    hechos = set(orden[:min(paso, len(orden))])
    actual = orden[paso - 1] if 0 < paso <= len(orden) else None

    partes = ['<svg viewBox="0 0 %d %d" style="width:100%%;max-width:%dpx;height:auto;'
              'background:#fff;border:1px solid #dde1ea">' % (ancho, alto, ancho)]
    partes.append('<defs><marker id="fl" markerWidth="8" markerHeight="8" refX="7" refY="2.5" '
                  'orient="auto"><path d="M0,0 L0,5 L7,2.5 z" fill="#b6bcc9"/></marker></defs>')

    for vertice in grafo:
        for dependencia in grafo[vertice]:
            x1, y1 = posiciones[dependencia]
            x2, y2 = posiciones[vertice]
            color = '#c9a227' if vertice == actual else '#b3bac8'
            partes.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" '
                          'stroke-width="1.2" marker-end="url(#fl)"/>'
                          % (x1 + 40, y1 + 7, x2, y2 - 7, color))

    for vertice in grafo:
        x, y = posiciones[vertice]
        relleno = '#fff'
        if vertice in hechos:
            relleno = '#e6f4ea'
        if vertice == actual:
            relleno = '#fff3cd'
        partes.append('<rect x="%d" y="%d" width="78" height="20" rx="4" fill="%s" '
                      'stroke="#9aa3b5" stroke-width="0.9"/>'
                      % (x - 34, y - 10, relleno))
        partes.append('<text x="%d" y="%d" font-size="9.5" text-anchor="middle" '
                      'fill="#28303f">%s</text>'
                      % (x + 5, y + 3.5,
                         esc(sdd.texto_atributo(vertice, nodos, indice))))

    partes.append('</svg>')
    return ''.join(partes)


# ------------------------------------------------------------------- inicio
def vista_inicio(ctx, ctx_sdd):
    """Portada: las dos gramaticas con su veredicto y el guion de la demostración."""
    partes = ['<h2>Visualizador del proyecto</h2>',
              '<p class="nota">Cuatro vistas para explicar el trabajo en orden: '
              'conjuntos, tablas, traza y evaluación de la SDD. Todo sale de los módulos '
              'del proyecto; aquí no se calcula nada. Las tres primeras usan la gramática '
              'de los ítems 1 y 2; la cuarta, la gramática del ítem 3.</p>']

    partes.append('<div style="display:flex;gap:18px;flex-wrap:wrap">')
    partes.append('<div><h3 style="font-size:13px;color:#1f3864;margin:0 0 6px">'
                  'Gramática de los ítems 1 y 2</h3>%s</div>' % tarjeta_estado(ctx))
    partes.append('<div><h3 style="font-size:13px;color:#1f3864;margin:0 0 6px">'
                  'Gramática del ítem 3 (SDD)</h3>%s</div>' % tarjeta_estado(ctx_sdd))
    partes.append('</div>')

    partes.append('<div class="tarjetas" style="margin-top:8px">')
    for numero, nombre, ruta, descripcion in VISTAS:
        partes.append('<div class="tarjeta"><h3>%s. %s</h3><p>%s</p>'
                      '<a class="boton" href="%s">Abrir</a></div>'
                      % (numero, esc(nombre), esc(descripcion), ruta))
    partes.append('</div>')

    partes.append('<h3 style="margin:22px 0 6px;font-size:14px;color:#1f3864">'
                  'Guion de la demostración (5 minutos)</h3>'
                  '<ol style="font-size:13px;line-height:1.7;color:#394050">'
                  '<li>Vista 1: mostrar FIRST y FOLLOW y cómo cada producción llena sus '
                  'celdas; señalar el <code>]</code> de FOLLOW.</li>'
                  '<li>Vista 2: la tabla predictiva; si hay celdas rojas, ahí está el '
                  '"no es LL(1)".</li>'
                  '<li>Vista del autómata: clic en I2 para ver por qué no hay conflicto '
                  '(shift con <code>;</code>, reduce solo con <code>$</code>).</li>'
                  '<li>Vista 3: analizar <code>[x;x];x</code> y avanzar con las flechas '
                  'hasta <i>accept</i>.</li>'
                  '<li>Vista 4: <code>1207</code>, avanzar unos pasos, mostrar el grafo y '
                  'cerrar con la SDD circular.</li></ol>')
    return ''.join(partes)


# ------------------------------------------------------------------- servidor
class Manejador(BaseHTTPRequestHandler):
    """Atiende las rutas del visualizador."""

    contexto = {}       # gramatica de los items 1 y 2 (conjuntos, tablas, traza)
    contexto_sdd = {}   # gramatica del item 3 (vista del SDD)

    def do_GET(self):
        partes = urllib.parse.urlparse(self.path)
        parametros = urllib.parse.parse_qs(partes.query)
        ruta = partes.path

        ctx = self.contexto
        ctx_sdd = Manejador.contexto_sdd
        try:
            if ruta == '/favicon.ico':
                self.send_response(204)
                self.end_headers()
                return

            if ruta == '/':
                contenido = pagina('Inicio', vista_inicio(ctx, ctx_sdd), ctx, '/')
            elif ruta == '/conjuntos':
                contenido = pagina('FIRST y FOLLOW', vista_conjuntos(ctx), ctx, '/conjuntos')
            elif ruta == '/tablas':
                contenido = pagina('Tablas', vista_tablas(ctx, 'slr'), ctx, '/tablas')
            elif ruta == '/automata':
                estado = parametro_entero(parametros, 'estado', None)
                contenido = pagina('Autómata LR(0)', vista_automata(ctx, estado), ctx, '/tablas')
            elif ruta == '/traza':
                parser = parametros.get('parser', ['ll1'])[0]
                cadena = parametros.get('cadena', ['[x;x];x' if ctx['reglas'] is None else '1207'])[0]
                paso = parametro_entero(parametros, 'paso', 10 ** 6)
                contenido = pagina('Traza del parser', vista_traza(ctx, parser, cadena, paso),
                                   ctx, '/traza')
            elif ruta == '/sdd':
                cadena = parametros.get('cadena', ['1207'])[0]
                paso = parametro_entero(parametros, 'paso', 0)
                circular = parametros.get('circular', ['0'])[0] == '1'
                contenido = pagina('SDD paso a paso',
                                   vista_sdd(ctx_sdd, cadena, paso, circular),
                                   ctx_sdd, '/sdd')
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(b'<h1>404</h1>')
                return
        except Exception as error:  # noqa: BLE001 - el visualizador no debe caerse
            contenido = pagina('Error', '<h2>Error al dibujar la vista</h2>'
                               '<pre class="mono">%s</pre><p class="nota">'
                               '<a href="/">volver al inicio</a></p>'
                               % esc(repr(error)), ctx, '')

        datos = contenido.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, format, *args):  # noqa: A002 - nombre de la clase base
        """Silencio: el visualizador no imprime una línea por petición."""
        return


def parametro_entero(parametros, nombre, por_omision):
    """Lee un entero de la URL; si no viene o no es número, devuelve el valor por omision."""
    if nombre not in parametros:
        return por_omision
    try:
        return int(parametros[nombre][0])
    except ValueError:
        return por_omision


# ---------------------------------------------------------------------- main
def revisar(ctx, ctx_sdd):
    """Prueba sin navegador: dibuja cada vista y comprueba que tenga lo esperado.

    Recibe: el contexto de la gramatica de los items 1 y 2 y el de la gramatica del
    item 3. Devuelve 0 si todo esta bien y 1 si algo falta. Sirve para verificar el
    visualizador sin levantar el servidor.
    """
    pruebas = []
    inicio = vista_inicio(ctx, ctx_sdd)
    pruebas.append(('inicio con las dos gramaticas',
                    'ítems 1 y 2' in inicio and 'ítem 3 (SDD)' in inicio))
    pruebas.append(('inicio con las cuatro tarjetas',
                    all(ruta in inicio for _, _, ruta, _ in VISTAS)))

    conjuntos = vista_conjuntos(ctx)
    pruebas.append(('conjuntos con First(', 'First(' not in conjuntos and 'FIRST' in conjuntos))
    pruebas.append(('conjuntos con tabla de producciones', 'FIRST(cuerpo)' in conjuntos))

    tablas = vista_tablas(ctx, 'slr')
    pruebas.append(('tablas con ACTION', 'ACTION' in tablas and 'acc' in tablas))

    automata = vista_automata(ctx, 2)
    pruebas.append(('automata con %d estados' % len(ctx['estados']),
                    automata.count('<circle') == len(ctx['estados'])))
    pruebas.append(('automata con los items del estado elegido',
                    'Ítems de I2' in automata and '&gt;' in automata))

    # Cadena valida para la gramatica que este cargada.
    cadena = '1207' if ctx['reglas'] is not None else '[x;x];x'
    traza = vista_traza(ctx, 'lr', cadena, 10 ** 6)
    pruebas.append(('traza con accept', 'aceptar' in traza and 'pertenece al lenguaje' in traza))
    pruebas.append(('traza que rechaza', 'no pertenece' in vista_traza(ctx, 'lr', 'z', 10 ** 6)))

    sdd_html = vista_sdd(ctx_sdd, '1207', 5, False)
    pruebas.append(('sdd con arbol', '<svg' in sdd_html and 'S#1' in sdd_html))
    pruebas.append(('sdd con orden de evaluacion', 'Orden de evaluación' in sdd_html))
    final = vista_sdd(ctx_sdd, '1207', 10 ** 6, False)
    pruebas.append(('sdd con el valor final', '1207' in final))
    circular = vista_sdd(ctx_sdd, '101', 0, True)
    pruebas.append(('sdd circular', 'SDD circular' in circular))

    correctas = 0
    for nombre, resultado in pruebas:
        print(('OK    ' if resultado else 'FALLA ') + nombre)
        correctas += 1 if resultado else 0
    print('\n%d de %d comprobaciones' % (correctas, len(pruebas)))
    return 0 if correctas == len(pruebas) else 1


def main():
    """Punto de entrada: carga las gramaticas y levanta el servidor (o hace --check)."""
    ruta_items = GRAMATICA_ITEMS
    ruta_sdd = GRAMATICA_SDD
    una_sola = None
    puerto = PUERTO
    argumentos = sys.argv[1:]
    indice_argumento = 0

    while indice_argumento < len(argumentos):
        argumento = argumentos[indice_argumento]
        if argumento == '--gramatica':
            indice_argumento += 1
            una_sola = argumentos[indice_argumento]
        elif argumento == '--puerto':
            indice_argumento += 1
            puerto = int(argumentos[indice_argumento])
        elif argumento in ('--ayuda', '-h'):
            print(__doc__)
            return 0
        elif argumento == '--check':
            pass
        else:
            print('Argumento desconocido: ' + argumento)
            return 2
        indice_argumento += 1

    if una_sola is not None:
        ruta_items = una_sola
        ruta_sdd = una_sola

    ctx = cargar(ruta_items)
    ctx_sdd = cargar(ruta_sdd)
    Manejador.contexto = ctx
    Manejador.contexto_sdd = ctx_sdd

    if '--check' in argumentos:
        return revisar(ctx, ctx_sdd)

    servidor = HTTPServer(('127.0.0.1', puerto), Manejador)
    print('Visualizador en http://127.0.0.1:%d  (Ctrl+C para salir)' % puerto)
    print('Gramática de los ítems 1 y 2: ' + ruta_items)
    print('Gramática del ítem 3 (SDD):   ' + ruta_sdd)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print('\nCerrado.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
