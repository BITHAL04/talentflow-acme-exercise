"""Analyse the cached Acme data (run fetch.py first). Pure pandas, no network.

Writes:
    outputs/findings.csv       claim, metric, value, method, confidence
    outputs/data_quality.csv   every data check: table, check, flagged, denominator, pct
    outputs/source_funnel.csv  per-source apps / hires / hire rate, two attributions
and prints everything to stdout.
"""
import json
import math
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "outputs"
OUT.mkdir(exist_ok=True)
pd.set_option("display.width", 200)


def load(t):
    recs = json.load(open(RAW / f"{t}.json"))
    return pd.DataFrame([{**r["fields"], "_id": r["id"]} for r in recs])


def one(x):  # Airtable linked-record field -> first id
    return x[0] if isinstance(x, list) and x else None


def D(s):
    return pd.to_datetime(s, errors="coerce")


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))


def pct(k, n):
    return round(100 * k / n, 1) if n else float("nan")


dep, ppl, job, cand, app, itv, off = (load(t) for t in
    ["Departments", "People", "Job_Openings", "Candidates", "Applications", "Interviews", "Offers"])
ps, js, cs = ppl.set_index("_id"), job.set_index("_id"), cand.set_index("_id")

app["cand"], app["open"] = app.Candidate.map(one), app.Opening.map(one)
app["ref"] = app["Referred By"].map(one)
app["src"] = app.cand.map(cs.Source)
for col in ["Applied On", "Screened On", "First Interview On", "Final Interview On", "Offered On", "Closed On"]:
    app[col + "_d"] = D(app[col])
ai = app.set_index("_id")
off["app"] = off.Application.map(one)
itv["app"], itv["iv"] = itv.Application.map(one), itv.Interviewer.map(one)

# Snapshot date = latest date anywhere in the data (not today's date).
date_cols = [D(cand["Created On"]), D(app["Applied On"]), D(app["Closed On"]), D(off["Decision On"]),
             D(itv["Scheduled On"])]
AS_OF = max(s.max() for s in date_cols)

F = []  # findings rows


def finding(claim, metric, value, method, confidence):
    F.append(dict(claim=claim, metric=metric, value=value, method=method, confidence=confidence))
    print(f"[{claim}] {metric}: {value}")


print(f"Snapshot as-of (max date in data): {AS_OF.date()}")
print({t: len(d) for t, d in zip(["Departments", "People", "Job Openings", "Candidates", "Applications",
                                  "Interviews", "Offers"], [dep, ppl, job, cand, app, itv, off])})

# ---------------------------------------------------------------- Claim 1: job boards
hired = app.Stage == "Hired"
H = int(hired.sum())
funnel = []
for label, col in [("as recorded (Candidate.Source)", "src"), ("referrer wins (Referred By set => Referral)", "src_alt")]:
    if col == "src_alt":
        app["src_alt"] = app.src.where(app.ref.isna(), "Referral")
    g = app.groupby(col).agg(apps=("_id", "size"), hires=("Stage", lambda s: int((s == "Hired").sum())))
    g["hire_rate_pct"] = [pct(h, n) for h, n in zip(g.hires, g.apps)]
    g["hire_rate_ci95"] = [wilson(h, n) for h, n in zip(g.hires, g.apps)]
    g["share_of_apps_pct"] = [pct(n, len(app)) for n in g.apps]
    g["share_of_hires_pct"] = [pct(h, H) for h in g.hires]
    g.insert(0, "attribution", label)
    funnel.append(g.reset_index().rename(columns={col: "source"}))
funnel = pd.concat(funnel)
funnel.to_csv(OUT / "source_funnel.csv", index=False)
print(funnel.to_string(index=False))

jb = funnel[(funnel.attribution.str.startswith("as")) & (funnel.source == "Job Board")].iloc[0]
rf = funnel[(funnel.attribution.str.startswith("as")) & (funnel.source == "Referral")].iloc[0]
jb2 = funnel[(funnel.attribution.str.startswith("referrer")) & (funnel.source == "Job Board")].iloc[0]
rf2 = funnel[(funnel.attribution.str.startswith("referrer")) & (funnel.source == "Referral")].iloc[0]
cand_jb = int((cand.Source == "Job Board").sum())
finding("C1", "Job Board share of candidates", f"{cand_jb}/{len(cand)} = {pct(cand_jb, len(cand))}%",
        "Candidates.Source value counts", "High")
finding("C1", "Job Board share of applications", f"{jb.apps}/{len(app)} = {jb.share_of_apps_pct}%",
        "Applications joined to Candidate.Source", "High")
finding("C1", "Job Board share of hires (VP's 26.9%)", f"{jb.hires}/{H} = {jb.share_of_hires_pct}% (CI95 {wilson(jb.hires, H)})",
        "Stage=Hired, by Candidate.Source", "High that it reproduces; Low as a basis for decisions (n=26)")
