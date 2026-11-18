"""
Pruebas del proyecto de Lenguajes Formales.

Se ejecuta desde la raiz del proyecto:

    python3 tests/pruebas.py              # las 93 pruebas
    python3 tests/pruebas.py ll1 sdd      # solo esos grupos
    python3 tests/pruebas.py --lista      # nombres de los grupos

Cada prueba compara texto exacto, porque el enunciado fija el formato de
salida. Las pruebas se agregan fase por fase.
"""

import contextlib
import io
import os
import subprocess
import sys

# La raiz del proyecto es el directorio padre de tests/.
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import grammar
import first_follow
import ll1
import sdd
import slr1


# Contadores globales de resultados.
CORRECTAS = [0]
FALLIDAS = [0]


def comprobar(nombre, obtenido, esperado):
    """Compara dos textos y anota el resultado.

    Recibe: nombre de la prueba, texto obtenido y texto esperado.
    No devuelve nada; imprime OK o FALLA con el detalle.
    """
    if obtenido == esperado:
        CORRECTAS[0] += 1
        print('OK    ' + nombre)
    else:
        FALLIDAS[0] += 1
        print('FALLA ' + nombre)
        print('  esperado: ' + repr(esperado))
        print('  obtenido: ' + repr(obtenido))


def conjuntos(entrada):
    """Devuelve el texto que imprimiria --sets para una gramatica dada.

    Recibe: la gramatica como texto en el formato de la Seccion 2.2.
    Devuelve: el texto de imprimir_conjuntos, capturado de la salida estandar.
    """
    g = grammar.leer_gramatica(io.StringIO(entrada))
    first = first_follow.first_de_simbolos(g)
    follow = first_follow.follow(g, first)

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        first_follow.imprimir_conjuntos(g, first, follow)

    return buffer.getvalue()


# Gramaticas de los tres ejemplos del enunciado (Seccion 5).
EJEMPLO_1 = '3\nS -> S+T T\nT -> T*F F\nF -> (S) i\n'
EJEMPLO_2 = '3\nS -> AB\nA -> aA d\nB -> bBc e\n'
EJEMPLO_3 = '1\nS -> SS a\n'

# Gramatica propia: epsilon que se propaga por una cadena de no terminales.
# Ojo con el formato: el cuerpo 'AB' son dos simbolos; 'A B' serian dos
# alternativas distintas (Seccion 2.2: las alternativas se separan con espacios).
PROPIA_EPSILON = '3\nS -> AB\nA -> aA e\nB -> bB e\n'

# Gramatica propia: recursion por la izquierda y una produccion epsilon.
PROPIA_RECURSIVA = '3\nS -> E\nE -> E+T T\nT -> t e\n'

# Gramatica con un no terminal inalcanzable: su FOLLOW queda vacio.
PROPIA_FOLLOW_VACIO = '2\nS -> a\nX -> b\n'

# Gramatica LL(1) que NO es SLR(1). En el estado 0 conviven los items A -> . y
# B -> . y FOLLOW(A) = FOLLOW(B) = {a, b}, asi que la tabla SLR(1) tiene dos
# conflictos reduce/reduce. El lenguaje es {ab, ba}.
# (Ejemplo clasico; se verifico con el programa antes de usarlo.)
LL1_SIN_SLR = '3\nS -> AaAb BbBa\nA -> e\nB -> e\n'

# Gramatica y SDD del Item 3. Es la misma que esta en docs/gramatica_sdd.txt y
# en sdd.py: tres no terminales, trece producciones y N recursiva por la derecha.
GRAMATICA_SDD = '3\nS -> N\nN -> DN e\nD -> 0 1 2 3 4 5 6 7 8 9\n'


