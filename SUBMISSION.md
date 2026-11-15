# TalentFlow × Acme: Q3 roadmap decision

**Data:** Airtable base `appYePRAI75PMbQNQ`, pulled once and cached; latest date in the data is **2026-08-30**, which I use as "as of". 300 candidates, 350 applications, 160 interviews, 36 offers, 26 hires, 24 openings.
**Reproduce:** `python fetch.py && python analyze.py`. Every number below comes from `outputs/findings.csv`, `outputs/data_quality.csv` or `outputs/source_funnel.csv`.
**Small-sample warning up front:** the whole decision rests on 26 hires and 36 offers. I give 95% Wilson intervals wherever a number carries a decision.

---

## D5: Memo (one page)

**To:** CEO · **Re:** Acme VP People's two asks for next quarter

**Bottom line.** Both of the VP's numbers reproduce exactly. Neither one supports the build she asked for. I'd spend the 6 engineer-weeks making Acme's offer and source data trustworthy, plus fixing the pipeline hygiene that's distorting both numbers. I would not bring the job-board integration forward.

**1. Job boards: "biggest channel, 26.9% of hires."** True as stated: 67.4% of applications and 7 of 26 hires. But referrals *also* produced 7 of 26 hires (26.9%), from 13 applications instead of 236. Job-board applications convert to a hire **3.0%** of the time (CI 1.4–6.0%). For referrals the rate is **53.8%** (CI 29–77%). The intervals don't overlap, so this isn't noise despite the small n. More job-board volume mostly means more screening work for recruiters. On top of that, 24 of the 27 applications that name a referrer are labelled as some other source. Fix the labelling and referrals become the biggest *hiring* channel (10 of 26 hires; job boards fall to 6).

**2. Offer acceptance: "around 72%, need it moving."** 72.2% is 26 accepted out of all 36 offers. That counts 5 "Pending" offers as failures. Four of those five already have a decision date; the status field was simply never updated. The fifth has had no answer for 120 days. Among decided offers, acceptance is **83.9%** (26/31, CI 67–93%). Only 5 offers were declined in ten months, 3 of them to counter-offers. That's too few to design a feature around. The board's number moves when the metric is defined correctly, and that's the fix I'd ship.

**What we're building (6 weeks):** (1) offer-status integrity plus a properly specified acceptance metric (1.5 wk); (2) source attribution and referral capture at the application level, with duplicate detection (2 wk); (3) closing a req also disposes of its live candidates, and hires can't exceed headcount (1.5 wk); 1 week of validation rules and buffer.

**What we're not building:** job-board integration (lowest-yield channel); offer-acceptance "improvement" features (n=5 declines); a time-to-hire dashboard for the board (the underlying dates aren't reliable yet).

**What I'd tell the VP:** "Your numbers are right. Your best channel is referrals, not job boards, and your acceptance rate is closer to 84% than 72%. Your system is under-reporting both. We'll fix the reporting first, so next quarter's board deck uses numbers you can defend."

**Biggest risks to this plan:** the data has real integrity problems (see D4). Most importantly, 59 of the 105 "active" applications belong to reqs that are already filled or cancelled, and 4 of 24 reqs show more hires than headcount. That calls the hire count of 26 itself into question. Both verdicts survive every alternative reading I tested, but the precise percentages don't.

**Next I'd look at:** how Source is set in practice (candidate-level? self-reported? job-board imports?); whether the 4 hires on cancelled reqs are real; recruiter time per source, the actual cost of job-board volume. With 6+ months of clean data, I'd revisit the job-board question on cost-per-hire.

---

## D1: Verdicts on the VP's two claims

| Claim | Verdict | The number that decides it |
|---|---|---|
| "Job boards are our biggest channel and bring 26.9% of hires → bring job-board integration forward" | **Don't build. Build something different:** source attribution + referral capture | **3.0% vs 53.8%** application→hire, job board vs referral (CI 1.4–6.0 vs 29.1–76.8). Same 7 hires from 236 vs 13 applications. |
| "Offer acceptance ~72%, the board wants it moving → build to move it" | **Don't build acceptance features. Build something different:** offer-status integrity + a correct metric | **83.9%** (26/31) acceptance among decided offers. 4 of 5 "Pending" offers already have a Decision On date. |

