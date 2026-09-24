# Weekly activity log

Scans what you worked on in the past week and writes a readable log. Runs from
cron **Friday 06:00**, ahead of the 10:00 group meeting. Costs nothing: the
summarization runs on the CHPC-hosted model, not a paid API.

## Pieces

| File | Role |
|---|---|
| `scan.py` | Collects git commits, changed files, and SLURM jobs into a markdown digest. No network, no LLM. |
| `summarize.py` | POSTs the digest to the nimbus vLLM endpoint, writes the log. |
| `run.sh` | Cron entrypoint. Runs both, keeps the digest alongside the log. |
| `weeks/` | `YYYY-MM-DD.md` (the log) and `YYYY-MM-DD.digest.md` (the raw evidence). |
| `logs/cron.log` | Cron output, appended. |

## Usage

`weeklog` is on PATH (`~/software/bash/bin/weeklog`) and prints to the terminal
as well as saving:

    weeklog                     # last 7 days
    weeklog --since-last        # since the last log was generated
    weeklog --days 3            # last 3 days
    weeklog --since 2026-09-12  # since a specific date

**For a mid-week meeting** (e.g. Wednesday with John), `weeklog --since-last`
is the one you want: it covers exactly what has happened since Friday's
group-meeting log, with no overlap and no gap.

`run.sh` takes the same options; `weeklog` just adds `--print`. Cron calls
`run.sh` with no arguments, i.e. a fixed 7-day window -- deliberately *not*
`--since-last`, so an ad-hoc mid-week run cannot shorten the Friday report.

Ad-hoc runs save to `weeks/<today>.md` like any other, so there is a record of
what you reported and when.

    python3 scan.py --days 7                          # digest only, inspect it
    python3 summarize.py --digest weeks/X.digest.md   # re-summarize, no re-scan
    python3 summarize.py --digest X.md --dry-run      # see the exact prompt

Re-summarizing from a kept digest is the cheap way to iterate on the prompt --
no filesystem walk needed.

## What it scans

- **Git commits** -- `~/software/python/pkgs/*`, `~/wkspace/*`,
  `~/lgs/jkm/27/stilt/code/*`, the UATAQ repos under `~/lgs/jkm/24/uataq/`
  (`*`, `web/*`, `pi/air-trend`), and `~/.chpc-config`, filtered to your authorship.
  Highest-signal source by far; your commit messages do most of the work.
- **Uncommitted work** -- `git status` in those same repos. Catches what you
  were mid-way through. Untracked files (`??`) are skipped as editor noise.
- **Changed files** -- the `ROOTS` list in `scan.py` (stable `~/lgs/jkm/...` paths, not the
  pruned `~/wkspace` shelf), with `methane` and `stilt`
  given the most depth per your preference. Deliberately covers *workspaces
  only*, not the packages -- see below.
- **SLURM jobs** -- `sacct` for the window, grouped by job name with state
  counts and elapsed hours.

## Why the packages are not in the file walk

`~/software/python/pkgs/*` is scanned for **commits and uncommitted changes**,
but is deliberately *not* in `ROOTS`. Two sources, two jobs:

| | Covered by |
|---|---|
| Packages (`pkgs/*`, `stilt/code/*`) | git -- they are all repos |
| Workspaces (`methane`, `stilt`, ...) | file walk -- these are not repos |

Adding the packages to the file walk was measured and rejected. In `slv`, a
depth-4 pruned walk yields 22 files: 15 already described by that week's commit
messages, and of the remaining 7, five are `.egg-info` build artifacts. The
last two are worse than useless -- `src/slv/measurements/aggregate.py` showed a
2026-09-15 mtime while being clean in git and last committed **2026-03-23**. A
git operation rewrote its mtime; no one worked on it that week.

So in a git repo, mtime is strictly the weaker signal: its true positives are
already stated better by commit messages, and its false positives invent work
that never happened. `git status` closes the only genuine gap (uncommitted
edits) with no false positives. That is why `dirty_section()` exists.

The file walk is still right for the workspaces, because they are not git
repos, so mtime is the only signal available there.

## Two things to know if you edit it

**The depth cap is load-bearing.** An uncapped `find` over `wkspace/methane`
takes over 5 minutes of NFS metadata traffic; depth-capped it takes 0.3s. The
`PRUNE` list also skips the STILT output trees (`simulations`, `chunks`,
`by-id`, `footprints`) which hold far too many files to walk. Do not remove
`-maxdepth` or shorten `PRUNE` without timing it first -- this runs on a login
node, and only stays acceptable there because it is bounded.

**Two nimbus quirks**, both already handled in `summarize.py`:
- The server hard-caps completions at **2048 tokens** no matter what
  `max_tokens` says.
- Qwen3 defaults to thinking mode, which spends that entire budget on a
  `reasoning` field and returns **empty content**. Disabled via
  `chat_template_kwargs: {"enable_thinking": false}`. If you ever see "empty
  completion" with a large `reasoning_chars`, this setting got lost.

Scripts use only the Python standard library, so no conda env is needed --
which is why `run.sh` works in a bare cron environment.

## Endpoint

`http://nimbus.chpc.utah.edu:44242/v1` -- OpenAI-compatible vLLM serving
`Qwen/Qwen3.8-27B-FP8`, 262k context, no API key. Internal to CHPC, so prompts
stay on CHPC hardware. Declared in
`/uufs/chpc.utah.edu/sys/etc/agents/opencode.json`.
