"""
Definicion dirigida por la sintaxis (SDD) del Item 3 y su evaluador.

Secciones del libro que se siguen (Aho et al., 2a edicion):

  5.1.1  atributos sintetizados y heredados; reglas de verificacion del SDD.
  5.1.2  arbol de analisis anotado (un valor por atributo en cada nodo).
  5.2.1  grafo de dependencias: un vertice por atributo de cada nodo y una
         arista desde el atributo que se USA hasta el atributo que se DEFINE.
  5.2.2  orden de evaluacion: orden topologico del grafo; si hay ciclo el SDD
         es circular y no se evalua.
  5.2.3  definiciones S-atribuidas.
  5.2.4  definiciones L-atribuidas.

La SDD es DATOS, no codigo: el evaluador (grafo + orden topologico + llamado de
las funciones) no sabe nada de esta gramatica ni de estos atributos. Cambiar la
SDD es cambiar las tablas TABLA_ATRIBUTOS y REGLAS de este archivo.

Gramatica elegida (formato de la Seccion 2.2 del enunciado):

    S -> N
    N -> DN e
    D -> 0 1 2 3 4 5 6 7 8 9

Genera los numeros naturales escritos en decimal (con ceros a la izquierda
permitidos) y el numero vacio. La cadena "101" se interpreta como el entero 101.

Idea de la SDD: el valor de un digito depende del lugar que ocupa, y el lugar se
cuenta desde la DERECHA (unidades = 10^0). Por eso el exponente se hereda de
izquierda a derecha, pero la raiz solo puede saber el exponente del primer digito
cuando ya conoce la LONGITUD del numero: esa longitud se sintetiza de derecha a
izquierda. Es el caso tipico de una SDD que no es L-atribuida (Seccion 5.2.4) y
que por eso mismo obliga al metodo general del grafo de dependencias: ninguna
pasada unica (ni postorden ni preorden) puede calcularla.
"""

import grammar

# Atributo del simbolo inicial que el programa reporta como resultado principal.
ATRIBUTO_PRINCIPAL = 'v'

# Tabla de atributos del informe: (simbolo, atributo, clase, tipo, significado).
TABLA_ATRIBUTOS = [
    ('S', 'v', 'sintetizado', 'entero', 'valor del numero que representa la cadena'),
    ('N', 'len', 'sintetizado', 'entero', 'cantidad de digitos del sufijo que representa N'),
    ('N', 'e', 'heredado', 'entero', 'exponente (potencia de 10) del primer digito de N'),
    ('N', 'v', 'sintetizado', 'entero', 'valor del numero que representa N'),
    ('D', 'e', 'heredado', 'entero', 'exponente (potencia de 10) que ocupa ese digito'),
    ('D', 'v', 'sintetizado', 'entero', 'valor numerico del digito'),
    ('digito', 'lexval', 'sintetizado', 'caracter', 'el caracter del digito (lo aporta el analizador lexico; aqui es el propio caracter)'),
]


# ---------------------------------------------------------------------------
# Funciones de las reglas semanticas.
#
# Cada una recibe los valores de los atributos que la regla USA, en el mismo
# orden en que estan escritos en 'usa', y devuelve el valor del atributo que la
# regla DEFINE. Son funciones pequenas y con nombre: asi el informe puede
# citarlas y la sustentacion puede explicarlas una por una.
# ---------------------------------------------------------------------------

def identidad(valor):
    """Devuelve el mismo valor. Se usa cuando un atributo copia a otro."""
    return valor


def exponente_del_primero(longitud):
    """Exponente del digito mas a la izquierda de un numero de 'longitud' digitos.

    Recibe: la cantidad de digitos (atributo len).
    Devuelve: longitud - 1, porque el ultimo digito es el de las unidades (10^0).
    """
    return longitud - 1


def exponente_siguiente(exponente):
    """Exponente del digito que sigue: un lugar menos, o sea una potencia menos."""
    return exponente - 1


def longitud_con_digito(longitud_del_resto):
    """Longitud de 'digito seguido del resto': un digito mas que el resto."""
    return 1 + longitud_del_resto


def cero():
    """Valor de la produccion N -> e: sin digitos, longitud 0 y valor 0."""
    return 0


def valor_del_digito(lexval):
    """Convierte el caracter del digito en su valor numerico ('7' -> 7)."""
    return int(lexval)


