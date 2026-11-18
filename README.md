# Lenguajes Formales — LL(1) and SLR(1) parsers with an SDD evaluator

Course project for *Lenguajes Formales* (SI2002), Universidad EAFIT, November 2026. The program is
written in plain Python (standard library only: no parser generators and no
library that computes FIRST/FOLLOW sets, LR automata or parsing tables). It reads
a context-free grammar, computes `FIRST` and `FOLLOW`, decides whether the
grammar is **LL(1)** and/or **SLR(1)**, parses strings with the corresponding
algorithm, and evaluates a syntax-directed definition (SDD) on the parse tree
using the dependency-graph method. Every algorithm follows Aho, Lam, Sethi and
Ullman, *Compilers: Principles, Techniques, and Tools* (2nd edition):

| Part | Book |
|---|---|
| `FIRST` and `FOLLOW` by fixed point | 4.4.2, pp. 220-222 |
| LL(1) definition and predictive table `M[A, a]` | 4.4.3, Algorithm 4.31, p. 224 |
| Table-driven predictive parser with a stack | 4.4.4, Algorithm 4.34 and Fig. 4.20, pp. 226-227 |
| Shift-reduce parsing and conflicts | 4.5.4 |
| LR(0) items, `CLOSURE`, `GOTO`, canonical collection | 4.6.2, Fig. 4.32 and Fig. 4.33, pp. 242-246 |
| `ACTION`/`GOTO` tables of SLR(1) from `FOLLOW` | 4.6.4, Algorithm 4.46, pp. 253-254 |
| LR parsing algorithm | 4.6.3, Algorithm 4.44 and Fig. 4.36, pp. 250-251 |
| Synthesized and inherited attributes, annotated parse trees | 5.1.1, 5.1.2, pp. 304-305 |
| Dependency graphs and evaluation order | 5.2.1, pp. 310-311; 5.2.2, p. 312 |
| S-attributed and L-attributed definitions | 5.2.3, pp. 312-313; 5.2.4, pp. 313-314 |

The grammar is **never transformed**: it is tested as written, left recursion
included. If the grammar is left recursive it is not LL(1) and the program
reports it that way.

## Group members

- Juan David Giraldo Regino
- Camilo Andrés Rodríguez Agudelo
- Daniel Rojas Grajales

## Versions used

- Operating system: Windows 11 with WSL2, Ubuntu 24.04.2 LTS (also run on Linux).
- Programming language: Python 3. No third-party packages, only the standard
  library. Tested with Python 3.13.5 and Python 3.12.3.
- Other tools: Git 2.47.3. No parser generator, no parsing library, no build
  step.

## How to run

Nothing to install: only Python 3 is needed. Commands for Windows (PowerShell or cmd) and for
Linux/macOS are the same, except `py` becomes `python3`.

```powershell
git clone https://github.com/ArrozConPollo7/lenguajes-formales-parser.git
cd lenguajes-formales-parser
py main.py            # reads the grammar, decides LL(1) / SLR(1)
py main.py --sets     # prints FIRST and FOLLOW, then decides
py tests\pruebas.py   # 93 tests, exact-text comparison
```

```bash
python3 main.py            # same three commands on Linux/macOS
python3 main.py --sets
python3 tests/pruebas.py
```

The grammar is read from standard input in the format of Section 2.2 of the
assignment:

```
3
S -> AB
A -> aA d
B -> bBc e
```

- The first line is the number of nonterminals.
- Each following line is `A -> alternative1 alternative2 ...`; **alternatives are
  separated by blanks**, so `S -> AB` is **one** body with two symbols and
  `S -> A B` is two bodies (`A` and `B`). Symbols inside one alternative are
  written together, with no blank in between.
- `e` is the empty string (ε). The end marker `$` is added by the program.
- The start symbol is always `S`.

After the grammar the program behaves according to the four cases of Section
2.2.2. When the grammar is both LL(1) and SLR(1) it prints the menu

```
Select a parser (T: for LL(1), B: for SLR(1), Q: quit):
```

