<!-- The user's team matchup guide (2026-10-06), binding for every single-game read: follow it exactly. Only change: the tier ladder table is replaced by the user's caption (same day). -->

# Team matchup section — report format and voice guide

A companion to the player-props section. Keep expected volume and offense-versus-defense as separate sections. The team section should explain the matchup well enough that the player section can immediately address workload, share, line and price.

The TB–DAL examples below use the snapshot supplied in the conversation. They illustrate the writing style; they are not newly verified game reporting. Brackets are template fields, not facts.

## Purpose

Tell the reader what game the market expects, how the teams have actually been playing, how their strengths and weaknesses meet in this matchup, and which circumstances could change the opportunities available to players.

The reader should finish with a concrete, conditional picture of the game. Do not leave them with statistics and an instruction to interpret those statistics themselves.

## Overall structure

Matchup header → opening game thesis → market → expected volume → offense against defense → injuries → positional production allowed → weather → baseline limitations → expected game flow → player props.

Each numbered section contains a compact table followed by one or two short paragraphs. The table holds exact data; the paragraphs explain what that evidence suggests for THIS matchup. Show every table in the chat, in order; do not replace tables with a list of fields or direct the reader to a download. Keep separate score and grade columns. Put positional fantasy-points ranks beside the value in parentheses, written as “(13th most),” without a separate rank column. Include the one or two numbers needed to understand a conclusion when the table has scrolled off the phone screen.

### Matchup header and opening thesis

**[Away] at [Home]**

[Day, date, local kickoff] · [venue] · [confirmed roof status or retractable, decision pending] · [relevant rest/travel context]

Sources updated: [market time] · [injury report date] · [performance through week/game] · [weather forecast time]

Open with two or three sentences naming the likely game flow, the evidence supporting it, and the main uncertainty. Write this after evaluating the sections below. Do not manufacture a dramatic storyline when the evidence describes a balanced or uncertain matchup.

**Example**

> The market expects Dallas to win by more than a touchdown. Dallas’s passing tendency while games are close supports a base case of passing to establish control, followed by more rushing if a comfortable lead develops. Tampa may have to chase, but the change at quarterback makes its ability to sustain drives the main uncertainty.

The spread supports the expected winner and margin; the sequence of passing early and running late is analytical judgment supported by team tendencies, not something directly quoted by the market.

## 1. The market’s view of the game

### Table

| Market | [Home] | [Away] |
|---|---:|---:|
| Spread | [spread] | [spread] |
| Implied team points | [points] | [points] |
| Total points | [total] | — |
| Move since opening | [like-for-like opening → current quote] | [if needed] |

Book: [book] · Updated: [timestamp]. Derive team points from the same book and snapshot. State the spread sign convention.

If the run includes historical game-state comparisons, show the share of PLAYS spent ahead, close and behind for comparable spreads, with the source window and sample. Do not present those shares as probabilities of a blowout or time spent leading.

### Required narration

Explain who is expected to control the game and whether the expected scoring is evenly distributed or concentrated on one side. Translate that into a likely change in passing/running as the game develops. Distinguish the expected final margin from the timing of a lead.

A line move shows a changed market assessment. Attribute it to an injury or other news only when that connection is supported; keep the opening and current quotes comparable.

**Example**

> Dallas carries the larger scoring expectation, so my base case gives it more opportunities to protect a lead late. That supports extra Dallas rushing and more Tampa passing if the separation develops early enough. The timing matters: a game that stays close into the fourth quarter would preserve more of Dallas’s normal passing workload.

## 2. Expected volume and how the teams have been playing

### Table

| Workload measure | [Home] | [Away] |
|---|---:|---:|
| Expected passes | [number] | [number] |
| Expected runs | [number] | [number] |
| Season passes per game | [number] | [number] |
| Season runs per game | [number] | [number] |
| Close-game pass rate | [%] | [%] |

League close-game pass rate: [%]. Window: [games/weeks]. Use one number per cell. In the current team-outlook table, passes are attempts excluding sacks; runs include scrambles. State the exact close-game definition used. The passing-unit score in section 3 uses a different play grouping, including sacks and scrambles; do not compare unlike counts.

Include a compact recent-game comparison when it changes the read: volume during a comparable comfortable win, competitive game, QB change or key absence. A full game log belongs in supporting detail if it adds no distinction.

### Required narration

Describe each team's observed identity, whether the engine preserves it, and the specific reason this matchup might depart from it. Address total opportunities as well as the pass/run split. Higher pass rate does not necessarily mean more attempts if the offense plays fewer snaps.

**Example**

