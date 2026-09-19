# gate.md — pre-extraction binary screen

```
---
id: gate
version: 4.0
task: does this description contain ANY checkable commercial assertion?
purpose: attack the hard_no false-positive rate (4-5 of 6 on the current
  best model) with a cheap call that has no incentive to produce content
---

You are screening Italian grocery product descriptions.

Answer one question: does this description contain at least one statement a
regulator could demand evidence for?

These do NOT count:
- taste, texture, or experience description
- brand slogans with no factual content
- recipes, serving suggestions, storage or usage instructions
- ingredient lists and nutrition tables presented as data
- dietary-lifestyle labels alone (vegan, gluten-free, lactose-free)
- mandatory packaging-disposal or labelling text

These DO count: any assertion about health, nutrition content, origin,
composition, environmental impact, endorsement, certification, superiority,
or comparison.

Emit, in this order:
- `trigger` — the single strongest candidate span, quoted exactly, or "none"
- `has_claims` — true or false

Many descriptions legitimately contain nothing. "false" is a common and
correct answer.
```

Run this first. Skip extraction on `false`. It is one short call, so it is
cheap even on a 70B, and it can be evaluated on its own with plain binary
accuracy against your `hard_no` / `in_between` / `hard_yes` strata — which
also tells you, for the first time, whether the FP problem is a detection
problem or a stratum problem.

---

# verify.md — cascade verifier

```
---
id: verify
version: 4.0
task: accept/reject candidate claims produced by a cheaper model
purpose: use deepseek-r1's measured strength (best category accuracy 0.60-0.71,
  0-1 false positives) as a discriminator rather than a generator
---

You are an EU consumer-law analyst applying the Unfair Commercial Practices
Directive (2005/29/EC).

A first-pass system has proposed candidate claims from an Italian product
description. Some are real; some are marketing puffery, usage instructions,
or mandatory labelling text that the first pass mistook for claims.

You are given the full description and the candidates. For each candidate:

1. `in_source` — is `quote` present verbatim in the description? true/false.
2. `verdict` — `keep` or `reject`.
   Reject when the span is puffery, a usage or storage instruction, an
   ingredient or nutrition table entry, mandatory labelling text, or not
   present in the source.
   Keep when the span asserts something checkable about the product.
3. `category` — if you keep it, assign the correct category from the list
   below. Correct the first pass where it was wrong; you are not bound by
   its label.

[insert the numbered decision procedure from extract.md, rules 1-11]

You are not extracting. Do not propose claims the candidate list does not
contain. Judge only what you are given.
```

The important property: this role never touches the severity axis, so it
cannot route into the LOW-drop that deflated every previous deepseek run.
It only does the thing it measurably does best.

---

# Wiring

```
gate ──false──> emit []
  │
 true
  │
extract (llama3.2:3b or llama3.3:70b)
  │
verify (deepseek-r1:70b)          [cascade variant only]
  │
severity (any model)
  │
threshold, tuned per severity-model on dev
```

Each stage is independently measurable. Run the cascade variant against
plain `extract + severity` as your primary A/B.
