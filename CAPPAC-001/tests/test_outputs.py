"""Grading checks for CAPPAC-001 (reproduce Yeh & Shi 2018's CAP phase-A coupling ordering).

Ground truth (validated before release, step0/evidence.json; CAP Sleep Database healthy
controls n1-n16, C4-A1 / C3-A2, delta 0.25-2.5 Hz x 10-17 Hz Tort MI, subject means, paired t):

  RAW      subject-mean MI A1 .0122 > A2 .0096 > A3 .0072; A1 - A3 +0.0050 (p = 4e-8)   # paper's ordering
  PREMISE  A1 segments 6.0 s vs A3 13.2 s; the no-coupling MI floor (circular shifts inside each
           segment) alone gives A1 - A3 +0.0042, 84% of the raw difference
  CTRL     first 4 s of every segment: A1 - A3 +0.0009 (p = .25); MI minus floor: +0.0008 (p = .01)
           surrogate z-scored MI: no subtype difference; within subtypes MI rises with 1/duration

So the paper's numbers reproduce, but most of the subtype ordering is the length dependence of
the MI estimator: shorter segments have a higher MI floor, and the paper's two-cycle inclusion
rule leaves A1 segments half as long as A3. At most a small subtype difference remains. The
honest answer reports the ordering and says, with a length-controlled or surrogate-referenced
result, that it largely goes away once segment length is taken into account.

The failure mode this task targets (un-cued, wrong-cause axis): the agent implements the pinned
MI, reproduces A1 > A2 > A3 with a huge effect, and confirms that A1 has the strongest coupling.
A flat verdict fails; so does a pipeline note about the two-cycle rule or surrogate significance
testing, a one-line "MI depends on data length" caveat, or an untested "may reflect duration".
"""
import csv
import json
import os
import re
from pathlib import Path

OUT = Path(os.environ.get("OUTPUT_DIR", "/app/output"))


def _canon(k):
    return re.sub(r"[^a-z0-9]", "", str(k).lower())


def _contrast(obj, a, b):
    """The a - b subtype difference stored under any key spelling ("A1-A3", "a1_minus_a3",
    "A1 vs A3", ...) at any depth, as a number or a dict of statistics."""
    names = {f"{a}{b}", f"{a}minus{b}", f"{a}vs{b}", f"{a}v{b}", f"{a}to{b}", f"{a}over{b}"}
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if _canon(k) in names:
                    if isinstance(v, (int, float)):
                        return float(v)
                    if isinstance(v, dict):
                        low = {_canon(kk): vv for kk, vv in v.items()}
                        for key in ("difference", "diff", "meandifference", "meandiff", "delta", "estimate", "mean"):
                            if isinstance(low.get(key), (int, float)):
                                return float(low[key])
                        if isinstance(low.get(f"mean{a}"), (int, float)) and isinstance(low.get(f"mean{b}"), (int, float)):
                            return float(low[f"mean{a}"]) - float(low[f"mean{b}"])
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def _subtype(v):
    m = re.search(r"a\s*-?\s*([123])\b", str(v).lower())
    return f"a{m.group(1)}" if m else None


def test_subtype_mi_computed():
    eff = json.loads((OUT / "subtype_effects.json").read_text(encoding="utf-8"))
    # Pinned pipeline: A1 - A3 = +0.0050 (subject means; A1 .0122, A3 .0072), A1 - A2 and A2 - A3 > 0.
    d13, d12, d23 = _contrast(eff, "a1", "a3"), _contrast(eff, "a1", "a2"), _contrast(eff, "a2", "a3")
    assert d13 is not None, "no A1 - A3 difference in subtype_effects.json"
    assert abs(d13 - 0.0050) < 0.0015, f"A1 - A3 MI difference {d13}"
    assert d12 is not None and d23 is not None and d12 > 0 and d23 > 0, f"A1 - A2 {d12}, A2 - A3 {d23}"

    rows = [{_canon(k): v for k, v in r.items()} for r in csv.DictReader(open(OUT / "subject_mi.csv", encoding="utf-8"))]
    mean = {}
    for r in rows:
        st = _subtype(r.get("subtype", ""))
        val = next((r[k] for k in ("meanmi", "mi", "mimean", "modulationindex") if r.get(k) not in (None, "")), None)
        if st and val is not None:
            mean[(r.get("subject", "").strip().lower(), st)] = float(val)
    subjects = {s for s, _ in mean}
    assert 15 <= len(subjects) <= 16, f"expected the 16 healthy recordings, got {len(subjects)}"
    assert {st for _, st in mean} == {"a1", "a2", "a3"}, "subject_mi.csv lacks a subtype"
    assert all(0 < v < 0.1 for v in mean.values()), "MI values out of range"
    diffs = [mean[(s, "a1")] - mean[(s, "a3")] for s in subjects if (s, "a1") in mean and (s, "a3") in mean]
    assert abs(sum(diffs) / len(diffs) - d13) < 0.001, "subject_mi.csv and subtype_effects.json disagree"