**Claim 1 detail.** Biggest channel by volume? Yes: 63.7% of candidates, 67.4% of applications. 26.9% of hires? Yes, 7/26, but the interval is 13.7–46.1%, and referral ties it exactly. "Bring the integration forward" assumes the bottleneck is job-board volume. It isn't: job boards already supply two-thirds of the pipeline and convert worst. Attribution is also unreliable in both directions. 24 of 27 applications with a named referrer aren't labelled Referral, and 10 of 13 Referral-labelled applications have no referrer. Under a "referrer wins" rule, job boards drop to 6/26 (23.1%) and referral rises to 10/26 (38.5%). **Either way, the verdict doesn't change.**

**Claim 2 detail.** The 72.2% is Accepted ÷ all offers, so undecided offers count as declines. The defensible range is **72.2%–86.1%**, depending on how the 5 pending offers resolve. The 4 pending offers with decision dates were 11–16 days old when decided, in line with accepted offers (median 10 days to decide). Decline reasons: Counter Offer 3, Location 1, Compensation 1. Quarterly: 2025Q4 7/8 decided accepted, 2026Q1 5/5, 2026Q2 8/12, 2026Q3 6/6. Q2 looks like a dip, but 4 declines is too few to call a trend.

---

## D2: The 6 engineer-weeks

### Build, in order

| # | What | Size | The number that justifies it |
|---|---|---|---|
| 1 | **Offer lifecycle integrity + acceptance metric (D3).** Status derived from Decision On; offers with no decision after 21 days become "Lapsed"; stale-pending alerts to the recruiter; dashboard tile built to the D3 spec. | 1.5 wk | 4/5 Pending offers already decided; reported rate 72.2% vs true 83.9%. The board is currently looking at an artefact. |
| 2 | **Application-level source attribution + referral capture.** Source stored per application, not per candidate; a named referrer always wins; required source + referrer link at intake; duplicate check on phone+name before a candidate is created. | 2 wk | 24/27 referred applications mis-attributed; referral converts 18× better than job boards (53.8% vs 3.0%); 6 duplicate people (2 with conflicting sources). Without this, every channel decision is a guess. |
| 3 | **Req-close cascade + headcount guard.** Filling or cancelling a req forces disposition of its active applications; hiring beyond Headcount is blocked; applications idle >30 days trigger a nudge. | 1.5 wk | 59/105 active applications sit on filled/cancelled reqs; 60/105 are >90 days old; 4/24 reqs have more hires than headcount; both cancelled reqs have hires (4 in total). |
| + | Validation rules for the remaining checks in D4 (no score on a no-show, interview dates inside the application's lifetime, offer within salary band), plus buffer | 1 wk | The interview, date and band failures in `data_quality.csv` (e.g. 4 scored no-shows, 16 interviews outside the application's dates, 7/36 offers out of band) are all preventable with a check when the record is saved. |

Total: 6 engineer-weeks. Sizes are rough, ±30%. #1 is first because it's the smallest piece, it's what the board sees, and it puts in place the "derive status from events" pattern that #3 reuses.

### Not building

| What | Why not |
|---|---|
| **Job-board integration (brought forward)** | 236 applications → 7 hires. Adding volume to a 3% channel adds screening load, not hires. Its share of hires is 23–27% depending on attribution, which we can't settle until #2 ships. Revisit next quarter on cost-per-hire with clean attribution. |
| **Offer-acceptance improvement features** (counter-offer alerts, comp benchmarking, offer-letter tooling) | 5 declines in ten months (3 counter-offers). I can't size a problem from n=5, and decided acceptance is already 84% (CI 67–93). Building here would be answering the loudest voice, not the data. |
| **Time-to-hire / funnel analytics for the board** | 25.7% of applications predate their own candidate record (median 106 days); 13/143 "First Interview On" dates disagree with the interview records; 56% of the "active" pipeline is on closed reqs. A dashboard now would publish wrong numbers with authority. It comes after #3. |

---

## D3: Metric spec: Offer Acceptance Rate (OAR)

**Purpose:** of the offers candidates have answered, what share did they accept?

**Unit of count:** one *offer outcome per application*. If an offer is re-issued (revised terms) on the same application, only the latest version counts. A person with offers on two different applications counts twice. Duplicate candidate records are merged first (phone + normalised name), and two offers to the same merged person for the same opening count once (latest).

**Cohort / time window:** offers are assigned to a period by **Offered On** (calendar quarter, Asia/Kolkata), never by decision date, so a period's denominator is fixed once it's issued. Default view: last completed quarter, plus the current quarter marked *provisional*.

**Outcome resolution**, applied in order:

