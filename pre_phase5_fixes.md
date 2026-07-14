# EchoLink — Pre-Phase-5 Fixes
*Plain language: what's broken, what we're doing about it*

---

## Fix 1 — FP-Growth: Guard Against Duplicate Rules

**File:** `phase_2c_fpgrowth.py`

### Problem
After FP-Growth generates its rules, there's no check to make sure the same directed pair (`A → B`) hasn't been written twice. If `mlxtend` ever emits a duplicate row (same antecedent AND same consequent), it would load into the database twice — inflating the rule count and skewing benchmark stats.

### Solution
Add one line after the rules are built:
```python
rules_df = rules_df.drop_duplicates(['antecedent', 'consequent'])
```
And print a warning if anything was actually dropped. This is a safety net — it doesn't change results if there are no duplicates, but prevents corruption if there ever are.

---

## Fix 2 — Passwords Hardcoded in Two Files

**Files:** `phase_3a_database.py`, `echolink_api/database.py`

### Problem
Both files contain the database password written directly in the code:
```python
'password': 'postgresql'
```
This is bad practice. If you ever change the password, share the code, or deploy it anywhere, you have to manually edit the source file. It's also a security risk.

### Solution
Read the password (and other connection details) from **environment variables** instead. If the variable isn't set, fall back to the current localhost defaults — so nothing breaks for you right now:
```python
'password': os.getenv('DB_PASSWORD', 'postgresql')
```
Now you can change credentials just by setting an environment variable, without touching any code.

---

## Fix 3 — Clarify Which Rules File Is the "Real" One

**Files:** `phase_3a_database.py`, `phase_2b_filter.py`

### Problem
There are two Apriori output files sitting in the folder:
- `apriori_rules.csv` — the full output (126,945 rules). This is what the database loads.
- `apriori_rules_clean.csv` — a filtered-down version made during exploration. This is **not** used anywhere.

The code already does the right thing (loads from `apriori_rules.csv`), but there's nothing in either file explaining this. Someone new reading the code would wonder which file is authoritative.

### Solution
Add a short comment in both files making the relationship explicit. Code-only — no logic changes, no data changes.

---

## Fix 4a — Wrong Numbers in the Benchmark Printout

**File:** `phase_2c_fpgrowth.py`

### Problem
At the end of the FP-Growth script, it prints a side-by-side comparison table showing Apriori vs FP-Growth stats. Two of the Apriori values are hardcoded from an old run and are now wrong:

| What's printed | What it should say |
|---|---|
| Apriori runtime: `76.1s` | `95.8s` (the actual v3 runtime, documented everywhere else) |
| Apriori rules: `324,278` | `126,945` (the actual v3 output) |

These wrong numbers would show up in terminal output and look inconsistent with the rest of the docs.

### Solution
Update the two hardcoded values to match the correct v3 numbers.

---

## Fix 4b — "Top 20 by Lift" Heading Is Misleading

**File:** `phase_2b_filter.py`

### Problem
Near the bottom of this script, it says:
```
🏆 Top 20 rules by Lift:
```
But the table is actually sorted by Jaccard — which is correct, since Jaccard is the primary ranking metric used everywhere in this project. Lift is only used in this script as a **filter gate** (`MIN_LIFT = 2.5` to remove weak rules), not as a ranking criterion. The heading is just wrong.

### Solution
Rename the heading to `🏆 Top 20 rules by Jaccard:` to match the actual sort order. No logic changes — the current Jaccard sort is the right behaviour.

---

## Fix 5 — Benchmark API Crashes on Empty Database

**File:** `echolink_api/main.py`

### Problem
The `/benchmark` API endpoint computes a "speedup factor" like this:
```python
max(runtime) / min(runtime)
```
If the database has no rulesets in it (e.g. after a wipe, before reload), this line throws a Python error and the whole API crashes with a 500 — with no useful message to the user or frontend.

The same crash happens for the "fastest algorithm" and "most rules" calculations.

### Solution
Add a simple guard: if the rulesets list is empty, return `null` for those fields instead of crashing. If there's only one ruleset, return `null` for speedup (you need two to compare). The endpoint stays functional under all conditions.

---

## Summary

| # | File(s) | What's wrong | Fix type |
|---|---|---|---|
| 1 | `phase_2c_fpgrowth.py` | No dedup guard on FP-Growth rules | Add 1 safety line |
| 2 | `phase_3a_database.py`, `echolink_api/database.py` | Password hardcoded in source | Read from env vars |
| 3 | `phase_3a_database.py`, `phase_2b_filter.py` | Unclear which rules file is canonical | Add comments only |
| 4a | `phase_2c_fpgrowth.py` | Stale Apriori stats in benchmark printout | Fix 2 constants |
| 4b | `phase_2b_filter.py` | Heading says "by Lift" but sort is already correct (Jaccard) | Rename heading only |
| 5 | `echolink_api/main.py` | `/benchmark` crashes if DB has no rulesets | Add empty-state guard |

> None of these require re-running Apriori or FP-Growth.
> No database schema changes.
> Fix 2 requires restarting the API server after editing.
