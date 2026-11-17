# Contexto del libro (Aho et al., Compilers 2ª ed.): resumen de los algoritmos

Resumen propio de las secciones 4.4, 4.5, 4.6, 5.1 y 5.2. Sirve para que el código siga el libro.
En los comentarios del código se debe citar la sección (ej. "Sección 4.4.2").

Notación: ε = cadena vacía (en la entrada se escribe `e`), `$` = marcador de fin.

---

## 4.4.2 FIRST y FOLLOW

**FIRST(X)** = terminales con los que puede empezar una cadena derivada de X. Si X ⇒* ε, ε ∈ FIRST(X).

Reglas (repetir hasta que ningún conjunto cambie, es decir, hasta el punto fijo):
1. Si X es terminal: FIRST(X) = {X}.
2. Si X → ε es producción: agregar ε a FIRST(X).
3. Si X → Y1 Y2 ... Yk es producción:
   - agregar a FIRST(X) todo lo de FIRST(Y1) menos ε;
   - si ε ∈ FIRST(Y1), agregar también FIRST(Y2) menos ε; y así sucesivamente;
   - si ε ∈ FIRST(Yi) para TODOS los i, agregar ε a FIRST(X).

**FIRST de una cadena** X1 X2 ... Xn: igual que la regla 3: unir FIRST(Xi) menos ε mientras los anteriores
deriven ε; agregar ε solo si todos derivan ε. (La cadena vacía tiene FIRST = {ε}.)

**FOLLOW(A)** = terminales que pueden aparecer inmediatamente a la derecha de A en alguna forma sentencial.
Nunca contiene ε. Reglas (repetir hasta punto fijo):
1. `$` ∈ FOLLOW(S), con S el símbolo inicial.
2. Si hay producción A → α B β: agregar FIRST(β) menos ε a FOLLOW(B).
3. Si hay A → α B, o A → α B β con ε ∈ FIRST(β): agregar FOLLOW(A) a FOLLOW(B).

*Referencia (informe): libro pp. 220-222.*

---

## 4.4.3 Gramáticas LL(1) y tabla predictiva

**Construcción de la tabla M[A, a]**: para cada producción A → α:
1. Para cada terminal a en FIRST(α): M[A, a] = A → α.
2. Si ε ∈ FIRST(α): para cada b en FOLLOW(A) (incluye `$`): M[A, b] = A → α.
Las celdas sin producción son error.

**Algoritmo 4.31 (libro p. 224).**
Nota: el texto impreso del paso 1 dice FIRST(A); es una errata, lo correcto es FIRST(α), como
muestra el Ejemplo 4.32.

**Prueba de LL(1)**: la gramática es LL(1) si y solo si ninguna celda de M recibe dos producciones distintas.
(Equivale a: para A → α | β, FIRST(α) y FIRST(β) disjuntos; a lo sumo uno deriva ε, y si β ⇒* ε entonces
FIRST(α) ∩ FOLLOW(A) = ∅.) Se debe probar sobre la gramática tal cual, sin quitar recursión izquierda.
Una gramática recursiva por la izquierda o ambigua nunca es LL(1).

*Referencia (informe): Algoritmo 4.31, libro p. 224.*

## 4.4.4 Parser predictivo no recursivo (con pila)

- Pila inicial: `$` en el fondo y el símbolo inicial S arriba. Entrada: w$. Apuntador `ip` al primer símbolo.
- Sea X el tope de la pila y a el símbolo actual de la entrada. Repetir hasta X = `$`:
  - Si X = a: sacar X de la pila y avanzar ip.
  - Si X es otro terminal: error.
  - Si M[X, a] es error: error.
  - Si M[X, a] = X → Y1 Y2 ... Yk: sacar X y apilar Yk, ..., Y1 (Y1 queda arriba). Si la producción es X → ε, solo sacar X.
- Acepta si termina con pila = `$` y entrada = `$`.
- Para el SDD se puede construir el árbol de parseo al aplicar cada producción.

**Algoritmo 4.34 / Fig. 4.20 (libro pp. 226-227).** El bucle del libro
termina cuando X = `$` pero NO verifica que la entrada esté en `$`. El código debe aceptar solo si
la pila quedó en `$` Y el símbolo actual de la entrada es `$`; si no, rechazar.

*Referencia (informe): Algoritmo 4.34 y Fig. 4.20, libro pp. 226-227.*

---

## 4.5 Shift-reduce (contexto)

Un parser bottom-up reduce la entrada hacia S usando una pila de símbolos. Acciones: **shift** (mover el siguiente
terminal a la pila), **reduce** (reemplazar el cuerpo de una producción en el tope por su cabeza), **accept**, **error**.
Conflictos (4.5.4): **shift/reduce** y **reduce/reduce**. Si la tabla los tiene, la gramática no es de esa clase LR.