`T` parses with LL(1), `B` with SLR(1), `Q` ends the program. Strings are given
one per line and an empty line closes the list; the empty string is written `e`.
For each string the program prints `yes` or `no`.

### Example

```
$ printf '1\nS -> aSb e\nT\naabb\n\nQ\n' | python3 main.py
Select a parser (T: for LL(1), B: for SLR(1), Q: quit):
yes
```

(`1` is the number of nonterminals and both alternatives of `S` are written on
its single line: `aSb` and `e`.)

### Item 3: the SDD evaluator

The SDD is defined for its own grammar, which is stored in
`docs/gramatica_sdd.txt`:

```
3
S -> N
N -> DN e
D -> 0 1 2 3 4 5 6 7 8 9
```

It generates decimal numerals (leading zeros allowed) and the empty number, and
the SDD computes the integer value of the numeral. The grammar is read from
standard input like in Items 1 and 2, followed by the strings, so `--sdd` is used
with the grammar file prepended to the strings:

```bash
# LL(1) parser: the grammar file, then the strings, then an empty line
$ printf '101\n7\ne\n12x\n\n' | cat docs/gramatica_sdd.txt - | python3 main.py --sdd

# SLR(1) parser instead of LL(1)
$ printf '101\n\n' | cat docs/gramatica_sdd.txt - | python3 main.py --sdd --lr
```

On Windows, type the grammar and the strings by hand after `py main.py --sdd`, or prepend the file
with PowerShell:

```powershell
@(Get-Content docs\gramatica_sdd.txt) + @('101','7','') | py main.py --sdd
```

For the string `7` the output is:

```
$ printf '7\n\n' | cat docs/gramatica_sdd.txt - | python3 main.py --sdd
Annotated parse tree:
S#1 [v=7]
  N#2 [e=0, len=1, v=7]
    D#3 [e=0, v=7]
      7#4 [lexval=7]
    N#5 [e=-1, len=0, v=0]
Evaluation order:
  7#4.lexval
  D#3.v
  N#5.len
  N#2.len
  N#2.e
  D#3.e
  N#5.e
  N#5.v
  N#2.v
  S#1.v
S#1.v = 7
```

For every string the output is:

- `no` if the string is not generated by the grammar;
- otherwise the annotated parse tree, one node per line, indented by depth. Each
  node is labelled `symbol#number` (the number is the position of the node in
  preorder) and lists its attributes in alphabetical order;
- the evaluation order: one attribute per line, in the topological order of the
  dependency graph;
- the value of the main attribute of the start symbol, `S#1.v`.

If the dependency graph has a cycle the program prints `SDD is circular: ...`
with the attributes that form the cycle and stops, as required in Section 3,
step 5. The circular SDD needed by step 6 of the guide is loaded with:

```bash
$ printf '101\n' | cat docs/gramatica_sdd.txt - | python3 main.py --sdd --circular
SDD is circular: N#2.v -> D#3.e -> N#2.e -> N#2.v
```

Only one rule is changed: in `S -> N`, `N.e` is defined as `N.v` instead of
`N.len - 1`, so the value of the number ends up depending on itself.

### Optional visualizer

`visualizador.py` is a client of the modules above: it computes nothing, it only draws what
`first_follow`, `ll1`, `slr1` and `sdd` return. It uses only the standard library (an
`http.server` whose pages contain SVG generated in Python), so there is nothing to install and no
network access is needed.

```bash
python3 visualizador.py             # serves http://127.0.0.1:8000
python3 visualizador.py --puerto 8100
python3 visualizador.py --gramatica docs/gramatica_ejemplo.txt   # one grammar for every view
python3 visualizador.py --check     # draws every view without a browser (quick test)
```

It has five views that follow the explanation, each one with a plain-language "what am I looking
at" paragraph, the data, and the algorithm it comes from:

1. **Conjuntos** — FIRST and FOLLOW per nonterminal, FIRST of every production, and the fixed-point
   rules that compute them.
