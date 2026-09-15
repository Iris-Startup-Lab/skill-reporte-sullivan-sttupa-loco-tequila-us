# Loco Tequila USA — Weekly Sales Report System

## An assessment: what exists, what it produces, and what it would take to make it production-ready

---

## 1. Why this document exists

You shared the folder containing the system that builds your weekly
**Sales Report Loco USA** workbook. We read all of it — every module, every rules
document, every generated output — to answer three questions:

1. **What is actually in there?** A precise inventory, so nothing depends on anyone's
   memory.
2. **What does it produce?** Sheet by sheet, with the real numbers it currently
   reports.
3. **What would it take to turn this into something that runs reliably, for anyone,
   without hand-editing code every week?** Including an honest list of what should
   *not* be carried forward.

One thing to say up front, because it frames everything below: **the business logic
in this system is the valuable part, and it is genuinely hard-won.** The code is
replaceable. The rules encoded in it — the double-counting fix, the account aliases,
the unit conversions, the historical corrections — represent months of real
discoveries, each one written down next to the bug it fixed. That is the asset. The
recommendations in this document are all in service of protecting it.

---

## 2. What is in the folder

**3,271 lines of Python across 20 modules**, plus four reference documents, four
historical data files, eight generated workbooks, and a separate voice-capture
subsystem holding 108 MB of field audio.

### 2.1 The data pipeline — 18 modules, 3,123 lines

| Module | Lines | What it does |
| :--- | ---: | :--- |
| `final_report.py` | 1,305 | The report builder. Writes all 9 sheets. This is what you run. |
| `pipeline.py` | 248 | Loads the Master Account List from the three per-rep route workbooks; does the fuzzy account matching; holds the alias, consolidation and override tables. |
| `ca_load.py` | 257 | SGWS (Signature) and Park Street California sales, current year plus 2025 history. Applies FOB and DTR margin rates; reroutes the six known Alebrije bundle orders. |
| `inventory_load.py` | 183 | On-hand inventory from three sources: SGWS, Park Street and Favorite Brands. Produces one row per product across eight warehouse columns. |
| `tx_monday_snapshots.py` | 173 | Reads every Monday Favorite Brands snapshot and **diffs consecutive weeks** to isolate true weekly volume. Skips non-7-day gaps rather than mis-attributing a multi-week jump to one week. |
| `acs_load.py` | 98 | ACS historical depletions, 2024 through July 2025. Walks 18 differently-named monthly tabs. |
| `mantarraya_load.py` | 81 | Shopify Memory Bottles: Mantarraya private sales plus core-rep sales. Filters to two employees, drops one permanently-excluded refunded order. |
| `dtc_load.py` | 77 | Shopify main store. Contains the multi-line-order tag fix and the `OUR COLLECTION` bundle explosion. |
| `verify_totals.py` | 68 | The post-run check suite. 16 assertions. |
| `ydrink_load.py` | 62 | Y Drink reporting for the Texas Class B child accounts. |
| `sgws2025_load.py` | 60 | SGWS 2025 history. |
| `wholesale_load.py` | 59 | Park Street wholesale sell-in; flags any customer outside the four known wholesalers. |
| `export_pdf.py` | 59 | PDF companion via LibreOffice. |
| `tx_load.py` | 58 | Favorite Brands Texas, current year. |
| `dtc_individuals.py` | 53 | Maps order tags to the 14 named DTC individuals. |
| `tx2025_load.py` | 52 | Favorite Brands 2025 history. |
| `config.py` | 187 | Finds this week's input folder and matches each file by keyword rather than exact name. |
| `tx_weekly_ydrink.py` | 43 | **Dead code** — superseded by `tx_monday_snapshots.py`, still on disk. |

### 2.2 The reference documents — the most valuable files in the folder

- **`docs/RULES.md` (15.6 KB, 12 sections).** The real business logic. Margin rates,
  unit conversions, the Melrose Gas double-counting rule, the Class B hierarchy,
  order definitions, the alias and consolidation tables, the one-time historical
  corrections, formatting conventions. Your own README says to read this before
  touching any code, and that is correct advice.
- **`docs/KNOWN_ISSUES.md`.** What was simplified or approximated at the last
  handoff. Worth noting: three of the six items listed here **have since been
  fixed** in code, so this file now understates the system.
- **`docs/INPUT_FILE_REFERENCE.md`.** The 14 expected input sources and their
  filename patterns.
- **`README.md`.** How to run it. Now partly out of date — steps 2 and 3 tell you to
  hand-edit paths and dates in the source each week, which `config.py` has since
  automated.

### 2.3 Reference data that never refreshes

`static/` holds four one-time historical files totalling 212 KB: Favorite Brands
2025 Texas depletions, Park Street 2025 full data, SGWS 2025, and the Y Drink
reporting snapshot. A fifth historical source, the ACS 2024–2025 depletion summary,
is referenced by an absolute path rather than copied in.