def pruebas_item_1():
    """Pruebas de FIRST y FOLLOW sobre los ejemplos y gramaticas propias."""

    # Ejemplo 1: sin epsilon; FOLLOW(S) recibe ')' desde F -> (S) y '+' desde S -> S+T.
    # El orden de impresion es alfabetico: F, S, T.
    comprobar('sets ejemplo 1', conjuntos(EJEMPLO_1),
              'First(F) = {(, i}\n'
              'Follow(F) = {), *, +, $}\n'
              'First(S) = {(, i}\n'
              'Follow(S) = {), +, $}\n'
              'First(T) = {(, i}\n'
              'Follow(T) = {), *, +, $}\n')

    # Ejemplo 2: epsilon en A y en B. FIRST(S) no contiene 'e' porque
    # FIRST(A) = {a, d} no deriva epsilon. FOLLOW(B) contiene 'c' por la
    # recursion B -> bBc: la 'c' sigue a la B interior.
    comprobar('sets ejemplo 2', conjuntos(EJEMPLO_2),
              'First(A) = {a, d}\n'
              'Follow(A) = {b, $}\n'
              'First(B) = {b, e}\n'
              'Follow(B) = {c, $}\n'
              'First(S) = {a, d}\n'
              'Follow(S) = {$}\n')

    # Ejemplo 3: la recursion S -> SS obliga a que FOLLOW(S) se retroalimente.
    comprobar('sets ejemplo 3', conjuntos(EJEMPLO_3),
              'First(S) = {a}\n'
              'Follow(S) = {a, $}\n')

    # Propia con epsilon: FIRST(S) si contiene 'e' porque A y B pueden
    # desaparecer; FOLLOW(A) hereda FOLLOW(S) al final de S -> AB.
    comprobar('sets propia con epsilon', conjuntos(PROPIA_EPSILON),
              'First(A) = {a, e}\n'
              'Follow(A) = {b, $}\n'
              'First(B) = {b, e}\n'
              'Follow(B) = {$}\n'
              'First(S) = {a, b, e}\n'
              'Follow(S) = {$}\n')

    # Propia recursiva por la izquierda: '+' entra en FIRST(E) por E -> E+T
    # cuando E deriva epsilon a traves de T -> e; '+' entra en FOLLOW(E) por
    # la misma produccion, y FOLLOW(T) hereda FOLLOW(E) al final.
    comprobar('sets propia recursiva', conjuntos(PROPIA_RECURSIVA),
              'First(E) = {+, t, e}\n'
              'Follow(E) = {+, $}\n'
              'First(S) = {+, t, e}\n'
              'Follow(S) = {$}\n'
              'First(T) = {t, e}\n'
              'Follow(T) = {+, $}\n')

    # No terminal inalcanzable: validaciones de formato con conjunto vacio.
    comprobar('sets con FOLLOW vacio', conjuntos(PROPIA_FOLLOW_VACIO),
              'First(S) = {a}\n'
              'Follow(S) = {$}\n'
              'First(X) = {b}\n'
              'Follow(X) = {}\n')

    # La lectura debe guardar epsilon como cuerpo vacio y el resto como tuplas.
    g = grammar.leer_gramatica(io.StringIO('2\nS -> AB\nB -> bBc e\n'))
    comprobar('lectura de cuerpos', g,
              {'S': [('A', 'B')], 'B': [('b', 'B', 'c'), ()]})

    # Las alternativas se separan con espacios: 'A B' son dos alternativas.
    g = grammar.leer_gramatica(io.StringIO('2\nS -> AB A B\nB -> bBc e\n'))
    comprobar('alternativas separadas por espacios', g,
              {'S': [('A', 'B'), ('A',), ('B',)], 'B': [('b', 'B', 'c'), ()]})

    # Una alternativa repetida es la misma produccion: no se guarda dos veces.
    g = grammar.leer_gramatica(io.StringIO('1\nS -> a a\n'))
    comprobar('alternativa repetida se guarda una vez', g, {'S': [('a',)]})

    # Por eso S -> a a es LL(1) y SLR(1) y no un falso conflicto.
    comprobar('alternativa repetida no es conflicto LL(1)', tabla_ll1('1\nS -> a a\n')[1], [])
    comprobar('alternativa repetida no es conflicto SLR(1)',
              preparar_slr('1\nS -> a a\n')[3], [])

    # El orden de los terminales es ASCII, no alfabetico: ')' (41) < '*' (42) < '+' (43).
    comprobar('orden ASCII en conjuntos',
              first_follow.formatear_conjunto({')', '*', '+', 'i'}),
              '{), *, +, i}')


