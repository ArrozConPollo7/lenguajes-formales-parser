# Notas de trabajo

Indicaciones y decisiones que se acordaron durante el desarrollo del proyecto.
Están aquí para que el código se pueda sustentar y modificar en vivo sin
adivinar por qué está hecho así.

## Reglas de estilo

1. **Código simple y didáctico.** Sin patrones de diseño innecesarios, sin
   herencia compleja, sin decoradores, sin metaclases, sin *type hints*
   avanzados y sin *one-liners* crípticos. Funciones cortas, un solo propósito,
   bucles `for`/`while` claros, diccionarios, listas, conjuntos y clases
   pequeñas solo cuando aclaran.
2. **Comentarios y docstrings en español.** Cada función dice qué hace, qué
   recibe, qué devuelve y qué sección del libro sigue (por ejemplo
   «Sección 4.4.2»).
3. **El algoritmo se copia del libro**, no se «mejora». La fuente de verdad es
   el resumen de Aho et al. (4.4–5.2) que está en `docs/CONTEXTO_LIBRO.md`; si
   algo no está ahí, se consulta el libro, no otra fuente.

## Formato de entrada (sección 2.2 del enunciado)

- Primera línea: `n`, el número de no terminales.
- Luego `n` líneas `A -> alternativa1 alternativa2 ...`.
- Las alternativas se separan por **espacios**, así que `S -> AB` es un cuerpo
  de dos símbolos, no dos producciones.
- `e` es la cadena vacía (ε) y se guarda como tupla vacía.
- `$` lo agrega el programa; el usuario nunca lo escribe.
- El símbolo inicial es siempre `S`.
- Una letra del menú distinta de `T`, `B` o `Q` vuelve a imprimir el menú; se
  aceptan minúsculas.

## Textos exactos

El enunciado fija el formato carácter a carácter (dos puntos finales, comas,
espacios). Las pruebas comparan texto exacto, no «contiene»: si se agrega un
mensaje de bienvenida, un *prompt* o una línea en blanco, las pruebas fallan.

## Trampas que aparecieron

- **Alternativas repetidas.** Una gramática es un *conjunto* de producciones:
  `S -> a a` debe guardar un solo cuerpo. Si se guardan dos, cada uno recibe un
  índice distinto y aparecen falsos conflictos — LL(1) con dos entradas en
  `M[S, a]` y un reduce/reduce falso en SLR. La corrección son cuatro líneas en
  `grammar.py` y arregla los dos parsers a la vez.
- **Reduce de ε en SLR.** Con `len(cuerpo) == 0` hay que sacar **cero** estados
  de la pila. `del pila_estados[-0:]` en Python borra la pila entera, así que
  esa rama va explícita.
- **Producción aumentada al final.** `S' -> S` se agrega al final de la lista
  para no renumerar las producciones originales. Consecuencia: la numeración de
  estados no coincide con las figuras del libro (está documentado en el
  docstring).
- **`shift` solo para terminales.** Un no terminal después del punto no genera
  acción de `shift`; `accept` solo con `$` para `S' -> S.`; `GOTO` solo para no
  terminales.
- **`parsear_ll1` no traduce `e`.** La traducción de `e` a cadena vacía vive en
  `leer_cadenas`, que es la misma función que usa el modo SDD.
- **`parsear_ll1` no valida la tabla.** Con una tabla conflictiva y recursión
  por la izquierda no terminaría; `main` solo llama al parser cuando la
  gramática ya pasó la comprobación de LL(1).
- **Errata del Algoritmo 4.31 (libro p. 224).** El paso 1 impreso dice
  `FIRST(A)`; en realidad es `FIRST(α)`, el FIRST del cuerpo, como muestra el
  Ejemplo 4.32. `construir_tabla` usa `first_de_cadena(cuerpo, first)`, que es
  la versión correcta; no "corregir" el código para seguir el texto impreso.
