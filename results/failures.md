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

**Why this error costs the most.** Hiding a genuine review is the only action that removes a real customer's words while giving the seller no route to contest it, and its cost is multiplied by the volume factor, so a shop with few reviews absorbs nearly the whole penalty. Permitting a fake is diffuse and shared across many buyers; hiding a genuine review is concentrated on one business and one customer at once. This asymmetry is why the fixed-band policy was restricted to flag-with-explanation after the r/Amazonsellercentral discussion, and it is the clearest argument against letting the expected-cost policy select `hide` at all.

## Held-out test set

### NEGATIVE-FAKE-MISSED: a hostile fake that resembles a real complaint (11)

- **T001** · baseline_keyword · true state `fake` · rating 3.0 · action `permit` · P(not genuine) n/a
  > This is an interesting product, and it's an interesting product for a lot of reasons. First, it's very easy to put together and is easy to clean. The material is thick, and it's easy to cut out. The size is adjustable, a...
- **T005** · baseline_keyword · true state `fake` · rating 1.0 · action `permit` · P(not genuine) n/a
  > Came broken and cracked frame.  The only way to fix it was to just fix the frame
- **T005** · fixed_band · true state `fake` · rating 1.0 · action `permit` · P(not genuine) 0.33857
  > Came broken and cracked frame.  The only way to fix it was to just fix the frame
- **T008** · baseline_keyword · true state `fake` · rating 2.0 · action `permit` · P(not genuine) n/a
  > The stitching doesn't hold up, it feels a little tight but it's not a big deal.
- **T011** · baseline_keyword · true state `fake` · rating 1.0 · action `permit` · P(not genuine) n/a
  > This is similar to a real gun, with the instructions included.  There is a button that activates a two-step trigger.  There is also a plastic "lock" that activates the slide.  The slide will not stay in place.  This is w...
- **T011** · fixed_band · true state `fake` · rating 1.0 · action `permit` · P(not genuine) 0.018744
  > This is similar to a real gun, with the instructions included.  There is a button that activates a two-step trigger.  There is also a plastic "lock" that activates the slide.  The slide will not stay in place.  This is w...

### GENERIC-PRAISE-COLLISION: a genuine happy customer who wrote nothing specific (5)

- **T000** · baseline_keyword · true state `genuine` · rating 5.0 · action `flag_with_explanation` · P(not genuine) n/a
  > Quality and quite nonstick

I bought a "Scanpan Classic 11-Piece Deluxe Cookware Set" in 2007, and they have been great non stick pans, serving me well for nearly a decade.

Even with a lifetime warranty, I can't expect ...
- **T013** · fixed_band · true state `genuine` · rating 4.0 · action `flag_with_explanation` · P(not genuine) 0.98311
  > My dog loves this toy and is always chewing on it and he has nice strong, clean teeth.  This is my 3rd one.
- **T013** · expected_cost · true state `genuine` · rating 4.0 · action `hide` · P(not genuine) 0.98311
  > My dog loves this toy and is always chewing on it and he has nice strong, clean teeth.  This is my 3rd one.
- **T030** · baseline_keyword · true state `genuine` · rating 4.0 · action `flag_with_explanation` · P(not genuine) n/a
  > Remodeled our laundry room and got this for the wash sink. Been in use for over 6 months and has held up well still looks brand new after a lot of use. Spring/hose is pretty stiff and doesn't have a lot of play to it. Ov...
- **T035** · baseline_keyword · true state `genuine` · rating 4.0 · action `flag_with_explanation` · P(not genuine) n/a
  > I bought myself 2 and 1 as gift.  I LOVE that they are "real glass"  Really cant get better for $$$  The "Chain" Pet Stores more expensive!!  These were packed REALLY well.  I LOVE!!!  BTW: Do NOT put more than 3 or 4 gu...

### FLUENT-FAKE: machine text that reads like an ordinary short review (4)

- **T018** · baseline_keyword · true state `fake` · rating 4.0 · action `permit` · P(not genuine) n/a
  > It's sugary and tasty. Similar to an ice cream cone. I also love that it's easier
- **T018** · fixed_band · true state `fake` · rating 4.0 · action `permit` · P(not genuine) 0.09632
  > It's sugary and tasty. Similar to an ice cream cone. I also love that it's easier
- **T018** · expected_cost · true state `fake` · rating 4.0 · action `permit` · P(not genuine) 0.09632
  > It's sugary and tasty. Similar to an ice cream cone. I also love that it's easier
- **T039** · baseline_keyword · true state `fake` · rating 4.0 · action `permit` · P(not genuine) n/a
  > After reading Armored Hearts I was a little frustrated because it was a prequel to the first book.

I had a lot of fun with the characters and the storyline. I enjoyed that it was a little short.

I liked the ending. I l...

### TERSE-GENUINE: a real reviewer who wrote almost nothing (3)

- **T009** · baseline_keyword · true state `genuine` · rating 2.0 · action `flag_with_explanation` · P(not genuine) n/a
  > I was very disappointed with this purchase for my 5 year old.  It is very small, hard to transform, and comes apart very easily.  There are better Transformers out there.
- **T021** · baseline_keyword · true state `genuine` · rating 2.0 · action `flag_with_explanation` · P(not genuine) n/a
  > Normally I feed my cats Fromm Four Star dry foods but I was looking for something a little more budget friendly available with Prime shipping that was still a better brand. With four cats it gets expensive! After doing s...
- **T031** · baseline_keyword · true state `genuine` · rating 1.0 · action `flag_with_explanation` · P(not genuine) n/a
  > This GPS served me fairly well (although my first update seemed to mess up its routing) for three years.  It routed in basic fashion, and did not surprise me too much.  The selection to favor back roads was especially go...

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
