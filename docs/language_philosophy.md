# Language Philosophy

## Why a New Language?

Most programming languages answer the question: **"How do I tell a computer what to do?"**

The Aster asks a different question: **"How do I express what a system *means*?"**

This shift — from instruction to meaning — is the philosophical core of the language.

---

## Semantic-First Programming

Traditional languages parse **syntax** first and derive meaning second.

In this language, meaning is primary.  The grammar is designed so that every
valid program is also a **statement about the world**:

- `entity dataset` declares that *a dataset exists*.
- `action learn(dataset -> model)` declares that *learning transforms data into knowledge*.
- `cycle training { ... }` declares that *training repeats these transformations*.

The code is not a recipe for a machine.  It is a **description of a system**.

---

## The Four Pillars

### 1. Entities — Things That Exist

Entities are the nouns of the language.  They represent anything that can hold
state or be transformed: datasets, models, queues, services, agents.

An entity has no behaviour.  It simply *is*.

### 2. Actions — Things That Happen

Actions are the verbs.  Each action declares a directed transformation:
something flows *from* a source entity *to* a target entity.

```
action learn(dataset -> model)
```

The direction matters.  It encodes causality.

### 3. Relations — How Things Affect Each Other

The `->` arrow is not just syntax.  It is a **semantic claim**: the source
influences the target.  The collection of all relations forms a directed
graph — the *meaning graph* of the program.

### 4. Cycles — Repeating Processes

Cycles express that certain sequences of actions are not one-off procedures
but **ongoing rhythms**: training loops, pipeline runs, simulation ticks.

---

## Coherence as a First-Class Concern

Before executing any action, the coherence engine asks:

- Are all referenced entities declared?
- Are all called actions defined?
- Does every entity participate in at least one relation?
- Do cycles have meaningful bodies?

A program that fails coherence is not just buggy — it is *incoherent*.  It
makes claims that contradict themselves.

This mirrors an insight from linguistics: **an utterance that violates semantic
rules is not just grammatically wrong — it is meaningless**.

---

## Linguistic Inspiration

Many Algonquian languages are **verb-central**: the verb carries most of the
meaning, and nouns attach to it as participants.  The sentence is not built
around a subject performing an action but around the **event itself**.

This language borrows that intuition.  Actions are not called on objects;
they describe transformations in which entities *participate*.

See [linguistic_inspiration.md](linguistic_inspiration.md) for a deeper
exploration of this connection.

---

## What This Language Is Not

- It is not a general-purpose programming language.
- It is not a query language.
- It is not a configuration format.

It is a **semantic meta-language** — a way to express the *shape of a system*
that can then be translated into any target language or model.
