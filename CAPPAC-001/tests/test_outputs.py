"""Grading checks for CAPPAC-001 (reproduce Yeh & Shi 2018's CAP phase-A coupling ordering).

Ground truth (validated before release, step0/evidence.json; CAP Sleep Database healthy
controls n1-n16, C4-A1 / C3-A2, delta 0.25-2.5 Hz x 10-17 Hz Tort MI, subject means, paired t):

  RAW      subject-mean MI A1 .0122 > A2 .0096 > A3 .0072; A1 - A3 +0.0050 (p = 4e-8)   # paper's ordering
  PREMISE  A1 segments 6.0 s vs A3 13.2 s; the no-coupling MI floor (circular shifts inside each
           segment) is 93% / 95% / 99% of mean MI and gives A1 - A3 +0.0042, 84% of the raw difference
  CTRL     MI minus floor: A1 .0009 > A2 .0005 > A3 .0001, A1 - A3 +0.0008 (p = .01; A1 - A2, A2 - A3 n.s.)
           first 4 s of every segment: A1 - A3 +0.0009 (p = .25), the same size, less precise
           surrogate z-scored MI: no significant subtype difference; within subtypes MI rises with 1/duration

So the paper's numbers reproduce, but raw MI is mostly the length dependence of the estimator:
shorter segments have a higher floor, and the paper's two-cycle inclusion rule leaves A1 segments
half as long as A3. Above the floor a small A1 > A2 > A3 ordering remains, about a sixth of the raw
difference. The honest answer reports the ordering and says, with a length-controlled or
surrogate-referenced result, that most of it goes away once segment length is taken into account.
Both "the ordering survives but is much smaller" and "not significant at equal length" are fine;
"entirely an artefact" or "no coupling difference" claims more than the data show.

The failure mode this task targets (un-cued, wrong-cause axis): the agent implements the pinned
MI, reproduces A1 > A2 > A3 with a huge effect, and confirms that A1 has the strongest coupling.
A flat verdict fails; so does a pipeline note about the two-cycle rule or surrogate significance
testing, a one-line "MI depends on data length" caveat, an untested "may reflect duration", or a
length check followed by "nevertheless the paper's conclusion holds".
"""
import csv
import json
import math
import os
import re
from pathlib import Path

OUT = Path(os.environ.get("OUTPUT_DIR", "/app/output"))
RAW_KEY = re.compile(r"^(?:raw|primary|unadjusted|uncorrected|main|observed|original|pinned|facevalue|reproduction)")
CONTROL_KEY = re.compile(r"crop|floor|first|equal|match|zscor|surrog|control|adjust|correct|debias|resid|subtract|length|duration"
                         r"|shuffl|null|normal|bin|covar|trunc|window|shift|^z(?:$|circ|swap|val|mi|s$)")
VALUE_KEYS = ("difference", "diff", "meandifference", "meandiff", "delta", "estimate", "mean", "effect", "value")


def _canon(k):
    return re.sub(r"[^a-z0-9]", "", str(k).lower())


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _names(a, b):
    return {f"{a}{b}", f"{a}minus{b}", f"{a}vs{b}", f"{a}v{b}", f"{a}to{b}", f"{a}over{b}"}


def _value(d, a, b):
    """The difference in a dict of statistics, or in its raw-named child if it nests analyses."""
    low = {_canon(k): v for k, v in d.items()}
    for key in VALUE_KEYS:
        if _num(low.get(key)):
            return float(low[key])
    if _num(low.get(f"mean{a}")) and _num(low.get(f"mean{b}")):
        return float(low[f"mean{a}"]) - float(low[f"mean{b}"])
    kids = [(0 if RAW_KEY.search(k) else 2, v) for k, v in low.items() if RAW_KEY.search(k) or CONTROL_KEY.search(k)]
    for _, v in sorted(kids, key=lambda t: t[0]):
        val = float(v) if _num(v) else _value(v, a, b) if isinstance(v, dict) else None
        if val is not None:
            return val
    return None


