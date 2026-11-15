"""
Conjuntos FIRST y FOLLOW de la Seccion 4.4.2 del libro (Aho et al., 2a edicion).

Se implementan las reglas del libro tal cual, por punto fijo: se repiten las
reglas hasta que ningun conjunto cambie. No se usan librerias externas ni
algoritmos alternativos.
"""

from grammar import EPSILON, FIN, INICIAL, no_terminales, terminales


def first_de_cadena(cadena, first):
    """FIRST de una cadena de simbolos X1 X2 ... Xn (Seccion 4.4.2, regla 3).

    Recibe: 'cadena' (tupla de simbolos) y 'first' (diccionario simbolo -> set).
    Devuelve: el conjunto FIRST de la cadena, que puede contener EPSILON.

    Se aplica la misma idea que la regla 3: se van uniendo los FIRST(Xi) sin
    epsilon mientras los simbolos anteriores puedan derivar epsilon; al final
    solo se agrega epsilon si TODOS los simbolos pueden derivarlo.

    El caso de la cadena vacia (n = 0) devuelve {'e'}, que es exactamente lo
    que la regla 2 dice para una produccion A -> e, y lo que hace falta cuando
    se calcula FIRST de la parte derecha de una produccion epsilon.
    """
    resultado = set()

    for simbolo in cadena:
        # Todos los terminales de Xi entran, menos epsilon (si Xi deriva epsilon
        # hay que seguir mirando los simbolos siguientes).
        resultado |= first[simbolo] - {EPSILON}

        # Si este simbolo no deriva epsilon, la cadena no puede empezar con lo
        # que sigue: se corta aqui.
        if EPSILON not in first[simbolo]:
            return resultado

    # Se recorrieron todos los simbolos y todos podian derivar epsilon.
    resultado.add(EPSILON)
    return resultado


def first_de_simbolos(gramatica):
    """Calcula FIRST(X) para cada simbolo X de la gramatica (Seccion 4.4.2).

    Recibe: la gramatica (diccionario de grammar.leer_gramatica).
    Devuelve: diccionario {simbolo: set} con terminales y EPSILON, valido para
    terminales y para no terminales.

    Se aplican las tres reglas del libro:
      1. Si X es terminal, FIRST(X) = {X}.
      2. Si X -> e es produccion, epsilon entra en FIRST(X).
      3. Para X -> Y1...Yk se usa first_de_cadena, que es la regla 3.
    """
    first = {}

    # Regla 1: el FIRST de un terminal es el mismo.
    for terminal in terminales(gramatica):
        first[terminal] = {terminal}

    # Los no terminales empiezan vacios y se llenan con el punto fijo.
    for no_terminal in gramatica:
        first[no_terminal] = set()

    # Punto fijo: se repite el recorrido de todas las producciones hasta que
    # ninguna agregue un simbolo nuevo a un FIRST.
    cambio = True

    while cambio:
        cambio = False

        for cabeza in gramatica:
            for cuerpo in gramatica[cabeza]:
                # Reglas 2 y 3 a la vez: first_de_cadena devuelve {'e'} cuando
                # el cuerpo es vacio, y si no aplica las dos reglas sobre Y1...Yk.
                nuevos = first_de_cadena(cuerpo, first)

                # Solo hay cambio si aparece algo que no estaba.
                if not nuevos <= first[cabeza]:
                    first[cabeza] |= nuevos
                    cambio = True

    return first


def follow(gramatica, first):
    """Calcula FOLLOW(A) para cada no terminal (Seccion 4.4.2).

    Recibe: la gramatica y el diccionario de FIRST ya calculado.
    Devuelve: diccionario {no_terminal: set} con terminales y FIN ('$').
    Nunca contiene EPSILON, porque FOLLOW son terminales que pueden aparecer
    a la derecha del no terminal.

    Reglas del libro:
      1. '$' esta en FOLLOW(S).
      2. Si A -> alpha B beta, entonces FIRST(beta) - {e} esta en FOLLOW(B).
      3. Si A -> alpha B, o A -> alpha B beta con epsilon en FIRST(beta),
         entonces FOLLOW(A) esta en FOLLOW(B).
    """
    s = {}

    for no_terminal in gramatica:
        s[no_terminal] = set()

    # Regla 1: el fin de la entrada sigue al simbolo inicial.
    s[INICIAL].add(FIN)

    # Punto fijo sobre todas las producciones.
    cambio = True

    while cambio:
        cambio = False

        for cabeza in gramatica:
            for cuerpo in gramatica[cabeza]:

                # Se mira cada posicion del cuerpo: si el simbolo de esa
                # posicion es un no terminal B, lo que viene despues es beta.
                for i in range(len(cuerpo)):
                    b = cuerpo[i]

                    # Los terminales no tienen FOLLOW.
                    if b not in gramatica:
                        continue

                    beta = cuerpo[i + 1:]

                    # FIRST(beta) ya resuelve los dos casos: si beta es vacia
                    # devuelve {'e'}, o sea que la regla 2 no agrega nada y la
                    # regla 3 se aplica; si beta empieza con algo que no deriva
                    # epsilon, la regla 3 no se aplica.
                    first_beta = first_de_cadena(beta, first)

                    # Regla 2: FIRST(beta) sin epsilon.
                    aporte = first_beta - {EPSILON}
                    if not aporte <= s[b]:
                        s[b] |= aporte
                        cambio = True

                    # Regla 3: si beta puede desaparecer (o no hay beta),
                    # lo que sigue a A tambien sigue a B.
                    if EPSILON in first_beta and not s[cabeza] <= s[b]:
                        s[b] |= s[cabeza]
                        cambio = True

    return s


def formatear_conjunto(conjunto):
    """Devuelve un conjunto en el formato de la Seccion 2.1 del enunciado.

    Recibe: un set de simbolos.
    Devuelve: texto '{a, d}' con los terminales en orden ASCII, despues 'e' (si
    esta) y despues '$' (si esta). Es el orden que pide el enunciado, y no el
    orden ASCII puro, porque '$' tiene un codigo menor que las letras.
    """
    partes = []

    # Terminales en orden ASCII (sorted de cadenas de un caracter).
    for simbolo in sorted(conjunto):
        if simbolo == EPSILON or simbolo == FIN:
            continue
        partes.append(simbolo)

    # Epsilon va despues de todos los terminales.
    if EPSILON in conjunto:
        partes.append(EPSILON)

    # El marcador de fin va al final.
    if FIN in conjunto:
        partes.append(FIN)

    return '{' + ', '.join(partes) + '}'


def imprimir_conjuntos(gramatica, first, follow_sets):
    """Imprime First(A) y Follow(A) de cada no terminal, en orden alfabetico.

    Recibe: la gramatica, FIRST y FOLLOW ya calculados.
    No devuelve nada: escribe en la salida estandar el formato exacto que pide
    la Seccion 2.1, una linea por conjunto y por no terminal:

        First(A) = {a, d}
        Follow(A) = {b, $}
    """
    for no_terminal in no_terminales(gramatica):
        print('First(' + no_terminal + ') = ' + formatear_conjunto(first[no_terminal]))
        print('Follow(' + no_terminal + ') = ' + formatear_conjunto(follow_sets[no_terminal]))
