"""
Programa principal del proyecto.

Entrada y salida segun las Secciones 2.1 y 2.2 del enunciado:

  python3 main.py            lee la gramatica y decide LL(1) / SLR(1);
  python3 main.py --sets     imprime FIRST y FOLLOW antes de decidir;
  python3 main.py --sdd      evalua la SDD del Item 3 sobre cada cadena.

Modos del Item 3 (Seccion 3 del enunciado):

  python3 main.py --sdd --lr          usa el parser SLR(1) en vez del LL(1);
  python3 main.py --sdd --circular    carga la SDD con una regla cambiada para
                                      que sea circular y muestra la deteccion.

La gramatica se lee de la entrada estandar en el formato de la Seccion 2.2 y
las cadenas se leen despues, una por linea, hasta una linea vacia. La cadena
vacia se escribe 'e'. El marcador de fin '$' lo agrega el programa.
"""

import sys

import first_follow
import grammar
import ll1
import sdd
import slr1

# Textos exactos que pide el enunciado; no se imprime nada mas.
TEXTO_MENU = 'Select a parser (T: for LL(1), B: for SLR(1), Q: quit):'
TEXTO_LL1 = 'Grammar is LL(1).'
TEXTO_SLR1 = 'Grammar is SLR(1).'
TEXTO_NINGUNA = 'Grammar is neither LL(1) nor SLR(1).'


def main():
    """Lee la gramatica, calcula los conjuntos y despacha a uno de los 4 casos.

    No recibe argumentos: lee sys.argv para '--sets' y sys.stdin para la entrada.
    No devuelve nada.
    """
    # El enunciado solo define el argumento --sets para los Items 1 y 2.
    mostrar_conjuntos = '--sets' in sys.argv[1:]

    gramatica = grammar.leer_gramatica(sys.stdin)

    # Sin gramatica no hay nada que analizar (entrada vacia).
    if gramatica is None:
        return

    # Item 3: la SDD se evalua sobre el arbol de parseo, no sobre las tablas.
    if '--sdd' in sys.argv[1:]:
        modo_sdd(gramatica, '--lr' in sys.argv[1:], '--circular' in sys.argv[1:])
        return

    # Item 1: FIRST y FOLLOW, que necesitan los dos parsers.
    first = first_follow.first_de_simbolos(gramatica)
    follow_sets = first_follow.follow(gramatica, first)

    if mostrar_conjuntos:
        first_follow.imprimir_conjuntos(gramatica, first, follow_sets)

    # Item 2a: tabla predictiva y prueba de LL(1) (Seccion 4.4.3).
    tabla_ll1, conflictos_ll1 = ll1.construir_tabla(gramatica, first, follow_sets)
    gramatica_ll1 = ll1.es_ll1(conflictos_ll1)

    # Item 2b: automata LR(0), tablas y prueba de SLR(1) (Secciones 4.6.2 y 4.6.4).
    producciones, por_cabeza = slr1.aumentar(gramatica)
    estados, transiciones = slr1.automata_lr0(producciones, por_cabeza)
    action, goto_tabla, conflictos_slr = slr1.construir_tablas(
        producciones, estados, transiciones, follow_sets)
    gramatica_slr1 = slr1.es_slr1(conflictos_slr)

    # Se despacha al caso que corresponda (Seccion 2.2.2 del enunciado).
    if gramatica_ll1 and gramatica_slr1:
        # Caso 1: las dos pruebas pasan, el usuario elige el parser.
        bucle_menu(gramatica, tabla_ll1, producciones, action, goto_tabla)

    elif gramatica_ll1:
        # Caso 2: solo existe parser LL(1).
        print(TEXTO_LL1)
        bucle_ll1(gramatica, tabla_ll1)

    elif gramatica_slr1:
        # Caso 3: solo existe parser SLR(1).
        print(TEXTO_SLR1)
        bucle_slr(producciones, action, goto_tabla)

    else:
        # Caso 4: ninguna de las dos; no se leen cadenas.
        print(TEXTO_NINGUNA)


