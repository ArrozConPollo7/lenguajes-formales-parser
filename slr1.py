"""
Items LR(0), automata, tabla SLR(1) y parser LR.

Secciones del libro (Aho et al., 2a edicion):
  4.6.2  items LR(0), CLOSURE(I), GOTO(I, X) y coleccion canonica;
  4.6.4  construccion de las tablas ACTION y GOTO a partir de FOLLOW;
  4.6.3  algoritmo de parsing LR (shift-reduce con pila de estados).

La gramatica se aumenta con S' -> S. El nombre "S'" no choca con ningun simbolo
de la entrada porque todos los simbolos de entrada son de un solo caracter.
"""

from grammar import AUMENTADO, FIN, INICIAL, formatear_cuerpo, lista_producciones
from ll1 import Nodo


def aumentar(gramatica):
    """Aumenta la gramatica con la produccion S' -> S (Seccion 4.6.2).

    Recibe: la gramatica.
    Devuelve: (producciones, por_cabeza) donde
      producciones: lista [(cabeza, cuerpo)] de las producciones originales MAS
                    la produccion aumentada al final;
      por_cabeza  : diccionario {no_terminal: [indices de sus producciones]}.

    La produccion aumentada se agrega al FINAL a proposito: asi los indices de
    las producciones originales no cambian y los nodos del arbol pueden guardar
    ese mismo indice, igual que en el parser LL(1).
    """
    producciones = lista_producciones(gramatica)

    # La produccion aumentada queda en la ultima posicion.
    producciones.append((AUMENTADO, (INICIAL,)))

    # Indice de cada produccion agrupado por cabeza: lo usa CLOSURE para saber
    # que producciones agregar cuando aparece un no terminal despues del punto.
    por_cabeza = {}
    for i in range(len(producciones)):
        cabeza = producciones[i][0]
        if cabeza not in por_cabeza:
            por_cabeza[cabeza] = []
        por_cabeza[cabeza].append(i)

    return producciones, por_cabeza


def cerradura(items, producciones, por_cabeza):
    """CLOSURE(I) de la Seccion 4.6.2.

    Recibe: 'items' (conjunto de items (indice_produccion, punto)),
            las producciones aumentadas y el indice por cabeza.
    Devuelve: el conjunto cerrado, como frozenset de items.

    Para cada item A -> alpha . B beta con B no terminal, se agregan los items
    B -> . gamma de todas las producciones de B. Se repite hasta que no cambie,
    usando una pila de trabajo en vez de recursion.
    """
    resultado = set(items)
    pendientes = list(items)

    while pendientes:
        indice, punto = pendientes.pop()
        cabeza, cuerpo = producciones[indice]

        # Si el punto no llego al final, el simbolo siguiente puede ser un no
        # terminal que hay que expandir.
        if punto < len(cuerpo):
            simbolo = cuerpo[punto]

            # Si el simbolo es cabeza de alguna produccion, es un no terminal.
            if simbolo in por_cabeza:
                for j in por_cabeza[simbolo]:
                    nuevo = (j, 0)
                    if nuevo not in resultado:
                        resultado.add(nuevo)
                        pendientes.append(nuevo)

    return frozenset(resultado)


def goto(items, simbolo, producciones, por_cabeza):
    """GOTO(I, X) de la Seccion 4.6.2: la cerradura de los items A -> alpha X . beta.

    Recibe: un conjunto de items, un simbolo de la gramatica y las producciones.
    Devuelve: frozenset con el conjunto destino (vacio si no hay items que
    avancen con X).
    """
    nucleo = set()

    for indice, punto in items:
        cabeza, cuerpo = producciones[indice]

        # Solo avanzan los items que tienen X justo despues del punto.
        if punto < len(cuerpo) and cuerpo[punto] == simbolo:
            nucleo.add((indice, punto + 1))

    if len(nucleo) == 0:
        return frozenset()

    return cerradura(nucleo, producciones, por_cabeza)


