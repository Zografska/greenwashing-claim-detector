#!/usr/bin/env python3
"""Validator for golden_set_coop_ucpd_250.json at schema_version 1 (dataset generation v2).

Ships with migrate_v2.py and is run by it. Can also be run standalone:
    python3 validate_v2.py [golden_set_coop_ucpd_250.json] [discarded_claims_v2.json]

Exits non-zero if any record fails. Prints every violation; does not stop at the first.
"""
import json, sys, os

LABELS = {"IN_SCOPE", "NEEDS_VERIFICATION"}
VTYPES = {"certification_scheme", "substantiation_evidence", "test_standard",
          "on_pack_disclosure", "third_party_endorsement", None}
REASONS = {"health_nutrition", "product_performance", "heritage_origin",
           "ip_regulatory_status", "other_regime"}
ADJ = {"human", "model_proposed"}
SCHEMA_VERSION = 1

REMOVED_FIELDS = ["recycling", "recycling_other", "matched_signals",
                  "legit_or_disclosed_basis_detected", "heuristic_bucket",
                  "redo_schema_version"]


def validate(records, discarded, v1_records=None):
    errs = []
    def e(where, msg):
        errs.append(f"{where}: {msg}")

    # ---- product level
    seen_ids = set()
    for i, r in enumerate(records):
        w = f"record[{i}] product_id={r.get('product_id')!r}"
        if not isinstance(r.get("product_id"), str) or not r["product_id"]:
            e(w, "product_id missing or not a non-empty string")
        if r.get("product_id") in seen_ids:
            e(w, "duplicate product_id")
        seen_ids.add(r.get("product_id"))
        if r.get("schema_version") != SCHEMA_VERSION:
            e(w, f"schema_version is {r.get('schema_version')!r}, expected {SCHEMA_VERSION}")
        for f in REMOVED_FIELDS:
            if f in r:
                e(w, f"removed field {f!r} is still present")
        if not isinstance(r.get("claims"), list):
            e(w, "claims is not a list")
            continue
        if not isinstance(r.get("has_claims"), bool):
            e(w, "has_claims missing or not a bool")
        elif r["has_claims"] != (len(r["claims"]) > 0):
            e(w, f"has_claims={r['has_claims']} disagrees with len(claims)={len(r['claims'])}")

        # ---- claim level
        for j, c in enumerate(r["claims"]):
            cw = f"{w} claims[{j}]"
            if not isinstance(c.get("claim_text"), str) or not c["claim_text"]:
                e(cw, "claim_text missing or not a non-empty string")
            lab = c.get("label")
            if lab not in LABELS:
                e(cw, f"label {lab!r} not in {sorted(LABELS)} (UNCERTAIN and DISCARD must not survive into v2)")
            if not isinstance(c.get("rationale_it"), str) or not c["rationale_it"].strip():
                e(cw, "rationale_it missing or empty")
            if c.get("adjudicated_by") not in ADJ:
                e(cw, f"adjudicated_by {c.get('adjudicated_by')!r} not in {sorted(ADJ)}")
            if not isinstance(c.get("changed_in"), str) or not c["changed_in"]:
                e(cw, "changed_in missing")
            if c.get("origin") not in ("v1_extraction", "v2_extraction_gap"):
                e(cw, f"origin {c.get('origin')!r} not in ('v1_extraction', 'v2_extraction_gap')")

            v = c.get("verification")
            if lab == "IN_SCOPE":
                # adjudicated 2026-09-20: IN_SCOPE + non-null verification is rejected outright
                if v is not None:
                    e(cw, "IN_SCOPE carries a non-null verification object (rejected: a verification "
                          "object IS what NEEDS_VERIFICATION means)")
            elif lab == "NEEDS_VERIFICATION":
                if not isinstance(v, dict):
                    e(cw, "NEEDS_VERIFICATION without a verification object")
                else:
                    if v.get("required") is not True:
                        e(cw, "verification.required must be true")
                    if v.get("type") not in VTYPES or v.get("type") is None:
                        e(cw, f"verification.type {v.get('type')!r} invalid")
                    q = v.get("question")
                    if not isinstance(q, str) or len(q.strip()) < 15:
                        e(cw, "verification.question missing or too short to be a specific checkable question")
                    for k in ("on_pack_qualifier", "scheme"):
                        if k not in v:
                            e(cw, f"verification.{k} key absent (use null, not omission)")
                    if c.get("expected_citation") is not None:
                        e(cw, "NEEDS_VERIFICATION must have expected_citation null "
                              "(the outcome is by definition undetermined)")

            ec = c.get("expected_citation")
            if ec is not None:
                if not isinstance(ec, dict):
                    e(cw, "expected_citation must be an object or null")
                else:
                    for k in ("article", "comma", "letter", "citation_it"):
                        if k not in ec:
                            e(cw, f"expected_citation.{k} absent")

    # ---- discard log
    for i, dr in enumerate(discarded):
        w = f"discarded[{i}]"
        for k in ("product_id", "claim_text", "reason", "removed_in"):
            if not dr.get(k):
                e(w, f"{k} missing")
        if dr.get("reason") not in REASONS:
            e(w, f"reason {dr.get('reason')!r} not in {sorted(REASONS)}")
        if dr.get("reason") == "other_regime" and not dr.get("note"):
            e(w, "other_regime requires a free-text note naming the regime")

    # ---- reconciliation against v1
    if v1_records is not None:
        v1 = []
        for r in v1_records:
            for c in (r.get("extracted_claims") or []):
                v1.append((r["product_id"], c["claim_text"]))
        # Claims carried over from v1 must reconcile exactly. Claims ADDED in v2 (certification
        # badges v1's extractor never produced) are excluded from the identity and counted
        # separately — folding them in would hide exactly what they are.
        v2 = [(r["product_id"], c["claim_text"]) for r in records for c in r["claims"]
              if c.get("origin") == "v1_extraction"]
        added = [(r["product_id"], c["claim_text"]) for r in records for c in r["claims"]
                 if c.get("origin") == "v2_extraction_gap"]
        dl = [(d["product_id"], d["claim_text"]) for d in discarded]
        if len(v1) != len(v2) + len(dl):
            e("RECONCILE", f"claims_v1 ({len(v1)}) != retained_from_v1 ({len(v2)}) + discarded ({len(dl)})")
        if sorted(v1) != sorted(v2 + dl):
            missing = set(v1) - set(v2 + dl)
            extra = set(v2 + dl) - set(v1)
            if missing:
                e("RECONCILE", f"{len(missing)} v1 claim(s) vanished unlogged, e.g. {list(missing)[:3]}")
            if extra:
                e("RECONCILE", f"{len(extra)} claim(s) marked v1_extraction were not in v1, "
                               f"e.g. {list(extra)[:3]}")
        # every added claim must be a verbatim badge from that product's certifications field
        for pid, ct in added:
            rec = next((r for r in v1_records if r["product_id"] == pid), None)
            certs = (rec or {}).get("certifications") or []
            if not isinstance(certs, list) or ct not in [str(x).strip() for x in certs]:
                e("ADDED", f"added claim {ct!r} on product {pid} is not a verbatim certifications entry")
        # byte-equality: no normalisation, trimming or re-casing
        v1set = set(v1)
        for pid, ct in v2 + dl:   # added claims are exempt: they have no v1 counterpart
            if (pid, ct) not in v1set:
                e("VERBATIM", f"claim_text altered for product {pid}: {ct[:60]!r}")
    return errs


def main():
    g = sys.argv[1] if len(sys.argv) > 1 else "golden_set_coop_ucpd_250.json"
    dl = sys.argv[2] if len(sys.argv) > 2 else "discarded_claims_v2.json"
    v1p = "golden_set_coop_ucpd_250.v1.json"
    records = json.load(open(g, encoding="utf-8"))
    discarded = json.load(open(dl, encoding="utf-8"))
    v1 = json.load(open(v1p, encoding="utf-8")) if os.path.exists(v1p) else None
    errs = validate(records, discarded, v1)
    n = len(records)
    bad = len({x.split(" claims[")[0] for x in errs if x.startswith("record[")})
    print(f"records validated : {n}")
    print(f"records passing   : {n - bad}/{n}")
    print(f"violations        : {len(errs)}")
    for x in errs[:60]:
        print("   !", x)
    if len(errs) > 60:
        print(f"   ... and {len(errs)-60} more")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
