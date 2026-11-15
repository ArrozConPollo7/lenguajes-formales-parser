"""
Lectura de una gramatica libre de contexto en el formato de la Seccion 2.2
del enunciado del proyecto.

Formato de entrada:

    n
    <no terminal> -> <alternativa1> <alternativa2> ...

Convenciones que fija el enunciado (Seccion 2.2):

  - El simbolo inicial es siempre la letra 'S'.
  - Los no terminales son letras mayusculas.
  - Los terminales son un solo caracter y nunca una letra mayuscula.
  - La cadena vacia (epsilon) se escribe 'e' y NO es un terminal valido.
  - El marcador de fin '$' tampoco es un terminal valido.

Decision de representacion: una produccion con cuerpo epsilon se guarda con
la tupla vacia (). Asi el resto del programa (FIRST de cadenas, items LR(0),
reducciones del parser LR) no necesita un caso especial para epsilon: una
cadena vacia es simplemente una secuencia de cero simbolos. Al imprimir se
vuelve a escribir como 'e' (ver formatear_cuerpo).
"""

# Simbolo con el que se escribe la cadena vacia en la entrada.
EPSILON = 'e'

# Marcador de fin de la cadena de entrada. El programa lo agrega, nunca viene en la entrada.
FIN = '$'

# Simbolo inicial de toda gramatica de entrada (Seccion 2.2).
INICIAL = 'S'

# Nombre del simbolo inicial de la gramatica aumentada (Seccion 4.6.2).
# No choca con ningun simbolo de entrada porque todos son de un solo caracter.
AUMENTADO = "S'"


def leer_gramatica(flujo):
    """Lee una gramatica completa desde 'flujo' (un archivo o sys.stdin).

    Recibe: un objeto con readline() del cual se leen n y luego n lineas.
    Devuelve: un diccionario {no_terminal: [cuerpo1, cuerpo2, ...]} donde cada
    cuerpo es una tupla de simbolos, o None si no habia entrada.
    Sigue la Seccion 2.2 del enunciado (formato de entrada).

    Los diccionarios de Python conservan el orden de insercion, asi que el
    diccionario mantiene el orden en que aparecen las lineas y las alternativas.
    """
    primera = flujo.readline()

    # Sin entrada no hay gramatica: el programa principal simplemente termina.
    if primera.strip() == '':
        return None

    # Primera linea: cantidad de no terminales.
    n = int(primera.strip())

    gramatica = {}

    for _ in range(n):
        linea = flujo.readline()

        # La linea tiene la forma "A -> alternativas". Se corta en la primera
        # flecha: a la izquierda queda la cabeza y a la derecha el resto.
        if '->' not in linea:
            raise ValueError("Falta '->' en la produccion: " + linea.strip())

        izquierda, derecha = linea.split('->', 1)
        cabeza = izquierda.strip()

        # La cabeza debe ser un unico no terminal: una letra mayuscula.
        if len(cabeza) != 1 or not cabeza.isupper():
            raise ValueError("Cabeza de produccion invalida: " + repr(cabeza))

        cuerpos = []

        # Las alternativas vienen separadas por espacios en blanco.
        # split() sin argumentos tolera varios espacios y espacios al final.
        for alternativa in derecha.split():

            if alternativa == EPSILON:
                # 'e' sola es la cadena vacia: cuerpo de cero simbolos.
                cuerpo = ()
            else:
                # Cada caracter de la alternativa es un simbolo de la gramatica
                # (los simbolos son de un solo caracter, Seccion 2.2).
                cuerpo = tuple(alternativa)

            # Una gramatica es un CONJUNTO de producciones: si la misma
            # alternativa aparece repetida en la linea (por ejemplo S -> a a),
            # se guarda una sola vez. Si no, la tabla de la Seccion 4.4.3
            # contaria dos producciones distintas donde solo hay una y diria que
            # la gramatica no es LL(1) cuando el libro dice que si lo es.
            if cuerpo not in cuerpos:
                cuerpos.append(cuerpo)

        gramatica[cabeza] = cuerpos

    return gramatica


def lista_producciones(gramatica):
    """Devuelve las producciones numeradas como lista [(cabeza, cuerpo), ...].

    Recibe: la gramatica (diccionario de leer_gramatica).
    Devuelve: lista de producciones en el orden de la entrada.

    El indice de una produccion en esta lista es su identidad en el resto del
    programa: los items LR(0) de la Seccion 4.6.2 son (indice, posicion del
    punto) y las reglas semanticas del SDD se asocian a una produccion.
    """
    producciones = []

    for cabeza in gramatica:
        for cuerpo in gramatica[cabeza]:
            producciones.append((cabeza, cuerpo))

    return producciones


def no_terminales(gramatica):
    """Lista de no terminales en orden alfabetico.

    Es el orden en que la Seccion 2.1 pide imprimir los conjuntos con --sets.
    """
    return sorted(gramatica.keys())


def terminales(gramatica):
    """Lista de terminales de la gramatica en orden ASCII.

    Recibe: la gramatica.
    Devuelve: lista ordenada de los simbolos de los cuerpos que no son no
    terminales. Como todos son de un caracter, sorted() los deja en orden
    ASCII, que es el que pide la Seccion 2.1.

    Nota: 'e' nunca aparece aqui, porque se convirtio en cuerpo vacio al leer.
    """
    conjunto = set()

    for cuerpo in gramatica.values():
        for alternativa in cuerpo:
            for simbolo in alternativa:
                # Un simbolo que no esta en el diccionario es un terminal.
                if simbolo not in gramatica:
                    conjunto.add(simbolo)

    return sorted(conjunto)


def es_epsilon(cuerpo):
    """Devuelve True si el cuerpo es la cadena vacia (produccion A -> e)."""
    return len(cuerpo) == 0


def formatear_cuerpo(cuerpo):
    """Texto legible de un cuerpo, para mensajes y trazas.

    Recibe: una tupla de simbolos.
    Devuelve: los simbolos pegados (por ejemplo 'S+T') o 'e' si es vacio.
    """
    if len(cuerpo) == 0:
        return EPSILON

    return ''.join(cuerpo)