def automata_lr0(producciones, por_cabeza):
    """Coleccion canonica de conjuntos de items LR(0) (Seccion 4.6.2).

    Recibe: las producciones aumentadas y el indice por cabeza.
    Devuelve: (estados, transiciones) donde
      estados     : lista de frozensets de items; el estado 0 es I0;
      transiciones: diccionario {(estado, simbolo): estado_destino}.

    I0 = CLOSURE({S' -> . S}). Despues se repite: para cada estado y cada
    simbolo X con GOTO(I, X) no vacio, si el conjunto es nuevo se agrega como
    estado nuevo. Los simbolos se recorren en orden ASCII para que la
    numeracion de los estados sea siempre la misma.
    """
    # Indice de la produccion aumentada: la ultima de la lista.
    indice_aumentada = len(producciones) - 1

    estado_inicial = cerradura({(indice_aumentada, 0)}, producciones, por_cabeza)

    estados = [estado_inicial]
    transiciones = {}

    i = 0
    while i < len(estados):
        conjunto = estados[i]

        # Simbolos que aparecen justo despues del punto en algun item.
        simbolos = []
        for indice, punto in conjunto:
            cabeza, cuerpo = producciones[indice]
            if punto < len(cuerpo):
                simbolo = cuerpo[punto]
                if simbolo not in simbolos:
                    simbolos.append(simbolo)

        # Orden fijo: estados y transiciones reproducibles entre ejecuciones.
        for simbolo in sorted(simbolos):
            destino = goto(conjunto, simbolo, producciones, por_cabeza)

            # Si el conjunto ya existe, se reutiliza ese estado; si no, se crea.
            if destino in estados:
                j = estados.index(destino)
            else:
                estados.append(destino)
                j = len(estados) - 1

            transiciones[(i, simbolo)] = j

        i += 1

    return estados, transiciones


def construir_tablas(producciones, estados, transiciones, follow_sets):
    """Construye ACTION y GOTO y detecta conflictos (Seccion 4.6.4).

    Recibe: producciones aumentadas, estados, transiciones y FOLLOW.
    Devuelve: (action, goto_tabla, conflictos) donde
      action    : {(estado, terminal): accion}, con accion
                  ('s', j) desplazar, ('r', indice) reducir, ('acc',) aceptar;
      goto_tabla: {(estado, no_terminal): estado};
      conflictos: lista de celdas de ACTION con dos acciones distintas.

    Reglas del libro, para cada estado i y cada item de Ii:
      1. A -> alpha . a beta con 'a' terminal y GOTO(Ii, a) = Ij  => shift j;
      2. A -> alpha . con A distinto de S'                        => reduce A -> alpha
         en cada terminal de FOLLOW(A);
      3. S' -> S .                                                => accept con '$'.
    Despues, para cada no terminal A: si GOTO(Ii, A) = Ij, entonces GOTO[i, A] = j.
    """
    # Los no terminales son las cabezas de las producciones (incluida S').
    no_terminales = set()
    for cabeza, cuerpo in producciones:
        no_terminales.add(cabeza)

    # Se acumulan acciones por celda para poder detectar conflictos despues.
    celdas = {}

    for i in range(len(estados)):
        for indice, punto in estados[i]:
            cabeza, cuerpo = producciones[indice]

            # El punto no llego al final: puede haber un shift.
            if punto < len(cuerpo):
                simbolo = cuerpo[punto]

                if simbolo not in no_terminales:
                    destino = transiciones.get((i, simbolo))
                    if destino is not None:
                        agregar_accion(celdas, (i, simbolo), ('s', destino))

                continue

            # El punto llego al final. Si la cabeza es S', se acepta; si no,
            # se reduce en todos los terminales de FOLLOW de la cabeza.
            if cabeza == AUMENTADO:
                agregar_accion(celdas, (i, FIN), ('acc',))
            else:
                for terminal in follow_sets[cabeza]:
                    agregar_accion(celdas, (i, terminal), ('r', indice))

    # Se colapsa cada celda a una sola accion y se anotan los conflictos.
    action = {}
    conflictos = []

    for celda in celdas:
        acciones = celdas[celda]
        action[celda] = acciones[0]

        # Dos acciones distintas en la misma celda: shift/reduce o reduce/reduce.
        if len(acciones) > 1:
            conflictos.append(celda)

    # Tabla GOTO: solo para no terminales.
    goto_tabla = {}
    for i in range(len(estados)):
        for no_terminal in sorted(no_terminales):
            destino = transiciones.get((i, no_terminal))
            if destino is not None:
                goto_tabla[(i, no_terminal)] = destino

    return action, goto_tabla, sorted(conflictos)


def agregar_accion(celdas, celda, accion):
    """Agrega una accion a la lista de acciones de una celda de ACTION.

    Recibe: el diccionario de celdas, la celda (estado, terminal) y la accion.
    No devuelve nada. No repite la misma accion dos veces: el conflicto es
    entre acciones distintas, no entre la misma accion escrita dos veces.
    """
    if celda not in celdas:
        celdas[celda] = []

    if accion not in celdas[celda]:
        celdas[celda].append(accion)


def es_slr1(conflictos):
    """Prueba de SLR(1) de la Seccion 4.6.4.

    Recibe: la lista de celdas en conflicto que devuelve construir_tablas.
    Devuelve: True si y solo si la tabla ACTION no tiene conflictos.
    """
    return len(conflictos) == 0