2. **Tablas** — the LL(1) table (click a cell to see why that production was chosen) and the
   ACTION/GOTO tables, with conflicting cells highlighted.
3. **Autómata** — the LR(0) states drawn as a graph, with the items of the selected state and where
   each symbol leads.
4. **Traza** — the parser step by step: stack, remaining input and action, next to the algorithm's
   pseudo-code with the line being executed highlighted, plus a plain-Spanish explanation of every
   action. Arrow keys move between steps and "Reproducir" plays the whole trace.
5. **SDD** — annotated tree, dependency graph and evaluation order, one attribute at a time.

Every view is a URL, so any step of the explanation can be reproduced exactly, for example
`/sdd?cadena=12&paso=5` or `/traza?parser=ll1&cadena=aabb&paso=7`. The visualizer never recomputes
anything: `main.py` and the five modules are untouched by it.

The visualizer does not change the behaviour of `main.py`: the output required by the assignment is
still produced by `python3 main.py`, as described above.

## Repository layout

```
grammar.py            grammar reader and utilities (ε, $, numbered production list)
first_follow.py       FIRST and FOLLOW by fixed point (4.4.2)
ll1.py                predictive table, LL(1) test and stack parser (4.4.3, 4.4.4)
slr1.py               LR(0) items, CLOSURE/GOTO, automaton, tables, LR parser (4.6.2, 4.6.4, 4.6.3)
sdd.py                the SDD as data, dependency graph, topological order, cycle detection (5.1, 5.2)
main.py               input/output, menu, and the modes --sets, --sdd, --sdd --lr, --sdd --circular
visualizador.py       optional visualizer: five didactic views (client only, standard library)
tests/pruebas.py      93 exact-text tests
docs/ENUNCIADO.md     assignment statement
docs/CONTEXTO_LIBRO.md summary of sections 4.4 to 5.2 of the book
docs/NOTAS.md         working notes and the traps we found (in Spanish)
docs/gramatica_sdd.txt   grammar of Item 3
docs/gramatica_ejemplo.txt  grammar used in the report for Items 1 and 2
Informe_Lenguajes_Formales.pdf   the report (Item 4), generated from Informe.tex
Informe.tex           LaTeX source of the report (optional in the submission)
figuras/              the figures used by Informe.tex (annotated tree, dependency graph, visualizer)
```

The report is written in LaTeX and compiled with `tectonic Informe.tex` (or
`pdflatex Informe.tex` twice); the figures are PNG files generated from the
program's own output.

## Implementation decisions

- **Repeated alternatives are stored once**: a grammar is a *set* of
  productions. Without this, `S -> a a` created two different indices for the
  same production and the program reported false LL(1) conflicts and a false
  reduce/reduce conflict in SLR.
- **The augmented production `S' -> S` is appended at the end** of the
  production list so the original indices do not change; those indices are the
  identity of an LR(0) item and of a semantic rule.
- **ε is stored as an empty tuple**, never as the character `'e'`. FIRST of
  strings, the item `A -> ·` and the reduction of an empty body then need no
  special case; it is written back as `e` when printing.
- **A reduce by an empty body pops zero states**: there is an explicit branch for
  `len(body) == 0`, because in Python `del stack[-0:]` deletes the whole stack.
- **Deterministic state numbering**: the item sets are `frozenset`, whose
  iteration order depends on hashing, so transitions are traversed with
  `sorted()`; otherwise the automaton printed in the report would not match the
  one the program builds.
- **The parse tree is built by both parsers** (`ll1.Nodo`), so the SDD works
  with either one, and the same string produces the same tree with LL(1) and with
  SLR(1).
- **The SDD is data, not code**: for each production there is a list of rules,
  and each rule has the attribute it defines, the attributes it uses and the
  function that computes it. The evaluator knows nothing about this particular
  SDD. The rules are keyed by the production as written (head and body) and then
  converted to production indices, so a rule cannot be attached to the wrong
  production.
