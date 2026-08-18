# Failure analysis

Every incorrect decision, with a named failure condition. Routed cases are not failures - the agent declined to decide, which is a permitted action.

## Highest-cost error

Worst single decision: **T013** by `expected_cost` - `hide` on a review whose true state is `genuine`, costing **10.00** units.

> My dog loves this toy and is always chewing on it and he has nice strong, clean teeth.  This is my 3rd one.

| Error type | Count | Cost each | Total |
|---|---|---|---|
| permit on a fake review | 19 | 5.00 | 95.00 |
| flag_with_explanation on a genuine review | 10 | 2.00 | 20.00 |
| hide on a genuine review | 1 | 10.00 | 10.00 |
| permit on a solicited review | 5 | 2.00 | 10.00 |

**Per-decision, the most expensive single error is `hide` on a `genuine` review at 10.00 units.** In aggregate the largest contributor is different: *permit on a fake review*, 19 occurrences totalling 95.00 units. Both readings matter and they do not agree - a rare catastrophic error and a common cheap one can carry similar totals, which is exactly what the cost model is for.

Hiding a genuine review is the worst *single* decision because it removes a real customer's words with no route to contest, and its cost is scaled by the volume factor so a small shop absorbs almost all of it. Permitting a fake is cheaper per case but far more frequent. Note this table pools all systems and both datasets; it is not a per-system cost.

## Held-out test set

### SHORT-FAKE-MISSED: too little text to separate from a real short review (9)

- **T005** · baseline_keyword · true state `fake` · rating 1.0 · action `permit` · P(not genuine) n/a
  > Came broken and cracked frame.  The only way to fix it was to just fix the frame
- **T005** · fixed_band · true state `fake` · rating 1.0 · action `permit` · P(not genuine) 0.33857
  > Came broken and cracked frame.  The only way to fix it was to just fix the frame
- **T008** · baseline_keyword · true state `fake` · rating 2.0 · action `permit` · P(not genuine) n/a
  > The stitching doesn't hold up, it feels a little tight but it's not a big deal.
- **T018** · baseline_keyword · true state `fake` · rating 4.0 · action `permit` · P(not genuine) n/a
  > It's sugary and tasty. Similar to an ice cream cone. I also love that it's easier
- **T018** · fixed_band · true state `fake` · rating 4.0 · action `permit` · P(not genuine) 0.09632
  > It's sugary and tasty. Similar to an ice cream cone. I also love that it's easier
- **T018** · expected_cost · true state `fake` · rating 4.0 · action `permit` · P(not genuine) 0.09632
  > It's sugary and tasty. Similar to an ice cream cone. I also love that it's easier

### SPECIFIC-GENUINE-FLAGGED: detailed real review acted on anyway (8)

- **T000** · baseline_keyword · true state `genuine` · rating 5.0 · action `flag_with_explanation` · P(not genuine) n/a
  > Quality and quite nonstick

I bought a "Scanpan Classic 11-Piece Deluxe Cookware Set" in 2007, and they have been great non stick pans, serving me well for nearly a decade.

Even with a lifetime warranty, I can't expect ...
- **T009** · baseline_keyword · true state `genuine` · rating 2.0 · action `flag_with_explanation` · P(not genuine) n/a
  > I was very disappointed with this purchase for my 5 year old.  It is very small, hard to transform, and comes apart very easily.  There are better Transformers out there.
- **T013** · fixed_band · true state `genuine` · rating 4.0 · action `flag_with_explanation` · P(not genuine) 0.98311
  > My dog loves this toy and is always chewing on it and he has nice strong, clean teeth.  This is my 3rd one.
- **T013** · expected_cost · true state `genuine` · rating 4.0 · action `hide` · P(not genuine) 0.98311
  > My dog loves this toy and is always chewing on it and he has nice strong, clean teeth.  This is my 3rd one.
- **T021** · baseline_keyword · true state `genuine` · rating 2.0 · action `flag_with_explanation` · P(not genuine) n/a
  > Normally I feed my cats Fromm Four Star dry foods but I was looking for something a little more budget friendly available with Prime shipping that was still a better brand. With four cats it gets expensive! After doing s...
- **T030** · baseline_keyword · true state `genuine` · rating 4.0 · action `flag_with_explanation` · P(not genuine) n/a
  > Remodeled our laundry room and got this for the wash sink. Been in use for over 6 months and has held up well still looks brand new after a lot of use. Spring/hose is pretty stiff and doesn't have a lot of play to it. Ov...

### FLUENT-FAKE: long, fluent machine text with no checkable content (5)

- **T001** · baseline_keyword · true state `fake` · rating 3.0 · action `permit` · P(not genuine) n/a
  > This is an interesting product, and it's an interesting product for a lot of reasons. First, it's very easy to put together and is easy to clean. The material is thick, and it's easy to cut out. The size is adjustable, a...