> Dallas has favored passing while games are close, so I expect its quarterback and receivers to remain central early. The reason to move toward more Dallas carries is a later lead, rather than an expectation that it starts the game as a run-heavy offense.
>
> Tampa's normal approach has been more balanced. Falling behind could increase its passing share, but short possessions could still leave it with fewer throws than the baseline. Its ability to stay on the field is therefore as important as its willingness to throw.

Keep expected volume separate from section 3.

## 3. Unit performance and matchup: scores and tiers

### Matchup table

| Matchup | Offense score | Offense tier | Defense faced: score | Defense tier |
|---|---:|---|---:|---|
| [Home] passing vs. [Away] | [score] | [grade] | [score] | [grade] |
| [Home] rushing vs. [Away] | [score] | [grade] | [score] | [grade] |
| [Away] passing vs. [Home] | [score] | [grade] | [score] | [grade] |
| [Away] rushing vs. [Home] | [score] | [grade] | [score] | [grade] |

Window: [games/weeks]. Garbage-time filter: [exact rule used]. Show the engine's blended unit scores and grades in the main report, rather than raw EPA and success-rate columns. Each offense and opposing defense has its OWN score; these are not a single combined matchup grade.

Explain once: the score blends EPA per play and success rate with twice as much weight on EPA, then puts each unit type on a scale centered at 50. Higher is better for BOTH offenses and defenses. A score of 50 is the average unit; a 10-point difference is one standard deviation within that unit type. This is a descriptive performance scale, not a win probability, expected points scored or a yardage multiplier.

### Tier caption (user's amendment, 2026-10-06: no ladder table)

Keep the matchup table and replace the full ladder with this caption, verbatim:

> 50 = league average; higher is better for both offense and defense. S is the highest tier. +/− indicates position within a tier; compare the scores because neighboring grades can be very close.

That gives the reader the useful comparison without a second large table. Tiers are still equal-width bands counted down from each unit type's best team; never invent fixed cutoffs.

A + or - marks the top or bottom third within a band. Preserve those modifiers. A C- and a D+ can be close neighbors; do not describe them as a major difference based on their letters alone. Read the scores and the ladder together.

### Data availability and distinction from section 4

This section is implemented in the repo: the scorer retrieves current-season play-by-play, and research.unit_efficiency calculates EPA/success-based scores and tiers. Values require the relevant fields and eligible plays in that run. The table describes HOW the units have performed in the games already played; it does not establish who is available for this game.

### Required narration

For BOTH teams, say which side of its offense has performed better, how strong the opposing unit is, and what that combination suggests about moving the ball in THIS matchup. A strong offense facing a strong defense is a contested strength, not automatically an easy path. A weak offense facing a weak defense provides an opportunity, not proof it will execute well.

Compare the numerical scores as well as the grades. The offense and defense are standardized separately; subtracting their scores does not produce a validated matchup advantage or prop adjustment. The table supports judgment about relative unit performance.

Connect performance to opportunities carefully: sustaining drives can support more work, while failed drives can limit it. A favorable efficiency matchup does not automatically change a player's share.

**Voice example — only when the populated scores support it**

> Dallas's passing unit has been its stronger route to moving the ball, and Tampa's pass defense offers less resistance on the unit scores. That supports Dallas building its expected lead through passing before becoming more willing to run. The case for extra late carries still comes primarily from the lead; it needs separate evidence before becoming a rushing-efficiency increase.

Then give Tampa its own paragraph, identifying whether its passing or rushing unit has the more supportive opponent and whether today's quarterback/personnel match the games underlying those scores.

### Missing-data wording

“Not included in this run” means the report lacks the value. “The source has not published it” requires checking the source. “Unavailable” requires an established retrieval or coverage limitation. Never infer that the engine cannot compute a metric merely because it is absent from a snapshot.

If unit scores are absent, do not manufacture grades or replace the score with a fantasy-points ranking. In a template, brackets show the slots to populate. In a finished report, state the actual gap once and omit wholly empty tables.

## 4. Who plays: injuries and replacements

### Table

| Unit | [Home] | [Away] |
|---|---|---|
| Quarterback | [starter; official status; replacement] | [starter; official status; replacement] |
| Offensive line | [regulars available; names and statuses] | [regulars available; names and statuses] |
| Receivers, tight ends and backs | [relevant starter/rotation changes] | [relevant changes] |
| Pass rush and coverage | [relevant changes] | [relevant changes] |

Official report date: [date]. Note estimated practice participation, pending reports and unresolved statuses. Include a reserve or replacement only when that player directly changes the priced starters’ work.

### Data availability and distinction from section 3

The repo retrieves weekly rosters, depth charts, snap counts and injury reports. It identifies the starting quarterback, relevant skill-player designations and the regular offensive linemen, then checks their availability. Official reports take priority; a labeled Sleeper fallback can supply some offensive statuses when needed. The defensive personnel summary depends on the available injury report and explicitly says when no current report is present.