| Recorded state | Resolved as | In numerator? | In denominator? |
|---|---|---|---|
| Accepted (with Decision On) | Accepted | ✓ | ✓ |
| Declined (with Decision On) | Declined | — | ✓ |
| No decision and Offered On ≥ 21 days ago | **Lapsed** (counts as not accepted) | — | ✓ |
| No decision and < 21 days old | Open | — | — (shown separately) |
| Status = Pending **but** Decision On present | **Data conflict** | — | — (shown separately, alert raised) |
| Offer rescinded by employer / req cancelled after offer | Withdrawn by company | — | — (shown separately) |
| Accepted then candidate never joins (renege) | Accepted | ✓ | ✓ (renege tracked as a separate "joining rate" metric) |

The 21-day lapse threshold is configurable. It's set just above the slowest decided offer in Acme's data (20 days; accepted offers take a median of 10).

**Formula:** `OAR = Accepted / (Accepted + Declined + Lapsed)` for the cohort.

**Provisional rule:** a period is *final* when every offer in it is resolved. At the latest that's period end + 21 days.

**What the dashboard shows:**
- Always the fraction **k / n** next to the percentage, and the Wilson 95% interval.
- **n < 10:** show the counts only, no percentage. **10 ≤ n < 30:** show the percentage greyed out with a "low sample" label.
- A **range** line: [all open + conflict offers declined … all accepted]. When the range is wider than 10 points, the headline is replaced by the range.
- Counts of Open, Data-conflict and Withdrawn-by-company offers next to the rate, linking to the records.
- Segments (source, department, level) appear only where the segment has n ≥ 10.
- The legacy "Accepted ÷ all offers" figure is shown once, labelled *legacy*, for one quarter, so the board sees why the number changed.

**Applied to Acme today:** n = 31 resolved (26 accepted, 5 declined, 0 lapsed). Pending offers: 4 data conflicts plus 1 with no decision after 120 days, which resolves as Lapsed. So the true denominator is 32: **OAR = 26/32 = 81.3%**. The dashboard would also flag the 4 conflicts; if those are fixed and turn out to be acceptances, it rises further.

---

## D4: What in this data I would not trust

### How I looked
I didn't hunt for anomalies one at a time. I ran the same six questions against every table, all coded in `analyze.py` → `outputs/data_quality.csv` (31 checks):
1. **Uniqueness:** is each real-world entity in the data once?
2. **Completeness:** are required fields populated for the record's state?
3. **State-machine consistency:** do Stage, Status and reason fields agree with each other?
4. **Temporal consistency:** do dates happen in a possible order, within and across tables?
5. **Cross-table agreement:** where the same fact is stored twice (offer date, first-interview date, recruiter, source vs referrer), do the copies match?
6. **Business rules:** headcount, salary bands, active work on closed reqs.

I also checked what *passed*. Milestone dates inside an application are never out of order (0/350), every rejected application has a reason, and every Hired application has a matching Accepted offer (26/26). So the problems are concentrated, not everywhere.

### What I found, by severity for the decisions

| Problem | How much | Affects |
|---|---|---|
| **Source vs referrer contradict each other** | 24/27 referred apps not labelled Referral; 10/13 Referral apps have no referrer; source lives on the candidate, but 50 candidates have 2 applications | Claim 1 directly. Hire share for job boards is 23.1–26.9% depending on which field you trust. |
| **"Pending" offers that are actually decided** | 4/5 Pending have a Decision On; 3/5 have a start date in the past; the one truly undecided offer is 120 days old (oldest Pending overall: 225 days) | Claim 2 directly. This alone explains 72% vs 84%. |
| **Pipeline left open on closed reqs** | 59/105 active apps on filled/cancelled reqs; 60/105 active apps >90 days old | Any funnel or conversion metric that uses "active"; open-pipeline counts are overstated. |
| **Hires vs openings don't reconcile** | 4/24 reqs have more hires than headcount; both cancelled reqs have hires (4); 2/8 "Filled" reqs have 0 hires; 5/11 "Open" reqs are already at headcount | The hire count (26) itself: 5 hires exceed their req's headcount and 4 sit on cancelled reqs (overlapping sets), so several hires may be linked to the wrong req or mis-staged. |
| **Duplicate people** | 6 people appear twice (same name + phone, different email); 2 of those pairs have conflicting sources; 24 applications | Source counts and candidate-level rates. Small effect (24 apps). |
| **Candidate "Created On" is unreliable** | 90/350 applications (25.7%) are dated before their candidate existed, median gap 106 days | Can't measure time-to-hire from candidate creation. Use Applied On. |
| **Stage/reason coding** | All 14 Withdrawn apps use Rejection Reason "Withdrew"; 2 Hired apps carry a rejection reason; 5/10 Offer-stage apps are Closed (declined offers never moved stage) | Funnel stage counts; "rejection reason" analytics would double-count withdrawals. |
| **Interview records vs application fields** | 13/143 First Interview On ≠ earliest interview; 9 interviews before the application date; 7 after it closed; 4 No-show/Cancelled interviews have scores | Time-in-stage, interviewer calibration. |
| **Offer fields** | 7/36 offers outside the req's salary band (4 above); 3/36 offer dates differ from the application's copy; 3/36 start date before offer date | Any comp analysis, and therefore any "fix compensation to raise acceptance" proposal. |
| Minor | 3 apps before the req opened; 4 apps with a recruiter other than the req's; 6 repeat applications to the same req; 4 candidates expecting less than current CTC; 21% of candidates have no Notes | Low. |

