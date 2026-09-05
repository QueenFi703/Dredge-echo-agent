# Architecture

## Overview

The Aster is implemented as a layered pipeline that
transforms `.co` source files into semantic graphs, coherence reports, and
target-language output.

```
.co source
    │
    ▼
┌─────────────┐
│  Tokenizer  │  language/parser/tokenizer.py
└──────┬──────┘
       │ token stream
       ▼
┌─────────────┐
│   Parser    │  language/parser/parser.py
└──────┬──────┘
       │ AST (ast_builder.py nodes)
       ▼
┌──────────────────┐
│ Semantic Analysis│
│  entity_model    │  language/semantics/entity_model.py
│  action_model    │  language/semantics/action_model.py
│  relation_graph  │  language/semantics/relation_graph.py
└────────┬─────────┘
         │ semantic models + relation graph
         ▼
┌──────────────────┐
│ Coherence Engine │  language/runtime/coherence_engine.py
└────────┬─────────┘
         │ CoherenceReport
         ▼
┌──────────────────┐        ┌───────────────────┐
│   Interpreter    │        │    Transpiler      │
│  (runtime exec.) │        │  compiler/         │
│  runtime/        │        │  transpiler.py     │
│  interpreter.py  │        │  → Python          │
└──────────────────┘        │  → Rust            │
                            │  → JavaScript      │
                            │  → Neural pipeline │
                            └─────────┬──────────┘
                                      │
                            ┌─────────▼──────────┐
                            │     Optimizer       │
                            │  compiler/          │
                            │  optimizer.py       │
                            └────────────────────┘
```

---

## Directory Structure

```
QueenFi703Be-operational-coherence
│
├── language/
│   ├── grammar/
│   │   ├── syntax.ebnf          # Formal grammar definition
│   │   └── morphology.json      # Compound-token morphology rules
│   │
│   ├── parser/
│   │   ├── tokenizer.py         # Lexical analysis
│   │   ├── parser.py            # Recursive-descent parser
│   │   └── ast_builder.py       # AST node definitions
│   │
│   ├── semantics/
│   │   ├── entity_model.py      # Registry of declared entities
│   │   ├── action_model.py      # Registry of declared actions
│   │   └── relation_graph.py    # Directed semantic graph
│   │
│   └── runtime/
│       ├── interpreter.py       # End-to-end execution engine
│       └── coherence_engine.py  # Semantic coherence validation
│
├── bridge/
│   ├── python_adapter.py        # Bind .co actions to Python functions
│   ├── rust_adapter.rs          # CoAction trait for Rust targets
│   ├── js_adapter.js            # CoRuntime for JavaScript/Node.js
│   └── llm_adapter.py           # Drive LLMs from .co action declarations
│
├── compiler/
│   ├── transpiler.py            # Multi-target code generator
│   └── optimizer.py             # Graph-level optimisations
│
├── examples/
│   ├── ai_training.co           # AI training pipeline example
│   ├── data_pipeline.co         # Multi-stage data processing example
│   └── simulation.co            # Agent-based simulation example
│
└── docs/
    ├── language_philosophy.md   # Why this language exists
    ├── linguistic_inspiration.md# Algonquian morphology connection
    └── architecture.md          # This document
```

---

## Layer Descriptions

### 1. Grammar Layer (`language/grammar/`)

Defines the language formally.

- **`syntax.ebnf`** — The complete EBNF grammar.  Every valid `.co` program
  can be derived from the `program` non-terminal.
- **`morphology.json`** — Meaning units and composition rules for compound
  tokens like `data-stream-ingest`.

### 2. Parser Layer (`language/parser/`)

Transforms source text into an AST.

| Module | Responsibility |
|--------|----------------|
| `tokenizer.py` | Breaks source into typed tokens |
| `ast_builder.py` | Defines AST node dataclasses |
| `parser.py` | Recursive-descent parser → AST |

### 3. Semantics Layer (`language/semantics/`)

Builds structured models from the AST.

| Module | Responsibility |
|--------|----------------|
| `entity_model.py` | Tracks declared entities |
| `action_model.py` | Tracks declared actions and their relations |
| `relation_graph.py` | Directed graph of entity→action→entity triples |

### 4. Runtime Layer (`language/runtime/`)

Validates and executes programs.

| Module | Responsibility |
|--------|----------------|
| `coherence_engine.py` | Checks semantic validity before execution |
| `interpreter.py` | Ties parsing + semantics + execution together |

### 5. Compiler Layer (`compiler/`)

Generates target-language code from the semantic graph.

| Module | Responsibility |
|--------|----------------|
| `transpiler.py` | Emits Python, Rust, JavaScript, or neural notation |
| `optimizer.py` | Applies graph-level optimisations before code generation |

### 6. Bridge Layer (`bridge/`)

Connects `.co` programs to external runtimes.

| Module | Responsibility |
|--------|----------------|
| `python_adapter.py` | Bind Python callables to .co actions |
| `rust_adapter.rs` | `CoAction` trait + `ActionRegistry` for Rust |
| `js_adapter.js` | `CoRuntime` class for Node.js / browser |
| `llm_adapter.py` | Prompt-based LLM integration |

---

## Data Flow Example

For the program:

```
entity data
entity model
action train(data -> model)
cycle training { train }
```

1. **Tokenizer** emits:
   `ENTITY "data"`, `ENTITY "model"`, `ACTION "train"`, `LPAREN`, `IDENTIFIER "data"`,
   `ARROW`, `IDENTIFIER "model"`, `RPAREN`, `CYCLE "training"`, `LBRACE`, `IDENTIFIER "train"`, `RBRACE`

2. **Parser** builds:
   `Program([EntityDecl("data"), EntityDecl("model"), ActionDecl("train", Relation("data","model")), CycleDecl("training", [ActionCall("train")])])`

3. **Semantic analysis** produces:
   - `EntityModel`: `{data, model}`
   - `ActionModel`: `{train: data->model}`
   - `RelationGraph`: `data --train--> model`

4. **Coherence engine** verifies: all references resolve, no isolated nodes,
   cycle body is non-empty → `CoherenceReport(is_coherent=True)`

5. **Interpreter** executes: logs `[cycle:training] execute train(data -> model)`

6. **Transpiler** generates (Python):
   ```python
   data = None
   model = None

   def train(data, model):
       return model

   def cycle_training():
       train(data, model)
   ```