This section describes WHO is available now and what has changed from the players behind section 3's scores. A defense can retain a strong historical score while losing a starter this week; the personnel read explains why today's matchup may differ. Missing or unpublished statuses remain unknown.

### Required narration

For each material issue, explain the chain: WHO changes → WHICH job changes → WHICH opportunities or efficiency become less certain → WHAT confirmation changes the read.

A QB replacement can change accuracy, depth and target allocation, but do not automatically assume more checkdowns or lower efficiency without evidence. An offensive-line absence creates a protection or blocking question; it does not establish a numeric production penalty.

Questionable players get separate plays-normal-role and out cases. Do not invent participation probabilities or limited-role assumptions. Confirming availability does not by itself prove a normal workload.

**Example**

> The quarterback change is Tampa’s main personnel issue because the existing receiver baseline does not establish how accurately Daniels will throw or whom he will target. A deficit can create demand for passing while the offense still struggles to turn those throws into catches and yards. The most relevant evidence is the workload and distribution already observed with Daniels, adjusted for any difference in the available receivers.

## 5. Production allowed by position

### Table

| Defense | To RBs | To WRs | To TEs |
|---|---|---|---|
| [Home] | [value] ([ordinal] most) | [value] ([ordinal] most) | [value] ([ordinal] most) |
| [Away] | [value] ([ordinal] most) | [value] ([ordinal] most) | [value] ([ordinal] most) |
| League average | [value] | [value] | [value] |

PPR points allowed per game. Rank: 1 = most allowed, out of [teams]. Write the ordinal explicitly, for example “21.9 (13th most).” Window: [games/weeks]. These totals include touchdowns and aggregate all players at each position.

### Required narration

Identify a meaningful positional contrast and say how much weight it deserves beside the player’s own usage and the unit matchup. Do not translate fantasy points into a yardage multiplier, a target forecast or a coverage diagnosis.

**Example**

> Tampa’s observed results are more supportive for opposing tight-end production than for wide receivers. That makes the Dallas tight end’s involvement worth examining in the player section. It cannot establish that targets will move toward him, and four games of PPR results can reflect touchdowns and the opponents faced as much as a persistent defensive tendency.

When the contrast adds little, keep this section brief. Do not repeat the offense-versus-defense conclusion with different numbers.

## 6. Weather and venue

### Compact line or table

[Forecast game window: temperature, sustained wind, gusts, precipitation probability] · [provider/update time] · [confirmed roof status]

Retractable roof does not mean closed roof. Use confirmed roof status when known.

### Required narration

State whether the conditions supply a supported reason to change the passing/rushing read. If they do not, one sentence is enough.

Apply the skill’s passing-impact screen only above 15 mph SUSTAINED wind; gusts alone do not cross it. Crossing the screen prompts analysis, not an invented numerical penalty. Keep the forecast timestamp and uncertainty visible.

**Example**

> The supplied forecast gives no weather-based reason to depart from the normal workload baseline. Quarterback availability and the score are more consequential to this matchup.

Short rest and travel belong in the header and receive additional discussion only when there is specific evidence connecting them to this game’s personnel or preparation.

## 7. Where the baseline could miss this game

### Table

| Matchup issue | What the baseline may miss | Separate scenario to examine |
|---|---|---|
| [Backup QB] | [Catch efficiency, yards per target, target allocation or drive volume] | [Explicit input change; quantify only after running] |
| [Expected lead / deficit] | [Team run/pass workload change] | [Higher runs / lower passes; affected player share] |
| [Changed player role] | [Historical role no longer representative] | [Carry or target share range] |
| [Unresolved injury] | [Teammate redistribution] | [Plays normally versus out] |

Include only issues this matchup activates and limitations confirmed for the engine version actually used. Do not copy stale model limitations into every report.

### Required narration

Prioritize the biggest issue and explain which baseline numbers deserve a second scenario. Keep the baseline estimate, the assumption and the resulting scenario output distinct.

**Example**

> The baseline combines an ordinary Dallas workload with a Tampa passing game whose personnel has changed. I would examine a stronger late-running scenario for Dallas and separate lower-volume and lower-efficiency scenarios for Tampa. Lowering Tampa’s yards alone would obscure whether the concern is fewer opportunities or worse production from each opportunity.

Do not claim a narrative adjustment is already reflected in the model unless the run actually applies it. Label experimental results, including “with market carries,” alongside the baseline.

## 8. Expected game flow and what would change it

### Table

| Game path | How it develops | [Home] opportunities | [Away] opportunities |
|---|---|---|---|
| Base case | [Evidence-supported sequence] | [Pass/run implications] | [Pass/run implications] |
| Competitive alternative | [What keeps the game close] | [What changes] | [What changes] |
| Main failure branch | [Specific uncertainty resolves differently] | [What changes] | [What changes] |