def pruebas_item_2_ll1():
    """Pruebas de la tabla predictiva y del parser LL(1) (Secciones 4.4.3 y 4.4.4)."""

    # Tabla del ejemplo 2. Producciones numeradas:
    # 0 S -> AB, 1 A -> aA, 2 A -> d, 3 B -> bBc, 4 B -> e.
    # Las celdas de B salen de FOLLOW(B) = {c, $} porque B -> e.
    tabla, conflictos = tabla_ll1(EJEMPLO_2)
    comprobar('tabla LL(1) ejemplo 2', tabla,
              {('S', 'a'): 0, ('S', 'd'): 0,
               ('A', 'a'): 1, ('A', 'd'): 2,
               ('B', 'b'): 3, ('B', 'c'): 4, ('B', '$'): 4})
    comprobar('sin conflictos en ejemplo 2', conflictos, [])

    # El ejemplo 2 es LL(1); el 3 es ambiguo; el 1 es recursivo por la izquierda,
    # asi que M[S, i] recibiria S -> S+T y S -> T a la vez.
    comprobar('ejemplo 2 es LL(1)', acepta_ll1(EJEMPLO_2, 'd'), True)
    # El ejemplo 3 tiene una sola celda en conflicto: M[S, a] recibe S -> SS
    # (FIRST(SS) = {a}) y S -> a. La celda (S, S) no existe: las columnas de la
    # tabla son terminales, nunca no terminales.
    comprobar('ejemplo 3 no es LL(1)', tabla_ll1(EJEMPLO_3)[1], [('S', 'a')])
    comprobar('ejemplo 1 no es LL(1)', tabla_ll1(EJEMPLO_1)[1],
              [('S', '('), ('S', 'i'), ('T', '('), ('T', 'i')])

    # Cadenas del ejemplo 2: d y adbc se generan, 'a' no.
    comprobar('LL(1) d', acepta_ll1(EJEMPLO_2, 'd'), True)
    comprobar('LL(1) adbc', acepta_ll1(EJEMPLO_2, 'adbc'), True)
    comprobar('LL(1) a', acepta_ll1(EJEMPLO_2, 'a'), False)
    comprobar('LL(1) simbolo ajeno', acepta_ll1(EJEMPLO_2, 'z'), False)

    # Aceptacion estricta (Algoritmo 4.34 y Fig. 4.20, pp. 226-227): el bucle
    # del libro termina cuando el tope es '$' sin volver a mirar la entrada, asi
    # que aceptaria 'aa' con S -> a. Aqui se exige tambien que el simbolo actual
    # sea '$': si sobran simbolos, la cadena se rechaza.
    g_corta, first_corta, follow_corta = preparar('1\nS -> a\n')
    tabla_corta, conflictos_corta = ll1.construir_tabla(g_corta, first_corta, follow_corta)
    comprobar('gramatica corta es LL(1)', ll1.es_ll1(conflictos_corta), True)
    comprobar('accept exige entrada en $',
              [ll1.parsear_ll1(g_corta, tabla_corta, cadena)[0] for cadena in ('a', 'aa')],
              [True, False])
    traza_sobra = []
    ll1.parsear_ll1(g_corta, tabla_corta, 'aa', traza_sobra)
    comprobar('traza de sobran simbolos', traza_sobra[-1][2], 'error: sobran simbolos')

    # Arbol de 'd': S -> AB, A -> d, B -> e. El nodo de B existe y no tiene hijos:
    # eso es lo que despues necesita el SDD para instanciar reglas epsilon.
    g, first, follow = preparar(EJEMPLO_2)
    tabla, conflictos = ll1.construir_tabla(g, first, follow)
    aceptada, raiz = ll1.parsear_ll1(g, tabla, 'd')
    comprobar('arbol de d', (aceptada, arbol_texto(raiz)), (True, 'S(A(d) B())'))

    # El nodo de B quedo con la produccion B -> e, no en None.
    comprobar('produccion epsilon en el arbol', raiz.hijos[1].produccion, 4)

    # La traza del informe debe terminar en aceptar y no estar vacia.
    traza = []
    ll1.parsear_ll1(g, tabla, 'adbc', traza)
    comprobar('traza con pasos', len(traza) > 0, True)
    comprobar('traza termina aceptando', traza[-1][2], 'aceptar')


def preparar_slr(entrada):
    """Devuelve las tablas SLR(1) de una gramatica.

    Devuelve: (producciones_aumentadas, action, goto, conflictos, estados).
    """
    g, first, follow = preparar(entrada)
    producciones, por_cabeza = slr1.aumentar(g)
    estados, transiciones = slr1.automata_lr0(producciones, por_cabeza)
    action, goto_tabla, conflictos = slr1.construir_tablas(
        producciones, estados, transiciones, follow)
    return producciones, action, goto_tabla, conflictos, estados


def acepta_slr(entrada, cadena):
    """Parsea 'cadena' con el parser LR y devuelve True, False o None (no SLR)."""
    producciones, action, goto_tabla, conflictos, estados = preparar_slr(entrada)

    if not slr1.es_slr1(conflictos):
        return None

    aceptada, raiz = slr1.parsear_lr(producciones, action, goto_tabla, cadena)
    return aceptada


def arbol_slr(entrada, cadena):
    """Devuelve (aceptada, texto del arbol) del parser LR."""
    producciones, action, goto_tabla, conflictos, estados = preparar_slr(entrada)
    aceptada, raiz = slr1.parsear_lr(producciones, action, goto_tabla, cadena)
    return (aceptada, arbol_texto(raiz))


