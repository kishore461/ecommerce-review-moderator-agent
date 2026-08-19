# X thread

Post as a thread from @Kishore_mint. Attach `paper/preprint.pdf` to tweet 1.
Every tweet below is under 280 characters.

---

**1/7**

I built an agent that decides whether to permit, warn, hide or report a
customer review, seeing only the review text and the star rating. No account
age, no purchase history. Preprint attached. The useful part is where it loses.

**2/7**

It keeps a belief over three hidden states and picks the action with the lowest
expected cost, rather than firing at a threshold. I built the threshold version
too so the two could be compared. Against a keyword baseline, precision went
0.647 to 0.933.

**3/7**

Then I wrote 12 cases designed to attack my own assumptions. On those the
keyword baseline beats the agent on recall, 0.857 to 0.333. The probe set did
its job. A result that only ever goes up means the test was too easy.

**4/7**

Worst single decision it made: it hid a real customer's review at 98.3%
confidence.

"My dog loves this toy and is always chewing on it and he has nice strong,
clean teeth. This is my 3rd one."

A person wrote that. My agent removed it.

**5/7**

I also ablated my own six hand-designed features. Removing them costs one case
out of forty. A plain unigram model does nearly all the work. The
interpretable part I was proudest of turned out to be close to decoration.

**6/7**

The design change I'd never have found in a paper: someone in r/Yelp said that
by "fake" he meant a friend writing a review for a business he knows. Real
visit, real detail, not independent. My best signal is blind to it. That became
a third hidden state.

**7/7**

Biggest limitation, said plainly: the dataset labels machine-vs-human text,
but my problem is a paid human. Different question. Code, splits, failure
analysis and every AI review comment I accepted or rejected:

https://github.com/kishore461/ecommerce-review-moderator-agent