def parsear_lr(producciones, action, goto_tabla, cadena, traza=None):
    """Parser LR con pila de estados (Seccion 4.6.3).

    Recibe:
      producciones: las producciones aumentadas;
      action      : tabla ACTION;
      goto_tabla  : tabla GOTO;
      cadena      : la cadena a analizar, SIN el '$' final;
      traza       : lista opcional donde se registran los pasos (para el informe).
    Devuelve: (aceptada, raiz), donde raiz es el Nodo del arbol de parseo.

    Funcionamiento del libro:
      - pila de estados, inicialmente [0]; entrada w$;
      - con s en el tope y a en la entrada:
          * ACTION[s, a] = shift t: se apila t y se avanza;
          * ACTION[s, a] = reduce A -> beta: se sacan |beta| estados, se toma
            t el nuevo tope y se apila GOTO[t, A];
          * ACTION[s, a] = accept: exito;
          * celda vacia: error.

    Para poder construir el arbol se mantiene una segunda pila con los nodos,
    en paralelo con la de estados: cada shift apila la hoja del terminal y cada
    reduccion cuelga los |beta| nodos sacados como hijos del nodo A.
    """
    entrada = cadena + FIN
    ip = 0

    pila_estados = [0]
    pila_nodos = []

    while True:
        s = pila_estados[-1]
        a = entrada[ip]
        accion = action.get((s, a))

        # Celda vacia: la cadena no se puede analizar.
        if accion is None:
            texto = 'error: ACTION[' + str(s) + ', ' + a + '] vacia'
            registrar_traza(traza, pila_estados, pila_nodos, entrada, ip, texto)
            return False, None

        if accion[0] == 's':
            # Shift: se apila el estado destino y la hoja del terminal.
            registrar_traza(traza, pila_estados, pila_nodos, entrada, ip,
                            'desplazar ' + str(accion[1]))
            pila_estados.append(accion[1])
            pila_nodos.append(Nodo(a))
            ip += 1

        elif accion[0] == 'r':
            indice = accion[1]
            cabeza, cuerpo = producciones[indice]
            registrar_traza(traza, pila_estados, pila_nodos, entrada, ip,
                            'reducir ' + cabeza + ' -> ' + formatear_cuerpo(cuerpo))

            # Los |cuerpo| hijos son los ultimos nodos de la pila.
            # Ojo: una reduccion epsilon (cuerpo vacio) no saca nada.
            if len(cuerpo) == 0:
                hijos = []
            else:
                hijos = pila_nodos[-len(cuerpo):]
                del pila_nodos[-len(cuerpo):]
                del pila_estados[-len(cuerpo):]

            nodo = Nodo(cabeza, indice)
            nodo.hijos = hijos

            # Nuevo estado: GOTO del estado que queda en el tope con la cabeza.
            destino = goto_tabla.get((pila_estados[-1], cabeza))
            if destino is None:
                registrar_traza(traza, pila_estados, pila_nodos, entrada, ip,
                                'error: falta GOTO[' + cabeza + ']')
                return False, None

            pila_estados.append(destino)
            pila_nodos.append(nodo)

        else:
            # Accept: el unico nodo que queda es el del simbolo inicial.
            registrar_traza(traza, pila_estados, pila_nodos, entrada, ip, 'aceptar')
            return True, pila_nodos[-1]


def formatear_item(producciones, indice, punto):
    """Devuelve un item LR(0) como texto: 'A -> alpha . beta'.

    Recibe: las producciones, el indice de la produccion y la posicion del punto.
    Sirve para imprimir el automata en el informe y para los mensajes de error.
    """
    cabeza, cuerpo = producciones[indice]

    # Se mete el punto en el cuerpo justo en su posicion.
    cuerpo_con_punto = cuerpo[:punto] + ('.',) + cuerpo[punto:]

    return cabeza + ' -> ' + ''.join(cuerpo_con_punto)


def registrar_traza(traza, pila_estados, pila_nodos, entrada, ip, accion):
    """Agrega un paso a la traza del parser LR, si el llamador pidio traza.

    Recibe: la lista de traza (o None), la pila de estados, la pila de nodos,
    la entrada con '$', la posicion actual y el texto de la accion.
    No devuelve nada y no imprime: la traza solo la usan el informe y las pruebas.
    """
    if traza is None:
        return

    estados_texto = ' '.join(str(estado) for estado in pila_estados)
    simbolos_texto = ''.join(nodo.simbolo for nodo in pila_nodos)

    traza.append((estados_texto, simbolos_texto, entrada[ip:], accion))
