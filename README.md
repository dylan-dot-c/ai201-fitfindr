# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

A user types what secondhand item they're after in plain language, like
`vintage graphic tee under $30` or `denim jacket size S`. FitFindr searches 40
thrift listings from Depop, thredUp and Poshmark for the best match within
that price and size, then suggests one or two outfits built around it using
clothes from the user's saved wardrobe (or general styling ideas if the
wardrobe is empty). Finally it writes a short caption they could post about the
find, mentioning the item, its price and the platform. If nothing matches, it
stops before calling the model and tells the user what to change — raise the
price limit, drop the size, or use different words.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Finds listings in `data/listings.json` whose text shares keywords with the description, keeps only the ones that pass the size and price filters, and returns them best match first.
- **Inputs:**
  - `description` (str) — free-text keywords, e.g. `"vintage graphic tee"`. Lowercased and split into words; words under 2 characters and stopwords (`a`, `the`, `for`, `in`, `looking`, `size`, `under`, …) are dropped.
  - `size` (str | None, default `None`) — `None` skips size filtering. Otherwise both the requested size and the listing's size are lowercased and split into tokens on spaces, `/` and parentheses. A listing matches if every requested token is one of the listing's tokens, so `"M"` matches `"S/M"` and `"M/L"`, `"8"` matches `"US 8"` but not `"US 8.5"`, and `"S"` does **not** match `"US 9"` or `"XL"`. Listings whose size starts with `"One Size"` match any requested size.
  - `max_price` (float | None, default `None`) — inclusive ceiling. `None` skips price filtering.
- **Returns:** a `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` (10) listing dicts, sorted by score, highest first (ties keep data order). Score = number of distinct keywords that appear as whole words in the listing's title, description, category, style_tags, colors or brand. Listings scoring 0 are dropped. Each dict is the unchanged listing with all 11 fields: `id` (str), `title` (str), `description` (str), `category` (str), `style_tags` (list[str]), `size` (str), `condition` (str), `price` (float), `colors` (list[str]), `brand` (str or None), `platform` (str).
- **When it has nothing:** returns `[]` — an empty list, never `None`, never an exception. This includes a description with no usable keywords.

### `suggest_outfit`

- **What it does:** Asks the model (through `generate()`) for one or two outfits built around the new item, using pieces the user already owns.
- **Inputs:**
  - `new_item` (dict) — one listing dict, same 11 fields as above.
  - `wardrobe` (dict) — `{"items": list[dict]}`, each item with `name` (str), `category` (str), `colors` (list[str]), `style_tags` (list[str]), `notes` (str or None). `items` may be empty.
- **Returns:** a non-empty `str` of plain text describing one or two outfits. With a non-empty wardrobe, each outfit names at least one wardrobe item by its `name`.
- **When it has nothing:** if `wardrobe["items"]` is empty or missing, it still calls the model but asks for general styling advice for the item, and the returned string starts with `"No saved wardrobe yet — general styling ideas:"`. If the model sends back blank text, it returns `"Couldn't come up with an outfit for <title> — try again."` It never returns `""`. (`ModelUnavailable` is not caught here; the loop handles it in unit 4.)

### `create_fit_card`

- **What it does:** Asks the model (through `generate()`) to write a short caption someone would post about the find and how they're wearing it.
- **Inputs:**
  - `outfit` (str) — the string `suggest_outfit` returned.
  - `new_item` (dict) — the same listing dict that went into `suggest_outfit`.
- **Returns:** a `str` caption of 2–4 sentences that mentions the item, its price as `$NN`, and its platform, each once. Not cached between runs of the same input at `TEMPERATURE = 0.9`, so wording varies.
- **When it has nothing:** if `outfit` is empty or only whitespace, it does **not** call the model and returns `"Can't write a fit card for <title>: no outfit suggestion was given."`

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that names what the user could change (price ceiling, size, or wording) and stop — `suggest_outfit` and `create_fit_card` are never called and `session["fit_card"]` stays `None`. Otherwise, put the first result in `session["selected_item"]` and go to `suggest_outfit`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, no model call — `agent.py::parse_query`. A price like `under $30`, `$30`, `max $40` or `under 30` becomes `max_price`; `size M`, `size US 8` or `size W30 L30` becomes `size`; whatever text is left is the `description`.

