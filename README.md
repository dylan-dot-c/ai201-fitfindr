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

**Unit 4.** After doing Milestone 1 myself, I asked Claude (Claude Code) to
carry out Milestones 2–6 in this repo: trigger the failures, add the trace,
write the scenarios, run the evals, and draft the write-up. Three specific moments:

**Moment 3 — the MCP move broke the branch, and only the branch**

- _What I asked for:_ to check my Milestone 1 swap before building on it.
- _What came back:_ running the impossible query gave `NameError: name 'search_listings' is not defined`. My swap had removed the direct import, but `_no_results_message` still called `search_listings` to work out its hints. The happy path worked, so I hadn't noticed. Claude also pointed out that my MCP tool docstring still had the template's `<-- YOUR DESCRIPTION GOES HERE` text in it, which is what a client sees as the tool's description.
- _What I changed:_ every search now goes through one `_search()` helper that calls `call_tool`, and I rewrote the description. Claude compared the MCP result against the direct call on three queries (`==` on all three) before calling the move done.

**Moment 4 — the first eval hung for 20 minutes**

- _What I asked for:_ to run the before eval.
- _What came back:_ no output for 20 minutes. Claude checked the process: no CPU use, no MCP child, one open connection to Google. It was stuck in a Gemini call with no timeout. It had already got through 5 of 14 scenarios.
- _What I changed:_ added `REQUEST_TIMEOUT_MS` (60s) to `config.py` and passed it to the Gemini client, so a stuck call becomes `ModelUnavailable` and gets a message. This counts as part of the Milestone 2 "don't hang" handler, not the Milestone 5 improvement, so it went in before the before run was restarted.

**Moment 5 — keeping a bad-looking before run**

- _What came back:_ Gemini was overloaded during the before run, and criterion 1 came back 0/5. Claude asked whether to keep the run, re-run it later, or fix retries first.
- _What I decided:_ keep it. The outage exposed a real weakness (no retry on 503/504), and fixing it before measuring would have left Milestone 5 with nothing to measure. The retry became the one improvement.
- _How the verdicts were reached:_ Claude scored every try with a script against the wording in `criteria.md`, then checked the script by hand (sentence counts, `id`s at each step). It read the targets plainly: criterion 4's one good card is 1/5, not "the prompt works", and criterion 3's unproven query is a miss even though the session never failed. Criterion 3 is revised underneath the original only because, as written, it measured model uptime instead of the session.

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

| Criterion                                                   | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict      |
| ----------------------------------------------------------- | ------ | ----- | ----- | ----- | ----- | ----- | ------------ |
| 1. A matching query completes all three tools               | 4 of 5 | FAIL  | FAIL  | FAIL  | FAIL  | FAIL  | MISSED (0/5) |
| 2. An impossible query stops before the second tool         | 5 of 5 | PASS  | PASS  | PASS  | PASS  | PASS  | MET (5/5)    |
| 3. The item search found is the item the next tools receive | 5 of 5 | PASS  | PASS  | FAIL  | PASS  | PASS  | MISSED (4/5) |
| 4. The fit card is a postable length                        | 4 of 5 | FAIL  | FAIL  | FAIL  | FAIL  | PASS  | MISSED (1/5) |
| 5. Search returns the right category for the item type      | 4 of 5 | PASS  | PASS  | PASS  | PASS  | PASS  | MET (5/5)    |

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

| #   | Criterion                                                | Target | Verdict          | How I decided                                                                                                                                                                                                                                       |
| --- | -------------------------------------------------------- | ------ | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | A matching query completes all three tools               | 4 of 5 | **MISSED (0/5)** | No run of `vintage graphic tee under $30` returned a fit card. Every one stopped at `suggest_outfit` on a 503 or 504. 0 is below 4.                                                                                                                 |
| 2   | An impossible query stops before the second tool         | 5 of 5 | **MET (5/5)**    | All five stopped after `search_listings` returned `[]`. `suggest_outfit` is absent from every trace, 0 model calls were made, and the message names what to change.                                                                                 |
| 3   | The item search found is the item the next tools receive | 5 of 5 | **MISSED (4/5)** | Four queries showed the same `id` going into both later tools. Platform sneakers never reached `create_fit_card` in five runs, so for that query the criterion's condition was never shown to hold. 5 of 5 means a single unproven query is a miss. |
| 4   | The fit card is a postable length                        | 4 of 5 | **MISSED (1/5)** | The criterion asks for a postable card on five runs of the same item. Four of the five runs produced no card, and no card is not a postable card. The one card that was produced passed (3 sentences, 199 characters).                              |
| 5   | Search returns the right category for the item type      | 4 of 5 | **MET (5/5)**    | The top result's `category` matched the expected one for all five item types, identically in all five runs of each.                                                                                                                                 |