### 2.4 The field-visit voice capture subsystem

`Field Sales Reports/` — 148 lines across two scripts, plus **93 audio files
(~108 MB)** and 92 transcripts. It transcribes rep voice memos locally, then uses an
AI model to extract structured visit data (account, activation type, order line
items) into CSVs for human review.

Section 5.2 covers this separately, because our recommendation differs from the rest.

### 2.5 The generated outputs

Seven weekly workbooks in `outputs/`, from July 20 through August 31, 2026, each
roughly 120 KB — plus a standalone `2025 vs 2026 Depletions Comparison.xlsx` that
nothing in the code reads or writes, so it appears to be maintained by hand.

**A structural point that matters a great deal:** the weekly report is built by
**copying last week's workbook and overwriting the data cells**. There is no
template file. All the formatting, headers, merged cells, number formats — and the
entire 2025 and 2024 historical record — exist *only inside those `.xlsx` files*.
Lose `outputs/`, and the report's structure and history are gone with it.

---

## 3. What the system produces

### 3.1 The workbook — nine sheets

Verified against `Sales Report Loco USA August 31, 2026.xlsx`.

| # | Sheet | Contents |
| :--- | :--- | :--- |
| 1 | **YTD Summary** | Ten metrics per region — depletions in 9L and bottles, gross margin, GM per 9L case, on- and off-premise account counts, order count, average order size in both bottles and GM. Rows for TOTAL, California, Texas, DTC and Ecommerce; then one row per salesperson; then a **Wholesale** block for the four distributors in 9L and revenue; a **Direct to Retail** block; and a **Product** block across nine SKUs. |
| 2 | **Monthly Summary** | The same regions across all twelve months, in four stacked blocks: bottles, gross margin, wholesale 9L, wholesale revenue. |
| 3 | **Salesperson by Week** | Weeks 1–52 down the rows, one column per rep, plus a year-to-date row. |
| 4 | **Accounts H2-2026** | Every account × July–December, with full-year YTD, salesperson, channel and Class B parent. Placed before H1 by your convention. |
| 5 | **Accounts H1-2026** | Same, January–June. |
| 6 | **Account Summary Total Business** | Lifetime bottles and GM per account; order counts for 2026, 2025, 2024 and all-time; average months between orders; last order date; days since last order; channel; salesperson. |
| 7 | **DTC Sales by Month** | Twelve months × (bottles, GM) in three sections: by product, by the 14 named DTC individuals, and ecommerce. |
| 8 | **DTC Sales by Year** | 2026, 2025, 2024 and combined. Only 2026 is recomputed; the history is preserved in place. |
| 9 | **Inventory** | Each product across grand total 9L, total CA, total TX, SO CAL SGWS, NOR CAL SGWS, CA Park Street, Texas FB, open orders and inbound — plus a separate non-sellable/samples block. |

**One sheet specified in `RULES.md` does not exist: Overdue Accounts.** Sections 9
and 10 define it, including the overdue threshold formula, but no code builds it and
it is not in the workbook.

### 3.2 The numbers it currently reports

As of the August 31 workbook, so the scale is concrete:

| | 9L cases | Bottles | Gross margin | GM / 9L | On-prem | Off-prem | Orders |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **TOTAL** | **90.67** | **1,088** | | | 97 | 43 | |
| California | 46.08 | 553 | $27,835.60 | $604.03 | 34 | 20 | 110 |
| Texas | 27.08 | 325 | $14,316.66 | $528.62 | 63 | 23 | 63 |

Inventory on the same date: **212.98** 9L cases total — CA 196.07, TX 16.92.

And from the depletions comparison: 2025 closed at 992 bottles and $46,701 gross
margin; 2026 stands at 1,051 bottles and $56,708 — **+5.9% in volume but +21.4% in
margin**. Excluding Total Wine, the same comparison reads +86.3% and +89.8%.

### 3.3 The PDF companion

`export_pdf.py` sets print areas from real content bounds, fits each sheet to width
in landscape (portrait only for Salesperson by Week), repeats the header row, adds
page footers — then converts via LibreOffice.

### 3.4 The verification suite

`verify_totals.py` runs 16 assertions with a 5-cent tolerance and exits with an error
on any failure. Each one checks that a TOTAL row equals the sum of the detail rows
beneath it, across the YTD Summary, Monthly Summary, both DTC sheets, Inventory and
Salesperson by Week.

It exists because two real bugs shipped: a Region TOTAL that silently included
Melrose, and a Combined-Years column that dropped values because of a numeric type
mismatch. The principle it enforces — *if a row says TOTAL, it must be an accurate
total of the figures below it* — is the right one, and we have adopted it.

