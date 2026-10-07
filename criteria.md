# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. _"The agent handles errors"_ is an opinion.
_"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"_ is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; _"80% seemed reasonable"_ does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
My search is a plain whole-word keyword match with no stemming, so a phrasing
like "tees" or "sneaker" can miss listings that say "tee" or "sneakers", and
the size filter is a strict token match. On top of that, two of the three tools
call a model that can return blank text. 5 of 5 would assume none of that ever
happens.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path never touches the model. It's one `if` on whether `search_listings`
returned an empty list, and search is deterministic, so the same query takes
the same branch every time. A single miss here is a bug, not bad luck.

---

## 3. The item search found is the item the next tools receive

For 5 queries that match at least one listing, the `id` in
`session["selected_item"]` is the same `id` as the item passed into
`suggest_outfit` and into `create_fit_card`, and that `id` exists in
`data/listings.json` — 5 of 5 tries.

**Why this target:**
Moving the item through the session is plain code with no model involved: take
`session["search_results"][0]`, store it, read it back. If the `id` ever
changes between steps, something overwrote the session or read the wrong index,
and that's a bug every time, so I'm not allowing any misses.

---

## 4. The fit card is a postable length

For 5 runs of `create_fit_card` on the same item, the card is 2–4 sentences
and no longer than 300 characters — in at least 4 of 5 runs.

**Why this target:**
`TEMPERATURE` is 0.9, so the wording and length change every run, and the
model doesn't always follow a length instruction exactly. 2–4 sentences is what
my Tool Inventory promises, and 300 characters is about as long as a caption
anyone would actually post. I allow one miss in five for model drift; 5 of 5
would be grading the model, not my prompt.

---

## 5. Search returns the right category for the item type asked for

For 5 queries that each name one item type (jacket, jeans, tee, sneakers,
bag), the top search result's `category` matches the expected category
(jacket → outerwear, jeans → bottoms, tee → tops, sneakers → shoes,
bag → accessories) — in at least 4 of 5 queries.

**Why this target:**
My search scores keyword hits across title, description, style_tags, colors
and brand, not just category, so a top whose description says "throw a jacket
over it" can tie with or outrank a real jacket, and ties keep data order. The
data also has only 4 shoes and 3 accessories listings, so those queries have
few right answers to find.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
