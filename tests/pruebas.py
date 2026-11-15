"""
Pruebas del proyecto de Lenguajes Formales.

Se ejecuta desde la raiz del proyecto:

    python3 tests/pruebas.py

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


def main():
    """Ejecuta todas las pruebas y devuelve 0 si todo paso, 1 si algo fallo."""
    pruebas_item_1()
    pruebas_item_2_ll1()
    pruebas_item_2_slr1()
    pruebas_main()

    print('')
    print('Correctas: ' + str(CORRECTAS[0]) + '   Fallidas: ' + str(FALLIDAS[0]))

    if FALLIDAS[0] > 0:
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