---

## 4.6.2 Ítems LR(0), CLOSURE, GOTO

- **Ítem LR(0)**: una producción con un punto en el cuerpo. A → α·β. Para A → ε solo existe A → ·.
- **Aumentar la gramática**: agregar S' → S, con S' nuevo símbolo inicial. (Usar un nombre que no choque con los
  símbolos de la entrada. Como todos los símbolos de entrada son de un solo carácter, un nombre como "S'" es seguro.)
- **CLOSURE(I)**: empezar con I. Mientras se pueda: si hay un ítem A → α·Bβ con B no terminal, agregar B → ·γ para
  cada producción B → γ que aún no esté.
- **GOTO(I, X)**: CLOSURE del conjunto de todos los ítems A → αX·β tales que A → α·Xβ está en I.
- **Colección canónica**: I0 = CLOSURE({S' → ·S}). Repetir: para cada conjunto I y cada símbolo X (terminal o no
  terminal) tal que GOTO(I, X) no sea vacío y sea nuevo, agregarlo. Cada conjunto es un estado del autómata.

*Referencia (informe): Fig. 4.32 (CLOSURE) y Fig. 4.33 (items(G')), libro pp. 242-246.*

## 4.6.4 Tabla SLR(1)

Para cada estado i (conjunto Ii):
1. Si A → α·aβ ∈ Ii (a terminal) y GOTO(Ii, a) = Ij: ACTION[i, a] = shift j.
2. Si A → α· ∈ Ii con A ≠ S': para cada a en FOLLOW(A): ACTION[i, a] = reduce A → α.
3. Si S' → S· ∈ Ii: ACTION[i, $] = accept.
4. Para cada no terminal A: si GOTO(Ii, A) = Ij entonces GOTO[i, A] = j.
Lo demás es error. Estado inicial = el que contiene S' → ·S.
**La gramática es SLR(1) si y solo si no hay celdas con dos acciones distintas** (conflictos).

*Referencia (informe): Algoritmo 4.46, libro pp. 253-254.*

## 4.6.3 Algoritmo de parsing LR

- Pila de estados, inicialmente [0]. Entrada w$.
- Sea s el estado en el tope y a el símbolo actual:
  - ACTION[s, a] = shift t: apilar t y avanzar.
  - ACTION[s, a] = reduce A → β: sacar |β| estados (0 si β = ε), sea t el nuevo tope, apilar GOTO[t, A]
    (para el árbol: crear un nodo A con los |β| hijos sacados).
  - accept: terminar con éxito. Error o celda vacía: rechazar.

*Referencia (informe): Algoritmo 4.44 y Fig. 4.36, libro pp. 250-251.*

---

## 5.1 Definiciones dirigidas por la sintaxis (SDD)

- A cada símbolo se le asocian **atributos**. Una SDD asocia a cada producción **reglas semánticas**.
- **Sintetizado**: atributo de la cabeza A de la producción, calculado desde atributos de los hijos y
  atributos (incluidos heredados) del propio nodo A.
- **Heredado**: atributo de un símbolo B del cuerpo, calculado desde atributos de la cabeza (padre), de
  los hermanos y del propio B (libro pp. 304-305).
- Los terminales solo tienen atributos sintetizados que da el scanner (aquí `lexval` = el carácter).
- El símbolo inicial no tiene atributos heredados: es una regla del enunciado, no del libro.
- **Árbol de parseo anotado**: árbol de parseo con los valores de los atributos en cada nodo.

*Referencia (informe): libro pp. 304-305.*

## 5.2 Grafo de dependencias y orden de evaluación

- **Grafo de dependencias**: un vértice por cada atributo de cada nodo del árbol. Para cada regla `b = f(c1, ..., ck)`
  de una producción (instanciada en un nodo), una arista de cada ci hacia b: **del atributo usado al atributo definido**.
- **Orden de evaluación**: cualquier **orden topológico** del grafo. Si el grafo tiene un ciclo, la SDD es **circular**
  y no existe orden válido.
- **S-atribuida**: solo atributos sintetizados (se puede evaluar en postorden / con un parser bottom-up).
- **L-atribuida**: cada atributo heredado de Xi en A → X1...Xn depende solo de (a) atributos heredados de A, o
  (b) atributos (heredados o sintetizados) de X1...X(i-1), o (c) atributos del propio Xi sin formar ciclos.
  Toda SDD S-atribuida es también L-atribuida.
- Aquí hay que implementar el método general (grafo + orden topológico), aunque la SDD sea L-atribuida.

*Referencias (informe): 5.2.1 pp. 310-311; 5.2.2 p. 312; 5.2.3 pp. 312-313; 5.2.4 pp. 313-314.*