def pruebas_item_2_slr1():
    """Pruebas del automata, la tabla y el parser SLR(1) (Secciones 4.6.2 a 4.6.4)."""

    # Ejemplo 1: el clasico de expresiones. 12 estados y ninguna celda en conflicto.
    producciones, action, goto_tabla, conflictos, estados = preparar_slr(EJEMPLO_1)
    comprobar('ejemplo 1 es SLR(1)', conflictos, [])
    comprobar('ejemplo 1 tiene 12 estados', len(estados), 12)

    # La celda ACTION[S, i] del estado 0 es un desplazamiento; en cambio M[S, i]
    # no existe porque S -> S+T es recursivo por la izquierda (eso lo vio LL(1)).
    comprobar('ACTION[0, i] desplaza', action[(0, 'i')], ('s', 5))
    comprobar('ACTION[3, $] acepta', action[(3, '$')], ('acc',))

    # Cadenas del ejemplo 1.
    comprobar('SLR i+i', acepta_slr(EJEMPLO_1, 'i+i'), True)
    comprobar('SLR (i)', acepta_slr(EJEMPLO_1, '(i)'), True)
    comprobar('SLR (i+i)*i', acepta_slr(EJEMPLO_1, '(i+i)*i'), True)
    comprobar('SLR (i+i)*i)', acepta_slr(EJEMPLO_1, '(i+i)*i)'), False)
    comprobar('SLR i+', acepta_slr(EJEMPLO_1, 'i+'), False)
    comprobar('SLR +i', acepta_slr(EJEMPLO_1, '+i'), False)
    comprobar('SLR cadena vacia', acepta_slr(EJEMPLO_1, ''), False)

    # Ejemplo 3: S -> SS | a. El conflicto esta en el estado 3, donde conviven
    # el item S -> SS. (reducir) y los items S -> .SS y S -> .a (desplazar en a),
    # y ademas 'a' pertenece a FOLLOW(S) = {a, $}.
    producciones, action, goto_tabla, conflictos, estados = preparar_slr(EJEMPLO_3)
    comprobar('ejemplo 3 tiene 4 estados', len(estados), 4)
    comprobar('ejemplo 3 conflicto en (3, a)', conflictos, [(3, 'a')])
    comprobar('ejemplo 3 no es SLR(1)', slr1.es_slr1(conflictos), False)

    # Ejemplo 2: es SLR(1) y LL(1) a la vez, asi que el programa pedira el menu.
    producciones, action, goto_tabla, conflictos, estados = preparar_slr(EJEMPLO_2)
    comprobar('ejemplo 2 es SLR(1)', conflictos, [])
    comprobar('SLR d', acepta_slr(EJEMPLO_2, 'd'), True)
    comprobar('SLR adbc', acepta_slr(EJEMPLO_2, 'adbc'), True)
    comprobar('SLR a', acepta_slr(EJEMPLO_2, 'a'), False)

    # Reduccion epsilon en LR: B -> e se reduce sacando 0 estados de la pila.
    g, first, follow = preparar('2\nS -> aB\nB -> b e\n')
    comprobar('gramatica con epsilon es SLR(1)',
              slr1.es_slr1(preparar_slr('2\nS -> aB\nB -> b e\n')[3]), True)
    comprobar('arbol LR con reduccion epsilon', arbol_slr('2\nS -> aB\nB -> b e\n', 'a'),
              (True, 'S(a B())'))
    comprobar('SLR ab con epsilon', acepta_slr('2\nS -> aB\nB -> b e\n', 'ab'), True)

    # Los dos parsers deben producir el mismo arbol para una cadena comun.
    tabla_ll, conflictos_ll = ll1.construir_tabla(g, first, follow)
    aceptada_ll, raiz_ll = ll1.parsear_ll1(g, tabla_ll, 'ab')
    comprobar('mismo arbol en LL(1) y SLR(1)', (aceptada_ll, arbol_texto(raiz_ll)),
              arbol_slr('2\nS -> aB\nB -> b e\n', 'ab'))

    # Caso "LL(1) pero no SLR(1)": dos no terminales que solo producen epsilon
    # y tienen el mismo FOLLOW. Es el unico caso del enunciado en que el
    # programa no ofrece el menu, porque solo existe el parser LL(1).
    comprobar('LL1_SIN_SLR es LL(1)', tabla_ll1(LL1_SIN_SLR)[1], [])
    comprobar('LL1_SIN_SLR no es SLR(1)', preparar_slr(LL1_SIN_SLR)[3],
              [(0, 'a'), (0, 'b')])
    comprobar('LL1_SIN_SLR ab', acepta_ll1(LL1_SIN_SLR, 'ab'), True)
    comprobar('LL1_SIN_SLR ba', acepta_ll1(LL1_SIN_SLR, 'ba'), True)
    comprobar('LL1_SIN_SLR aa', acepta_ll1(LL1_SIN_SLR, 'aa'), False)
    comprobar('LL1_SIN_SLR vacia', acepta_ll1(LL1_SIN_SLR, ''), False)