Also: every record's Airtable `createdTime` falls on a single day. The base was bulk-loaded, so there's no audit trail to tell when a field was last edited. The snapshot ends 2026-08-30, roughly 2.5 months before today.

### How this changes my answers
- **Claim 1 verdict holds under every attribution:** job-board conversion is 2.7–3.0%, the lowest of any meaningful channel. **But I would not quote "26.9%" or "biggest channel by hires" to the board.** The honest statement is "23–27% of hires, tied with or behind referrals".
- **Claim 2 verdict gets stronger:** the data problem *is* the finding. I'd quote "84% among decided offers (n=31)" and refuse to quote a trend.
- **Roadmap:** three of my three builds are data-integrity work. I'd rather spend the quarter making the next decision possible than make a feature bet on numbers I can't stand behind.
- **What I'd check with more time:** interview Acme recruiters on how Source is entered and whether job-board candidates are auto-imported (which would explain the created-date gap); open the 4 hires on cancelled reqs one by one; look at Airtable revision history for the Pending offers; get recruiter hours per channel to put a cost on job-board volume; check whether the 6 duplicate pairs were hired twice.

---

## Findings table
See `outputs/findings.csv` (claim, metric, value, method, confidence) and `outputs/data_quality.csv` (all 31 checks). Key rows:

| Claim | Metric | Value | Method | Confidence |
|---|---|---|---|---|
| C1 | Job Board share of applications | 236/350 = 67.4% | Apps joined to Candidate.Source | High |
| C1 | Job Board share of hires | 7/26 = 26.9% (CI 13.7–46.1) | Stage=Hired by source | High it reproduces; low as decision basis |
| C1 | Referral share of hires | 7/26 = 26.9% | same | High; n small |
| C1 | Job Board app→hire | 7/236 = 3.0% (CI 1.4–6.0) | hires/apps | Medium-high |
| C1 | Referral app→hire | 7/13 = 53.8% (CI 29.1–76.8) | hires/apps | Medium (n=13) |
| C1 | Referred apps not labelled Referral | 24/27 | Referred By vs Source | High |
| C1 | Hire share if referrer wins | Job Board 23.1%, Referral 38.5% | re-attribution | Medium |
| C2 | Naive acceptance | 26/36 = 72.2% | Accepted / all | High it reproduces; wrong definition |
| C2 | Acceptance among decided | 26/31 = 83.9% (CI 67.4–92.9) | Accepted / (Acc+Dec) | Medium |
| C2 | Bounds | 72.2%–86.1% | Pending → all decline / all accept | High |
| C2 | Pending with a decision date | 4/5 | Pending ∧ Decision On | High |
| C2 | OAR per D3 spec | 26/32 = 81.3% | 120-day undecided offer → Lapsed; 4 conflicts excluded | Medium |

---

## Method notes and uncertainty
- **"Hire" = Application.Stage = Hired.** Cross-checked: identical to the set of applications with an Accepted offer (26/26).
- **Source = Candidate.Source** joined onto each application (the base has no application-level source). That is itself one of the problems.
- **Confidence intervals:** Wilson 95%. With n=26 hires, differences under ~15 points in hire share aren't distinguishable. I don't rank Agency vs Career Site vs LinkedIn for that reason.
- **The OAR of 81.3% in D3** depends on the 21-day lapse rule I chose. Under the no-lapse definition it's 83.9%. Either way it's well above 72%.
- **Environment note:** the analysis sandbox couldn't reach api.airtable.com, so the data was pulled through the browser with the same pagination/rate-limit logic as `fetch.py`, and `analyze.py` was executed unchanged on that cache (Python 3.12 / pandas 2.2 via Pyodide). Running `fetch.py` then `analyze.py` locally should reproduce every number, provided the base hasn't changed.