finding("C1", "Referral share of hires", f"{rf.hires}/{H} = {rf.share_of_hires_pct}%",
        "Stage=Hired, by Candidate.Source", "High that it reproduces; n small")
finding("C1", "Job Board app->hire rate", f"{jb.hires}/{jb.apps} = {jb.hire_rate_pct}% (CI95 {jb.hire_rate_ci95})",
        "hires / applications per source", "Medium-High: CI does not overlap Referral's")
finding("C1", "Referral app->hire rate", f"{rf.hires}/{rf.apps} = {rf.hire_rate_pct}% (CI95 {rf.hire_rate_ci95})",
        "hires / applications per source", "Medium: n=13")
ref_set = app.ref.notna()
finding("C1", "Apps with a named referrer that are NOT attributed to Referral",
        f"{int((ref_set & (app.src != 'Referral')).sum())}/{int(ref_set.sum())}",
        "Applications.Referred By non-empty vs Candidate.Source", "High")
finding("C1", "Job Board share of hires if referrer wins", f"{jb2.hires}/{H} = {jb2.share_of_hires_pct}%; Referral {rf2.hires}/{H} = {rf2.share_of_hires_pct}%",
        "Re-attribute any app with Referred By to Referral", "Medium: assumes Referred By is the truer field")

# ---------------------------------------------------------------- Claim 2: offer acceptance
st = off.Status.value_counts().to_dict()
acc, dec, pen = st.get("Accepted", 0), st.get("Declined", 0), st.get("Pending", 0)
N = len(off)
off["off_d"], off["dec_d"], off["start_d"] = D(off["Offered On"]), D(off["Decision On"]), D(off["Proposed Start Date"])
pend = off[off.Status == "Pending"]
pend_with_decision = int(pend["Decision On"].notna().sum())
finding("C2", "Naive acceptance (VP's ~72%)", f"{acc}/{N} = {pct(acc, N)}%", "Accepted / all offers incl. Pending",
        "High that it reproduces; wrong definition")
finding("C2", "Acceptance among decided offers", f"{acc}/{acc + dec} = {pct(acc, acc + dec)}% (CI95 {wilson(acc, acc + dec)})",
        "Accepted / (Accepted + Declined)", "Medium: n=31")
finding("C2", "Bounds if Pending all decline / all accept", f"{pct(acc, N)}% - {pct(acc + pen, N)}%",
        "Pending treated as declined / accepted", "High")
finding("C2", "'Pending' offers that already have a Decision On date", f"{pend_with_decision}/{pen}",
        "Status=Pending and Decision On non-empty", "High")
finding("C2", "Age of Pending offers at snapshot (days)",
        f"min {int((AS_OF - pend.off_d).dt.days.min())}, max {int((AS_OF - pend.off_d).dt.days.max())}",
        f"AS_OF {AS_OF.date()} minus Offered On", "High")
finding("C2", "Decline reasons", json.dumps(off["Decline Reason"].value_counts().to_dict()),
        "Offers.Decline Reason", "High count; too few (n=5) to act on")
q = off.assign(q=off.off_d.dt.to_period("Q").astype(str)).groupby("q").Status.value_counts().unstack(fill_value=0)
print("Offers by quarter:\n", q.to_string())

# ---------------------------------------------------------------- Data-quality checks
DQ = []


def check(table, name, flagged, denom, note=""):
    flagged, denom = int(flagged), int(denom)
    DQ.append(dict(table=table, check=name, flagged=flagged, denominator=denom, pct=pct(flagged, denom), note=note))


# Candidates
cand["ph"] = cand.Phone.str.replace(r"\D", "", regex=True).str[-10:]
cand["nm"] = cand["Full Name"].str.lower().str.split().str.join(" ")
dup = cand[cand.duplicated(["ph", "nm"], keep=False)]
check("Candidates", "Duplicate person (same name+phone, different email/ID)", len(dup), len(cand),
      f"{dup.ph.nunique()} people")
conf = dup.groupby("ph").Source.nunique().gt(1).sum()
check("Candidates", "Duplicate pairs whose Source disagrees", conf, dup.ph.nunique())
check("Candidates", "Expected CTC below Current CTC", (cand["Expected CTC"] < cand["Current CTC"]).sum(), len(cand))
check("Candidates", "Notes empty", cand.Notes.isna().sum(), len(cand))
app["cand_created"] = D(app.cand.map(cs["Created On"]))
check("Applications", "Applied On earlier than the candidate's Created On", (app["Applied On_d"] < app.cand_created).sum(), len(app),
      f"median gap {int((app.cand_created - app['Applied On_d'])[app['Applied On_d'] < app.cand_created].dt.days.median())} days")
check("Applications", "Same candidate applied twice to the same opening", app.duplicated(["cand", "open"], keep=False).sum(), len(app))
check("Applications", "Apps belonging to duplicate-person candidates", app.cand.isin(set(dup._id)).sum(), len(app))

