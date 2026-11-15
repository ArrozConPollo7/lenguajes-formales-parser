"""
Programa principal del proyecto.

Entrada y salida segun las Secciones 2.1 y 2.2 del enunciado:

  python3 main.py            lee la gramatica y decide LL(1) / SLR(1);
  python3 main.py --sets     imprime FIRST y FOLLOW antes de decidir.

La gramatica se lee de la entrada estandar en el formato de la Seccion 2.2 y
las cadenas se leen despues, una por linea, hasta una linea vacia. La cadena
vacia se escribe 'e'. El marcador de fin '$' lo agrega el programa.
"""

import sys

import first_follow
import grammar
import ll1
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
    # El enunciado solo define el argumento --sets.
    mostrar_conjuntos = '--sets' in sys.argv[1:]

    gramatica = grammar.leer_gramatica(sys.stdin)

    # Sin gramatica no hay nada que analizar (entrada vacia).
    if gramatica is None:
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