Two cross-checks that `RULES.md` identifies as having caught real bugs are **not** in
the suite and remain manual: that each rep's weekly total equals their YTD Summary
total, and that the on-premise account count matches the regional row.

---

## 4. What can be carried forward

Most of the value, and more cheaply than you might expect — because the valuable
parts are **rules, not code**.

| What | Why it transfers well |
| :--- | :--- |
| **Margin rates per bottle** — FOB for three-tier, DTR for direct-to-retail and DTC, including Aureo's two rates by channel | Becomes an editable configuration file you can update yourself, with no code change. This one item lets us report gross margin, which we could not before. |
| **Unit conversions** — ×6 for 4.5L case equivalents, Park Street's per-row unit handling, ÷12 to 9L cases with the 200 mL exception at ÷45 | Small, exact, and easy to verify |
| **Account → salesperson → channel mapping** | Derivable directly from your Accounts H1/H2 sheets. This is the single highest-impact item: it is what currently leaves a large share of California volume unattributed. |
| **The alias and chain-consolidation tables** | Become data files rather than code constants |
| **Order definitions** — California as account-and-date, Texas as account-and-week with an increase, DTC as distinct order IDs | Enables the YTD order counts you asked for |
| **The Texas attribution default** and the rule to ignore ACS's own rep field | Two lines of rule, materially better attribution |
| **The Monday-snapshot diffing method** | The only sound way to get true weekly Texas volume from cumulative reports. You have 119 weekly snapshots; today only the most recent is read. |
| **The Shopify multi-line-order fix, the word-boundary account matcher, the total-rows-must-sum invariant** | Each of these is a real bug already found and solved. Re-deriving them would be waste. |

What you gain in exchange:

- **No weekly code editing.** Point at a folder; the system identifies what is there,
  says what it found and what is missing, and generates from that.
- **Gross margin in our reporting**, which was previously impossible.
- **A version history.** Every change recorded, every past state recoverable.
- **Runs on any machine** — Mac, Windows, or in the browser — with no Python setup,
  no LibreOffice, no Google Drive path assumptions.
- **An interactive dashboard alongside the workbook**, with a tab showing which file
  and column every number came from, and a listing of every unattributed line with
  the reason it could not be assigned.
- **A workbook with live pivot tables and charts** built on a single underlying
  dataset — so any figure can be drilled into, and the totals are independently
  re-derived by Excel as a cross-check. Your current workbooks contain no pivot
  tables and no native charts; every figure is a static value.

---

## 5. What should not be carried forward

### 5.1 The copy-forward workbook model

Not because it is badly built — it is ingenious given the constraints — but because
its structure and its entire history live only inside the output files. There is no
template under version control. Reproducing that model would mean inheriting that
fragility, in order to hand you the Excel file you already have.

Instead we build from a versioned template that contains no data, so the layout is
recoverable independently of any output.

### 5.2 The voice transcription subsystem

This one we recommend setting aside, and the reason is not only technical.

**Technically**, it cannot run in the same environment as the reporting. That
environment has no internet access and cannot install software, and this pipeline
needs `ffmpeg` installed, a speech model downloaded, and an API key with network
access. Those are irreconcilable.

**But the stronger argument is about the workflow itself.** Looking at the current
state:

- 92 transcripts are waiting for extraction.
- The approved folder is **empty** — the review loop has never been completed once,
  end to end.
- Four per-rep folders of audio sit inside the inbox where the script cannot see
  them, because it only reads files at the top level. That audio would never be
  processed no matter how long it ran.

And the output of all that machinery is a small set of structured fields: account,
date, rep, activation type, and order line items. A rep could enter those in under a
minute on a phone form, correctly the first time, with no transcription step and no
human reviewing every extracted row afterwards.

Your own documentation already treats this as Phase 2, not connected to the weekly
report. We agree — and we would go further: **capture the structured data at the
source instead.** The 93 recordings already made are not wasted; they are a good
argument for what fields the form should have.

If you do want the transcription flow eventually, it belongs as a separate tool on a
normal computer, feeding its reviewed CSVs in as one more input. It should not be
inside the reporting system.

### 5.3 Machine-specific assumptions

Three things tie the system to one computer and one person:

- **Three absolute Google Drive paths** for the route workbooks, the Monday snapshot
  folder, and the ACS file.
- **The project must sit inside the Drive folder** that holds the weekly data
  folders, because inputs are located relative to the project's own parent directory.
- **Two macOS-only behaviours** that stop it running on Windows at all: a date format
  flag that raises an error, and the LibreOffice conversion step with its POSIX-only
  path handling.

None of these is hard to fix. They are listed because they are why the system
currently runs on exactly one machine.

### 5.4 Smaller items worth retiring

- **The year 2026 is hardcoded** in five places as the current year. It will not roll
  over on its own.
- **One dead module** (`tx_weekly_ydrink.py`) still on disk.
- **A dependency listed but never used**, and **one used but not listed** — so a fresh
  install fails partway through.