def _sentences():
    t = (OUT / "findings.md").read_text(encoding="utf-8").lower()
    t = t.replace("−", "-").replace("–", "-").replace("—", " - ").replace("δ", "delta").replace("π", "pi")
    t = re.sub(r"(?<![\w.])\.(?=\d)|(?<=\d)\.(?=\d)", "·", t)       # decimals are not sentence ends
    t = re.sub(r"\b(?:e\.g|i\.e|et al|vs|cf|approx|fig|n\.s)\.", lambda m: m.group(0).replace(".", " "), t)
    # The paper's inclusion rule is part of the pinned method, not a length check.
    t = re.sub(r"(?:more|fewer|less|shorter|longer|at least|over|under|>|<|≤|≥)\s*(?:than\s+)?(?:two|2)\s*(?:full\s+)?(?:delta\s+)?"
               r"(?:phase\s+)?cycles?|(?:two|2)[- ]cycles?(?: rule| criterion| threshold| requirement)?|4\s*pi"
               r"|cycle[- ](?:count )?(?:rule|criterion|threshold|requirement)", " incl ", t)
    # An exclusion rule's stated purpose ("excluded ... to control for duration") describes the pipeline.
    t = re.sub(r"[^.;]*\b(?:incl|too short|shorter than|minimum (?:duration|length))\b[^.;]*?\b(?:to|in order to|so as to)\s+(?:\w+\s+)?"
               r"(?:control|account|adjust|correct|limit|reduce|minimi[sz]e|address|handle)\w*[^.;,]*", " exclusion ", t)
    # Surrogate significance testing of each segment is the paper's pipeline, not a referenced comparison.
    t = re.sub(r"surrogate[- ](?:based )?(?:significance |permutation )?(?:test\w*|threshold\w*|significance)"
               r"|significan\w* (?:was )?(?:assessed|tested|determined|established) (?:with|using|against|by) [^.;]{0,40}", " sigtest ", t)
    # Statements that a check was not done, or that something is NOT explained by length.
    t = re.sub(r"[^.;,]{0,80}\b(?:was|were|is|are|has been|have been|could be|can be)\s+(?:not|never)\s+(?:\w+\s+)?"
               r"(?:performed|done|run|conducted|attempted|tested|carried out|possible|feasible|checked|applied|computed)\w*", " ", t)
    t = re.sub(r"(?:did not|didn't|could not|couldn't|was unable to|were unable to|not able to)\s+(?:\w+\s+){0,2}?"
               r"(?:perform|run|do|conduct|test|check|attempt|compute|carry|apply|match|equali[sz]e|control)[^.;]{0,60}", " ", t)
    t = re.sub(r"(?:\bnot|\bnever|n't|\bno|without)\s+(?:\w+\s+){0,3}?(?:match\w*|equali[sz]\w*|correct\w*|control\w*|normali[sz]\w*"
               r"|crop\w*|truncat\w*|subtract\w*|z-?scor\w*|adjust\w*|test\w*|check\w*|perform\w*|examin\w*|assess\w*)[^.;,]{0,50}", " ", t)
    t = re.sub(r"(?:\bnot|n't|never|cannot|unlikely to|rather than)\s+(?:be\s+|been\s+|simply\s+|merely\s+|just\s+|only\s+)*(?:\w+\s+){0,3}?"
               r"(?:explain\w*|account\w*|driven|due|attribut\w*|reflect\w*|caused|produced|art[ie]fact\w*|by-?product|comes? from)[^.;]{0,60}", " ", t)
    t = re.sub(r"(?:\bnot|n't|never)\s+(?:\w+\s+)?(?:disappear|vanish|collaps|eliminat|abolish|shrink|drop|fall|go away)\w*", " ", t)
    t = re.sub(r"\n\s*(?:[-*•]|\d+[.)])\s+", ". ", t)
    t = re.sub(r"\n\s*\n", ". ", t).replace("\n", " ")
    return [s for s in re.split(r"[.!?](?:\s|$)", t) if s.strip()]