def valor_con_digito(valor_del_digito_actual, exponente, valor_del_resto):
    """Valor del numero: digito por su potencia de 10, mas el valor del resto."""
    return valor_del_digito_actual * (10 ** exponente) + valor_del_resto


# ---------------------------------------------------------------------------
# La SDD. Se guarda como datos:
#
#   REGLAS[(cabeza, cuerpo)] = [regla, ...]
#
# y cada regla es un diccionario con:
#   'define' : (posicion, atributo) del atributo que la regla define.
#              0 es la cabeza de la produccion; 1..n son los simbolos del cuerpo.
#   'usa'    : lista de (posicion, atributo) que la regla necesita.
#   'funcion': la funcion de arriba que calcula el valor.
#
# Se indexa por la produccion escrita (cabeza y cuerpo) y no por su numero,
# porque el numero depende del orden de las lineas de la entrada: asi una regla
# no puede quedar pegada a la produccion equivocada.
# ---------------------------------------------------------------------------

REGLAS = {
    # S -> N : el exponente del primer digito sale de la longitud de N, y el
    # valor del numero sube tal cual al simbolo inicial.
    ('S', ('N',)): [
        {'define': (1, 'e'), 'usa': [(1, 'len')], 'funcion': exponente_del_primero},
        {'define': (0, 'v'), 'usa': [(1, 'v')], 'funcion': identidad},
    ],

    # N -> D N : el digito toma el exponente de N y el resto hereda uno menos;
    # la longitud y el valor se sintetizan de derecha a izquierda.
    ('N', ('D', 'N')): [
        {'define': (1, 'e'), 'usa': [(0, 'e')], 'funcion': identidad},
        {'define': (2, 'e'), 'usa': [(0, 'e')], 'funcion': exponente_siguiente},
        {'define': (0, 'len'), 'usa': [(2, 'len')], 'funcion': longitud_con_digito},
        {'define': (0, 'v'), 'usa': [(1, 'v'), (1, 'e'), (2, 'v')], 'funcion': valor_con_digito},
    ],

    # N -> e : no quedan digitos.
    ('N', ()): [
        {'define': (0, 'len'), 'usa': [], 'funcion': cero},
        {'define': (0, 'v'), 'usa': [], 'funcion': cero},
    ],

    # D -> 0 ... D -> 9 : el valor del digito sale de su lexval.
    ('D', ('0',)): [{'define': (0, 'v'), 'usa': [(1, 'lexval')], 'funcion': valor_del_digito}],
    ('D', ('1',)): [{'define': (0, 'v'), 'usa': [(1, 'lexval')], 'funcion': valor_del_digito}],
    ('D', ('2',)): [{'define': (0, 'v'), 'usa': [(1, 'lexval')], 'funcion': valor_del_digito}],
    ('D', ('3',)): [{'define': (0, 'v'), 'usa': [(1, 'lexval')], 'funcion': valor_del_digito}],
    ('D', ('4',)): [{'define': (0, 'v'), 'usa': [(1, 'lexval')], 'funcion': valor_del_digito}],
    ('D', ('5',)): [{'define': (0, 'v'), 'usa': [(1, 'lexval')], 'funcion': valor_del_digito}],
    ('D', ('6',)): [{'define': (0, 'v'), 'usa': [(1, 'lexval')], 'funcion': valor_del_digito}],
    ('D', ('7',)): [{'define': (0, 'v'), 'usa': [(1, 'lexval')], 'funcion': valor_del_digito}],
    ('D', ('8',)): [{'define': (0, 'v'), 'usa': [(1, 'lexval')], 'funcion': valor_del_digito}],
    ('D', ('9',)): [{'define': (0, 'v'), 'usa': [(1, 'lexval')], 'funcion': valor_del_digito}],
}


def reglas_circulares():
    """Devuelve una copia de REGLAS con UNA regla cambiada para que sea circular.

    Recibe: nada.
    Devuelve: diccionario con la misma forma que REGLAS.

    El cambio es el de la Seccion 3, paso 6 del enunciado: en S -> N el
    exponente del primer digito se define con N.v en lugar de con N.len - 1.
    Entonces N2.e depende de N2.v, N2.v depende de D3.e y D3.e depende de N2.e:
    el grafo queda con un ciclo y el evaluador debe reportarlo.
    """
    copia = {}

    for produccion in REGLAS:
        copia[produccion] = []

        for regla in REGLAS[produccion]:
            if produccion == ('S', ('N',)) and regla['define'] == (1, 'e'):
                # La unica regla que cambia: e se define con el valor del numero.
                copia[produccion].append(
                    {'define': (1, 'e'), 'usa': [(1, 'v')], 'funcion': identidad})
            else:
                copia[produccion].append(regla)

    return copia


