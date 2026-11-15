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

## Verificación

Las 64 pruebas se corren desde la raíz del proyecto y comparan la salida exacta
de los cuatro casos del enunciado, los conjuntos de `FIRST`/`FOLLOW` y los
parsers sobre gramáticas de prueba:

```bash
python3 tests/pruebas.py
```