- **No recursion over the tree or over the string**: all traversals use an
  explicit stack. The Item 3 grammar is right recursive, so a long numeral
  produces a very deep tree and Python recursion would fail.
- **The predictive parser checks both ends (Algorithm 4.34, pp. 226-227)**: the
  book's loop stops as soon as the top of the stack is `$` and never looks at the
  input again, so it accepts `aa` with the grammar `S -> a`. Here the parse is
  accepted only if the stack is `$` **and** the current input symbol is `$`;
  otherwise the string is rejected as having symbols left over.
- **Attribute dependencies follow 5.1 (pp. 304-305)**: a synthesized attribute of
  `A` may use attributes of the children and of `A` itself, inherited ones
  included; an inherited attribute of `B` may use attributes of the head, of the
  siblings and of `B` itself. The SDD of Item 3 is **L-attributed but not
  S-attributed**: in `S -> N` the inherited `N.e` is defined from `N.len`, a
  synthesized attribute of the same symbol, which clause (c) of 5.2.4 allows as
  long as those attributes do not form a cycle (here `len` does not depend on
  `e`). It is still evaluated with the general method, because `N.len -> N.e`
  goes up inside one node and a single pass cannot compute it. The rule "the start
  symbol has no inherited attributes" comes from the assignment, not from the
  book.

## Tests

```powershell
py tests\pruebas.py                 # all 93 tests
py tests\pruebas.py ll1 sdd         # only those groups
py tests\pruebas.py -v              # every check with what it compares
py tests\pruebas.py --demo          # one example end to end, step by step
py tests\pruebas.py --lista         # group names
```

```bash
python3 tests/pruebas.py            # the same on Linux/macOS
```

Each test compares exact text against a fixed expected output. The groups can be run on their own,
which is useful to show one part at a time:

| Group | Checks | What it covers |
|---|---|---|
| `item1` | 12 | FIRST/FOLLOW sets, including the fixed point and the `--sets` output |
| `ll1` | 16 | predictive table, conflicts and the LL(1) parser |
| `slr` | 28 | LR(0) items, CLOSURE/GOTO, automaton, ACTION/GOTO and the LR parser |
| `main` | 11 | `main.py` and its modes (`--sets`, `--sdd`, `--sdd --lr`, `--sdd --circular`) |
| `sdd` | 26 | SDD values, annotated tree, dependency graph and evaluation order |

`--demo` is the one to use in the presentation: it reads the example grammar, prints its
FIRST/FOLLOW sets, says which parser applies, and then walks the SLR(1) parse of `x;[x]` one step per
line (state stack, symbols, remaining input, action) until it accepts. `-v` does the same for each
individual check: it shows what the test compares, with tables drawn as tables. `--completo` stops
`-v` from cropping long outputs.

The script prints `OK`/`FAIL` per check and a final count, and exits with code 1 if anything fails.
Run it from the root of the project (the tests read `docs/` and run `main.py` as a subprocess).

Between them the 93 checks cover the four output cases of the assignment, the `--sets` output, the
LL(1) tables, the SLR(1) tables and automaton sizes, the engines on several grammars, the SDD
values, the annotated tree and evaluation order, the topological order itself, the cross-check
between both parsers and the circular-SDD detection.

## Use of AI tools

Following Section 1 of the assignment, we declare the generative AI tools we
used and what for:

- **Claude (Anthropic)**: used as a reading aid to clarify concepts of Aho et
  al. that we found difficult (fixed point of FIRST/FOLLOW, the difference
  between S-attributed and L-attributed definitions, the direction of the edges
  of the dependency graph). We checked every explanation against the book.
- **Hermes Agent**: used as support for the code — locating bugs, reviewing the
  implementation, writing the interface of the optional visualizer (its HTTP layer,
  its HTML and its SVG drawing, which contain no algorithmic logic: the visualizer
  only draws what the modules return), and helping to draft this README and the
  report.

We did not use AI tools to replace the reading of the book or the hand-worked
examples: the FIRST/FOLLOW sets and tables in the report were computed by the
program and verified by hand.