def reglas_por_indice(gramatica, conjunto=None):
    """Convierte un conjunto de reglas a {indice_de_produccion: [regla, ...]}.

    Recibe: la gramatica ya leida (diccionario de grammar.leer_gramatica) y,
    opcionalmente, el conjunto de reglas (por omision REGLAS; tambien sirve el
    que devuelve reglas_circulares).
    Devuelve: el diccionario indexado por el numero de produccion, que es la
    misma identidad que usan los items LR(0) y el parser.

    El SDD esta escrito para una gramatica concreta: si la entrada trae otra
    produccion, la regla no existiria y el arbol no se podria anotar. Por eso se
    lanza ValueError en vez de evaluar atributos de una gramatica equivocada.
    """
    if conjunto is None:
        conjunto = REGLAS

    por_indice = {}

    for indice, produccion in enumerate(grammar.lista_producciones(gramatica)):
        if produccion not in conjunto:
            raise ValueError('La SDD no tiene reglas para la produccion '
                             + produccion[0] + ' -> ' + grammar.formatear_cuerpo(produccion[1]))
        por_indice[indice] = conjunto[produccion]

    return por_indice


# ---------------------------------------------------------------------------
# Arbol: numeracion de nodos y etiquetas.
# ---------------------------------------------------------------------------

def numerar(raiz):
    """Numera los nodos en preorden con una pila explicita (sin recursion).

    Recibe: la raiz del arbol de parseo.
    Devuelve: (nodos, indice) donde 'nodos' es la lista de nodos en preorden e
    'indice' es {id(nodo): numero}. El numero empieza en 1 y sirve para nombrar
    cada nodo en la salida: N2, D3, ...

    Se usa pila explicita porque una cadena larga produce un arbol muy profundo
    (la gramatica es recursiva por la derecha) y la recursion de Python se cae.
    """
    nodos = []
    pila = [raiz]

    while pila:
        nodo = pila.pop()
        nodos.append(nodo)

        # Los hijos se apilan al reves para que el primero quede arriba.
        for hijo in reversed(nodo.hijos):
            pila.append(hijo)

    indice = {}

    for numero in range(len(nodos)):
        indice[id(nodos[numero])] = numero + 1

    return nodos, indice


def etiqueta(nodo, indice):
    """Texto que identifica un nodo en la salida: simbolo, # y numero (N#2).

    El '#' separa el simbolo del numero para que un terminal (que es un caracter
    suelto, por ejemplo '1') no se confunda con un numero de nodo: '1#4' es el
    terminal '1' en el nodo 4 y '14' no seria legible.
    """
    return nodo.simbolo + '#' + str(indice[id(nodo)])


# ---------------------------------------------------------------------------
# Grafo de dependencias (Seccion 5.2.1).
# ---------------------------------------------------------------------------

def grafo_dependencias(raiz, reglas):
    """Construye el grafo de dependencias del arbol (Seccion 5.2.1).

    Recibe: la raiz del arbol y las reglas ya indexadas por produccion.
    Devuelve: (nodos, indice, grafo) donde grafo es
      {(numero_de_nodo, atributo): conjunto de (numero, atributo) que DEBE calcularse antes}.

    Para cada nodo interno se instancian las reglas de su produccion: por cada
    atributo que la regla usa se agrega una arista desde ESE atributo hasta el
    atributo que la regla define. La direccion es la del libro: la arista va del
    atributo usado al atributo definido, no al reves.

    Las hojas no tienen produccion: aportan su lexval ya conocido (el caracter),
    que es un vertice sin dependencias.

    Los vertices usan el NUMERO del nodo (preorden) y no direcciones de memoria:
    asi el orden topologico es el mismo en cada ejecucion y el orden que se
    imprime para el informe se puede reproducir.
    """
    nodos, indice = numerar(raiz)
    grafo = {}

    for nodo in nodos:
        if nodo.produccion is None:
            # Hoja: el analizador lexico entrega el caracter del terminal.
            grafo[(indice[id(nodo)], 'lexval')] = set()
            continue

        for regla in reglas[nodo.produccion]:
            posicion, atributo = regla['define']
            destino = (indice[id(referenciado(nodo, posicion))], atributo)

            if destino not in grafo:
                grafo[destino] = set()

            for posicion_usada, atributo_usado in regla['usa']:
                origen = (indice[id(referenciado(nodo, posicion_usada))], atributo_usado)
                grafo[destino].add(origen)

                # El atributo usado puede ser de otra produccion: se registra
                # como vertice aunque sus dependencias se agreguen despues.
                if origen not in grafo:
                    grafo[origen] = set()

    return nodos, indice, grafo