**What moves through the session:** `query` → `parsed` (description, size, max_price) → `search_results` (up to 10 listing dicts) → either `error` (and stop) or `selected_item` (the first result) → `outfit_suggestion` → `fit_card`. Each tool reads its inputs back out of the session, not from the previous call's return value.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'
  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit one pairs the Y2K baby tee with baggy straight-leg jeans, dark wash for a classic 2000s streetwear look. Add chunky white sneakers and the black crossbody bag to complete the casual, nostalgic everyday style.

Outfit two combines the Y2K baby tee with wide-leg khaki trousers for a softer earth-toned mix of cottagecore and minimal aesthetics. Layer the vintage black denim jacket over top and finish the outfit with black combat boots to add a subtle edge.

  Fit card: Scored this dream Y2K baby tee on Depop for just $18 and I’m obsessed with the butterfly print. Gives me total 2000s streetwear energy when paired with baggy jeans, but looks just as good dressed down with khakis.
```

And a query that matches nothing — it stops before `suggest_outfit`, makes no model calls, and `fit_card` stays `None`:

```
$ python app.py ask 'designer ballgown size XXS under $5'
  Nothing matched "designer ballgown" in size XXS under $5. Try: use different words for the item — the listings use terms like tee, hoodie, jeans, cargo pants, jacket, boots and bag.

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; r=search_listings('graphic tee', max_price=30); print(len(r), [(x['title'],x['price'],x['size']) for x in r])"
6 [('Y2K Baby Tee — Butterfly Print', 18.0, 'S/M'), ('Graphic Tee — 2003 Tour Bootleg Style', 24.0, 'L'), ('Mesh Long-Sleeve Top — Black', 15.0, 'S/M'), ('Vintage Band Tee — Faded Grey', 19.0, 'L'), ('Low-Rise Cargo Pants — Khaki', 27.0, 'W29'), ('Vintage Graphic Hoodie — Faded Black', 26.0, 'L')]

$ python -c "from tools import search_listings; print(search_listings('ballgown tiara', max_price=5))"
[]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Outfit 1: Pair the vintage Levi's with the white ribbed tank top for a classic, fitted silhouette. Layer the vintage black denim jacket on top for a cohesive denim-on-denim look. Finish the outfit with the chunky white sneakers and the black crossbody bag for an effortless, everyday streetwear style.

Outfit 2: Combine the medium wash jeans with the oversized grey crewneck sweatshirt for a relaxed, cozy aesthetic. Cinch the waist using the brown leather belt to add definition, and step into the black combat boots to introduce a touch of grunge edge. Bring the black crossbody bag along to complete this comfortable, casual ensemble.

$ python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"
No saved wardrobe yet — general styling ideas: For a casual daytime look, pair the vintage Levi's with a simple white ribbed tank top or a fitted black baby tee. Add a classic black leather belt, a pair of worn-in canvas sneakers like white Converse or black Vans, and a canvas tote bag for an effortless, streetwear-inspired aesthetic. [...]
```

```
$ AI201_CACHE=0 python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"   # run 3 times
Scored these vintage Levi's 501 jeans on Depop for just $38 and I am obsessed. The medium wash indigo has the ultimate broken-in streetwear vibe. Paired them with crisp white sneakers for an effortless classic look.
Scored these vintage Levi's 501 jeans on depop for just $38 and I am obsessed. The medium wash is so effortlessly 90s. Paired them with crisp white sneakers for the ultimate everyday streetwear vibe.
Found these vintage Levi's 501 jeans on Depop for just $38 and I am obsessed. The medium wash indigo gives off the ultimate effortless streetwear vibe. Paired them with crisp white sneakers and honestly, nothing beats classic denim that actually fits right.

$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"
Can't write a fit card for Vintage Levi's 501 Jeans — Medium Wash: no outfit suggestion was given.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1 — testing my criteria**

- _What I asked for:_ I gave Claude my three draft criteria (state, fit card, my choice) and asked it to make sure they were valid and checkable. My drafts were things like "the fit must be referred to a reasonable size if not it's wrong" and "the category for each must be a suitable category".
- _What came back:_ It said none of the three could be tested from the sentence alone: "reasonable size" could mean caption length or clothing size, "suitable category" had no definition, and "in the original data set" didn't say what to compare. It suggested comparing the listing `id` at each step, a sentence and character limit, and a fixed word → category map using the five categories actually in `listings.json`. It also pointed out that passing the item through the session is plain code with no model, so 4 of 5 was too easy a target for criterion 3.
- _What I changed:_ Criterion 3 now compares `id`s and the target went up to 5 of 5. Criterion 4 became 2–4 sentences and under 300 characters (matching what my Tool Inventory promises). Criterion 5 now names the expected category for each of five query words. I had Claude draft the "why this target" reasons from my tool specs, then read them to check I could defend each one.

