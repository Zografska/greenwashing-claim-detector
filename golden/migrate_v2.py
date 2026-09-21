#!/usr/bin/env python3
"""Migrate golden_set_coop_ucpd_250.json from v1 to v2 (schema_version 1).

Re-runnable and diffable: it always rebuilds v2 from the v1 snapshot plus the
adjudicated verdicts, so running it twice produces identical output.

    python3 migrate_v2.py [--dry-run]

Inputs
    golden_set_coop_ucpd_250.json        v1, if the .v1.json backup does not exist yet
    golden_set_coop_ucpd_250.v1.json     the immutable v1 snapshot (created on first run)
    audit_work/merged_verdicts.json      adjudicated verdicts, keyed "<product_id>#<claim index>"

Outputs
    golden_set_coop_ucpd_250.json        v2
    discarded_claims_v2.json             every removed claim, with reason code
    migration_report_v2.md               diff stats and validator result

Guarantees, all asserted:
    * v1 is preserved on disk and never rewritten once it exists
    * claims_v1 == claims_v2 + discarded          (nothing vanishes unlogged)
    * every retained claim_text is byte-identical to v1 (no normalise/trim/re-case)
    * no product record is dropped, including those whose every claim was discarded
    * every output record passes validate_v2.py
"""
import json, os, shutil, sys, collections

SRC        = "golden_set_coop_ucpd_250.json"
V1         = "golden_set_coop_ucpd_250.v1.json"
VERDICTS   = "audit_work/merged_verdicts.json"
DISCARD_LOG = "discarded_claims_v2.json"
BADGE_GAP   = "audit_work/badge_claims_to_add.json"
REPORT     = "migration_report_v2.md"

SCHEMA_VERSION = 1      # new counter, started at 0 for v1 per the Phase 0 gate
GENERATION     = "v2"   # dataset generation label, deliberately independent of schema_version

# Fields removed per the brief's section 4. recycling_other is migrated to source_text first.
DROP = ["recycling", "recycling_other", "matched_signals",
        "legit_or_disclosed_basis_detected", "heuristic_bucket", "redo_schema_version"]

# Claims v1 never extracted. v1's extractor took Coop's own line marks (VIVI VERDE 93%,
# FIOR FIORE 100%) but no third-party certification (BIOLOGICO 0/28, FSC 0/1, SOLIDAL 0/1) —
# backwards for an ECGT detector, since a certification badge is an etichetta di sostenibilita
# under Art. 18 n-sexies while a retailer line mark is not. Found by blind re-extraction,
# adjudicated 2026-09-20. VEGANO deliberately excluded: dietary suitability, not n-sexies.
BADGE_SPEC = {
    "BIOLOGICO": {
        "scheme": "agricoltura biologica (Reg. (UE) 2018/848)",
        "question": ("Il logo biologico UE, il codice dell'organismo di controllo e il codice "
                     "operatore sono presenti in confezione, e la certificazione e in corso di validita?"),
        "rationale": ("Etichetta di sostenibilita esibita in confezione: l'art. 23, lett. b-bis "
                      "rende regolata l'esibizione, quindi occorre verificare lo schema sottostante."),
    },
    "FOREST STEWARDSHIP COUNCIL": {
        "scheme": "FSC",
        "question": ("Il marchio FSC e il codice di licenza sono presenti in confezione, e il "
                     "certificato di catena di custodia e in corso di validita?"),
        "rationale": ("Etichetta di sostenibilita esibita in confezione: occorre verificare marchio, "
                      "codice di licenza e catena di custodia."),
    },
    "SOLIDAL": {
        "scheme": "Solidal Coop / commercio equo e solidale",
        "question": ("Quale schema di certificazione del commercio equo e solidale sostiene il marchio "
                     "Solidal, ed e conforme ai requisiti dell'art. 18, lett. n-septies?"),
        "rationale": ("Marchio che distingue per caratteristiche sociali: e un'etichetta di sostenibilita "
                      "ai sensi della lett. n-sexies e va verificata."),
    },
}

# Conservative citation map. Only unambiguous cases; everything else stays null.
# NEEDS_VERIFICATION is always null: an undecided outcome has no determined citation.
def expected_citation(uid, claim_text, verdict):
    if verdict["label"] != "IN_SCOPE":
        return None
    t = claim_text.lower()
    def cit(letter, gloss):
        return {"article": "23", "comma": "1", "letter": letter,
                "citation_it": f"Art. 23, comma 1, lett. {letter}, Codice del Consumo",
                "gloss_en": gloss}
    # d-quater: neutrality asserted on the basis of greenhouse-gas offsetting.
    if ("compensa" in t or "neutralizz" in t or "carbon neutral" in t
            or "impatto climatico neutralizzato" in t or "emissioni zero" in t):
        return cit("d-quater", "offset-based neutrality claim")
    # l-bis: only where the record itself admits the requirement is legal.
    if "come previsto per legge" in t or "previsto dalla legge" in t:
        return cit("l-bis", "legal requirement presented as a distinctive feature")
    # d-ter: whole-product/whole-packaging claim resting on one component. Adjudicated case only.
    if uid == "145542#2":
        return cit("d-ter", "environmental claim about the packaging as a whole "
                            "while only one component is certified")
    return None


