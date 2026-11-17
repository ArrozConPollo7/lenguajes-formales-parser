"""
Gramaticas LL(1), tabla predictiva y parser no recursivo con pila.

Secciones 4.4.3 (definicion de LL(1) y construccion de la tabla, Algoritmo 4.31,
libro p. 224) y 4.4.4 (parser predictivo no recursivo, Algoritmo 4.34 y
Fig. 4.20, libro pp. 226-227) del libro (Aho et al., 2a edicion).

La gramatica NO se transforma: se prueba tal cual, con recursion por la
izquierda incluida, como pide el enunciado. Una gramatica recursiva por la
izquierda produce celdas con dos producciones y por tanto no es LL(1).
"""

from grammar import EPSILON, FIN, INICIAL, formatear_cuerpo, lista_producciones
from first_follow import first_de_cadena


class Nodo:
    """Nodo del arbol de parseo (Seccion 5.1.2).

    Es la misma clase para el parser LL(1) y para el parser LR: el arbol es
    solo una estructura de datos, no depende de como se construyo.

    Atributos:
      simbolo    : simbolo de la gramatica que etiqueta el nodo.
      produccion : indice de la produccion aplicada en el nodo, o None si el
                   nodo es una hoja (un terminal).
      hijos      : lista de nodos, en el orden de la parte derecha.
      atributos  : diccionario atributo -> valor; lo llena el evaluador del SDD.
    """

    def __init__(self, simbolo, produccion=None):
        self.simbolo = simbolo
        self.produccion = produccion
        self.hijos = []
        self.atributos = {}


def construir_tabla(gramatica, first, follow_sets):
    """Construye la tabla predictiva M[A, a] (Seccion 4.4.3).

    Recibe: la gramatica, FIRST y FOLLOW ya calculados.
    Devuelve: una tupla (tabla, conflictos) donde
      tabla     : {(A, a): indice_de_produccion}
      conflictos: lista de celdas que recibieron mas de una produccion distinta.

    Para cada produccion A -> alpha:
      1. para cada terminal a en FIRST(alpha): M[A, a] = A -> alpha;
      2. si epsilon esta en FIRST(alpha): para cada b en FOLLOW(A): M[A, b] = A -> alpha.

    Algoritmo 4.31 (libro p. 224). Nota: el texto impreso del paso 1 dice
    FIRST(A); es una errata, lo correcto es FIRST(alpha), como muestra el
    Ejemplo 4.32. Aqui se usa FIRST del cuerpo (first_de_cadena), que es la
    version correcta.

    Se usa una lista de indices por celda para poder ver despues si hubo
    conflicto; al final la tabla se queda con un solo indice por celda.
    """
    producciones = lista_producciones(gramatica)

    # Primero se acumulan todas las producciones que caen en cada celda.
    celdas = {}

    for indice in range(len(producciones)):
        cabeza, cuerpo = producciones[indice]

        # FIRST(alpha): si el cuerpo es epsilon, esto devuelve {'e'}.
        first_cuerpo = first_de_cadena(cuerpo, first)

        # Regla 1: los terminales con los que puede empezar alpha.
        for terminal in first_cuerpo - {EPSILON}:
            agregar_a_celda(celdas, (cabeza, terminal), indice)

        # Regla 2: si alpha puede desaparecer, la produccion sirve tambien en
        # cada terminal que puede seguir a la cabeza.
        if EPSILON in first_cuerpo:
            for terminal in follow_sets[cabeza]:
                agregar_a_celda(celdas, (cabeza, terminal), indice)

    # Se colapsa cada celda a un unico indice y se anotan los conflictos.
    tabla = {}
    conflictos = []

    for celda in celdas:
        indices = celdas[celda]
        tabla[celda] = indices[0]

        # Dos producciones distintas en la misma celda: la gramatica no es LL(1).
        if len(indices) > 1:
            conflictos.append(celda)

    return tabla, sorted(conflictos)


def agregar_a_celda(celdas, celda, indice):
    """Agrega 'indice' a la lista de producciones de una celda de la tabla.

    Recibe: el diccionario de celdas, la celda (A, a) y el indice de produccion.
    No devuelve nada. Si el indice ya estaba no lo repite: una produccion que
    cae dos veces en la misma celda sigue siendo una sola produccion.
    """
    if celda not in celdas:
        celdas[celda] = []

    if indice not in celdas[celda]:
        celdas[celda].append(indice)


def es_ll1(conflictos):
    """Prueba de LL(1) de la Seccion 4.4.3.

    Recibe: la lista de celdas en conflicto que devuelve construir_tabla.
    Devuelve: True si y solo si ninguna celda de la tabla tiene dos producciones.
    """
    return len(conflictos) == 0