def referenciado(nodo, posicion):
    """Devuelve el nodo de una posicion: 0 es el propio nodo, 1..n son los hijos."""
    if posicion == 0:
        return nodo

    return nodo.hijos[posicion - 1]


# ---------------------------------------------------------------------------
# Orden topologico y deteccion de ciclos (Seccion 5.2.2).
# ---------------------------------------------------------------------------

def orden_topologico(grafo):
    """Orden topologico del grafo por el algoritmo de Kahn (Seccion 5.2.2).

    Recibe: el grafo de dependencias.
    Devuelve: (orden, ciclo) donde
      orden : lista de (id_nodo, atributo) en un orden valido de evaluacion, o
              lista vacia si hay ciclo;
      ciclo : None si el grafo es aciclico, o la lista de atributos del ciclo.

    Kahn: se empieza por los atributos que no dependen de nada; al calcular uno
    se descuenta de la lista de pendientes de los que dependian de el. Si al
    final quedan atributos sin calcular es porque estan en un ciclo: un SDD
    circular no tiene orden de evaluacion posible.

    La cola se mantiene ordenada y se toma siempre el menor, para que el orden
    impreso sea el mismo en cada ejecucion.
    """
    # Cuantos atributos le faltan a cada uno para poder calcularse.
    pendientes = {}

    for vertice in grafo:
        pendientes[vertice] = len(grafo[vertice])

    # Quien depende de cada atributo (aristas al reves), para descontar rapido.
    dependientes = {}

    for vertice in grafo:
        dependientes[vertice] = []

    for vertice in grafo:
        for origen in grafo[vertice]:
            dependientes[origen].append(vertice)

    cola = []
    for vertice in pendientes:
        if pendientes[vertice] == 0:
            cola.append(vertice)
    cola.sort()

    orden = []

    while cola:
        vertice = cola.pop(0)
        orden.append(vertice)

        for siguiente in dependientes[vertice]:
            pendientes[siguiente] = pendientes[siguiente] - 1

            if pendientes[siguiente] == 0:
                cola.append(siguiente)
                cola.sort()

    if len(orden) == len(grafo):
        return orden, None

    # Quedaron atributos sin calcular: hay ciclo. Se busca uno para reportarlo.
    sin_calcular = set()
    for vertice in grafo:
        if pendientes[vertice] > 0:
            sin_calcular.add(vertice)

    return [], buscar_ciclo(grafo, sin_calcular)


def buscar_ciclo(grafo, sin_calcular):
    """Busca un ciclo dentro del subgrafo que quedo sin ordenar.

    Recibe: el grafo de dependencias y el conjunto de atributos sin calcular.
    Devuelve: lista de atributos que forman el ciclo, empezando y terminando en
    el mismo atributo (por ejemplo [A, B, C, A]).

    Solo se recorren vertices de 'sin_calcular': los demas ya tienen un orden de
    evaluacion valido y no pueden formar parte de un ciclo. El recorrido usa una
    pila explicita y guarda el camino desde el inicio; cuando se llega a un
    atributo que ya esta en el camino, ese tramo es el ciclo.
    """
    en_camino = set()

    for inicio in sorted(sin_calcular):
        camino = []
        pila = [(inicio, iter(sorted(grafo[inicio])))]

        while pila:
            vertice, siguientes = pila[-1]

            if vertice not in en_camino:
                camino.append(vertice)
                en_camino.add(vertice)

            avanzado = False

            for siguiente in siguientes:
                if siguiente in en_camino:
                    # Se cerro el ciclo: se devuelve el tramo que lo forma.
                    desde = camino.index(siguiente)
                    return camino[desde:] + [siguiente]

                if siguiente in sin_calcular:
                    pila.append((siguiente, iter(sorted(grafo[siguiente]))))
                    avanzado = True
                    break

            if not avanzado:
                pila.pop()
                en_camino.discard(vertice)
                camino.pop()

    # No deberia llegar aqui: si hubo vertices sin calcular, hay ciclo.
    return sorted(sin_calcular)