# Attribution
check("Applications", "Referred By set but Source != Referral", (ref_set & (app.src != "Referral")).sum(), ref_set.sum())
check("Applications", "Source = Referral but no Referred By", ((app.src == "Referral") & ~ref_set).sum(), (app.src == "Referral").sum())

# Stage / status logic
check("Applications", "Hired but has a Rejection Reason", (hired & app["Rejection Reason"].notna()).sum(), H)
check("Applications", "Withdrawn stage coded with a Rejection Reason ('Withdrew')",
      ((app.Stage == "Withdrawn") & app["Rejection Reason"].notna()).sum(), (app.Stage == "Withdrawn").sum())
check("Applications", "Stage=Offer but Status=Closed (offer declined, stage never moved)",
      ((app.Stage == "Offer") & (app.Status == "Closed")).sum(), (app.Stage == "Offer").sum())
app["open_status"] = app.open.map(js.Status)
active = app.Status == "Active"
check("Applications", "Active apps on Filled/Cancelled openings", (active & app.open_status.isin(["Filled", "Cancelled"])).sum(), active.sum())
check("Applications", "Active apps older than 90 days at snapshot", (active & ((AS_OF - app["Applied On_d"]).dt.days > 90)).sum(), active.sum())
check("Applications", "Applied before the opening was opened", (app["Applied On_d"] < D(app.open.map(js["Opened On"]))).sum(), len(app))
seq = ["Applied On", "Screened On", "First Interview On", "Final Interview On", "Offered On", "Closed On"]
bad = sum(int((app[seq[k2] + "_d"] < app[seq[k1] + "_d"]).sum()) for k1 in range(6) for k2 in range(k1 + 1, 6))
check("Applications", "Out-of-order milestone dates within an application", bad, len(app))
check("Applications", "Recruiter differs from the opening's recruiter",
      (app.Recruiter.map(one) != app.open.map(js.Recruiter.map(one))).sum(), len(app))

# Openings
hpo = app[hired].groupby("open").size()
job["hires"] = job._id.map(hpo).fillna(0).astype(int)
check("Job Openings", "More hires than Headcount", (job.hires > job.Headcount).sum(), len(job))
check("Job Openings", "Cancelled opening with hires", ((job.Status == "Cancelled") & (job.hires > 0)).sum(), (job.Status == "Cancelled").sum(),
      f"{int(job[job.Status == 'Cancelled'].hires.sum())} hires")
check("Job Openings", "Filled opening with zero hires", ((job.Status == "Filled") & (job.hires == 0)).sum(), (job.Status == "Filled").sum())
check("Job Openings", "Open opening already at/over headcount", ((job.Status == "Open") & (job.hires >= job.Headcount)).sum(), (job.Status == "Open").sum())

# Offers
check("Offers", "Pending but has a Decision On date", pend_with_decision, pen)
check("Offers", "Pending with Proposed Start Date already passed", (pend.start_d < AS_OF).sum(), pen)
check("Offers", "Offer date differs from Application.Offered On", (off.off_d != D(off.app.map(ai["Offered On"]))).sum(), N)
check("Offers", "Proposed Start Date before Offered On", (off.start_d < off.off_d).sum(), N)
bmin, bmax = off.app.map(ai.open).map(js["Salary Band Min"]), off.app.map(ai.open).map(js["Salary Band Max"])
check("Offers", "Base CTC outside the opening's salary band", ((off["Base CTC"] < bmin) | (off["Base CTC"] > bmax)).sum(), N)

# Interviews
itv["sch"] = D(itv["Scheduled On"])
check("Interviews", "No Show / Cancelled but has a Score",
      (itv.Outcome.isin(["No Show", "Cancelled"]) & itv.Score.notna()).sum(), itv.Outcome.isin(["No Show", "Cancelled"]).sum())
check("Interviews", "Scheduled before the application's Applied On", (itv.sch < D(itv.app.map(ai["Applied On"]))).sum(), len(itv))
check("Interviews", "Scheduled after the application's Closed On", (itv.sch > D(itv.app.map(ai["Closed On"]))).sum(), len(itv))
first = itv.groupby("app").sch.min()
check("Interviews", "Application.First Interview On != earliest interview",
      (D(ai.loc[first.index, "First Interview On"]) != first).sum(), len(first))
check("Interviews", "Completed On differs from Scheduled On",
      (D(itv["Completed On"]).notna() & (D(itv["Completed On"]) != itv.sch)).sum(), itv["Completed On"].notna().sum())

dq = pd.DataFrame(DQ)
dq.to_csv(OUT / "data_quality.csv", index=False)
print("\nDATA QUALITY\n" + dq.to_string(index=False))

pd.DataFrame(F).to_csv(OUT / "findings.csv", index=False)
print(f"\nWrote {len(F)} findings, {len(dq)} checks to {OUT}")