- **T011** · baseline_keyword · true state `fake` · rating 1.0 · action `permit` · P(not genuine) n/a
  > This is similar to a real gun, with the instructions included.  There is a button that activates a two-step trigger.  There is also a plastic "lock" that activates the slide.  The slide will not stay in place.  This is w...
- **T011** · fixed_band · true state `fake` · rating 1.0 · action `permit` · P(not genuine) 0.018744
  > This is similar to a real gun, with the instructions included.  There is a button that activates a two-step trigger.  There is also a plastic "lock" that activates the slide.  The slide will not stay in place.  This is w...
- **T011** · expected_cost · true state `fake` · rating 1.0 · action `permit` · P(not genuine) 0.018744
  > This is similar to a real gun, with the instructions included.  There is a button that activates a two-step trigger.  There is also a plastic "lock" that activates the slide.  The slide will not stay in place.  This is w...
- **T038** · baseline_keyword · true state `fake` · rating 1.0 · action `permit` · P(not genuine) n/a
  > Shoveling Snow  is by far my favorite book of this series.  This is the first book in the series and the first I have read by this author

### DETAILED-FAKE: fabricated text carrying concrete detail (1)

- **T039** · baseline_keyword · true state `fake` · rating 4.0 · action `permit` · P(not genuine) n/a
  > After reading Armored Hearts I was a little frustrated because it was a prequel to the first book.

I had a lot of fun with the characters and the storyline. I enjoyed that it was a little short.

I liked the ending. I l...

## Supplementary probe set

### SOLICITED-INVISIBLE: real visit, true detail, not independent (5)

- **P000** · fixed_band · true state `solicited` · rating 5.0 · action `permit` · P(not genuine) 0.188216
  > Ordered the ribeye for my brother-in-law's opening night. Came out at a perfect medium rare and the kitchen sent out extra bread when they saw we were waiting. Been going since they opened in March.
- **P000** · expected_cost · true state `solicited` · rating 5.0 · action `permit` · P(not genuine) 0.188216
  > Ordered the ribeye for my brother-in-law's opening night. Came out at a perfect medium rare and the kitchen sent out extra bread when they saw we were waiting. Been going since they opened in March.
- **P001** · baseline_keyword · true state `solicited` · rating 5.0 · action `permit` · P(not genuine) n/a
  > My sister runs the front of house here and I eat here most Fridays. The carbonara is genuinely good, and they fixed the noise problem by adding panels to the back wall about two months ago.
- **P001** · fixed_band · true state `solicited` · rating 5.0 · action `permit` · P(not genuine) 0.105644
  > My sister runs the front of house here and I eat here most Fridays. The carbonara is genuinely good, and they fixed the noise problem by adding panels to the back wall about two months ago.
- **P001** · expected_cost · true state `solicited` · rating 5.0 · action `permit` · P(not genuine) 0.105644
  > My sister runs the front of house here and I eat here most Fridays. The carbonara is genuinely good, and they fixed the noise problem by adding panels to the back wall about two months ago.

### SPECIFICITY-HARVESTED: concrete detail copied from the page (2)

- **P002** · fixed_band · true state `fake` · rating 5.0 · action `permit` · P(not genuine) 0.303729
  > The lifetime sharpening on the custom knives is a great value and the craftsmanship is on another level. Worth every penny. Ask for the flagship model.
- **P002** · expected_cost · true state `fake` · rating 5.0 · action `permit` · P(not genuine) 0.303729
  > The lifetime sharpening on the custom knives is a great value and the craftsmanship is on another level. Worth every penny. Ask for the flagship model.

### SARCASM-INVERTED: polarity contradicts the rating (2)

- **P004** · baseline_keyword · true state `genuine` · rating 1.0 · action `flag_with_explanation` · P(not genuine) n/a
  > Absolutely wonderful. Truly a fantastic experience waiting fifty minutes for a cold sandwich. Perfect.
- **P005** · baseline_keyword · true state `genuine` · rating 5.0 · action `flag_with_explanation` · P(not genuine) n/a
  > Terrible, awful, I hated every second of having to admit this is the best pizza in the city and now I have to drive here every week.

### VAGUE-NEGATIVE-FAKE: emotional one star, no detail (2)

- **P011** · fixed_band · true state `fake` · rating 1.0 · action `permit` · P(not genuine) 0.196337
  > Do not waste your money here. Worst place in town. Absolutely terrible, never going back.
- **P011** · expected_cost · true state `fake` · rating 1.0 · action `permit` · P(not genuine) 0.196337
  > Do not waste your money here. Worst place in town. Absolutely terrible, never going back.

### TERSE-GENUINE: a real reviewer who wrote almost nothing (1)

- **P007** · baseline_keyword · true state `genuine` · rating 5.0 · action `flag_with_explanation` · P(not genuine) n/a
  > Good product, arrived on time.