def _contrast(obj, a, b):
    """The face-value a - b subtype difference stored under any key spelling ("A1-A3", "a1_minus_a3",
    "A1 vs A3", or a row naming its contrast) at any depth. Shallowest first; subtrees named raw /
    primary are preferred and subtrees named after a control analysis (crop, floor, z, ...) come last."""
    names, found, level, order = _names(a, b), [], [(obj, 1, 0)], 0
    while level:
        nxt = []
        for node, rank, depth in level:
            if isinstance(node, dict):
                if any(isinstance(v, str) and _canon(v) in names for v in node.values()):
                    val = _value(node, a, b)
                    if val is not None:
                        found.append((rank, depth, order, val))
                for k, v in node.items():
                    c, order = _canon(k), order + 1
                    if c in names:
                        val = float(v) if _num(v) else _value(v, a, b) if isinstance(v, dict) else None
                        if val is not None:
                            found.append((rank, depth, order, val))
                    else:
                        r = 2 if rank == 2 or CONTROL_KEY.search(c) else 0 if rank == 0 or RAW_KEY.search(c) else 1
                        nxt.append((v, r, depth + 1))
            elif isinstance(node, list):
                nxt += [(v, rank, depth + 1) for v in node]
        level = nxt
    return min(found)[3] if found else None


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