def preparar(entrada):
    """Lee una gramatica y devuelve (gramatica, first, follow)."""
    g = grammar.leer_gramatica(io.StringIO(entrada))
    first = first_follow.first_de_simbolos(g)
    follow = first_follow.follow(g, first)
    return g, first, follow


def tabla_ll1(entrada):
    """Devuelve la tabla LL(1) y la lista de conflictos de una gramatica."""
    g, first, follow = preparar(entrada)
    return ll1.construir_tabla(g, first, follow)


def arbol_texto(nodo):
    """Forma textual de un arbol de parseo, para compararlo en las pruebas.

    Un nodo interno se escribe A(hijos...) y una hoja se escribe con su simbolo.
    """
    if nodo.produccion is None:
        return nodo.simbolo

    partes = []
    for hijo in nodo.hijos:
        partes.append(arbol_texto(hijo))

    return nodo.simbolo + '(' + ' '.join(partes) + ')'


def acepta_ll1(entrada, cadena):
    """Parsea 'cadena' con el parser LL(1) y devuelve True o False."""
    g, first, follow = preparar(entrada)
    tabla, conflictos = ll1.construir_tabla(g, first, follow)

    # Si la gramatica no es LL(1), la tabla no sirve para parsear.
    if not ll1.es_ll1(conflictos):
        return None

    aceptada, raiz = ll1.parsear_ll1(g, tabla, cadena)
    return aceptada


def ejecutar(argumentos, entrada):
    """Corre main.py con 'entrada' en la entrada estandar.

    Recibe: lista de argumentos de la linea de comandos y el texto de la entrada.
    Devuelve: (salida estandar, salida de error, codigo de salida).
    """
    resultado = subprocess.run([sys.executable, 'main.py'] + argumentos,
                               input=entrada, capture_output=True, text=True,
                               cwd=RAIZ)
    return (resultado.stdout, resultado.stderr, resultado.returncode)


# Textos del enunciado que salen en los dos casos con parser unico.
MENU = 'Select a parser (T: for LL(1), B: for SLR(1), Q: quit):\n'


def pruebas_main():
    """Pruebas de punta a punta: los 4 casos de salida y el menu (Seccion 2.2.2)."""

    # Caso 3: SLR(1) pero no LL(1). Imprime el aviso y analiza con el parser LR.
    salida, error, codigo = ejecutar([], EJEMPLO_1 + 'i+i\n(i)\n(i+i)*i)\n\n')
    comprobar('main ejemplo 1', salida, 'Grammar is SLR(1).\nyes\nyes\nno\n')
    comprobar('main ejemplo 1 sin errores', (error, codigo), ('', 0))

    # Caso 1: las dos pruebas pasan. Menu, cadenas, menu otra vez, Q termina.
    salida, error, codigo = ejecutar([], EJEMPLO_2 + 'T\nd\nadbc\na\n\nQ\n')
    comprobar('main ejemplo 2 con T', salida, MENU + 'yes\nyes\nno\n' + MENU)

    salida, error, codigo = ejecutar([], EJEMPLO_2 + 'B\nd\nadbc\na\n\nQ\n')
    comprobar('main ejemplo 2 con B', salida, MENU + 'yes\nyes\nno\n' + MENU)

    # Una letra que no es T, B ni Q hace que se repita el menu.
    salida, error, codigo = ejecutar([], EJEMPLO_2 + 'X\nQ\n')
    comprobar('main menu con letra invalida', salida, MENU + MENU)

    # El menu se lee sin importar mayusculas o minusculas.
    salida, error, codigo = ejecutar([], EJEMPLO_2 + 'q\n')
    comprobar('main menu con q minuscula', salida, MENU)

    # Caso 4: ninguna de las dos pruebas pasa; no se leen cadenas.
    salida, error, codigo = ejecutar([], EJEMPLO_3)
    comprobar('main ejemplo 3', salida, 'Grammar is neither LL(1) nor SLR(1).\n')

    # Caso 2: LL(1) pero no SLR(1). No hay menu: se usa el parser LL(1).
    salida, error, codigo = ejecutar([], LL1_SIN_SLR + 'ab\nba\naa\n\n')
    comprobar('main caso LL(1) solamente', salida, 'Grammar is LL(1).\nyes\nyes\nno\n')

    # --sets imprime los conjuntos y despues sigue con el caso que corresponda.
    salida, error, codigo = ejecutar(['--sets'], EJEMPLO_1 + '\n')
    comprobar('main --sets', salida,
              'First(F) = {(, i}\n'
              'Follow(F) = {), *, +, $}\n'
              'First(S) = {(, i}\n'
              'Follow(S) = {), +, $}\n'
              'First(T) = {(, i}\n'
              'Follow(T) = {), *, +, $}\n'
              'Grammar is SLR(1).\n')

    # La cadena vacia se escribe 'e' y la gramatica la genera (S -> aSb | e).
    salida, error, codigo = ejecutar([], '1\nS -> aSb e\n' + 'T\ne\nab\naabb\naab\n\nQ\n')
    comprobar('main cadena vacia y anidamiento', salida,
              MENU + 'yes\nyes\nyes\nno\n' + MENU)

    # Si la entrada termina sin Q el programa no falla: sale del menu.
    salida, error, codigo = ejecutar([], EJEMPLO_2 + 'T\nd\n\n')
    comprobar('main sin Q al final', (salida, codigo), (MENU + 'yes\n' + MENU, 0))