- **Documentation drift**: `RULES.md` still describes the Melrose netting behaviour
  that was deliberately removed in August; `INPUT_FILE_REFERENCE.md` says the three
  inventory loaders were never rebuilt, but they exist and work.

---

## 6. What is needed to make it production-ready

### 6.1 Files we need from you

| File | Why |
| :--- | :--- |
| **Bottle Costs and Gross Margin workbook** | Your `INPUT_FILE_REFERENCE.md` names it as the source for the margin rates, which are currently transcribed into code. We want the source file, or written confirmation of the rates, before we publish any margin figure. |
| **The Master Account List**, in its current form | `RULES.md` notes an updated version was requested and not yet received. This is what drives salesperson and channel attribution. |
| **The ACS 2024–2025 depletion summary** | Referenced by absolute path, never copied into the project. It is the basis of all lifetime account metrics. |
| **One complete weekly input folder** | We have the code and the outputs but no raw inputs, so nothing can be run or reconciled end to end today. |

### 6.2 Decisions only you can make

1. **Melrose Gas and Shopify.** Your report treats Melrose as sell-in to your own
   warehouse and excludes untagged Shopify orders from volume. Ours currently counts
   DTC on top of Melrose's depletion. **These produce different totals, and the two
   cannot be reconciled until you decide which is correct.** This is the single
   biggest open item.
2. **Aureo's two margin rates.** Which sources count as Park Street wholesale at
   $614.50 and which as DTC at $864.50?
3. **The Texas default** — unmatched accounts to Joe Pat Clayton and Off Premise.
   Adopting it materially changes the rep leaderboard. Confirm?
4. **The six approved chain consolidations**, and routing anything beginning
   "TOTAL WINE" to a consolidated row under Sara. Confirm these are still current?
5. **The one-time historical corrections** in `RULES.md` section 7 — still to be
   applied, or superseded?
6. **Gross margin visibility.** Aggregate only, or per account and per salesperson?
7. **The Overdue Accounts sheet** — specified but never built. Do you want it?
8. **How much raw detail should the deliverable contain?** A single underlying dataset
   with one row per transaction, including account and salesperson names, is what
   makes drill-down and verification possible. It is also the most sensitive file we
   would produce: anyone holding it can reconstruct the business. Your call on who
   receives it.

### 6.3 What we would do regardless

- Move every rule out of code into editable configuration files, so rates, aliases
  and mappings can be updated without a developer.
- Replace the four separate "unknown" labels with a single ranked attribution ladder
  where every line carries the rule that resolved it — and every unresolved line
  carries the specific reason it could not be.
- Keep the total-rows-must-sum checks, but anchored to derived ranges rather than
  fixed row numbers. Your current suite breaks whenever a row is inserted, and its
  own header comment notes this already happened.
- Add the two manual cross-checks `RULES.md` identifies as bug-catchers to the
  automated suite.
- Read all 119 Monday snapshots rather than only the latest, which is what makes a
  genuine weekly Texas view possible.

---

## 7. The risk worth naming

Your README states it more plainly than we would:

> *"This project has previously been rebuilt from a human's memory of a long chat
> history after a sandbox reset — that's fragile and error-prone."*

That was the right diagnosis and writing `RULES.md` was the right response. But the
exposure has not fully closed:

- **The workbook's structure and its 2024–2025 history exist only inside the output
  files.** There is no template and no separate record.
- **Three of the fourteen input sources are reachable only through one person's
  Drive paths.**
- **`RULES.md` and the code have already drifted apart** in at least two places, which
  means the written record and the actual behaviour are no longer the same thing.
- **The system runs on one machine**, and would not start on a Windows computer.

None of this is urgent in the sense that this week's report is at risk. It is urgent
in the sense that the knowledge is concentrated in a way that a single laptop
failure, or a single person's absence, would expose.

---

## 8. What we recommend

**Take the rules, not the workbook.**

Carry across the margin rates, the unit conversions, the account mapping, the alias
tables, the order definitions and the hard-won fixes — all of it as configuration you
can read and edit. Generate from that a dashboard, a PDF, and an Excel workbook with
live pivot tables over a single underlying dataset, so every figure can be traced
back to the file and column it came from and independently re-derived.

Keep your existing workbook running in parallel until the two agree, number for
number, on the same week's data. That comparison is the acceptance test, and it is
also the only honest way to settle the Melrose question.

Leave the voice capture aside, and if the field-visit data matters, capture it as
structured data at the point of the visit rather than reconstructing it from audio
afterwards.

---

*Prepared from a complete review of the shared folder: all 20 Python modules, the
four reference documents, the four historical data files, and all eight generated
workbooks. Figures quoted are from the August 31, 2026 workbook and the 2025 vs 2026
depletions comparison.*
