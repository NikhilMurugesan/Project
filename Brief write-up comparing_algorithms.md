# Greedy vs Hungarian — what I learned

Short version: they're both fine, they share most of their code, and the interesting
question is *when* the extra work of Hungarian pays off.

## The headline

| Aspect                       | Greedy                                | Hungarian (in rounds)                  |
|------------------------------|----------------------------------------|----------------------------------------|
| What it looks at             | one order at a time                    | all current orders + trucks at once    |
| Roughly how expensive        | `O(N · M · R)`                         | per round: matrix build + `O(M³)`      |
| Quality when things are easy | basically optimal                      | basically optimal                      |
| Quality when things are tight| can lock the wrong truck early         | balances the trade-offs globally       |
| Works for streaming input?   | yes — decide as orders come in         | no, needs a batch                      |
| Reproducible?                | yes, but sensitive to sort order       | yes, stable for a given cost matrix    |

`R` is the average number of insertion checks per truck route — basically how many stops
are already on the route.

## The setup is identical

This matters more than it sounds: both algorithms use **the same** `cheapest_insertion`
router, **the same** hard-constraint checks (capability, capacity, time window, SLA,
shift), and **the same** soft scoring (distance + priority − workload). The only thing
that differs is the selection step. So any quality difference you see really is about
greedy-vs-batch, not about one algorithm being given better tools.

## When greedy is fine

- **There's enough slack.** Orders are spread out, every order has an obvious best truck,
  nobody is fighting over the same vehicle.
- **Orders arrive one at a time.** If you have to answer a request the moment it comes in,
  you can't wait around to batch — greedy is the only honest choice.
- **You're really tight on compute.** Greedy is linear in the number of orders for a
  fixed fleet size. On huge inputs it just keeps chugging.

## When Hungarian actually helps

- **Trucks are scarce and orders are competing.** Greedy commits early; once a truck is
  spoken for, the next order has to settle. Hungarian sees all the rows at once and
  trades.
- **Priorities + capacity together.** Greedy will happily put a high-priority order on
  the truck right next to it, then make a low-priority order do a long-haul. Hungarian
  notices that swapping them costs almost nothing on the high-priority leg and saves a
  lot on the low-priority one.
- **You want balanced workload.** Greedy has to "discover" balance through the workload
  penalty round by round. Hungarian's solver already factors that in when it picks.

## The tiny worked example (in `tests/test_algorithms.py`)

```
Trucks: T1 at (51.5, -0.100)
        T2 at (51.5,  0.045)        ~10 km east of T1
Orders: A  at (51.5, -0.0275)       midpoint — ~5 km from each truck, priority 5
        B  at (51.5, -0.093)        almost on top of T1 — ~0.5 km from T1, ~9.5 km from T2, priority 1
Both orders 80 kg, trucks hold 100 kg → one order each.
```

| Algorithm   | What it does          | Total distance |
|-------------|------------------------|----------------|
| Greedy      | A → T1 (5 km), B → T2 (9.5 km) | **14.5 km** |
| Hungarian   | A → T2 (5 km), B → T1 (0.5 km) | **5.5 km**  |

Greedy processes A first because it has the higher priority, picks T1 (closest, free,
fine), and then B is stuck with T2. The cost of A → T1 vs A → T2 is identical, so the
"correct" swap is free — but greedy can't see that, because by the time it looks at B,
A is already committed.

This same shape shows up in bigger random scenarios any time two or more orders share
their best truck but disagree on the runner-up.

## What I see on the seeded scenarios

Comparing on `medium-demo` (8 trucks × 25 orders) and `large-demo` (15 × 60):

- **Assignments completed**: usually equal. Both algorithms enforce hard constraints
  the same way, so whatever is feasible for one is feasible for the other.
- **Total distance**: Hungarian is at least as good as greedy, and often a few km
  better on medium scenarios, more often on large ones.
- **Workload spread**: Hungarian tends to be more even. Greedy lets the geographically
  lucky truck collect cheap stops while the others stay underused.
- **Runtime**: greedy wins on tiny inputs. On bigger ones the gap shrinks, because most
  of the time in both is spent computing the same insertion deltas — Hungarian just
  reuses them as a matrix instead of throwing them away.
- **SLA met**: identical in most runs. SLA is a hard constraint, so both algorithms
  either honor it or skip the order.

## Things I want to be honest about

- The Hungarian wrapper runs in **rounds**. Each round is provably optimal on its own,
  but stitching rounds together is a heuristic. A real VRP solver would jointly
  optimize the multi-stop sequences, and would beat both of these.
- Hungarian is only as good as the cost matrix you feed it. I'm feeding it the
  *marginal* cost of inserting one more stop into the current route, which is the
  right thing for round-by-round work but stops being optimal if you wanted to plan
  many days ahead.
- Distances are straight-line. Conclusions transfer to real road distances because
  the *ordering* between options is usually preserved, but the absolute km numbers
  obviously wouldn't match a routing engine.

## So what should you use?

- For **planning ahead** (you have a list of today's orders and you want the best
  plan), use Hungarian. The global view is cheap and the wins are real.
- For **live dispatch** (orders are coming in, you have to answer now), use greedy
  with reasonable priority and workload weights. It's the right *shape* of algorithm
  for the situation, and the soft penalties keep it from doing anything silly.
- If I had to ship one thing, I'd ship both, behind a flag — which is roughly what
  the API does now. Switching is a one-line change because everything underneath is
  shared.
