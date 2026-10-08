# Yahoo Fantasy Sports API — access request brief (for a computer-use agent)

Context: since 2026-07-22 Yahoo gates the Fantasy Sports API behind a manual
review. This brief tells an agent how to submit the request. Nothing here is
secret; the Client ID is supplied by the human at submit time.

## Task for the agent

Submit a read-only access application at:

    https://sports.yahoo.com/developer/access/

Ground rules for the agent:
- The human signs in to Yahoo themselves if a sign-in wall appears. Never enter a
  password, 2FA code, or the Client SECRET anywhere. Only the Client ID goes in
  the form, and only if the human pastes it into the chat for you.
- Read every field label on the live page; if a field exists that is not listed
  below (e.g. Name, Email, Organization, Product name, Website), fill it from the
  "Identity" block. Do not invent facts.
- Show the human the completed form (screenshot or field-by-field summary) and
  get an explicit "yes" BEFORE clicking "Submit Application". Submitting is
  irreversible.
- After submitting, capture any confirmation text / reference number and report
  it back verbatim.

## Field values

| Field on page                | Value                                                            |
|------------------------------|------------------------------------------------------------------|
| Expected Users (dropdown)    | Small (< 1,000 users)                                             |
| Notes / use case (textarea)  | Paste the "Notes text" block below, unchanged                    |
| Client ID (optional text)    | The Client ID of the NEW app created 2026-08-19 on developer.yahoo.com — human pastes it; leave blank if not provided |
| Read/Write request           | Do NOT request write access. Read-only is all that is needed.    |
| Consent                      | Submitting implies agreeing to Yahoo's Terms & Privacy Policy — confirm with the human first |

Identity block (only if the page asks):
- Name: [human's full name]
- Email: [the Yahoo account email used for the fantasy league]
- Organization / company: Individual — personal use, no organization
- Product / app name: fantasy-retro
- Website / URL: none (personal, local-only script)

## Notes text (paste verbatim into the Notes / description field)

Personal, single-league retrospective analysis of my own 2025 Yahoo Fantasy
Football league (12-team, PPR). A Python script running locally on my own
computer will read — read-only — my league's settings and scoring rules, draft
results, weekly rosters with points, weekly matchup results, transactions
(adds/drops/trades/waivers), and final standings. Output is a private season
summary for my own use in preparing for the 2026 season: points returned per
draft pick vs draft slot, best/worst value picks, bench points left unused,
value of waiver pickups, positional scarcity in hindsight, and my team's
weekly luck vs the league median.

Data needed: league, settings, draftresults, teams, roster (per week),
scoreboard/matchups (per week), transactions, standings — for one league key
only (game 461 / NFL 2025).

Intended users: only me, a member of that league. Access is limited to personal,
single-league use. No data is redistributed, published, or shown to anyone
else. No write operations are performed. Expected request volume: a one-time
pull of roughly a few hundred requests total, throttled with delays, plus
occasional re-runs. Client credentials are stored only in a git-ignored local
file.

## After submission
- Delete the OLD app on https://developer.yahoo.com/apps/ (its secret was
  exposed once). Keep the NEW app — that is the Client ID Yahoo will scope.
- When Yahoo approves: `cd` to the repo, `Remove-Item .yahoofantasy` if it
  still holds the old app, then `.\venv\Scripts\yahoofantasy.exe login`,
  and confirm the consent screen now mentions Fantasy Sports.
