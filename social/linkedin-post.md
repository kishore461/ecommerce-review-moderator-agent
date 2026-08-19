# LinkedIn post

One post, published once this week, with `paper/preprint.pdf` attached.

---

I spent this week building an agent that decides what to do with a customer
review it cannot verify, and the most useful thing I can report is where it
loses.

**The problem, in one sentence:** the agent observes a newly submitted customer
review's text and star rating, and must permit, warn, hide, or report it,
because whether the post is a genuine customer experience or a paid or
competitor fake is not known.

**Why the agent is built this way.** It sees the text and the rating and
nothing else — no account age, no purchase history, no reviewer history. That
constraint is enforced in code, not promised in a README. A practitioner in
r/LanguageTechnology told me flatly that a single review cannot be classified
without user history or graph features. He is right, so the agent is scoped as
a cold-start triage filter whose most valuable output is often the admission
that it does not know. It can decline to decide and hand the case to a person.
That is the one human faculty I tried to imitate, and it is the only one.

**Why a probability model rather than a threshold.** The agent keeps a full
belief over three hidden states and picks the action with the lowest expected
cost under an asymmetric cost matrix. I built a fixed-threshold version too, so
the two could be compared. The difference shows up in the decision record: at a
91% belief the threshold policy acts, and the cost policy still routes to a
human, because the residual chance the review is genuine is not worth the harm
of being wrong. A threshold cannot see that the cost of being wrong changed. It
only sees that a number crossed a line.

**The result I did not want.** On the held-out set the agent beats a keyword
baseline — precision 0.647 to 0.933. On a 12-case probe set I wrote
specifically to attack my own assumptions, the baseline wins on recall, 0.857
against 0.333. The single worst decision in the whole experiment was the agent
hiding a real customer's review at 98.3% confidence:

> "My dog loves this toy and is always chewing on it and he has nice strong,
> clean teeth. This is my 3rd one."

A real person wrote that, and my agent removed it.

**A design change that came from a conversation, not from a paper.** I had two
hidden states, genuine and fake. Someone in r/Yelp told me that when he says
"fake" he does not mean paid spam — he means a friend or family member writing
a review for someone they know. The visit happened. The detail is real. So the
strongest signal I had, whether the review names something checkable, is blind
to it by construction. I added a third hidden state for this, and it is the
change I would never have found in the literature.

**The largest limitation, stated plainly.** The dataset labels machine-written
versus human-written text. My problem statement is about a *paid human* writing
a fake. Those are not the same question, so every number above tests one corner
of the problem and says nothing about the case that motivated the work. There
is a second one I like even less: I have run no dialect or demographic bias
audit, and a unigram filter that treats brevity as evidence will sit most
confidently on exactly the writer with the least standard English.

Preprint attached — IJCAI style, written for a course, not submitted anywhere.
Code, data splits, failure analysis, and a record of every AI review comment I
accepted or rejected: https://github.com/kishore461/ecommerce-review-moderator-agent

Built with AI assistance for the code and the writing. Every public discussion
that changed the design was a conversation I had myself, and each one is logged
with a link.