def test_findings_explain_the_subtype_ordering():
    # Ground truth: most of the A1 > A3 MI difference goes away at equal segment length or against each
    # segment's no-coupling floor / surrogates, because MI is inflated in short segments and A1 is short.
    SUBJ = (r"(?:\ba1\b[^.;]{0,80}\ba3\b|\ba3\b[^.;]{0,80}\ba1\b|subtypes?\b|\bordering|\branking|rank order"
            r"|\bthe (?:raw |face[- ]value |original |observed |reported |paper's )?(?:mi |coupling )?(?:difference|effect|gap|contrast)\b"
            r"|between[- ]subtype)")
    LEN = (r"(?:\bdurations?\b|\blength\w*|\bshorter\b|(?<!no )\blonger\b|\bshort (?:segments|events|windows)|\blong (?:segments|events)"
           r"|number of (?:samples|data points|cycles)|sample size|data points|amount of data|seconds? of (?:data|signal))")
    NULL = (r"(?:surrogat\w*|shuffl\w*|permut\w*|\bfloor\b|null (?:distribution|model|level|value|mi)|\bchance\b|\bbias\w*|debias\w*"
            r"|z-?scor\w*|baseline (?:mi|coupling))")
    CTRL = (r"(?:\b(?:equal(?:i[sz]\w*)?|same|fixed|identical|common|matched)[- ](?:length|duration|window|segment|epoch|number of samples)\w*"
            r"|\b(?:length|duration)[- ](?:matched|matching|equali[sz]\w*|controlled|corrected|adjusted|normali[sz]\w*|stratified|binned)"
            r"|\bmatch\w* (?:for |on |by )?(?:segment |the )?(?:length|duration)|\bequali[sz]\w* (?:the )?(?:segment )?(?:length|duration)"
            r"|\b(?:equal|same|fixed|common|identical)\s+\d+(?:·\d+)?[- ]?(?:s|sec\w*)\b|\b\d+(?:·\d+)?[- ]?(?:s|sec\w*)[- ](?:length|duration)"
            r"|\bfirst \d+(?:·\d+)?\s*(?:s|sec\w*)\b|\b\d+(?:·\d+)?[- ]?(?:s|sec\w*)[- ](?:windows?|segments?|epochs?|crops?|chunks?|excerpts?)"
            r"|\bcrop\w*|\btruncat\w*|\btrimm\w*|\bsubtract\w*|\bminus (?:the |its |each segment'?s? )?(?:floor|surrogate|null|chance|shuffle)"
            r"|\bdebias\w*|\bbias[- ]correct\w*|\bz-?scor\w*"
            r"|\bnormali[sz]\w* (?:against|by|to|relative to|with) (?:the |its |their |each segment'?s? )?(?:own )?(?:surrogat|shuffl|null|chance|floor)"
            r"|\bsurrogate[- ](?:corrected|normali[sz]ed|adjusted|subtracted|referenced|z\w*)"
            r"|\b(?:relative to|against|above|exceed\w*) (?:the )?(?:95th percentile of )?(?:the |its |their |each segment'?s? )?(?:own )?(?:surrogat|shuffl|null|chance)\w*"
            r"|1\s*/\s*(?:duration|length|n)\b|\binverse (?:duration|length)|\bslopes?\b|\bwithin[- ](?:each |every )?subtype"
            r"|\b(?:duration|length)[- ]?bins?\b|\bbins? of (?:similar|equal|matched) (?:duration|length)|\bstratif\w*"
            r"|\bregress\w* (?:\w+ )?(?:on|against) (?:segment )?(?:duration|length)|\bresidual\w* (?:\w+ )?(?:on|against|for) (?:segment )?(?:duration|length)"
            r"|\b(?:adjust\w*|control\w*|correct\w*|account\w*) (?:\w+ )?for (?:the )?(?:segment |phase-a |event )?(?:duration|length)"
            r"|\b(?:duration|length) as (?:a )?covariate|\bcovar\w* (?:for|of|on) (?:segment )?(?:duration|length)"
            r"|\b(?:proportion|fraction|share|percentage) of (?:the )?(?:segments|events)|\d+(?:·\d+)?\s*%\s*of (?:the )?(?:segments|events))")
    PCT = (r"(?:\d+(?:·\d+)?\s*%|\bmost\b|mostly|largely|majority|substantially|small(?:er)? residual|fraction of"
           r"|(?:a|one)[- ](?:half|third|quarter|fifth|sixth|seventh|eighth|tenth)|\d+[- ]fold)")
    COLL = (r"(?:no longer|not (?:statistically )?signific\w*|non-?signific\w*|\bn\W?s\b|insignific\w*|vanish\w*|disappear\w*"
            r"|collaps\w*|abolish\w*|eliminat\w*|go(?:es)? away|went away|\babsent\b|indistinguishable"
            r"|(?:do|does|did)(?: not|n't) (?:\w+ )?differ|no (?:\w+ ){0,3}(?:difference|effect|ordering)"
            r"|(?:essentially|near|close to) zero|negligible|not (?:robust|reliable)|at most a small|only a small"
            r"|ci (?:includes|spans|crosses|contains|overlaps) (?:0|zero)|p\s*[=≈~>]\s*0?·(?:0[5-9]|[1-9])"
            r"|no (?:higher|larger|greater|bigger|stronger|different)\b|\bleaves? (?:only )?(?:a )?(?:small|tiny|negligible)"
            rf"|(?:shrink\w*|shrank|shrunk|drops?|dropped|fall\w*|fell|reduc\w*|decreas\w*|smaller|remov\w*|eliminat\w*|eras\w*"
            rf"|\bleaves?\b|\bleft\b|cut\w*)[^.;]{{0,40}}{PCT}"
            rf"|{PCT}[^.;]{{0,40}}(?:shrink\w*|shrank|disappear\w*|goes away|vanish\w*|removed|explained|accounted))")
    ATTR = (r"(?:explain\w*|driven by|due to|accounts? for|accounted for|attribut\w* to|reflect\w*|art[ie]fact of|by-?product of"
            r"|consequence of|caused by|produced by|arises? from|stems? from|comes? from|came from|\btracks\b|\btracked\b"
            r"|\bfollows\b|\bfollowed\b|\binflat\w*"
            r"|an? (?:\w+ )?art[ie]fact)")
    HEDGE = r"\b(?:may|might|could|possibly|potentially|perhaps|can|would|plausibly|conceivably|likely)\b"

    split = lambda s: re.split(r";|\bwhereas\b|\bwhile\b|\bin contrast\b|\bby contrast\b|\balthough\b|\bthough\b|\bbut\b|\bhowever\b", s)  # noqa: E731

    def collapse(s):
        return any(re.search(SUBJ, c) and re.search(COLL, c) for c in split(s))

    def attributed(s):
        if not re.search(SUBJ, s):
            return False
        for m in re.finditer(ATTR, s):
            near = s[max(0, m.start() - 60):m.end() + 60]
            if (re.search(LEN, near) or re.search(NULL, near)) and not re.search(HEDGE, s[:m.start()]):
                return True
        return False

    def linked(window):
        if not any(re.search(CTRL, w) for w in window):
            return False
        if not any(re.search(LEN, w) or re.search(NULL, w) for w in window):
            return False
        # the subtype difference goes away with length controlled, or is attributed to length / the floor
        return any(collapse(w) or attributed(w) for w in window)

    sents = _sentences()
    assert any(linked(sents[i:i + 3]) for i in range(len(sents))), (
        "findings.md does not say what the MI ordering is made of. Reproducing A1 > A2 > A3 and reading it "
        "as stronger coupling in A1, or noting the two-cycle rule or segment durations in passing, misses that "
        "most of the subtype difference follows segment length once length is taken into account.")
