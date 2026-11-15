# Lenguajes Formales — parser LL(1) y SLR(1)

Proyecto de Lenguajes Formales en Python puro (solo biblioteca estándar, sin
generadores de parsers ni dependencias externas). Lee una gramática libre de
contexto, calcula `FIRST` y `FOLLOW`, decide si es **LL(1)** y/o **SLR(1)**, y
parsea cadenas con el algoritmo que corresponda siguiendo el libro de Aho,
Lam, Sethi y Ullman (2.ª edición):

- **4.4.2** conjuntos `FIRST` y `FOLLOW` por punto fijo.
- **4.4.3** definición de LL(1) y tabla predictiva `M[A, a]`.
- **4.4.4** parser predictivo no recursivo con pila y árbol de análisis.
- **4.6.2** ítems LR(0), `CLOSURE`, `GOTO` y colección canónica.
- **4.6.4** tablas `ACTION` y `GOTO` de SLR(1) a partir de `FOLLOW`.
- **4.6.3** parser LR (shift-reduce con pila de estados).

La gramática **no se transforma**: se prueba tal cual, con recursión por la
izquierda incluida. Si es recursiva por la izquierda no será LL(1) y el
programa lo reporta como tal.

## Cómo se ejecuta

No hay nada que instalar: Python 3 y listo.

```bash
python3 main.py            # lee la gramática y decide LL(1) / SLR(1)
python3 main.py --sets     # imprime FIRST y FOLLOW antes de decidir
python3 tests/pruebas.py   # 64 pruebas con texto exacto
```

La gramática se lee de la entrada estándar, en el formato de la sección 2.2 del
enunciado:

```
3
S -> AB
A -> aA d
B -> bBc e
```

- La primera línea es el número de no terminales.
- Cada línea es `A -> alternativa1 alternativa2 ...`; las alternativas van
  separadas por espacios, así que `S -> AB` es **un** cuerpo de dos símbolos.
- `e` es la cadena vacía (ε). El `$` de fin de entrada lo agrega el programa.
- El símbolo inicial es siempre `S`.

Después de la gramática viene el menú:

```
Select a parser (T: for LL(1), B: for SLR(1), Q: quit):
```

`T` parsea con LL(1), `B` con SLR(1) y `Q` termina. Las cadenas se escriben una
por línea y una línea vacía cierra la lista. Si la gramática no es del tipo
pedido, el programa avisa y no parsea.

## Ejemplo

```
$ printf '2\nS -> aS b\nS -> e\nT\naabb\n\nQ\n' | python3 main.py
Select a parser (T: for LL(1), B: for SLR(1), Q: quit):
yes
```

## Estructura

```
grammar.py        lectura de la gramática y utilidades (ε, $, lista de producciones)
first_follow.py   FIRST y FOLLOW por punto fijo (4.4.2)
ll1.py            tabla predictiva, detección de conflictos y parser con pila (4.4.3, 4.4.4)
slr1.py           ítems LR(0), CLOSURE/GOTO, automáta, tablas y parser (4.6.2, 4.6.4, 4.6.3)
main.py           entrada/salida, menú y árbol de análisis
tests/pruebas.py  64 pruebas de texto exacto
docs/             enunciado del curso y notas de trabajo
```

## Decisiones de implementación

- Las alternativas repetidas se guardan una sola vez: una gramática es un
  **conjunto** de producciones. Sin esto, `S -> a a` generaba dos índices
  distintos para la misma producción y el programa reportaba falsos conflictos
  LL(1) y reduce/reduce en SLR.
- La producción aumentada `S' -> S` se agrega **al final** de la lista para no
  renumerar las producciones originales.
- En un reduce con cuerpo vacío (ε) se sacan **cero** estados de la pila: hay
  una rama explícita para `len(cuerpo) == 0`, porque en Python
  `del pila[-0:]` borra la pila entera.
- `shift` solo se genera para terminales, `accept` solo con `$` para `S' -> S.`
  y `GOTO` solo para no terminales.

Ver `docs/NOTAS.md` para las indicaciones de trabajo que se acordaron durante
el desarrollo.