def parsear_ll1(gramatica, tabla, cadena, traza=None):
    """Parser predictivo no recursivo con pila (Seccion 4.4.4).

    Recibe:
      gramatica : la gramatica;
      tabla     : la tabla de construir_tabla (la gramatica ya es LL(1));
      cadena    : la cadena a analizar, SIN el '$' final;
      traza     : lista opcional donde se registran los pasos (para el informe).
    Devuelve: (aceptada, raiz), donde raiz es el Nodo del arbol de parseo.

    Funcionamiento del libro:
      - pila inicial: '$' en el fondo y el simbolo inicial S arriba;
      - la entrada es w$ y 'ip' apunta al simbolo actual;
      - con X en el tope y a en la entrada:
          * si X = a, se saca X y avanza ip;
          * si X es otro terminal, error;
          * si M[X, a] es error, error;
          * si M[X, a] = X -> Y1...Yk, se saca X y se apilan Yk...Y1;
      - se acepta si la pila queda en '$' y la entrada en '$'.

    Algoritmo 4.34 / Fig. 4.20 (libro pp. 226-227): el bucle del libro termina
    cuando el tope es '$' pero NO verifica que la entrada este en '$'. Por eso
    la rama de FIN de abajo exige las dos condiciones: la pila en '$' Y el
    simbolo actual de la entrada en '$'. Si sobran simbolos, rechaza.

    El arbol se construye siempre (cuesta lo mismo que no construirlo) porque el
    SDD del Item 3 lo necesita; para responder yes/no solo se usa el booleano.

    Importante: no se comprueba que la tabla sea de una gramatica LL(1). Si se
    llama con una tabla que tiene celdas en conflicto, en una gramatica recursiva
    por la izquierda el parser puede no terminar (aplicaria S -> S+T una y otra
    vez y la pila creceria sin fin). Por eso el programa solo lo llama cuando
    construir_tabla + es_ll1 dieron True.
    """
    producciones = lista_producciones(gramatica)

    # La entrada que recibe el programa no trae el marcador de fin: se agrega aqui.
    entrada = cadena + FIN
    ip = 0

    # La pila guarda nodos, no solo simbolos, para poder colgar los hijos.
    raiz = Nodo(INICIAL)
    pila = [Nodo(FIN), raiz]

    while True:
        tope = pila[-1]
        x = tope.simbolo
        a = entrada[ip]

        # Tope '$': la pila se consumio hasta el fondo.
        if x == FIN:
            aceptada = (a == FIN)
            if aceptada:
                registrar_traza(traza, pila, entrada, ip, 'aceptar')
            else:
                registrar_traza(traza, pila, entrada, ip, 'error: sobran simbolos')
            return aceptada, raiz

        # Tope terminal: tiene que coincidir con el simbolo actual de la entrada.
        if x not in gramatica:
            if x == a:
                registrar_traza(traza, pila, entrada, ip, 'emparejar ' + x)
                pila.pop()
                ip += 1
                continue
            registrar_traza(traza, pila, entrada, ip, 'error: se esperaba ' + x)
            return False, raiz

        # Tope no terminal: se consulta la tabla.
        indice = tabla.get((x, a))
        if indice is None:
            registrar_traza(traza, pila, entrada, ip, 'error: M[' + x + ', ' + a + '] vacia')
            return False, raiz

        cabeza, cuerpo = producciones[indice]
        registrar_traza(traza, pila, entrada, ip,
                        'aplicar ' + cabeza + ' -> ' + formatear_cuerpo(cuerpo))

        # Se expande el nodo: un hijo por simbolo del cuerpo (ninguno si es epsilon).
        tope.produccion = indice
        tope.hijos = [Nodo(simbolo) for simbolo in cuerpo]

        # Se reemplaza X por sus hijos; se apilan al reves para que Y1 quede arriba.
        pila.pop()
        for hijo in reversed(tope.hijos):
            pila.append(hijo)


def registrar_traza(traza, pila, entrada, ip, accion):
    """Agrega un paso a la traza del parser, si el llamador pidio traza.

    Recibe: la lista de traza (o None), la pila de nodos, la entrada con '$',
    la posicion actual y el texto de la accion.
    No devuelve nada y no imprime: la traza solo la usa el informe y las pruebas.
    """
    if traza is None:
        return

    pila_texto = ' '.join(nodo.simbolo for nodo in pila)
    traza.append((pila_texto, entrada[ip:], accion))