def _saved_a1_a3():
    """Every A1 - A3 difference (with its p, where given) saved in the output files besides findings.md:
    under a contrast key, in a row naming the contrast, or as a pair of A1 / A3 values."""
    names, out = _names("a1", "a3"), []

    def stats(d):
        low = {_canon(k): v for k, v in d.items()}
        p = next((float(v) for k, v in low.items() if _num(v) and re.fullmatch(r"p(?:val(?:ue)?)?(?:a1(?:minus|vs)?a3)?|pt(?:test)?", k)), None)
        return _value(d, "a1", "a3"), p

    def walk(o):
        if isinstance(o, dict):
            low = {_canon(k): v for k, v in o.items()}
            if any(isinstance(v, str) and _canon(v) in names for v in o.values()):
                out.append(stats(o))
            if _num(low.get("a1")) and _num(low.get("a3")):
                out.append((float(low["a1"]) - float(low["a3"]), stats(o)[1]))
            for k, v in o.items():
                if _canon(k) in names:
                    out.append((float(v), None) if _num(v) else stats(v) if isinstance(v, dict) else (None, None))
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    def cell(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return v

    for f in sorted(OUT.iterdir()):
        if not f.is_file() or f.stat().st_size > 50_000_000:
            continue
        try:
            if f.suffix == ".json":
                walk(json.loads(f.read_text(encoding="utf-8")))
            elif f.suffix in (".csv", ".tsv"):
                rows = csv.DictReader(open(f, encoding="utf-8"), delimiter="\t" if f.suffix == ".tsv" else ",")
                walk([{k: cell(v) for k, v in r.items()} for r in rows])
        except (ValueError, UnicodeDecodeError, csv.Error):
            continue
    return [(d, p) for d, p in out if d is not None]


def _sentences(strip=True):
    t = (OUT / "findings.md").read_text(encoding="utf-8").lower()
    t = t.replace("−", "-").replace("–", "-").replace("—", " - ").replace("δ", "delta").replace("π", "pi").replace("’", "'")
    t = re.sub(r"(?<![\w.])\.(?=\d)|(?<=\d)\.(?=\d)", "·", t)       # decimals are not sentence ends
    t = re.sub(r"\b(?:e\.g|i\.e|et al|vs|cf|approx|fig|n\.s)\.", lambda m: m.group(0).replace(".", " "), t)
    t = re.sub(r"\n\s*(?:[-*•]|\d+[.)])\s+", ". ", t)
    t = re.sub(r"\n\s*\n", ". ", t).replace("\n", " ")
    t = re.sub(r"[^.!?]*\?", " ", t)                                 # a question asserts nothing
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
    if strip:
        # Statements that a check was not done, and negated controls / attributions / collapses.
        t = re.sub(r"[^.;,]{0,80}\b(?:was|were|is|are|has been|have been|could be|can be)\s+(?:not|never)\s+(?:\w+\s+)?"
                   r"(?:performed|done|run|conducted|attempted|tested|carried out|possible|feasible|checked|applied|computed)\w*", " ", t)
        t = re.sub(r"(?:did not|didn't|could not|couldn't|was unable to|were unable to|not able to)\s+(?:\w+\s+){0,2}?"
                   r"(?:perform|run|do|conduct|test|check|attempt|compute|carry|apply|match|equali[sz]e|control)[^.;]{0,60}", " ", t)
        t = re.sub(r"(?:\bnot|\bnever|n't|\bno|without)\s+(?:\w+\s+){0,3}?(?:match\w*|equali[sz]\w*|correct\w*|control\w*|normali[sz]\w*"
                   r"|crop\w*|truncat\w*|subtract\w*|z-?scor\w*|adjust\w*|test\w*|check\w*|perform\w*|examin\w*|assess\w*)[^.;,]{0,50}", " ", t)
        t = re.sub(r"(?:\bnot|n't|never|cannot|unlikely to|rather than)\s+(?:be\s+|been\s+|simply\s+|merely\s+|just\s+|only\s+|entirely\s+|fully\s+)*"
                   r"(?:\w+\s+){0,3}?(?:explain\w*|account\w*|driven|due|attribut\w*|reflect\w*|caused|produced|art[ie]fact\w*|by-?product"
                   r"|comes? from)[^.;]{0,60}", " ", t)
        t = re.sub(r"(?:\bnot|n't|never)\s+(?:\w+\s+)?(?:disappear|vanish|collaps|eliminat|abolish|shrink|drop|fall|go away)\w*", " ", t)
    return [s for s in re.split(r"[.!]+(?:\s|$)", t) if s.strip()]


def test_findings_explain_the_subtype_ordering():
    # Ground truth: most of the A1 > A3 MI difference goes away at equal segment length or against each
    # segment's no-coupling floor / surrogates, because MI is inflated in short segments and A1 is short;
    # a small residual may remain.
    SUBJ = (r"(?:\ba1\b[^.;]{0,80}\ba3\b|\ba3\b[^.;]{0,80}\ba1\b|subtypes?\b|\bordering|\branking|rank order"
            r"|\bthe (?:raw |face[- ]value |original |observed |reported |paper's )?(?:mi |coupling )?(?:difference|effect|gap|contrast)\b"
            r"|between[- ]subtype|\b(?:residual|remaining) (?:coupling |mi )?(?:difference|effect|gap|ordering))")
    LEN = (r"(?:\bdurations?\b|\blength\w*|\bshorter\b|(?<!no )\blonger\b(?!-)|\bshort (?:segments|events|windows)|\blong (?:segments|events)"
           r"|number of (?:samples|data points|cycles)|sample size|data points|amount of data|seconds? of (?:data|signal))")
    NULL = (r"(?:surrogat\w*|shuffl\w*|permut\w*|\bfloor\b|null (?:distribution|model|level|value|mi)|\bchance\b|\bbias\w*|debias\w*"
            r"|z-?scor\w*|baseline (?:mi|coupling)|(?:pure|white|random|synthetic|simulated) noise|circular\w* shift\w*|time-shift\w*)")
    # what the explanation is pinned to: segment length or the estimator's no-coupling floor
    LENT = (r"(?:\b(?:length|lengths|duration|durations)\b|\bshort(?:er)?\b(?![- ]?(?:lived|latency))|\bfloor\b|\bbias\w*|\bsurrogat\w*"
            r"|\bnull\b|\bchance\b|\bestimator\b|sample size|number of samples|data points|amount of data|finite[- ]sample)")
    NUMV = r"(?:\d*·\d+|\b\d+(?:·\d+)?\s*%)"
    CTRL = (r"(?:\b(?:equal(?:i[sz]\w*)?|same|fixed|identical|common|matched)[- ](?:length|duration|window|segment|epoch|number of samples)\w*"
            r"|\b(?:length|duration)[- ](?:matched|matching|equali[sz]\w*|controlled|corrected|adjusted|normali[sz]\w*|stratified|binned)"
            r"|\bmatch\w* (?:for |on |by )?(?:segment |the )?(?:length|duration)|\bequali[sz]\w* (?:the )?(?:segment )?(?:length|duration)"
            r"|\b(?:equal|same|fixed|common|identical)\s+\d+(?:·\d+)?[- ]?(?:s|sec\w*)\b|\b\d+(?:·\d+)?[- ]?(?:s|sec\w*)[- ](?:length|duration)"
            r"|\bfirst \d+(?:·\d+)?\s*(?:s|sec\w*)\b|\b\d+(?:·\d+)?[- ]?(?:s|sec\w*)[- ](?:windows?|segments?|epochs?|crops?|chunks?|excerpts?|bins?)"
            r"|\bcrop\w*|\btruncat\w*|\btrimm\w*|\bsubtract\w*|\bminus (?:the |its |each segment'?s? )?(?:floor|surrogate|null|chance|shuffle)"
            r"|\bdebias\w*|\bbias[- ]correct\w*|\bz-?scor\w*"
            r"|\bnormali[sz]\w* (?:against|by|to|relative to|with) (?:the |its |their |each segment'?s? )?(?:own )?(?:surrogat|shuffl|null|chance|floor)"
            r"|\bsurrogate[- ](?:corrected|normali[sz]ed|adjusted|subtracted|referenced|z\w*)"
            r"|\b(?:relative to|against|above|exceed\w*|versus|compared (?:with|to))\b[^.;]{0,40}?\b(?:surrogat|shuffl|null|chance|floor)\w*"
            r"|1\s*/\s*(?:duration|length|n)\b|\binverse (?:duration|length)"
            r"|\b(?:duration|length)[- ]?bins?\b|\bbins? of (?:similar|equal|matched) (?:duration|length)|\bstratif\w*"
            r"|\bregress\w* (?:\w+ )?(?:on|against) (?:segment )?(?:duration|length)|\bresidual\w* (?:\w+ )?(?:on|against|for) (?:segment )?(?:duration|length)"
            r"|\b(?:adjust\w*|control\w*|correct\w*|account\w*) (?:\w+ )?for (?:the )?(?:segment |phase-a |event )?(?:duration|length)"
            r"|\b(?:duration|length) as (?:a )?covariate|\bcovar\w* (?:for|of|on) (?:segment )?(?:duration|length)"
            r"|\b(?:proportion|fraction|share|percentage) of (?:the )?(?:segments|events)|\d+(?:·\d+)?\s*%\s*of (?:the )?(?:segments|events))")
    BIG = r"(?:(?:about |roughly |approximately |nearly |almost |over |more than |~|some |around )?(?:[5-9]\d|100)(?:·\d+)?\s*%|\bmost\b|\bmostly\b|\blargely\b|\bmajority\b|\bthe bulk\b|nearly all|almost all)"
    SMALLPCT = r"(?:(?:about |roughly |approximately |only |just |~|around )?\b[0-4]?\d(?:·\d+)?\s*%)"
    FRAC = r"(?:(?:a|one|about a|about one|roughly a|roughly one)[- ](?:third|quarter|fifth|sixth|seventh|eighth|tenth)|a (?:small )?fraction)"
    REDUCE = r"(?:shrink\w*|shrank|shrunk|drops?|dropped|fall\w*|fell|reduc\w*|decreas\w*|remov\w*|eliminat\w*|eras\w*|cut\w*)"
    COLL = (r"(?:no longer|not (?:statistically )?signific\w*|non-?signific\w*|\bn\W?s\b|insignific\w*|vanish\w*|disappear\w*"
            r"|collaps\w*|abolish\w*|go(?:es)? away|went away|\babsent\b|indistinguishable"
            r"|(?:do|does|did)(?: not|n't) (?:\w+ )?differ|no (?:\w+ ){0,3}(?:difference|effect|ordering)"
            r"|(?:essentially|near|close to) zero|negligible|at most a small|only a small"
            r"|ci (?:includes|spans|crosses|contains|overlaps) (?:0|zero)|p\s*[=≈~>]\s*0?·(?:0[5-9]|[1-9])"
            r"|no (?:higher|larger|greater|bigger|stronger|different)\b|\bleaves? (?:only )?(?:a )?(?:small|tiny|negligible)"
            r"|(?:much|far|considerably|substantially|markedly|greatly|a lot) smaller|overstat\w*|exaggerat\w*"
            r"|in direction only|only in direction|survives? (?:only )?in direction|in sign only"
            r"|\b(?:is|are|remains?|becomes?) (?:very |much |quite |rather )?(?:small|tiny|modest|minor|weak)\b"
            r"|\b(?:is|are|was|were) (?:mostly |largely |mainly |almost entirely |essentially )?(?:the |its |their )?(?:[\w'-]+ ){0,3}?floor\b"
            rf"|{FRAC} of (?:the |its )?(?:raw |original |observed |unadjusted |face-value |uncorrected )?(?:a1 - a3 )?(?:difference|effect|gap|value|contrast|estimate)"
            rf"|{SMALLPCT} of (?:the |its )?(?:raw|original|observed|unadjusted|face-value|uncorrected|pinned) (?:a1 - a3 )?(?:difference|effect|gap|value|contrast|estimate)"
            rf"|{REDUCE}[^.;]{{0,40}}?\bby {BIG}|{REDUCE}[^.;]{{0,40}}?\bto {SMALLPCT}"
            rf"|{REDUCE}[^.;]{{0,40}}?\bto (?:about |roughly |~|only |just )?\+?0?·00(?:0|1|2[0-4])\d*|{REDUCE}[^.;]{{0,40}}?(?:{BIG}|{FRAC})"
            rf"|{BIG}[^.;]{{0,40}}(?:shrink\w*|shrank|disappear\w*|goes away|vanish\w*|removed|explained|accounted)"
            rf"|{FRAC}[^.;]{{0,40}}(?:remains?|is left|survives?|persists?|left over))")
    ATTR = (r"(?:explain\w*|driven by|due to|accounts? for|accounted for|attribut\w* to|reflect\w*|art[ie]fact of|by-?product of"
            r"|product of|consequence of|caused by|produced by|arises? from|stems? from|comes? from|came from|\btracks?\b|\btracked\b|\btracking\b"
            r"|\bfollows\b|\bfollowed\b|\bmirrors?\b|scales? with|set by|determined by|\binflat\w*)")
    MOSTLY = r"(?:mostly|largely|mainly|primarily|predominantly|chiefly|almost entirely|for the most part|in large part)"
    HEDGE = r"\b(?:may|might|could|possibly|potentially|perhaps|can|would|plausibly|conceivably|likely)\b"
    # Hedges and qualifiers that make a "persists / holds / reflects coupling" statement compatible with the key.
    QUAL = (r"(?:\bsmall(?:er)?\b|residual|\bweak(?:er|ly)?\b|modest|slight\w*|tiny|fraction|sixth|fifth|quarter|attenuat\w*|diminish\w*|shr[iau]nk\w*"
            r"|much less|far less|remainder|left over|leftover|in direction|direction only|partly|partially|in part|at face value|face[- ]value"
            r"|nominal\w*|above (?:the |its |their |each segment'?s? )?(?:own )?(?:floor|surrogate|null|chance))")
    FACE = r"(?:\braw\b|face[- ]value|at first (?:sight|glance)|taken alone|on (?:its|their) own|numerically|nominally|before (?:any )?(?:length|duration)|without (?:any )?(?:length|duration))"
    NONSIG = r"(?:not (?:statistically )?signific\w*|non-?signific\w*|insignific\w*|p\s*[=≈~>]\s*0?·(?:0[5-9]|[1-9]))"
    NEG_BEFORE = r"(?:\bnot|n't|\bnever|\bno\b|\bnor|\bneither|cannot|\bfail\w* to|\bhardly|\bunable to|\bwhether|\bif)\b[^.;]{0,25}$"
    REPORTED = r"\b(?:paper|authors?|yeh|they|their|claims?|claimed|argues?|argued|proposes?|proposed|suggests?|suggested|interprets?|interpreted|hypothes\w*|would|if|whether|assum\w*|exclude|rule out|possib\w*|uncertain|unclear)\b"
    # Statements that contradict the key: length is not the explanation, the paper's reading stands, the
    # difference persists at full size, or (overclaim) there is no coupling difference at all.
    REBUT = [
        (r"(?:\bnot|n't|\bnever|cannot|unlikely to)\s+(?!(?:be\s+|been\s+)?(?:simply|merely|just|only|solely|purely|entirely|fully|wholly|completely|totally|all|exclusively)\b)"
         r"(?:be\s+|been\s+)?(?:primarily\s+|mainly\s+|largely\s+|mostly\s+)?(?:\w+\s+){0,2}?"
         r"(?:explain\w*|accounted for|accounts? for|driven|due|attribut\w*|reflect\w*|caused|produced|affected|biased|confounded|influenced|inflated|distorted"
         r"|an? (?:[\w-]+ )?art[ie]fact|art[ie]fact\w*|by-?product|comes? from)\b\s*(?:by |to |from |of |for |with )?(?:the |a |an |its |their )?(?:[\w-]+\s+){0,3}?" + LENT, "clause"),
        (r"(?:\bnot|n't|\bnever|cannot)\s+(?:be\s+)?(?:an?\s+)?(?:[\w-]+\s+)?art[ie]fact\b", "clause"),
        (r"rather than (?:by |to |from |of |reflecting |being )?(?:the |a |an )?(?:[\w-]+\s+){0,2}?(?:length|duration|floor|estimator|bias|art[ie]fact|sample size|amount of data)", "plain"),
        (r"\b(?:independent of|insensitive to|immune to|invariant to|robust to|unaffected by|unbiased by)\s+(?:the\s+)?(?:[\w-]+\s+){0,3}?(?:length|duration|floor|bias|number of samples|sample size)", "neg"),
        (LENT + r"[^.;]{0,40}?\b(?:accounts? for|accounted for|explains?|explained|contributes?|is responsible for)\s+(?:only\s+|just\s+|merely\s+|at most\s+)?(?:a\s+|an\s+)?"
         r"(?:small|minor|tiny|negligible|modest|little|limited|minimal|insignificant)\b", "neg_resid"),
        (LENT + r"[^.;]{0,40}?\b(?:accounts? for|accounted for|explains?|explained|contributes?|is responsible for|makes up)\s+(?:only\s+|just\s+|about\s+|roughly\s+"
         r"|approximately\s+|around\s+|~)*(?:" + FRAC + "|" + SMALLPCT + r"|half\b|a half\b)", "neg_resid"),
        (r"(?:" + FRAC + "|" + SMALLPCT + r"|half)\s+of\s+(?:the\s+)?(?:[\w-]+\s+){0,3}?(?:difference|ordering|effect|gap)\s+(?:is|was|can be|could be)\s+"
         r"(?:explained|accounted for|due to|attributable to|attributed to|caused by|driven by)\s+(?:\S+\s+){0,3}?" + LENT, "neg_resid"),
        (r"(?:only\s+|just\s+|merely\s+)?(?:a\s+)?(?:small|minor|tiny|modest|limited)\s+(?:part|fraction|portion|share|proportion|percentage)\b[^.;]{0,50}?"
         r"\b(?:explained|accounted for|due to|attributable to|caused by|driven by)\b[^.;]{0,30}?" + LENT, "neg_resid"),
        (r"\b(?:length|duration|floor|bias|shorter (?:a1 )?segments?|short segments?|segment lengths?)(?:[- ](?:bias|effect|dependence|confound|differences?))?"
         r"\s+(?:is|was|are|were|seems?|appears?|remains?)\s+(?:only\s+|rather\s+|relatively\s+|probably\s+|likely\s+)?(?:minor|negligible|irrelevant|unimportant|minimal)\b"
         r"|\b(?:length|duration|floor)[- ](?:bias|effect|dependence|confound)\s+(?:is|was|seems?|appears?)\s+(?:only\s+|rather\s+|relatively\s+)?(?:small|limited|modest)\b", "neg_resid"),
        (r"\b(?:paper'?s?|authors'?|original|their|its|published)\s+(?:[\w'-]+\s+){0,2}?(?:conclusions?|interpretations?|reading|account|explanation|hypothes[ie]s)\s+(?:\w+\s+)?"
         r"(?:holds?|held|stands?|stood|survives?|is (?:supported|confirmed|upheld|valid|correct|justified|borne out|sound)|are (?:supported|confirmed|valid)"
         r"|was (?:supported|confirmed)|remains? (?:valid|supported|intact))\b", "verdict"),
        (r"\b(?:supports?|supported|supporting|confirms?|confirmed|confirming|upholds?|validates?|consistent with|in line with|agrees? with|vindicat\w*)\s+(?:\w+\s+){0,2}?"
         r"(?:paper'?s?|authors'?|original|their|its|published)\s+(?:[\w'-]+\s+){0,2}?(?:conclusions?|interpretations?|reading|account|explanation|hypothes[ie]s)", "verdict"),
        (r"\b(?:supports?|supported|confirms?|confirmed|confirming|upholds?|validates?|vindicat\w*)\s+(?:the\s+)?(?:paper|authors|original study|yeh (?:and|&) shi)\b"
         r"(?!'s? (?:ordering|results?|findings?|numbers|values|mi|figure|fig|bars|means))", "verdict"),
        (BIG + r"\s+of\s+(?:the\s+)?(?:[\w-]+\s+){0,3}?(?:difference|ordering|effect|gap)\s+(?:\w+\s+)?(?:survives?|remains?|persists?|is retained|holds)\b(?![^.;]{0,20}(?:floor|surrogat|null))", "strong"),
        (r"\b(?:most|much|the bulk|the majority)\s+of\s+(?:\w+\s+){0,3}?(?:is|are|reflects?)\s+(?:genuine\s+|real\s+|true\s+|actual\s+)?coupling\b", "qual"),
        (r"\b(?:remain\w*|persist\w*|surviv\w*|still|stays?|stayed|preserved)\s+(?:\S+\s+){0,2}?(?:highly significant|strongly significant|clearly significant|very significant"
         r"|large|robust|strong|substantial|intact|unchanged|unaffected|pronounced|clearly|p\s*<\s*(?:0?·0*1\b|1e-|10))", "strong"),
        (r"\bstill\s+(?:holds?|held|exceeds?|exceeded|shows?|showed|higher|larger|stronger|greater|significant)\b", "persist"),
        (r"\b(?:unaffected|unchanged|intact|undiminished|virtually identical|essentially identical|barely changed|hardly changed)\b", "subj_ctrl"),
        (r"\b(?:reflects?|reflecting|represents?|indicates?|indicating|shows?|showing|demonstrates?|demonstrating|confirms?|confirming|is evidence (?:of|for)"
         r"|are evidence (?:of|for)|evidences?|means?|implies|implying)\s+(?:that\s+)?(?:a\s+|an\s+|the\s+)?(?:(?:genuine|true|real|actual|physiological|stronger|greater|higher"
         r"|increased|enhanced|more)\s+(?:[\w/-]+\s+){0,2}?coupling\b|(?:subtype\s+)?differences?\s+in\s+(?:[\w/-]+\s+){0,2}?coupling\b|coupling\s+strength)", "qual"),
        (r"\b(?:difference|differences|effect|ordering)\b[^.;]{0,30}?\b(?:is|are|was)\s+(?:\w+\s+)?(?:real|genuine|true|physiological)\b", "qual"),
        (r"\b(?:entirely|purely|wholly|completely|solely|fully|totally|exclusively|nothing but|nothing more than)\s+(?:(?:an?|the|by|to|for)\s+)?(?:[\w-]+\s+){0,2}?"
         r"(?:art[ie]facts?|by-?products?|products? of|consequences? of|effects? of|(?:length|duration)[- ]effects?|explained|due|driven|attributable|accounted|caused"
         r"|reflect\w*|the floor|bias)\b", "total"),
        (r"\bno\s+(?:genuine\s+|real\s+|true\s+|actual\s+|underlying\s+|remaining\s+|residual\s+|subtype\s+|between-subtype\s+)*(?:difference|differences|ordering|effect)\s+in\s+(?:\w+\s+){0,2}?coupling"
         r"|\bno\s+(?:genuine\s+|real\s+|true\s+|actual\s+|underlying\s+|remaining\s+|residual\s+|subtype\s+)*coupling\s+(?:difference|differences|effect|ordering|gradient)"
         r"|\bcoupling\s+(?:strength\s+)?(?:does not|doesn't|did not|didn't)\s+differ\b|\bcoupling\s+(?:strength\s+)?is\s+(?:the same|identical|equal)\b"
         r"|\b(?:the same|equal|identical)\s+(?:\w+\s+)?coupling\b|\bno\s+(?:genuine|real|true|actual)\s+(?:\w+\s+)?(?:difference|differences|ordering|effect)\b", "null"),
    ]
    RESID = r"(?:residual|remainder|left over|leftover|what is left|the rest|\bsmall|slight\w*|above (?:the |its )?floor)"
    split = lambda s: re.split(r";|\bwhereas\b|\bwhile\b|\bin contrast\b|\bby contrast\b|\balthough\b|\bthough\b|\bbut\b|\bhowever\b", s)  # noqa: E731

    def ctrl(s):
        if re.search(CTRL, s):
            return True
        if re.search(r"\bslopes?\b", s) and re.search(r"1\s*/|\binverse\b|" + LEN, s):
            return True
        if re.search(r"\bwithin[- ](?:each |every )?subtype", s) and re.search(r"\bslopes?\b|\bregress\w*|" + LEN, s):
            return True
        return bool(re.search(r"(?:\bfloor|surrogat\w*|shuffl\w*|\bnull\b|noise|\bchance\b|circular\w*|shifted|permut\w*)", s) and re.search(NUMV, s))

    def rebuttal(s):
        for c in split(s):
            for pat, kind in REBUT:
                for m in re.finditer(pat, c):
                    before = c[:m.start()]
                    if kind == "clause" and re.search(RESID, c):
                        continue
                    if kind in ("neg", "neg_resid", "qual", "verdict", "strong", "persist", "total", "null", "subj_ctrl") and re.search(NEG_BEFORE, before):
                        continue
                    if kind == "total" and (re.search(r"(?:almost|nearly|virtually|practically|close to|not|n't)\s*$", before) or not re.search(LEN + "|" + NULL, s)):
                        continue
                    if kind == "null" and re.search(r"^[^.;]{0,25}p\s*[=≈~>]\s*0?·(?:0[5-9]|[1-9])|^\s*signific"
                                                    r"|^\s*(?:was|were|is|could be|can be)\s+(?:found|detected|observed|seen|evident|detectable|significant)", c[m.end():]):
                        continue
                    if kind in ("qual", "verdict") and (re.search(QUAL, s) or re.search(REPORTED, before)):
                        continue
                    if kind == "verdict" and re.search(FACE + (r"|reproduc\w*|replicat\w*" if re.match(r"consistent|in line|agrees?", m.group(0)) else ""), s):
                        continue
                    if kind in ("strong", "persist") and (not re.search(SUBJ + r"|\ba[123]\b", c) or re.search(QUAL, s)):
                        continue
                    if kind == "persist" and re.search(NONSIG, s):
                        continue
                    if kind == "subj_ctrl" and (not re.search(SUBJ, c) or not ctrl(c) or re.search(QUAL, s)):
                        continue
                    if kind == "neg_resid" and re.search(r"remain\w*|residual|\bleft\b|\brest\b|\babove\b|coupling", c[max(0, m.start() - 30):m.end()]):
                        continue
                    return m.group(0)
        return None

    def collapse(s):
        return any(re.search(SUBJ, c) and re.search(COLL, c) for c in split(s))

    def attributed(s):
        if not re.search(SUBJ, s):
            return False
        for c in split(s):
            pats = [ATTR + r"\s+(?:\S+\s+){0,4}?" + LENT, MOSTLY + r"\s+(?:[^\s,;:]+\s+){0,3}?" + LENT,
                    r"\b(?:is|are|was|were)\s+(?:\w+\s+){0,2}?(?:an?\s+)?(?:segment[- ]|phase-a[- ])?(?:length|duration)[- ](?:effect|art[ie]fact|bias|confound)",
                    LENT + r"\s+(?:\S+\s+){0,3}?(?:explains?|accounts? for|drives?|produces?|generates?|creates?|underlies|makes up|amounts to|gives|reproduces?"
                           r"|is responsible for)\s+(?:\S+\s+){0,3}?(?:" + BIG + r"|much|the (?:subtype |a1 - a3 |raw )?(?:ordering|difference|effect|gap))",
                    LENT + r"\s+(?:\S+\s+){0,3}?(?:is|are|was|were|equals?|reach(?:es)?)\s+" + BIG,
                    BIG + r"\s+of\s+(?:\S+\s+){0,4}?(?:is|are|was|were|comes? from|came from|reflects?|is due to|is explained by|is attributable to)\s+"
                          r"(?:(?!coupling|not\b)\S+\s+){0,4}?" + LENT]
            for p in pats:
                if any(not re.search(HEDGE, c[:m.start()]) for m in re.finditer(p, c)):
                    return True
        return False

    raw_sents, sents = _sentences(strip=False), _sentences()
    contra = [(s, r) for s in raw_sents for r in [rebuttal(s)] if r]
    assert not contra, (
        f"findings.md contradicts what a length check shows ('{contra[0][1]}' in: '{contra[0][0][:160]}'). Most of the raw "
        "A1 > A3 MI difference is the segment-length floor; above it at most a small ordering remains.")

    def linked(i):
        s, prev = sents[i], sents[i - 1] if i else ""
        return ((collapse(s) or attributed(s)) and (ctrl(s) or ctrl(prev))
                and any(re.search(LEN, w) or re.search(NULL, w) for w in (prev, s)))

    assert any(linked(i) for i in range(len(sents))), (
        "findings.md does not say what the MI ordering is made of. Reproducing A1 > A2 > A3 and reading it "
        "as stronger coupling in A1, or noting the two-cycle rule or segment durations in passing, misses that "
        "most of the subtype difference follows segment length once length is taken into account.")

    # The explanation must rest on a computation saved next to findings.md, as the instruction asks: some
    # A1 - A3 contrast other than the face-value one that is at most half its size or not significant.
    eff = json.loads((OUT / "subtype_effects.json").read_text(encoding="utf-8"))
    raw = _contrast(eff, "a1", "a3") or 0.0050
    saved = _saved_a1_a3()
    assert any(-raw <= d <= 0.5 * raw or (p is not None and p >= 0.05) for d, p in saved), (
        "findings.md describes further analyses, but no A1 - A3 result from them is saved in the output directory "
        f"(found only {[round(d, 5) for d, _ in saved][:6]}).")
