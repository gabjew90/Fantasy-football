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

## overrides.csv (optional)

Hard projection overrides merged after the model runs (e.g., from PFF or
Fantasy Points Data Suite exports, or your own convictions):

```csv
sleeper_id,proj_pts
4034,285
```

Find sleeper_ids in tiers.csv.
