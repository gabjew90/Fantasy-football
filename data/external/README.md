# External data drop zone

## fantasypros.csv (optional)

A FantasyPros ECR/ADP export. Overrides the auto-pulled ECR when present.
Flexible column names; needs at least player + position and one of
ecr_rank/adp:

```csv
player,position,team,ecr_rank,adp
Ja'Marr Chase,WR,CIN,1,2.1
...
```

## overrides.csv / overrides.<league>.csv (optional)

Hard projection overrides merged after the model runs (e.g., from PFF or
Fantasy Points Data Suite exports, or your own convictions). The real header
(draftkit/overrides.py reads it; only `sleeper_id` and `proj_pts` are
required):

```csv
sleeper_id,name,proj_pts,status,reason,source,date_checked
4034,Example Player,285,candidate,"why the number differs from the model",https://example.com/dated-source,2026-08-19
```

- `status`: `confirmed` rows are applied; `candidate` rows are INERT (the
  model's number stands and the row is reported as pending). A file with no
  `status` column is treated as all candidate.
- `date_checked`: the date the FACT was verified against the dated `source`
  -- not the date the row was edited, ported or rescaled (CLAUDE.md, record
  integrity).

Find sleeper_ids in tiers.csv.