def arbol_sdd(cadena, circular=False):
    """Analiza una cadena con la gramatica del Item 3 y evalua su SDD.

    Recibe: la cadena (sin '$') y si se usa la SDD circular del paso 6.
    Devuelve la tupla (aceptada, raiz, nodos, indice, orden, ciclo).
    """
    g = grammar.leer_gramatica(io.StringIO(GRAMATICA_SDD))
    first = first_follow.first_de_simbolos(g)
    follow = first_follow.follow(g, first)
    tabla, conflictos = ll1.construir_tabla(g, first, follow)

    conjunto = sdd.reglas_circulares() if circular else None
    reglas = sdd.reglas_por_indice(g, conjunto)

    aceptada, raiz = ll1.parsear_ll1(g, tabla, cadena)

    if not aceptada:
        return False, None, [], {}, [], None

    nodos, indice, orden, ciclo = sdd.evaluar(raiz, reglas)

    return True, raiz, nodos, indice, orden, ciclo


def valor_sdd(cadena):
    """Valor del atributo principal (S.v) para una cadena del Item 3, o None."""
    aceptada, raiz, nodos, indice, orden, ciclo = arbol_sdd(cadena)

    if not aceptada or ciclo is not None:
        return None

    return sdd.valor_principal(raiz)


def atributos_de(simbolo):
    """Devuelve {atributo: clase} de un simbolo segun TABLA_ATRIBUTOS.

    Un terminal no aparece en la tabla (salvo 'digito', que representa a
    cualquiera de los diez): su unico atributo es la lexval que aporta el
    analizador lexico.
    """
    clases = {}

    for entrada in sdd.TABLA_ATRIBUTOS:
        if entrada[0] == simbolo:
            clases[entrada[1]] = entrada[2]

    if len(clases) == 0 and not simbolo.isupper():
        clases['lexval'] = 'sintetizado'

    return clases


def tiene_recursion(g, cabeza):
    """True si 'cabeza' aparece en el cuerpo de alguna de sus producciones (G2)."""
    for cuerpo in g[cabeza]:
        if cabeza in cuerpo:
            return True

    return False