- **Aceptación en el parser predictivo (Algoritmo 4.34, Fig. 4.20, pp. 226-227).**
  El bucle del libro termina cuando el tope es `$` y **no** vuelve a mirar la
  entrada, así que aceptaría `aa` con `S -> a`. Aquí se acepta solo si la pila
  quedó en `$` **y** el símbolo actual de la entrada es `$`; si sobran símbolos,
  se rechaza (la traza lo marca como «error: sobran simbolos»).

## Ítem 3: la SDD y su evaluador

Decisiones que hay que poder explicar en la sustentación.

- **La SDD es un dato.** `REGLAS[(cabeza, cuerpo)]` es una lista de reglas y cada
  regla dice qué atributo define, cuáles usa y con qué función se calcula. El
  evaluador (`grafo_dependencias`, `orden_topologico`, `evaluar`) no conoce esta
  gramática: cambiar la SDD es cambiar esa tabla. Las reglas se escriben por
  producción (cabeza y cuerpo) y `reglas_por_indice` las pasa a índices, porque el
  índice es lo que comparten los ítems LR(0), el parser y el árbol.
- **Los vértices del grafo son `(número de nodo, atributo)`**, no `id(nodo)`:
  con direcciones de memoria el orden topológico cambiaba entre ejecuciones y el
  orden impreso no se podía reproducir.
- **El valor se guarda en el nodo del vértice**, que no siempre es el nodo de la
  regla: en `N -> DN`, la regla `D.e = N.e` define un atributo heredado del hijo.
  Guardarlo en el nodo de la regla rompía la evaluación con un `KeyError` en el
  siguiente atributo que lo usaba.
- **Kahn para el orden, DFS con pila para el ciclo.** Si al final quedan vértices
  sin ordenar hay ciclo; se recorre el subgrafo restante con una pila y se
  reporta el tramo cerrado (`N#2.v -> D#3.e -> N#2.e -> N#2.v` con la SDD
  circular).
- **La gramática del ítem 3 se escribe `N -> DN e`**, no `N -> D N e`: el espacio
  separa alternativas, así que la segunda forma son tres producciones (`D`, `N`,
  `e`) y la gramática deja de ser LL(1): los conflictos aparecen en `M[N, a]`.
- **La SDD no es L-atribuida.** En `S -> N`, la regla `N.e = N.len - 1` define un
  atributo heredado con un sintetizado del mismo símbolo. Heredar con atributos
  del propio símbolo está permitido en general (5.1, pp. 304-305: un heredado de
  B puede usar atributos de la cabeza, de los hermanos y del propio B), pero la
  definición L-atribuida (5.2.4, pp. 313-314) lo prohíbe, y por eso es justamente
  el argumento de por qué se usa el método general del grafo: ninguna pasada
  única sobre el árbol evalúa esta SDD.
- **«El símbolo inicial no tiene heredados» es del enunciado**, no del libro: el
  libro no impone esa restricción. Se cumple aquí porque `S` solo tiene `v`, pero
  conviene no atribuírselo a Aho et al.
- **Salida del ítem 3**: por cada cadena aceptada, el árbol anotado (una línea por
  nodo, `simbolo#numero` y atributos en orden alfabético), el orden de evaluación
  y `S#1.v = valor`. Si la cadena no pertenece al lenguaje, solo `no`.

## Verificación

Las 93 pruebas se corren desde la raíz del proyecto y comparan la salida exacta
de los cuatro casos del enunciado, los conjuntos de `FIRST`/`FOLLOW`, los
parsers, el árbol anotado del ítem 3, el orden topológico, la detección de la SDD
circular y el cruce entre los dos parsers:

```bash
python3 tests/pruebas.py
```

## Errores del informe y de los ejemplos

- El ejemplo del README declaraba `2` no terminales con dos líneas de `S`, y
  partía el cuerpo `aSb` en dos alternativas. La forma correcta es `1` y
  `S -> aSb e`. Hay una prueba explícita del formato de las alternativas.