**Diagnoses**

**The pattern: criteria 1, 3 and 4 are one miss, not three.** All of them
missed for the same reason, at the same place: **the model call, inside
`generate.py::generate`**.

- _What happened:_ 93 model calls were made and 49 failed (53%). The errors
  were 36 × `503 UNAVAILABLE` ("high demand"), 9 × `504 DEADLINE_EXCEEDED` and
  4 × connection failure. By step, 37 failed in `suggest_outfit` and 12 in
  `create_fit_card`.
- _The mechanism:_ `generate()` has a retry loop (`MAX_RETRIES = 5`), but it
  only retries when the error text looks like a rate limit (`429`, "resource
  exhausted", "rate limit"). A 503 or 504 doesn't match, so it raises
  `ModelUnavailable` on the **first** attempt. The eval log contains **zero**
  `[rate limit]` retry lines. A temporary overload that would likely have
  cleared in a few seconds is treated the same as a revoked API key.
- _What did NOT fail:_ the tools' logic, the branch and the session. The
  `ModelUnavailable` handler in `run_agent` did its job in all 49 cases: no
  crashes, the found item kept, and a message saying what to do. Every
  `id` matched across steps (0 mismatches in 65 + 28 handoffs), and all 16
  fit cards that were produced met criterion 4's length rule. The failures
  are in _availability_, not in what the agent does when the model answers.

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
result's _title_ contains the item word, 5 of 5", which would catch ranking
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
`list[dict]` with `price` as a float, and `[]` for no match. What _did_ break was
the empty-search path. `_no_results_message` still called `search_listings`
directly to work out its hints, and once the import was gone every impossible
query raised `NameError: name 'search_listings' is not defined`. The happy
path worked, so this only showed up on the branch. Fixed by routing those calls
through MCP too. The one behaviour difference is speed: each `call_tool` starts
the server as a new Python process. One call timed at 5.6s, and the empty path
(three searches) took 11.5s end to end, against effectively instant before.

### Failure modes, triggered on purpose

| Failure                                              | How I triggered it                                                                                                              | What the agent said before any handler                                                                                                                                                                                                                                                                                                                           | Handled?                                                         |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Empty search                                         | `python app.py ask 'designer ballgown size XXS under $5'`                                                                       | `Nothing matched "designer ballgown" in size XXS under $5. Try: use different words for the item — the listings use terms like tee, hoodie, jeans, cargo pants, jacket, boots and bag.` (After the MCP move, and before the fix above, it said `NameError: name 'search_listings' is not defined`.)                                                              | Yes, already: the branch in `run_agent`                          |
| Empty wardrobe                                       | `python app.py ask 'denim jacket under $50' --empty-wardrobe`                                                                   | `No saved wardrobe yet — general styling ideas: For a casual daytime look, pair the cropped denim jacket with a fitted black ribbed tank top and high-waisted wide-leg trousers…` and a normal fit card                                                                                                                                                          | Yes, already: `tools.py::suggest_outfit` asks for general advice |
| Model unavailable (bad key)                          | Changed one character of `GEMINI_API_KEY`, asked `black leather boots for winter under $70` (never asked before, so not cached) | `ModelUnavailable: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.` That text only reached the user because `app.py`'s catch-all printed the exception. `run_agent` itself crashed, so the item it had found was thrown away, and `run_eval.py` / `serve.py` would have recorded a crash. | **Added a handler**                                              |
| Model unavailable (real outage, not triggered by me) | Happened by itself during testing: Gemini returned 503 "high demand"                                                            | `ModelUnavailable: Couldn't reach the model: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. ...` — a raw provider dict, and it suggested nothing to try                                                                                                                                                  | **Added a handler**                                              |

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

**What I changed:** One thing: `generate.py::generate` now retries Gemini's
overload errors. Before, its retry loop only fired on rate-limit errors (`429`,
"resource exhausted", "rate limit"). Any other error, including a temporary
`503 UNAVAILABLE` or `504 DEADLINE_EXCEEDED`, raised `ModelUnavailable` on the
first attempt. Now an error containing `503`, `unavailable`, `504` or
`deadline_exceeded` goes through the same backoff as a rate limit: up to
`MAX_RETRIES` (5) attempts, waiting 1, 2, 4, 8 and 16 seconds. If it is still
overloaded after the last attempt, it raises `ModelUnavailable`, which
`run_agent` already handles. Before, an exhausted retry raised `RuntimeError`,
which nothing caught, so widening the retry check without this fix would have
turned "a message" into "a crash". Nothing else changed: same prompts, tools,
loop, scenarios, temperature and five tries.

I checked it with a fake client before the real run. Two 503s followed by a
success returned the answer after 1s and 2s waits. A 503 on every attempt
waited out all five backoffs and raised `ModelUnavailable`, not a crash. Errors
that match neither check, such as a rejected key or a connection failure, still
fail on the first attempt as before. That follows from the code; I didn't
re-trigger them after the change. (Commit `deb50f8`.)

**Which failure it was meant to fix:** The one pattern behind criteria 1, 3 and
4 (see Diagnoses). 49 of 93 model calls failed in the before run: 36 × 503,
9 × 504, 4 × connection failure. None were retried (zero retry lines in the
log). This change targets the 45 that were 503/504. It does nothing for the 4
connection failures, so if they recur they will still stop a run. That's
deliberate, to keep this to one change.

**Why this and not something else:** The diagnosis found nothing wrong in the
tools, the branch, the session or the prompts. 0 `id` mismatches, and all 16
fit cards were within the length rule. Rewriting a prompt or adding a branch
would have changed something that wasn't failing. The only thing between the
agent and a passing run was a model call giving up on its first try.

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

**Known problems the improvement doesn't touch**

- **Connection failures still aren't retried.** In the after run, criterion 1
  try 4 got two 503s, retried, and then hit a connection failure on the third
  attempt. Connection errors still fail immediately. _What I'd do:_ add them
  to the retry check. _Why I stopped:_ that would have been a second change in
  the same run, and I couldn't have said which one moved the numbers.
- **An outage longer than ~30 seconds still ends the run.** In the after run,
  criterion 1 try 1 got a 503 on all five attempts (1+2+4+8+16s of waiting)
  and gave up. _What I'd do:_ fall back to a second model name when the first
  is overloaded, or honour a longer wait for `suggest_outfit` only. _Why I
  stopped:_ raising `MAX_RETRIES` just makes every failed run slower, and the
  free tier only allows 15 calls a minute.
- **Search ties go to data order.** `vintage band tee` returns "Graphic Tee —
  2003 Tour Bootleg Style" over "Vintage Band Tee — Faded Grey". Both score 3,
  and the graphic tee comes first in the file. Criterion 5 can't see this
  because both are `tops`. _What I'd do:_ break ties by how many keywords hit
  the _title_, and tighten criterion 5 to check the title. _Why I stopped:_ it
  isn't one of my current misses, and the diagnosis pointed elsewhere.
- **One listing has the wrong category in the data.** `lst_013` "90s Silk Slip
  Dress" is stored as `bottoms`. Any category check on dresses would fail
  because of the data. I haven't edited the data, since it ships with the
  starter.
- **The no-results hints can't suggest relaxing two filters at once.** For
  `denim jacket size XS under $20` it tries dropping the size, then the price,
  finds nothing either way, and falls back to "use different words", even
  though denim jackets exist. _What I'd do:_ also try dropping both filters.
- **MCP is slow.** Each `call_tool` starts `mcp_server.py` as a new process,
  about 3–5 seconds per search, and the empty path makes three. That's fine for
  a CLI, but it will matter behind `serve.py` in unit 9.

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

---

## Capstone

**What This Extends**

FitFindr, the agent from units 3–4: a user types what secondhand item they want
and gets a matching listing, an outfit suggestion and a fit card. The agent
itself is unchanged. What's new is that it runs on Render at
https://fitfindr-8uv3.onrender.com instead of only from `python app.py`, every
request writes a structured JSON log record (`serve.py::_log`), and
`run_live.py` drives the deployed service and matches each response to its
log record. The one improvement made this unit keeps the MCP server running
between searches instead of starting a new one per call (`mcp_client.py`).

**The Shape**

A — deploy and instrument.

I added a deployment step and some new criteria to test.

Out of scope: no changes to the agent or tools, as that would be too much work; no web UI as yet (would love to build one); and still no fix to the one-request-at-a-time error, but if I paid then yes.

**Running It**

Path A, hosted on Render's free tier: https://fitfindr-8uv3.onrender.com.
The service is defined in [render.yaml](render.yaml); setup, routes and every
log field are in [RUNNING.md](RUNNING.md). Routes: `POST /ask`,
`GET /health`, `GET /logs?n=20`.

The first deploy fell over after 2–4 requests. Render's health check calls
`/health`, and with a single sync gunicorn worker busy on a 20–50 s agent run,
nothing answered it. Render decided the app was dead and restarted it, which
also wiped the log. Probing `/health` every 3 s during an `/ask` showed it
timing out from t+3 s and the instance going down at about t+12 s. Starting
gunicorn with `--threads 4` fixed it; the same probe afterwards answered in
~0.2 s throughout. The runs from before the fix are kept as
`results/live_*_BEFORE-threads-fix_*`.

**Instrumentation**

Every `/ask` request, answered, rejected (400) or crashed (500), writes one
JSON record from `serve.py::_log` to stdout (kept by Render's Logs tab) and to
`logs/requests.jsonl` (read back by `GET /logs`, because the free instance
wipes its disk when it sleeps). Each record holds: `ts`, `request_id` (also
returned as the `X-Request-Id` header), `query`, `status`, `outcome`
(`ok` / `no_results` / `model_error` / `rejected` / `crash`), `error`, what
came out (`selected_id`, `selected_price`, `fit_card_chars`), spend
(`model_calls`, `prompt_tokens`, `output_tokens`), timing (`queue_wait_ms`,
`agent_ms`, `duration_ms`), `boot_id` and `uptime_s` (a new `boot_id` means
the instance restarted), and memory (`rss_mb`). After the improvement,
records also carry `mcp_calls`, `mcp_ms` and `mcp_persistent`.

All 14 records from `results/live_instrumentation_2026-11-17_122446.md`: 10
matching queries, 1 query that matches nothing, and 3 rejected bad inputs
(the failed runs, status 400).

```
{"agent_ms": 6584, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.1, "duration_ms": 6584, "error": null, "fit_card_chars": 256, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 161, "parsed": {"description": "vintage graphic tee", "max_price": 30.0, "size": null}, "peak_rss_mb": 100.1, "prompt_tokens": 589, "query": "vintage graphic tee under $30", "queue_wait_ms": 0, "request_id": "fad636d6", "results": 10, "rss_mb": 100.7, "selected_id": "lst_002", "selected_price": 18.0, "status": 200, "ts": "2026-11-17T17:20:49.025+00:00", "uptime_s": 477, "wardrobe_items": 10}
{"agent_ms": 10913, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.1, "duration_ms": 10913, "error": null, "fit_card_chars": 218, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 135, "parsed": {"description": "denim jacket", "max_price": 50.0, "size": null}, "peak_rss_mb": 100.1, "prompt_tokens": 566, "query": "denim jacket under $50", "queue_wait_ms": 0, "request_id": "b682eae9", "results": 7, "rss_mb": 100.7, "selected_id": "lst_007", "selected_price": 42.0, "status": 200, "ts": "2026-11-17T17:20:55.926+00:00", "uptime_s": 488, "wardrobe_items": 10}
{"agent_ms": 12902, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.1, "duration_ms": 12903, "error": null, "fit_card_chars": 276, "model": "gemini-3.5-flash-lite", "model_calls": 3, "outcome": "ok", "output_tokens": 178, "parsed": {"description": "90s track jacket", "max_price": null, "size": "M"}, "peak_rss_mb": 100.1, "prompt_tokens": 605, "query": "90s track jacket size M", "queue_wait_ms": 1, "request_id": "934a1612", "results": 5, "rss_mb": 100.7, "selected_id": "lst_004", "selected_price": 45.0, "status": 200, "ts": "2026-11-17T17:21:06.987+00:00", "uptime_s": 501, "wardrobe_items": 10}
{"agent_ms": 16839, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.1, "duration_ms": 16839, "error": null, "fit_card_chars": 187, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 159, "parsed": {"description": "silk slip dress", "max_price": 40.0, "size": null}, "peak_rss_mb": 100.1, "prompt_tokens": 614, "query": "silk slip dress under $40", "queue_wait_ms": 0, "request_id": "76ebec83", "results": 2, "rss_mb": 100.7, "selected_id": "lst_013", "selected_price": 30.0, "status": 200, "ts": "2026-11-17T17:21:20.048+00:00", "uptime_s": 518, "wardrobe_items": 10}
{"agent_ms": 15805, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.1, "duration_ms": 15805, "error": null, "fit_card_chars": 216, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 121, "parsed": {"description": "platform sneakers", "max_price": null, "size": "8"}, "peak_rss_mb": 100.1, "prompt_tokens": 554, "query": "platform sneakers size 8", "queue_wait_ms": 0, "request_id": "061f4f10", "results": 1, "rss_mb": 100.7, "selected_id": "lst_019", "selected_price": 48.0, "status": 200, "ts": "2026-11-17T17:21:37.038+00:00", "uptime_s": 534, "wardrobe_items": 10}
{"agent_ms": 17497, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.1, "duration_ms": 17497, "error": null, "fit_card_chars": 211, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 188, "parsed": {"description": "cargo pants", "max_price": 40.0, "size": null}, "peak_rss_mb": 100.1, "prompt_tokens": 625, "query": "cargo pants under $40", "queue_wait_ms": 0, "request_id": "2f4daa7e", "results": 2, "rss_mb": 100.7, "selected_id": "lst_011", "selected_price": 27.0, "status": 200, "ts": "2026-11-17T17:21:52.992+00:00", "uptime_s": 552, "wardrobe_items": 10}
{"agent_ms": 31926, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.1, "duration_ms": 31926, "error": null, "fit_card_chars": 228, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 172, "parsed": {"description": "baggy jeans", "max_price": null, "size": null}, "peak_rss_mb": 100.2, "prompt_tokens": 607, "query": "baggy jeans", "queue_wait_ms": 0, "request_id": "fd525ce2", "results": 3, "rss_mb": 100.7, "selected_id": "lst_031", "selected_price": 36.0, "status": 200, "ts": "2026-11-17T17:22:10.795+00:00", "uptime_s": 584, "wardrobe_items": 10}
{"agent_ms": 16341, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.2, "duration_ms": 16341, "error": null, "fit_card_chars": 194, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 171, "parsed": {"description": "leather bag", "max_price": null, "size": null}, "peak_rss_mb": 100.2, "prompt_tokens": 596, "query": "leather bag", "queue_wait_ms": 0, "request_id": "57fa5807", "results": 4, "rss_mb": 100.8, "selected_id": "lst_039", "selected_price": 38.0, "status": 200, "ts": "2026-11-17T17:22:42.892+00:00", "uptime_s": 600, "wardrobe_items": 10}
{"agent_ms": 77373, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.2, "duration_ms": 77373, "error": null, "fit_card_chars": 212, "model": "gemini-3.5-flash-lite", "model_calls": 3, "outcome": "ok", "output_tokens": 187, "parsed": {"description": "black jacket", "max_price": null, "size": null}, "peak_rss_mb": 100.2, "prompt_tokens": 610, "query": "black jacket", "queue_wait_ms": 0, "request_id": "251db922", "results": 10, "rss_mb": 100.8, "selected_id": "lst_022", "selected_price": 75.0, "status": 200, "ts": "2026-11-17T17:22:59.401+00:00", "uptime_s": 678, "wardrobe_items": 10}
{"agent_ms": 17159, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.2, "duration_ms": 17161, "error": null, "fit_card_chars": 167, "model": "gemini-3.5-flash-lite", "model_calls": 2, "outcome": "ok", "output_tokens": 124, "parsed": {"description": "white sneakers", "max_price": null, "size": null}, "peak_rss_mb": 100.2, "prompt_tokens": 567, "query": "white sneakers", "queue_wait_ms": 2, "request_id": "d92aa3b7", "results": 6, "rss_mb": 100.8, "selected_id": "lst_019", "selected_price": 48.0, "status": 200, "ts": "2026-11-17T17:24:16.938+00:00", "uptime_s": 695, "wardrobe_items": 10}
{"agent_ms": 12913, "boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.3, "duration_ms": 12914, "error": "Nothing matched \"designer ballgown\" in size XXS under $5. Try: use different words for the item — the listings use terms like tee, hoodie, jeans, cargo pants, jacket, boots and bag.", "fit_card_chars": 0, "model": "gemini-3.5-flash-lite", "model_calls": 0, "outcome": "no_results", "output_tokens": 0, "parsed": {"description": "designer ballgown", "max_price": 5.0, "size": "XXS"}, "peak_rss_mb": 100.3, "prompt_tokens": 0, "query": "designer ballgown size XXS under $5", "queue_wait_ms": 0, "request_id": "975a6dec", "results": 0, "rss_mb": 100.8, "selected_id": null, "selected_price": null, "status": 200, "ts": "2026-11-17T17:24:34.295+00:00", "uptime_s": 708, "wardrobe_items": 10}
{"boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.3, "duration_ms": 0, "error": "missing 'query'", "model": "gemini-3.5-flash-lite", "outcome": "rejected", "peak_rss_mb": 100.3, "query": null, "request_id": "a6621abf", "rss_mb": 100.8, "status": 400, "ts": "2026-11-17T17:24:47.450+00:00", "uptime_s": 709}
{"boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.3, "duration_ms": 0, "error": "missing 'query'", "model": "gemini-3.5-flash-lite", "outcome": "rejected", "peak_rss_mb": 100.3, "query": null, "request_id": "fa0ba82b", "rss_mb": 100.8, "status": 400, "ts": "2026-11-17T17:24:47.589+00:00", "uptime_s": 709}
{"boot_id": "c7da3a", "cache_enabled": false, "child_peak_rss_mb": 100.3, "duration_ms": 0, "error": "missing 'query'", "model": "gemini-3.5-flash-lite", "outcome": "rejected", "peak_rss_mb": 100.3, "query": null, "request_id": "bd2aad50", "rss_mb": 100.8, "status": 400, "ts": "2026-11-17T17:24:47.775+00:00", "uptime_s": 709}
```

**What It Costs**

Measured with `python run_live.py --label cost --only ok -n 10`: ten matching
queries against the deployed service, with the cache off (`AI201_CACHE=0`),
token counts as Gemini reported them in each log record
(`results/live_cost_2026-11-17_122807.md`).

| Per run (mean of 10) |        |
| -------------------- | ------ |
| Model calls          | 2.1    |
| Prompt tokens        | 593.3  |
| Output tokens        | 155.9  |
| Server time          | 19.5 s |

At `gemini-3.5-flash-lite`'s paid rates ($0.30 per 1M input tokens, $2.50 per
1M output tokens, from Google's pricing page on 2026-11-17):

- One run: 593.3 × $0.30/1M + 155.9 × $2.50/1M = $0.000178 + $0.000390 = **$0.00057**
- 100 people a day, one run each: 100 × $0.00057 = **$0.057 a day**, about
  $1.70 for 30 days
- In calls: 100 × 2.1 = 210 model calls a day

On the free tier this project actually runs on, the dollar cost is $0. The
real limit is 15 model calls a minute, which caps the service at about 7 runs
a minute however many people are asking.

**Run Log and Verdicts**

Criteria are in [criteria.md](criteria.md) under "Capstone criteria",
committed (`5300e3b add capstone criteria`) before these trials ran. Each
trial is one `python run_live.py --label trialN`: 16 requests against the
Render URL.

| Criterion                            | Target               | Trial 1 | Trial 2 | Trial 3 | Verdict |
| ------------------------------------ | -------------------- | ------- | ------- | ------- | ------- |
| 1. Every request leaves a log record | 16 of 16             | 16/16   | 16/16   | 16/16   | MET     |
| 2. Bad input gets a 400              | 5 of 5               | 5/5     | 5/5     | 5/5     | MET     |
| 3. Warm fit card within 30 s         | 9 of 10              | 9/10    | 10/10   | 10/10   | MET     |
| 4. 10 in a row, no restart           | 10/10, one `boot_id` | 10/10   | 10/10   | 10/10   | MET     |
| 5. At most 1,000 tokens per run      | 9 of 10              | 10/10   | 10/10   | 10/10   | MET     |

Trial 1 didn't meet criterion 3's "warm" condition: `/health` took 22.3 s
first, so the instance was waking up, and the first query took 40.4 s, the
only run over 30 s in the three trials. Counted anyway, it's 9 of 10, which
still meets the target. All three trials ran on one instance (`boot_id`
`d342f2`). The highest token count across all 30 runs was 817.

Real output from trial 2 (`results/live_trial2_2026-11-17_140202.md`, written
by `run_live.py::write`; the server columns come from `serve.py::_log`):

Criteria 1 and 4:

```
- With a matching server log record: 16 of 16
- Server boot ids seen (more than one = it restarted): ['d342f2']
```

Criteria 3, 4 and 5 (the 10 matching queries):

```
| # | kind | request body | HTTP | client ms | server outcome | server ms | queue ms | fit card | calls | tokens in/out | rss MB | child peak MB |
| 1 | ok | `{"query": "vintage graphic tee under $30"}` | 200 | 11116 | ok | 10967 | 0 | yes | 2 | 596/162 | 117.8 | 117.1 |
| 2 | ok | `{"query": "denim jacket under $50"}` | 200 | 9242 | ok | 9083 | 1 | yes | 2 | 565/133 | 117.8 | 117.1 |
| 3 | ok | `{"query": "90s track jacket size M"}` | 200 | 8819 | ok | 8644 | 1 | yes | 2 | 607/157 | 117.8 | 117.1 |
| 4 | ok | `{"query": "silk slip dress under $40"}` | 200 | 8436 | ok | 8121 | 0 | yes | 2 | 622/176 | 117.8 | 117.1 |
| 5 | ok | `{"query": "platform sneakers size 8"}` | 200 | 8469 | ok | 8315 | 0 | yes | 2 | 604/174 | 117.8 | 117.1 |
| 6 | ok | `{"query": "cargo pants under $40"}` | 200 | 8024 | ok | 7872 | 0 | yes | 2 | 605/161 | 117.8 | 117.3 |
| 7 | ok | `{"query": "baggy jeans"}` | 200 | 8730 | ok | 8567 | 0 | yes | 2 | 616/175 | 117.8 | 117.3 |
| 8 | ok | `{"query": "leather bag"}` | 200 | 7330 | ok | 7163 | 0 | yes | 2 | 593/160 | 117.8 | 117.3 |
| 9 | ok | `{"query": "black jacket"}` | 200 | 17129 | ok | 16953 | 0 | yes | 2 | 610/191 | 117.9 | 117.3 |
| 10 | ok | `{"query": "white sneakers"}` | 200 | 22924 | ok | 22589 | 0 | yes | 2 | 587/150 | 117.9 | 117.3 |
```

Criterion 2 (the 5 bad inputs), and one of their log records:

```
| # | kind | request body | HTTP | client ms | server outcome | server ms | queue ms | fit card | calls | tokens in/out | rss MB | child peak MB |
| 12 | bad_input | `{}` | 400 | 169 | rejected | 0 | - | no | - | - | 112.5 | 117.3 |
| 13 | bad_input | `{"query": "   "}` | 400 | 205 | rejected | 0 | - | no | - | - | 112.5 | 117.3 |
| 14 | bad_input | `this is not json` | 400 | 199 | rejected | 0 | - | no | - | - | 112.5 | 117.3 |
| 15 | bad_input | `{"query": null}` | 400 | 129 | rejected | 0 | - | no | - | - | 112.5 | 117.3 |
| 16 | bad_input | `{"query": 123}` | 400 | 154 | rejected | 0 | - | no | - | - | 112.5 | 117.3 |
{"boot_id": "d342f2", "cache_enabled": false, "child_peak_rss_mb": 117.3, "duration_ms": 0, "error": "missing 'query'", "model": "gemini-3.5-flash-lite", "outcome": "rejected", "peak_rss_mb": 117.3, "query": null, "request_id": "9d843923", "rss_mb": 112.5, "status": 400, "ts": "2026-11-17T19:02:04.132+00:00", "uptime_s": 285}
```

**The Improvement**

_What the trials showed._ The query that matches nothing made zero model calls
but still took 16–20 s in every trial. All it does is search, three times
(the search plus two hint searches with a filter dropped), through MCP. Every
`mcp_client.call_tool` started a new `mcp_server.py` process, connected,
listed the tools, made one call and stopped it; on Render's free-tier CPU that
came to several seconds per search. Every matching run paid it once too.

_The change._ `mcp_client.call_tool` now starts the server once per process
and keeps the session open on a background event-loop thread
(`_PersistentSession`). Same signature, same return value, so `agent.py`
didn't change. If the server process dies, the next call starts a new one
(tested locally by killing it mid-session). `AI201_MCP_PERSISTENT=0` restores
the old behaviour. Locally, a search went from ~900 ms to ~4 ms after the
first. Commit `4439456`.

_After, three more trials_ (`results/live_after_trial*`):

| Criterion                            | Target               | Trial 1 | Trial 2 | Trial 3 | Verdict |
| ------------------------------------ | -------------------- | ------- | ------- | ------- | ------- |
| 1. Every request leaves a log record | 16 of 16             | 16/16   | 16/16   | 16/16   | MET     |
| 2. Bad input gets a 400              | 5 of 5               | 5/5     | 5/5     | 5/5     | MET     |
| 3. Warm fit card within 30 s         | 9 of 10              | 10/10   | 8/10    | 9/10    | MISSED  |
| 4. 10 in a row, no restart           | 10/10, one `boot_id` | 10/10   | 10/10   | 10/10   | MET     |
| 5. At most 1,000 tokens per run      | 9 of 10              | 10/10   | 10/10   | 10/10   | MET     |

|                           | Before (3 trials)      | After (3 trials)     |
| ------------------------- | ---------------------- | -------------------- |
| No-match query            | 16.2 / 20.3 / 16.2 s   | 0.22 / 0.27 / 0.19 s |
| Median matching run       | 9.2 / 8.8 / 9.7 s      | 4.8 / 3.5 / 3.2 s    |
| MCP time per matching run | not logged (several s) | 5–46 ms              |
| Slowest matching run      | 40.4 / 22.9 / 27.0 s   | 29.3 / 62.3 / 96.7 s |

_Did it help?_ The median matching run went from ~9 s to ~3.5 s, and the no-match query
went from 16 s to a fifth of a second. But the slowest runs got much worse,
and criterion 3 went from MET to MISSED (8 of 10 in after-trial 2).

_Why criterion 3 now misses._ The stage is `generate.py::_wait_for_slot`, the
rate limiter that keeps the agent under Gemini's free-tier 15 calls a minute.
Each run makes 2 calls, so 15 calls a minute is about 7 runs a minute. Before
the fix, starting a new MCP server for every search held runs to ~9 s each,
which kept them just under that by accident. At ~3 s a run, 7–8 back-to-back
runs use up the minute, and the next run's second call waits for the window to
clear. Model calls in the 60 s before each slow run, from the after-trial log
records:

```
19:13:06 UTC  calls in prior 60 s: 14  this run:  29.3 s  leather bag
19:13:52 UTC  calls in prior 60 s: 14  this run:  50.7 s  denim jacket under $50
19:14:53 UTC  calls in prior 60 s:  4  this run:  62.3 s  platform sneakers size 8
19:16:15 UTC  calls in prior 60 s: 14  this run:  96.7 s  90s track jacket size M
```

Three of the four slow runs started with exactly 14 calls already made, so
their second call was the 16th. The fourth (62.3 s) had only a few calls
before it, but the run before it made 3 calls instead of 2, meaning Gemini
pushed back and `generate.py` retried; that one is Google's limit rather than
the local one. This part is inferred: the log doesn't record how long the
limiter waited.

**What's Still Broken**

Criterion 3 is difficult, but it's a valid trade-off for what it trades.

*Criterion 3 (missed after the improvement).* What I'd do: log how long
`generate.py::_wait_for_slot` waits on every call, as a `rate_limit_wait_ms`
field in the request record. Right now the diagnosis above is inferred from
call timestamps; with that field, every slow run would say for itself whether
it was the limiter, Gemini pushing back, or something else. Only then would I
pick a fix: a higher Gemini quota, or pacing requests so runs never bunch up
against the 15-a-minute limit. Why I stopped: the improvement and its re-run
used up the unit, and I'd rather report the trade honestly than rush a second
change I hadn't measured.

*Criterion 5 (met, but set too low).* I'd tighten criterion 5 by checking the
output; once that's good, it will be better. The highest of all 60 runs was
827 tokens against a limit of 1,000, so the target could never fail. I'd
tighten it to **at most 900 tokens in 9 of 10 runs**: about 10% above the
highest run measured, so a prompt that grows or a fit card that runs long
would actually show up as a miss.

*The one thing I'd do first with another unit:* add the rate-limit wait to the
log. It's the only miss left, it's the one part of the diagnosis that's
guessed rather than measured, and any fix for it can't be judged without that
number.

**How I Used AI**

I used AI to help me write the YAML file so I could deploy the app, and used AI to automate some commands and verify the live server and tools. I used Claude (Claude Code) throughout this unit.

*Moment 1: deploying.* I asked Claude to deploy FitFindr to Render. I got
`render.yaml`, structured logging in `serve.py`, and `run_live.py` to test the
live server. The first deploy kept restarting after 2–4 requests; Claude
probed `/health` during a request and found Render's health check was killing
the instance, and fixed it with `--threads 4`. What I changed: I ran the
trials myself and kept the failed runs in `results/` as evidence instead of
deleting them.

*Moment 2: the criteria.* The brief says to write criteria yourself, so I
wrote all five targets and reasons, then asked Claude to tighten them. It
kept my numbers and reasons and added the testing details (which 5 bad
inputs, client-side timing, how a restart is detected). What I changed: I
reviewed the details before committing; the 16-request count in criterion 1
came from adding two bad inputs I hadn't tested yet.

Claude also drafted the factual parts of this Capstone write-up from the
results files (the run logs, cost arithmetic and diagnosis), and expanded my
notes in What's Still Broken; the 900-token target there is Claude's
suggestion, which I accepted.