def pruebas_item_3():
    """Pruebas de la SDD del Item 3: definicion, evaluacion y circularidad."""

    g = grammar.leer_gramatica(io.StringIO(GRAMATICA_SDD))
    first = first_follow.first_de_simbolos(g)
    follow = first_follow.follow(g, first)

    # G1 (paso 1): la gramatica propia tiene que pasar la prueba de algun parser.
    comprobar('SDD: la gramatica es LL(1)', ll1.construir_tabla(g, first, follow)[1], [])
    producciones, por_cabeza = slr1.aumentar(g)
    estados, transiciones = slr1.automata_lr0(producciones, por_cabeza)
    comprobar('SDD: la gramatica es SLR(1)',
              slr1.construir_tablas(producciones, estados, transiciones, follow)[2], [])

    # G2 (paso 1): tres no terminales, seis producciones o mas y N recursivo.
    comprobar('SDD: tres no terminales', len(g), 3)
    comprobar('SDD: seis producciones o mas',
              len(grammar.lista_producciones(g)) >= 6, True)
    comprobar('SDD: N es recursivo', tiene_recursion(g, 'N'), True)

    # Paso 2: el simbolo inicial no tiene atributos heredados.
    comprobar('SDD: S sin atributos heredados',
              atributos_de('S').get('len'), None)
    comprobar('SDD: S no tiene heredados',
              'heredado' in atributos_de('S').values(), False)

    # Paso 2: cada atributo sintetizado de la cabeza y cada heredado de un no
    # terminal del cuerpo se define EXACTAMENTE UNA VEZ en su produccion.
    definiciones_correctas = True
    for produccion in sdd.REGLAS:
        cabeza, cuerpo = produccion
        esperados = set()

        for atributo in atributos_de(cabeza):
            if atributos_de(cabeza)[atributo] == 'sintetizado':
                esperados.add((0, atributo))

        for posicion in range(len(cuerpo)):
            clases = atributos_de(cuerpo[posicion])

            # Los terminales reciben su lexval del analizador lexico, no de una regla.
            if len(clases) == 0:
                continue

            for atributo in clases:
                if clases[atributo] == 'heredado':
                    esperados.add((posicion + 1, atributo))

        definidos = []
        for regla in sdd.REGLAS[produccion]:
            definidos.append(regla['define'])

        if sorted(definidos) != sorted(esperados):
            definiciones_correctas = False
            print('  produccion ' + cabeza + ' -> ' + grammar.formatear_cuerpo(cuerpo)
                  + ': definidos ' + str(sorted(definidos))
                  + ', esperados ' + str(sorted(esperados)))

    comprobar('SDD: define cada atributo una sola vez', definiciones_correctas, True)

    # Paso 2: todo atributo usado existe en esa produccion o es sintetizado del
    # hijo que lo aporta (por ejemplo D.v, que define la produccion D -> d).
    # En la posicion 0 solo se puede usar un atributo heredado de la cabeza: es
    # el unico que ya trae el padre (por ejemplo N.e al definir D.e).
    usos_correctos = True
    for produccion in sdd.REGLAS:
        cabeza, cuerpo = produccion
        definidos = set()

        for regla in sdd.REGLAS[produccion]:
            definidos.add(regla['define'])

        for regla in sdd.REGLAS[produccion]:
            for posicion, atributo in regla['usa']:
                if (posicion, atributo) in definidos:
                    continue

                if posicion == 0:
                    if atributos_de(cabeza).get(atributo) != 'heredado':
                        usos_correctos = False
                    continue

                clases = atributos_de(cuerpo[posicion - 1])

                if clases.get(atributo) != 'sintetizado':
                    usos_correctos = False

    comprobar('SDD: todo atributo usado esta disponible', usos_correctos, True)

    # Paso 6: cinco cadenas, con la mas corta (epsilon) y una de cinco digitos.
    comprobar('SDD valor 101', valor_sdd('101'), 101)
    comprobar('SDD valor 7', valor_sdd('7'), 7)
    comprobar('SDD valor de la cadena vacia', valor_sdd(''), 0)
    comprobar('SDD valor 999', valor_sdd('999'), 999)
    comprobar('SDD valor 0042', valor_sdd('0042'), 42)

    # Una cadena que no pertenece al lenguaje: no hay arbol ni evaluacion.
    comprobar('SDD cadena fuera del lenguaje', valor_sdd('12x'), None)

    # Paso 6: anidamiento profundo (300 digitos) sin recursion de Python.
    profunda = '7' * 300
    comprobar('SDD valor con 300 digitos', valor_sdd(profunda), int(profunda))

    # Arbol anotado exacto de '7' (paso 5 del enunciado).
    aceptada, raiz, nodos, indice, orden, ciclo = arbol_sdd('7')
    comprobar('SDD arbol anotado de 7', '\n'.join(sdd.texto_arbol(nodos, indice)),
              'S#1 [v=7]\n'
              '  N#2 [e=0, len=1, v=7]\n'
              '    D#3 [e=0, v=7]\n'
              '      7#4 [lexval=7]\n'
              '    N#5 [e=-1, len=0, v=0]')

    comprobar('SDD orden de evaluacion de 7',
              [sdd.texto_atributo(v, nodos, indice) for v in orden],
              ['7#4.lexval', 'D#3.v', 'N#5.len', 'N#2.len', 'N#2.e',
               'D#3.e', 'N#5.e', 'N#5.v', 'N#2.v', 'S#1.v'])

    # El orden impreso es un orden topologico: cada atributo aparece despues de
    # todos los que usa (Seccion 5.2.2).
    nodos101, indice101, grafo = sdd.grafo_dependencias(
        arbol_sdd('101')[1], sdd.reglas_por_indice(g))
    orden101 = arbol_sdd('101')[4]
    vistos = set()
    topologico = True
    for vertice in orden101:
        for dependencia in grafo[vertice]:
            if dependencia not in vistos:
                topologico = False
        vistos.add(vertice)
    comprobar('SDD orden topologico', topologico, True)
    comprobar('SDD orden determinista', orden101, arbol_sdd('101')[4])

    # El mismo arbol lo producen los dos parsers del Item 2 (cruce LL(1)/SLR(1)).
    aceptada_ll, raiz_ll = ll1.parsear_ll1(g, ll1.construir_tabla(g, first, follow)[0], '0042')
    aceptada_lr, raiz_lr = slr1.parsear_lr(producciones,
                                           slr1.construir_tablas(producciones, estados,
                                                                 transiciones, follow)[0],
                                           slr1.construir_tablas(producciones, estados,
                                                                 transiciones, follow)[1],
                                           '0042')
    reglas = sdd.reglas_por_indice(g)
    nodos_ll = sdd.evaluar(raiz_ll, reglas)
    nodos_lr = sdd.evaluar(raiz_lr, reglas)
    comprobar('SDD arbol LL(1) y SLR(1) identico',
              sdd.texto_arbol(nodos_ll[0], nodos_ll[1]),
              sdd.texto_arbol(nodos_lr[0], nodos_lr[1]))

    # Paso 6: la SDD circular se detecta y se informa el ciclo; no se evalua nada.
    aceptada, raiz, nodos, indice, orden, ciclo = arbol_sdd('101', circular=True)
    comprobar('SDD circular detectada', ciclo is not None, True)
    comprobar('SDD circular no evalua', orden, [])
    comprobar('SDD circular informa el ciclo',
              sdd.texto_ciclo(ciclo, nodos, indice),
              'N#2.v -> D#3.e -> N#2.e -> N#2.v')

    # Los mismos cinco casos desde la linea de comandos con --sdd.
    salida, error, codigo = ejecutar(['--sdd'], GRAMATICA_SDD + '101\n7\ne\n12x\n\n')
    comprobar('main --sdd valores', [linea for linea in salida.split('\n')
                                     if linea.startswith('S#1.v =') or linea == 'no'],
              ['S#1.v = 101', 'S#1.v = 7', 'S#1.v = 0', 'no'])

    salida, error, codigo = ejecutar(['--sdd', '--circular'], GRAMATICA_SDD + '101\n')
    comprobar('main --sdd --circular', salida,
              'SDD is circular: N#2.v -> D#3.e -> N#2.e -> N#2.v\n')


