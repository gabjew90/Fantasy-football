# The customer version: layout and editorial style (the user, 2026-10-08)

The external report (the PDF) follows the user's report guide
(docs/plans/2026-10-08-report-format-design.md) in its visual layout and editorial style:
spacing, paragraph length, table density and selective bolding. publish_render builds the layout;
the analyst writes the reads to these rules, and publish.check enforces the parts a machine can.

## Rules, throughout

- Preserve the guide's heading hierarchy and section order. Keep headings short and consistent.
- Use generous whitespace: a blank line around headings, tables, paragraphs and lists.
- Keep tables compact: short labels, concise cells, explanations beneath the table.
- Write short paragraphs, usually 2-4 sentences, each developing one clear insight.
  *(Checked: no prose field over four sentences; the opening is exactly three.)*
- Bold only the decisive takeaway: the workload requirement, the key assumption, the preferred
  market, or the failure condition. *(Checked: at most one bold phrase per paragraph the analyst
  writes; the renderer bolds the requirement and the market in each card.)*
- Give every paragraph a purpose. Explain what the evidence means for this matchup or prop. Do not
  repeat the table's numbers or teach the reader how to read them without drawing a conclusion.
- Use concrete football explanations. Connect claims to recent opponents, player involvement,
  injuries or observed performance. *(Checked: "favorable matchup", "tough matchup", "smash spot"
  and the like are refused; say why.)*
- Explain technical terms once, in a short shared note. Use ordinary language in the player cards.
- Keep recommendations conditional and direct: state the belief that supports the leg and the
  specific condition that undermines it.

## Player narration, in this order

The line requires -> the engine expects -> the matchup supports or challenges -> if you believe
this, choose that. The renderer writes the first two from the run and the matchup sentence from
the read; the analyst's `explanation` adds the football reasoning, and the branches close the card.

## Before delivering

Edit the complete report for repetition, dense paragraphs, crowded tables and unnecessary
technical language. Preserve the evidence and reasoning needed to understand each recommendation.