**Moment 2 — tools.py wouldn't import**

- _What I asked for:_ I asked Claude to build the three tools in `tools.py` to match the specs I'd already written in my Tool Inventory.
- _What came back:_ The first version didn't run: `python -c "import tools"` failed with `SyntaxError: unterminated f-string literal (detected at line 176)`. The script that wrote the file had turned the `\n` escapes inside the prompt strings into real line breaks, which broke the f-strings.
- _What I changed:_ I restored the stub with `git checkout tools.py` and rebuilt it with smaller edits, one function at a time. Then I tested each tool on its own from the terminal before wiring the loop. The search results also showed Low-Rise Cargo Pants coming back for "graphic tee", which I kept as a known weakness of keyword matching for unit 4.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

Produced by `python run_eval.py --label before` (`run_eval.py::main`, which calls
`agent.py::run_agent`), caching off, `TEMPERATURE` 0.9. Full output:
[`results/run_2026-10-13_1003_before.md`](results/run_2026-10-13_1003_before.md).
14 scenarios × 5 tries = 70 runs, 93 model calls.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1. A matching query completes all three tools | 4 of 5 | FAIL | FAIL | FAIL | FAIL | FAIL | MISSED (0/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item search found is the item the next tools receive | 5 of 5 | PASS | PASS | FAIL | PASS | PASS | MISSED (4/5) |
| 4. The fit card is a postable length | 4 of 5 | FAIL | FAIL | FAIL | FAIL | PASS | MISSED (1/5) |
| 5. Search returns the right category for the item type | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**How each row was scored**

- **1**: `vintage graphic tee under $30`, five runs. PASS = no early stop and
  `create_fit_card` returned a card.
- **2**: `designer ballgown size XXS under $5`, five runs. PASS = stopped,
  `suggest_outfit` never appears in the trace, and the message says what to try.
- **3**: the criterion is "for 5 queries", so Try N is query N: track jacket,
  slip dress, platform sneakers, denim jacket, cargo pants, each run 5 times.
  A query PASSes if in at least one of its runs the trace shows the selected
  `id` going unchanged into both `suggest_outfit` and `create_fit_card`, and no
  run ever shows a different `id`. Platform sneakers failed because none of
  its five runs got past `suggest_outfit`, so its `id` never reached
  `create_fit_card`. Across all 70 runs there were **0 id mismatches**:
  65 runs reached `suggest_outfit` and 28 reached `create_fit_card`, always with
  the selected `id`, and every `id` exists in `data/listings.json`.
- **4**: `baggy jeans`, the same item (`lst_031`) five times. PASS = a card
  of 2–4 sentences and ≤ 300 characters. Tries 1–4 produced no card at all.
- **5**: Try N is query N: `black jacket`, `baggy jeans`, `vintage band tee`,
  `white sneakers`, `leather bag`. PASS = the top result's `category` is the
  expected one. Search doesn't call the model, so each query gave the same top
  result in all five of its runs.

**Why runs stopped early:** 49 of the 65 runs that should have completed
stopped at a model call. The errors, counted from the results file: **36 ×
`503 UNAVAILABLE`** ("This model is currently experiencing high demand"),
**9 × `504 DEADLINE_EXCEEDED`**, **4 × connection failure**. No run crashed.

### Real output, one try per criterion

**Criterion 1, try 1** (`agent.py::run_agent` via `run_eval.py::run_once`):

```
- stopped early: yes — Found Y2K Baby Tee — Butterfly Print ($18 on depop), but couldn't write an outfit suggestion: the AI model is overloaded right now (the service returned 503, high demand). Nothing is wrong with your setup — wait a minute and ask again.
- selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
- search_results: 10

[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: selected id lst_002, going to suggest_outfit
[3] suggest_outfit
      in:  id lst_002 + 10 wardrobe items
      →    ModelUnavailable, stopping: Couldn't reach the model: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}
```

Try 2 of the same criterion stopped at the same step with a different error:

```
- stopped early: yes — Found Y2K Baby Tee — Butterfly Print ($18 on depop), but couldn't write an outfit suggestion. Couldn't reach the model: 504 DEADLINE_EXCEEDED. {'error': {'code': 504, 'message': 'Deadline expired before operation could complete.', 'status': 'DEADLINE_EXCEEDED'}}
```

**Criterion 2, try 1** (the branch in `agent.py::run_agent`, message from `agent.py::_no_results_message`):

```
- stopped early: yes — Nothing matched "designer ballgown" in size XXS under $5. Try: use different words for the item — the listings use terms like tee, hoodie, jeans, cargo pants, jacket, boots and bag.
- selected_item: (none)
- search_results: 0

[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit
[3] search_listings (via MCP, hint)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': None}
      out: [] (empty)
[4] search_listings (via MCP, hint)
      in:  {'description': 'designer ballgown', 'size': None, 'max_price': 5.0}
      out: [] (empty)
```

**Criterion 3, slip dress try 2.** The `id` `lst_013` is the same at all three steps (`agent.py::run_agent`):

```
[2] search_listings (via MCP)
      in:  {'description': 'silk slip dress', 'size': None, 'max_price': 40.0}
      out: 2 items: 90s Silk Slip Dress — Floral, Midi Length, Silk Button-Down — Sage Green
      →    branch: selected id lst_013, going to suggest_outfit
[3] suggest_outfit
      in:  id lst_013 + 10 wardrobe items
      out: Outfit one: Layer the 90s silk slip dress over the white ribbed tank top for a nostalgic 90s textured look, th…
[4] create_fit_card
      in:  id lst_013 + outfit suggestion
      out: Found this dreamy 90s silk slip dress on Depop for just $30 and I am obsessed. Totally channeling that grunge-…
```

The failing query was platform sneakers. All five of its runs stopped this way, before `create_fit_card`:

```
- stopped early: yes — Found Platform Sneakers — White Chunky Sole ($48 on poshmark), but couldn't write an outfit suggestion: the AI model is overloaded right now (the service returned 503, high demand). Nothing is wrong with your setup — wait a minute and ask again.
```

**Criterion 4, try 5** (`tools.py::create_fit_card`). This was the only one of the five tries that produced a card: 3 sentences, 199 characters, PASS.

```
Scored these baggy carpenter jeans on Depop for just $36 and I’m obsessed. They have that perfect 90s workwear slouch. Honestly living in them with chunky sneakers or an oversized crewneck right now.
```

**Criterion 5**, top result per query (`tools.py::search_listings` via `mcp_server.py`). Each query returned the same top result in all five of its runs:

```
black jacket      -> lst_022  90s Leather Bomber — Black             outerwear    (expected outerwear)   PASS
baggy jeans       -> lst_031  Baggy Carpenter Jeans — Dark Wash      bottoms      (expected bottoms)     PASS
vintage band tee  -> lst_006  Graphic Tee — 2003 Tour Bootleg Style  tops         (expected tops)        PASS
white sneakers    -> lst_019  Platform Sneakers — White Chunky Sole  shoes        (expected shoes)       PASS
leather bag       -> lst_039  Mini Shoulder Bag — Tan Leather        accessories  (expected accessories) PASS
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| #   | Criterion | Target | Verdict | How I decided |
| --- | --------- | ------ | ------- | ------------- |
| 1   | A matching query completes all three tools | 4 of 5 | **MISSED (0/5)** | No run of `vintage graphic tee under $30` returned a fit card. Every one stopped at `suggest_outfit` on a 503 or 504. 0 is below 4. |
| 2   | An impossible query stops before the second tool | 5 of 5 | **MET (5/5)** | All five stopped after `search_listings` returned `[]`. `suggest_outfit` is absent from every trace, 0 model calls were made, and the message names what to change. |
| 3   | The item search found is the item the next tools receive | 5 of 5 | **MISSED (4/5)** | Four queries showed the same `id` going into both later tools. Platform sneakers never reached `create_fit_card` in five runs, so for that query the criterion's condition was never shown to hold. 5 of 5 means a single unproven query is a miss. |
| 4   | The fit card is a postable length | 4 of 5 | **MISSED (1/5)** | The criterion asks for a postable card on five runs of the same item. Four of the five runs produced no card, and no card is not a postable card. The one card that was produced passed (3 sentences, 199 characters). |
| 5   | Search returns the right category for the item type | 4 of 5 | **MET (5/5)** | The top result's `category` matched the expected one for all five item types, identically in all five runs of each. |

**Diagnoses**

**The pattern: criteria 1, 3 and 4 are one miss, not three.** All of them
missed for the same reason, at the same place: **the model call, inside
`generate.py::generate`**.

- *What happened:* 93 model calls were made and 49 failed (53%). The errors
  were 36 × `503 UNAVAILABLE` ("high demand"), 9 × `504 DEADLINE_EXCEEDED` and
  4 × connection failure. By step, 37 failed in `suggest_outfit` and 12 in
  `create_fit_card`.
- *The mechanism:* `generate()` has a retry loop (`MAX_RETRIES = 5`), but it
  only retries when the error text looks like a rate limit (`429`, "resource
  exhausted", "rate limit"). A 503 or 504 doesn't match, so it raises
  `ModelUnavailable` on the **first** attempt. The eval log contains **zero**
  `[rate limit]` retry lines. A temporary overload that would likely have
  cleared in a few seconds is treated the same as a revoked API key.
- *What did NOT fail:* the tools' logic, the branch and the session. The
  `ModelUnavailable` handler in `run_agent` did its job in all 49 cases: no
  crashes, the found item kept, and a message saying what to do. Every
  `id` matched across steps (0 mismatches in 65 + 28 handoffs), and all 16
  fit cards that were produced met criterion 4's length rule. The failures
  are in *availability*, not in what the agent does when the model answers.

**Criterion 1.** Place: the model call, through `suggest_outfit`. Mechanism: as
above. Each run makes two model calls, and both must succeed. With about half of
calls failing and no retry, the chance of a run completing was roughly
0.47 × 0.47 ≈ 22%. The data agrees: 16 of the 65 runs that should have completed
did (25%). This query happened to draw 0 of 5.

**Criterion 3.** Place: the session criterion was blocked by the model call, not
by the session. Mechanism: the only failing query (platform sneakers) stopped at
`suggest_outfit` all five times, so `create_fit_card` never received an `id` to
check. The criterion as written can't separate "the session lost the item"
from "the model was down". That is a measurement problem, so I've written a
revision under it in `criteria.md`. The verdict above stays on the original
wording.

**Criterion 4.** Place: the model call, through `suggest_outfit` (tries 1–3)
and `create_fit_card` (try 4). Mechanism: same. `create_fit_card` only runs
after `suggest_outfit` succeeds, so a card needs two successful calls. When the
model did answer, the prompt held: every one of the 16 cards across the whole
eval was 2–4 sentences and 160–222 characters.

**Criterion 5: met, and the target was too low.** Search is deterministic and
these five queries have plain category words in them, so 4 of 5 was easy to hit.
The run did expose a weakness this criterion can't see. For `vintage band tee`
the top result was "Graphic Tee — 2003 Tour Bootleg Style", not "Vintage Band
Tee — Faded Grey". They tie on keyword score and ties keep data order. The
category was right, but the more exact item lost. I'd tighten this to "the top
result's *title* contains the item word, 5 of 5", which would catch ranking
mistakes, not just category ones. Also, `lst_013` "90s Silk Slip Dress" is
stored with `category: "bottoms"` in the data, so a dress query would fail a
category check because of the data, not the search.

**Criterion 2: met, and it should be.** The empty-search path never touches
the model, so the outage that hit everything else couldn't reach it.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path** — `python app.py ask 'vintage graphic tee under $30' --trace` (trace calls in `agent.py::run_agent`)

```
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: selected id lst_002, going to suggest_outfit
[3] suggest_outfit
      in:  id lst_002 + 10 wardrobe items
      out: Outfit one pairs the Y2K Baby Tee with baggy straight-leg jeans, dark wash for a classic noughties streetwear …
[4] create_fit_card
      in:  id lst_002 + outfit suggestion
      out: Obsessed with this Y2K baby tee I just scored for only $18! The butterfly print is so nostalgic and cute. Grab…

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop
  Fit card: Obsessed with this Y2K baby tee I just scored for only $18! The butterfly print is so nostalgic and cute. Grabbed it on depop and I've already styled it two ways, from baggy denim streetwear to an edgy layered look with my khaki trousers.

2 model calls this session, 590 prompt + 158 output tokens
```

**Empty search** — `python app.py ask 'designer ballgown size XXS under $5' --trace`

```
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit
[3] search_listings (via MCP, hint)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': None}
      out: [] (empty)
[4] search_listings (via MCP, hint)
      in:  {'description': 'designer ballgown', 'size': None, 'max_price': 5.0}
      out: [] (empty)

  Nothing matched "designer ballgown" in size XXS under $5. Try: use different words for the item — the listings use terms like tee, hoodie, jeans, cargo pants, jacket, boots and bag.

0 model calls this session
```

The empty path never reaches `suggest_outfit`. Steps 3 and 4 are the
no-results message re-running the search with one filter dropped each, to
work out which advice would actually find something. Both also go through MCP.

**On the MCP move:** `search_listings` is registered in `mcp_server.py`, and
`agent.py` no longer imports it directly. Every search goes through
`agent.py::_search`, which calls `mcp_client.call_tool("search_listings", {...})`.
The return value didn't change: for three probe queries (a match, a size-filtered
match and an empty one) the MCP result was `==` to the direct call, still a
`list[dict]` with `price` as a float, and `[]` for no match. What *did* break was
the empty-search path. `_no_results_message` still called `search_listings`
directly to work out its hints, and once the import was gone every impossible
query raised `NameError: name 'search_listings' is not defined`. The happy
path worked, so this only showed up on the branch. Fixed by routing those calls
through MCP too. The one behaviour difference is speed: each `call_tool` starts
the server as a new Python process. One call timed at 5.6s, and the empty path
(three searches) took 11.5s end to end, against effectively instant before.

### Failure modes, triggered on purpose

| Failure | How I triggered it | What the agent said before any handler | Handled? |
|---|---|---|---|
| Empty search | `python app.py ask 'designer ballgown size XXS under $5'` | `Nothing matched "designer ballgown" in size XXS under $5. Try: use different words for the item — the listings use terms like tee, hoodie, jeans, cargo pants, jacket, boots and bag.` (After the MCP move, and before the fix above, it said `NameError: name 'search_listings' is not defined`.) | Yes, already: the branch in `run_agent` |
| Empty wardrobe | `python app.py ask 'denim jacket under $50' --empty-wardrobe` | `No saved wardrobe yet — general styling ideas: For a casual daytime look, pair the cropped denim jacket with a fitted black ribbed tank top and high-waisted wide-leg trousers…` and a normal fit card | Yes, already: `tools.py::suggest_outfit` asks for general advice |
| Model unavailable (bad key) | Changed one character of `GEMINI_API_KEY`, asked `black leather boots for winter under $70` (never asked before, so not cached) | `ModelUnavailable: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.` That text only reached the user because `app.py`'s catch-all printed the exception. `run_agent` itself crashed, so the item it had found was thrown away, and `run_eval.py` / `serve.py` would have recorded a crash. | **Added a handler** |
| Model unavailable (real outage, not triggered by me) | Happened by itself during testing: Gemini returned 503 "high demand" | `ModelUnavailable: Couldn't reach the model: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. ...` — a raw provider dict, and it suggested nothing to try | **Added a handler** |

**The handler** — `agent.py::run_agent` catches `ModelUnavailable` around both
model-calling steps, records it in the trace, and puts a message in
`session["error"]` built by `agent.py::_model_down_message`. It keeps the item
the search found, names which step broke, and says what to do. After the
handler, with the bad key (`brown suede jacket under $90`):

```
[3] suggest_outfit
      in:  id lst_004 + 10 wardrobe items
      →    ModelUnavailable, stopping: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.

  Found 90s Track Jacket — Navy/White Stripe ($45 on poshmark), but couldn't write an outfit suggestion. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
```

And during a real 503:

```
  Found Y2K Baby Tee — Butterfly Print ($18 on depop), but couldn't write an outfit suggestion: the AI model is overloaded right now (the service returned 503, high demand). Nothing is wrong with your setup — wait a minute and ask again.
```

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1.        |        |       |       |       |       |       |         |
| 2.        |        |       |       |       |       |       |         |
| 3.        |        |       |       |       |       |       |         |
| 4.        |        |       |       |       |       |       |         |
| 5.        |        |       |       |       |       |       |         |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