# ---------------------------------------------------------------------------
# Evaluacion (Seccion 5.2.2).
# ---------------------------------------------------------------------------

def evaluar(raiz, reglas):
    """Evalua la SDD sobre el arbol en orden topologico.

    Recibe: la raiz del arbol y las reglas indexadas por produccion.
    Devuelve: (nodos, indice, orden, ciclo) donde
      orden : lista de (id_nodo, atributo) ya evaluados, en el orden usado;
      ciclo : None, o la lista de atributos que forman el ciclo.

    Los valores quedan guardados en nodo.atributos, que es el arbol anotado de
    la Seccion 5.1.2. Si hay ciclo no se evalua nada: se devuelve el ciclo.
    """
    nodos, indice, grafo = grafo_dependencias(raiz, reglas)
    orden, ciclo = orden_topologico(grafo)

    if ciclo is not None:
        return nodos, indice, [], ciclo

    # Numero de nodo -> nodo, para guardar los valores sin recorrer la lista.
    por_numero = {}

    for numero in range(len(nodos)):
        por_numero[numero + 1] = nodos[numero]

    # Que regla define cada atributo: se necesita para saber que funcion llamar.
    definidora = {}

    for nodo in nodos:
        if nodo.produccion is None:
            continue

        for regla in reglas[nodo.produccion]:
            posicion, atributo = regla['define']
            definidora[(indice[id(referenciado(nodo, posicion))], atributo)] = (nodo, regla)

    for vertice in orden:
        numero, atributo = vertice

        if vertice in definidora:
            nodo, regla = definidora[vertice]
            valores = []

            for posicion, usado in regla['usa']:
                valores.append(referenciado(nodo, posicion).atributos[usado])

            # El valor se guarda en el nodo del vertice, que puede no ser el nodo
            # de la regla: una regla de N define un atributo heredado de su hijo D.
            por_numero[numero].atributos[atributo] = regla['funcion'](*valores)

        else:
            # Sin regla definidora, es la lexval de una hoja: el caracter del terminal.
            nodo = por_numero[numero]
            nodo.atributos[atributo] = nodo.simbolo

    return nodos, indice, orden, None


# ---------------------------------------------------------------------------
# Textos de salida (paso 5 del enunciado).
# ---------------------------------------------------------------------------

def texto_arbol(nodos, indice):
    """Devuelve el arbol anotado como lista de lineas, un nodo por linea.

    Recibe: la lista de nodos en preorden y el diccionario de numeros.
    Devuelve: lista de textos, con dos espacios de sangria por nivel de
    profundidad y los atributos en orden alfabetico.

    La profundidad se calcula con una pila explicita, no con recursion.
    """
    lineas = []
    pila = [(nodos[0], 0)]

    while pila:
        nodo, profundidad = pila.pop()
        partes = []

        for atributo in sorted(nodo.atributos):
            partes.append(atributo + '=' + str(nodo.atributos[atributo]))

        lineas.append('  ' * profundidad + etiqueta(nodo, indice)
                      + ' [' + ', '.join(partes) + ']')

        for hijo in reversed(nodo.hijos):
            pila.append((hijo, profundidad + 1))

    return lineas


def texto_atributo(vertice, nodos, indice):
    """Texto de un atributo evaluado: etiqueta del nodo, punto y atributo (N#2.v).

    Recibe: el vertice (numero, atributo), la lista de nodos en preorden y el
    diccionario de numeros. El numero del vertice es la posicion en esa lista.
    """
    numero, atributo = vertice
    return etiqueta(nodos[numero - 1], indice) + '.' + atributo


def texto_ciclo(ciclo, nodos, indice):
    """Texto del ciclo detectado, con flechas entre los atributos que lo forman."""
    partes = []

    for vertice in ciclo:
        partes.append(texto_atributo(vertice, nodos, indice))

    return ' -> '.join(partes)


def valor_principal(raiz):
    """Valor del atributo principal del simbolo inicial (Seccion 3, paso 5)."""
    return raiz.atributos[ATRIBUTO_PRINCIPAL]