These are analytical scenarios. Give no scenario probabilities unless they have actually been estimated. Choose alternatives specific to the matchup; do not reuse the same three generic branches in every game.

### Required narration and handoff

Give the strongest supported directional workload read and the most conditional one. End by explaining what must be checked in the player section: the recipient’s role, the actual line, the price and the user’s expected workload.

**Example**

> My base case is Dallas passing while it establishes control, then leaning more on rushing if the lead becomes comfortable. Tampa would pass more often while chasing, with drive success and target quality still uncertain.
>
> If Tampa keeps it close, Dallas retains more late passing and Tampa can preserve more running. If Tampa’s offense stalls, its passing share can rise while its total attempts remain disappointing.
>
> The clearest team-level volume angle is additional Dallas rushing if the lead develops. The next question is which back keeps that work. Tampa receiving opportunities are more conditional because they require enough sustained drives and catchable targets, not simply a deficit.

## Voice guide

### Core voice

Write as a football analyst explaining a decision to someone who watches the game but does not follow betting mathematics. Be direct, specific and conversational. Spell out the inference rather than leaving it to the reader.

Use the recurring sequence:

**Observation → matchup implication → opportunity consequence → condition that could change it.**

Use one or two compact paragraphs under each table, usually two to four sentences each. A section may be shorter when the evidence adds little.

### Identify whose statement it is

| Type | Natural wording |
|---|---|
| Market expectation | “The market expects…” |
| Observed performance | “Through four games, Dallas has…” |
| Model estimate | “The engine projects…” |
| Judgment | “My base case is…” / “That supports…” |
| Conditional inference | “If the lead develops…” / “This would strengthen the case for…” |

Do not present projected volume as a verified future fact or your game sequence as a market quote. You do not need to label every sentence with a technical evidence category when these distinctions are clear in the wording.

### Interpret; do not narrate every table cell

Weak: “Dallas has a 63% close-game pass rate versus the league’s 56%.”

Better: “Dallas has favored passing while games are close, so I expect its passing game to remain central early. The reason to expect extra carries is a later lead, rather than a sudden change in its opening approach.”

Weak: “Tampa is projected for 33 attempts.”

Better: “The projection requires Tampa to sustain more passing opportunities than its backup quarterback’s first start produced. Falling behind could increase the need to throw, but short drives could prevent that need from turning into actual volume.”

Weak: “The defense allows the ninth-most points to tight ends.”

Better: “The positional results give the opposing tight end some matchup support, but his target role remains the deciding input. The total includes touchdowns and cannot establish that he will receive more work.”

Weak: “The quarterback is out, which boosts the running back’s receptions.”

Better: “The quarterback change makes target allocation less certain. A receiving boost for the back needs evidence that he is being used as an outlet; the absence alone does not establish it.”

### Required distinctions

- Score expectation versus offensive quality: implied points summarize the matchup, not an isolated ranking of the offense.
- Passing share versus passing count: a team can throw on a larger share of fewer plays.
- Workload versus efficiency: more targets do not ensure more catches or yards.
- Team volume versus player share: extra runs only help the back who receives them.
- Early-game versus late-game opportunity: the same offense can pass to take a lead and run to protect it.
- Receptions versus receiving yards: short catches can support one line while leaving the other short.
- Rushing versus combined yards: receiving helps only if the runner retains a meaningful passing-down role.
- Recent performance versus changed personnel: last week transfers more readily when the relevant QB and teammates remain the same.
- Model input versus context: a statistic in the report may inform judgment without being an adjustment in the engine.

### Avoid

Unexplained jargon; stock narratives; broadcast adjectives and metaphors such as “stingiest,” “explosive,” “air it out” and “feast”; “smash spot,” “lock,” “automatic Over”; unsupported scheme claims; guessing how a backup plays; attributing line moves without evidence; repeating generic uncertainty after every paragraph. Use plain “passes,” explain unit scores once, and do not show raw EPA in the main unit table.

Keep sample-size cautions next to the conclusion they actually limit. Give a counterargument that could change the read, rather than a generic “anything can happen.”

### Finished-report check

1. Does the opening explain the game expected and why?
2. Does each team get a performance and matchup interpretation?
3. Are expected volume and offense-versus-defense still separate?
4. Are section 3's observed unit performance and section 4's current availability clearly distinguished?
5. Does each injury explanation identify a pathway to opportunity or efficiency?
6. Are facts, estimates and judgment distinguishable?
7. Does the game-flow section state what would change the baseline?
8. Does the handoff explain which player roles and lines need examination next?
9. Are all quotations, forecasts, injury statuses and performance windows timestamped or dated?
10. Are missing data and unrun scenarios visible without invented numbers?