GRUPOS = [
    ('item1', 'conjuntos FIRST/FOLLOW', pruebas_item_1),
    ('ll1', 'tabla predictiva y analizador LL(1)', pruebas_item_2_ll1),
    ('slr', 'automata LR(0), ACTION/GOTO y analizador SLR(1)', pruebas_item_2_slr1),
    ('main', 'main.py y sus modos', pruebas_main),
    ('sdd', 'SDD, arbol anotado y orden de evaluacion', pruebas_item_3),
]


def ayuda():
    """Imprime el uso del script y la lista de grupos."""
    print('Uso: python3 tests/pruebas.py [grupo ...]')
    print('')
    print('Sin argumentos corre las 93 pruebas. Con uno o varios grupos corre')
    print('solo esos. Tambien acepta --lista para ver los grupos.')
    print('')
    print('Grupos:')
    for nombre, descripcion, _ in GRUPOS:
        print('  ' + nombre.ljust(6) + descripcion)


def main():
    """Ejecuta las pruebas pedidas y devuelve 0 si todo paso, 1 si algo fallo."""
    pedidos = sys.argv[1:]

    if pedidos and pedidos[0] in ('-h', '--ayuda', '--help'):
        ayuda()
        return 0

    if pedidos and pedidos[0] == '--lista':
        for nombre, descripcion, _ in GRUPOS:
            print(nombre.ljust(6) + descripcion)
        return 0

    if pedidos:
        conocidos = dict((nombre, funcion) for nombre, _, funcion in GRUPOS)
        desconocidos = [nombre for nombre in pedidos if nombre not in conocidos]
        if desconocidos:
            print('Grupo desconocido: ' + ', '.join(desconocidos))
            print('Grupos validos: ' + ', '.join(conocidos))
            return 1
        for nombre in pedidos:
            conocidos[nombre]()
    else:
        for _, _, funcion in GRUPOS:
            funcion()

    print('')
    print('Correctas: ' + str(CORRECTAS[0]) + '   Fallidas: ' + str(FALLIDAS[0]))

    if FALLIDAS[0] > 0:
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
