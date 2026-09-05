# Linguistic Inspiration

## Where the Language Borrows From Natural Language

The Aster is not a transliteration of any human
language.  It borrows *structural intuitions* — the way meaning flows — from
several linguistic traditions, particularly Algonquian languages.

---

## Algonquian Verb-Centrality

In languages such as Cree, Ojibwe, and Inuktitut, the verb is the core of
the utterance.  Nouns are not independent agents but *participants* in an
event described by the verb.

Consider the Cree sentence for "the dog sees the man":

> The dog-sees-the man  *(roughly: the event of seeing, with dog as agent and man as patient)*

The **event** is primary.  The participants attach to it.

In Aster:

```
action learn(dataset -> model)
```

`learn` is the event.  `dataset` and `model` are its participants.  The
arrow encodes the **animacy direction**: who acts upon whom.

---

## Animacy and Directionality

Algonquian languages encode a distinction between **animate** and **inanimate**
nouns, which affects verb agreement and sentence structure.

The `->` relation in this language is a simplified echo of that directionality:
it says not just that two things are connected, but *which one flows into which*.

This makes the relation graph naturally directional and causally meaningful.

---

## Compound Semantic Tokens

Many polysynthetic languages (including Algonquian ones) build complex meanings
by compounding morphemes.  A single word can encode what English requires a
full clause to say.

The morphology system in this language allows compound tokens:

```
data-stream-ingest
model-train-cycle
memory-context-bind
```

Each unit (`data`, `stream`, `ingest`) maps to a meaning primitive.  The
compound token expresses a *composite concept* — just as a polysynthetic verb
expresses a composite event.

See [`language/grammar/morphology.json`](../language/grammar/morphology.json)
for the full morphology definition.

---

## Structured Thought as Code

The deeper inspiration is this observation:

> Natural languages evolved to express how humans *think about* the world —
> entities, events, relationships, cycles.  Programming languages evolved
> to express how machines *execute* instructions.

The Aster attempts to close that gap.  Code in this
language reads like **structured thought** rather than machine commands.

```
entity knowledge
entity question

action infer(question -> knowledge)
```

This is closer to *"questions lead to knowledge through inference"* than to
*"call function infer with arguments question and knowledge"*.

---

## Further Reading

- [Language Philosophy](language_philosophy.md) — the core design principles
- [Architecture](architecture.md) — how the linguistic ideas map to code
- Mithun, M. (1999). *The Languages of Native North America*. Cambridge University Press.
- Wolfart, H. C. (1996). *Sketch of Cree, an Algonquian Language*. In *Handbook of North American Indians*, Vol. 17.