def modo_sdd(gramatica, usar_lr, circular):
    """Evalua la SDD del Item 3 sobre cada cadena de la entrada (Seccion 3.5).

    Recibe:
      gramatica : la gramatica del Item 3, ya leida;
      usar_lr   : True para parsear con el SLR(1), False para usar el LL(1);
      circular  : True para cargar la SDD con la regla cambiada del paso 6.
    No devuelve nada. Por cada cadena imprime 'no' si no pertenece al lenguaje o,
    si pertenece, el arbol anotado, el orden de evaluacion y el valor del
    atributo principal del simbolo inicial. Si el grafo tiene un ciclo, reporta
    que la SDD es circular y termina.
    """
    first = first_follow.first_de_simbolos(gramatica)
    follow_sets = first_follow.follow(gramatica, first)

    # La SDD como datos: el conjunto de reglas se convierte a indices de produccion.
    conjunto = sdd.reglas_circulares() if circular else None
    reglas = sdd.reglas_por_indice(gramatica, conjunto)

    # El arbol lo construye el parser del Item 2, el que se haya pedido.
    if usar_lr:
        producciones, por_cabeza = slr1.aumentar(gramatica)
        estados, transiciones = slr1.automata_lr0(producciones, por_cabeza)
        action, goto_tabla, conflictos = slr1.construir_tablas(
            producciones, estados, transiciones, follow_sets)

        if not slr1.es_slr1(conflictos):
            sys.stderr.write('El parser SLR(1) no sirve para esta gramatica.\n')
            return

    else:
        tabla_ll1, conflictos_ll1 = ll1.construir_tabla(gramatica, first, follow_sets)

        if not ll1.es_ll1(conflictos_ll1):
            sys.stderr.write('El parser LL(1) no sirve para esta gramatica. '
                             'Use --sdd --lr si la gramatica es SLR(1).\n')
            return

    for cadena in leer_cadenas():
        if usar_lr:
            aceptada, raiz = slr1.parsear_lr(producciones, action, goto_tabla, cadena)
        else:
            aceptada, raiz = ll1.parsear_ll1(gramatica, tabla_ll1, cadena)

        if not aceptada:
            print('no')
            continue

        nodos, indice, orden, ciclo = sdd.evaluar(raiz, reglas)

        # SDD circular: se reporta y se termina (Seccion 3, paso 5).
        if ciclo is not None:
            print('SDD is circular: ' + sdd.texto_ciclo(ciclo, nodos, indice))
            return

        print('Annotated parse tree:')
        for linea in sdd.texto_arbol(nodos, indice):
            print(linea)

        print('Evaluation order:')
        for vertice in orden:
            print('  ' + sdd.texto_atributo(vertice, nodos, indice))

        print(sdd.etiqueta(raiz, indice) + '.' + sdd.ATRIBUTO_PRINCIPAL
              + ' = ' + str(sdd.valor_principal(raiz)))


def bucle_menu(gramatica, tabla_ll1, producciones, action, goto_tabla):
    """Menu del caso 1: la gramatica es LL(1) y SLR(1).

    Recibe: la gramatica, la tabla LL(1) y las tablas del parser LR.
    No devuelve nada. Repite: imprime el menu, lee una letra y analiza cadenas
    con el parser elegido hasta una linea vacia. Termina con Q.

    Si la letra no es T, B ni Q se vuelve a imprimir el menu y se lee otra.
    """
    while True:
        print(TEXTO_MENU)

        linea = sys.stdin.readline()

        # Fin de la entrada: se termina sin imprimir nada mas.
        if linea == '':
            return

        letra = linea.strip().upper()

        if letra == 'T':
            bucle_ll1(gramatica, tabla_ll1)

        elif letra == 'B':
            bucle_slr(producciones, action, goto_tabla)

        elif letra == 'Q':
            return

        # Cualquier otra letra: no se hace nada y el while imprime el menu otra vez.


def bucle_ll1(gramatica, tabla):
    """Analiza cadenas con el parser LL(1) hasta una linea vacia.

    Recibe: la gramatica y su tabla predictiva.
    No devuelve nada; imprime 'yes' o 'no' por cada cadena (Seccion 2.2.2).
    """
    for cadena in leer_cadenas():
        aceptada, raiz = ll1.parsear_ll1(gramatica, tabla, cadena)

        if aceptada:
            print('yes')
        else:
            print('no')


def bucle_slr(producciones, action, goto_tabla):
    """Analiza cadenas con el parser SLR(1) hasta una linea vacia.

    Recibe: las producciones aumentadas y las tablas ACTION y GOTO.
    No devuelve nada; imprime 'yes' o 'no' por cada cadena (Seccion 2.2.2).
    """
    for cadena in leer_cadenas():
        aceptada, raiz = slr1.parsear_lr(producciones, action, goto_tabla, cadena)

        if aceptada:
            print('yes')
        else:
            print('no')


def leer_cadenas():
    """Genera las cadenas de la entrada estandar hasta la linea vacia.

    Devuelve (generador) cada cadena ya sin espacios sobrantes. Una linea con
    solo 'e' es la cadena vacia, que se entrega como ''.
    """
    while True:
        linea = sys.stdin.readline()

        # Fin de la entrada o linea vacia: se termina la lista de cadenas.
        if linea.strip() == '':
            return

        texto = linea.strip()

        if texto == 'e':
            yield ''
        else:
            yield texto


if __name__ == '__main__':
    main()