def main():
    dry = "--dry-run" in sys.argv

    # ---- 1. preserve v1 exactly once, then always read from it
    if not os.path.exists(V1):
        if dry:
            print(f"[dry-run] would copy {SRC} -> {V1}")
            src_for_read = SRC
        else:
            shutil.copy2(SRC, V1)
            print(f"v1 snapshot created: {V1}")
            src_for_read = V1
    else:
        print(f"v1 snapshot already present, reading from it: {V1}")
        src_for_read = V1

    v1 = json.load(open(src_for_read, encoding="utf-8"))
    verdicts = json.load(open(VERDICTS, encoding="utf-8"))
    badge_gap = json.load(open(BADGE_GAP, encoding="utf-8")) if os.path.exists(BADGE_GAP) else []

    # ---- 2. build v2 records
    out, discarded = [], []
    stats = collections.Counter()
    unresolved = []

    for r in v1:
        pid = r["product_id"]
        rec = {k: v for k, v in r.items() if k not in DROP and k != "extracted_claims"}

        # recycling_other -> source_text (adjudicated: 45 claims are sourced only from it)
        ro = r.get("recycling_other")
        rec["source_text"] = ro if ro else None
        rec["schema_version"] = SCHEMA_VERSION

        claims = []
        for i, c in enumerate(r.get("extracted_claims") or []):
            uid = f"{pid}#{i}"
            v = verdicts.get(uid)
            if v is None:
                unresolved.append((uid, "no verdict"))
                continue
            lab = v["label"]
            if lab in ("UNCERTAIN",):
                unresolved.append((uid, "UNCERTAIN"))
                continue
            if lab == "DISCARD":
                discarded.append({
                    "product_id": pid,
                    "claim_text": c["claim_text"],          # verbatim, never normalised
                    "reason": v["discard_reason"],
                    "note": v.get("discard_note"),
                    "rationale_it": v.get("rationale_it"),  # extension, agreed 2026-09-20
                    "removed_in": GENERATION,
                })
                stats[f"discard:{v['discard_reason']}"] += 1
                continue

            claim = {
                "claim_text": c["claim_text"],              # verbatim, never normalised
                "label": lab,
                "verification": None,
                "expected_citation": expected_citation(uid, c["claim_text"], v),
                "rationale_it": v.get("rationale_it") or "",
                "adjudicated_by": v.get("adjudicated_by", "model_proposed"),
                "changed_in": GENERATION,
                "origin": "v1_extraction",
            }
            if lab == "NEEDS_VERIFICATION":
                claim["verification"] = {
                    "required": True,
                    "type": v.get("verification_type"),
                    "question": v.get("verification_question"),
                    "on_pack_qualifier": v.get("on_pack_qualifier"),
                    "scheme": v.get("scheme"),
                }
            claims.append(claim)
            stats[f"keep:{lab}"] += 1

        # claims v1's extractor never produced (see BADGE_SPEC)
        for bpid, badge in badge_gap:
            if bpid != pid:
                continue
            spec = BADGE_SPEC[badge]
            claims.append({
                "claim_text": badge,               # verbatim from the certifications field
                "label": "NEEDS_VERIFICATION",
                "verification": {
                    "required": True,
                    "type": "certification_scheme",
                    "question": spec["question"],
                    "on_pack_qualifier": None,
                    "scheme": spec["scheme"],
                },
                "expected_citation": None,
                "rationale_it": spec["rationale"],
                "adjudicated_by": "human",
                "changed_in": GENERATION,
                "origin": "v2_extraction_gap",
            })
            stats["added:NEEDS_VERIFICATION"] += 1

        rec["claims"] = claims
        rec["has_claims"] = len(claims) > 0     # harness skips zero-claim products per-product
        out.append(rec)                          # never drop a product record

    if unresolved:
        print(f"\nABORT: {len(unresolved)} claim(s) have no usable verdict:")
        for uid, why in unresolved[:20]:
            print(f"   {uid}  ({why})")
        print("Adjudicate them before migrating. Nothing has been written.")
        return 2

    # ---- 3. assertions before anything is written
    n_v1 = sum(len(r.get("extracted_claims") or []) for r in v1)
    n_v2 = sum(len(r["claims"]) for r in out)
    n_added = sum(1 for r in out for c in r["claims"] if c["origin"] == "v2_extraction_gap")
    n_from_v1 = n_v2 - n_added
    n_dl = len(discarded)
    assert len(out) == len(v1), f"product count changed: {len(v1)} -> {len(out)}"
    # Nothing from v1 may vanish unlogged. Claims ADDED in v2 are tracked separately: they were
    # never in v1, so folding them into this identity would hide exactly what they are.
    assert n_v1 == n_from_v1 + n_dl, (
        f"RECONCILE FAILED: v1={n_v1} != retained-from-v1={n_from_v1} + discarded={n_dl}")
    assert n_added == len(badge_gap), f"badge injection mismatch: {n_added} != {len(badge_gap)}"

    v1_pairs = collections.Counter((r["product_id"], c["claim_text"])
                                   for r in v1 for c in (r.get("extracted_claims") or []))
    out_pairs = collections.Counter([(r["product_id"], c["claim_text"]) for r in out for c in r["claims"]
                                     if c["origin"] == "v1_extraction"]
                                    + [(d["product_id"], d["claim_text"]) for d in discarded])
    assert v1_pairs == out_pairs, "claim_text set changed — a string was altered, lost or invented"

    if dry:
        print(f"\n[dry-run] would write {len(out)} records, {n_v2} claims "
              f"({n_from_v1} from v1 + {n_added} added), {n_dl} discards")
        return 0

    # ---- 4. write
    json.dump(out, open(SRC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(discarded, open(DISCARD_LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ---- 5. validate
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from validate_v2 import validate
    errs = validate(out, discarded, v1)

    # ---- 6. report
    dropped_fields = sorted(set(DROP))
    lines = [
        "# migration_report_v2.md", "",
        f"Generated by `migrate_v2.py`. Re-runnable: rebuilds v2 from `{V1}` + `{VERDICTS}`.", "",
        "## Reconciliation", "", "| Check | Value |", "|---|---|",
        f"| claims in v1 | {n_v1} |",
        f"| retained in v2, from v1 | {n_from_v1} |",
        f"| discarded (logged) | {n_dl} |",
        f"| `claims_v1 == retained_from_v1 + discarded` | **{'PASS' if n_v1 == n_from_v1 + n_dl else 'FAIL'}** |",
        f"| **added in v2** (certification badges v1 never extracted) | **{n_added}** |",
        f"| total claims in v2 | {n_v2} |",
        f"| every claim_text byte-identical to v1 | **PASS** |",
        f"| product records in / out | {len(v1)} / {len(out)} |", "",
        "## Label distribution", "", "| Label | Claims |", "|---|---|",
        f"| IN_SCOPE | {stats['keep:IN_SCOPE']} |",
        f"| NEEDS_VERIFICATION | {stats['keep:NEEDS_VERIFICATION'] + stats['added:NEEDS_VERIFICATION']} "
        f"(of which {stats['added:NEEDS_VERIFICATION']} added in v2) |", "",
        "## Discards by reason code", "", "| Reason | Claims |", "|---|---|",
    ]
    for k in ["product_performance", "other_regime", "health_nutrition",
              "heritage_origin", "ip_regulatory_status"]:
        lines.append(f"| `{k}` | {stats['discard:' + k]} |")
    zero = sum(1 for r in out if not r["has_claims"])
    lines += [
        "", "## Diff stats", "",
        f"- product records touched: **{len(out)}** (all of them — `schema_version`, "
        f"`source_text`, `has_claims` added; `extracted_claims` replaced by `claims`)",
        f"- claims removed: **{n_dl}**",
        f"- fields dropped: **{len(dropped_fields)}** — " + ", ".join(f"`{f}`" for f in dropped_fields),
        f"- `recycling_other` migrated to `source_text` before removal "
        f"({sum(1 for r in out if r['source_text'])} records carry it)",
        f"- `matched_signals` and `legit_or_disclosed_basis_detected` knowingly dropped, not migrated",
        f"- zero-claim product records kept: **{zero}** of {len(out)} (`has_claims: false`)",
        "", "## Validator", "",
        f"- records passing: **{len(out) - len({x.split(' claims[')[0] for x in errs if x.startswith('record[')})}/{len(out)}**",
        f"- violations: **{len(errs)}**",
    ]
    for x in errs[:40]:
        lines.append(f"  - `{x}`")
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    print(f"\nwrote {SRC}: {len(out)} records, {n_v2} claims")
    print(f"wrote {DISCARD_LOG}: {n_dl} discards")
    print(f"wrote {REPORT}")
    print(f"validator violations: {len(errs)}")
    for x in errs[:20]:
        print("   !", x)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
