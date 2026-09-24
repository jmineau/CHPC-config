#!/usr/bin/env python3
"""Collect a digest of the past week's activity: git commits, changed files, SLURM jobs.

Writes plain markdown to stdout. No LLM, no network. Safe to run on a login node:
all filesystem walks are depth-limited and prune known bulk-output directories.

Edit ROOTS / PRUNE / GIT_REPOS below to change what gets scanned.
"""
import argparse
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

HOME = Path.home()

# Author regex for git log (matches "Name <email>"). Kept broad on purpose.
AUTHOR = r"Mineau|jameskmineau|James\.Mineau"

# (path, maxdepth) for the changed-file walk. Depth is the safety valve -- a full
# walk of the methane or stilt trees takes >5 min on NFS, a depth-capped one <1s.
# methane and stilt get the most depth; everything else is a shallow sweep.
# Stable ~/lgs/jkm paths, NOT ~/wkspace: the shelf is pruned whenever something
# goes dormant, which silently dropped mobile + inversion-dev from this scan (2026-09).
ROOTS = [
    ("~/lgs/jkm/24/methane", 5),
    ("~/lgs/jkm/27/stilt", 4),
    ("~/lgs/jkm/24/meteorology", 3),
    ("~/lgs/jkm/24/uataq/mobile", 3),
    ("~/lgs/jkm/24/inversion-dev", 3),
    ("~/lgs/jkm/24/uataq/pipeline", 3),
    ("~/lgs/jkm/24/uataq/web", 3),
]

# Directory names never descended into. "simulations" and "chunks" are the STILT
# output trees (millions of footprint files); the rest is caches and build junk.
PRUNE = [
    ".git", "__pycache__", ".ipynb_checkpoints", ".venv", "node_modules",
    "_build", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".Rproj.user",
    "site-packages", ".snakemake", ".conda", ".cache",
    "simulations", "chunks", "by-id", "footprints", "particles", "archive",
]

# Extensions treated as output/data rather than work-product worth logging.
SKIP_EXT = {
    ".pyc", ".nc", ".nc4", ".h5", ".hdf5", ".zarr", ".parquet", ".rds", ".rdata",
    ".pkl", ".pickle", ".npy", ".npz", ".gz", ".zip", ".tar", ".log", ".swp",
    ".png", ".pdf", ".jpg", ".jpeg", ".tif", ".tiff", ".gif",
}

MAX_FILES_PER_ROOT = 60


def repos():
    """Git repos to harvest, deduped by realpath."""
    found, seen = [], set()
    globs = [
        "software/python/pkgs/*",
        "wkspace/*",
        "lgs/jkm/27/stilt/code/*",
        "lgs/jkm/24/uataq/*",          # pipeline, mobile, docs
        "lgs/jkm/24/uataq/web/*",      # air.utah.edu, shiny-shire
        "lgs/jkm/24/uataq/pi/air-trend",
        ".chpc-config",
    ]
    for pattern in globs:
        for path in sorted(HOME.glob(pattern)):
            real = path.resolve()
            if (real / ".git").exists() and real not in seen:
                seen.add(real)
                found.append(real)
    return found


def run(cmd, cwd=None, timeout=90):
    try:
        out = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return out.stdout.strip()
    except (subprocess.TimeoutExpired, OSError) as err:
        return f"[scan error: {err}]"


def dirty_section():
    """Uncommitted work in progress.

    This is the one thing `git log` cannot see. An mtime walk of a git repo is
    NOT a substitute: git operations (checkout, pull, branch switch) rewrite
    file mtimes, so recent-mtime files are often months-old code that was never
    touched this week. `git status` has no such false positives.
    """
    lines = []
    for repo in repos():
        out = run(["git", "status", "--porcelain"], cwd=repo)
        if not out or out.startswith("[scan error"):
            continue
        entries = [ln for ln in out.splitlines() if ln.strip()]
        # Ignore untracked noise; staged/modified tracked files are the signal.
        tracked = [ln for ln in entries if not ln.startswith("??")]
        if not tracked:
            continue
        branch = run(["git", "branch", "--show-current"], cwd=repo) or "detached"
        lines.append(f"\n### {repo.name}  (branch {branch})")
        for ln in tracked[:20]:
            lines.append(f"  - {ln.strip()}")
        if len(tracked) > 20:
            lines.append(f"  - ...and {len(tracked) - 20} more")
    return "\n".join(lines) if lines else "\n_Working trees clean._"


def git_section(since, until):
    lines = []
    for repo in repos():
        log = run([
            "git", "log", "-E", "--all", "--no-merges", f"--author={AUTHOR}",
            f"--since={since}", f"--until={until}",
            "--pretty=format:  - %ad %h %s", "--date=short",
        ], cwd=repo)
        if not log or log.startswith("[scan error"):
            continue
        stat = run([
            "git", "log", "-E", "--all", "--no-merges", f"--author={AUTHOR}",
            f"--since={since}", f"--until={until}", "--shortstat",
            "--pretty=format:",
        ], cwd=repo)
        churn = [s.strip() for s in stat.splitlines() if s.strip()]
        lines.append(f"\n### {repo.name}  ({len(log.splitlines())} commits)")
        lines.append("\n".join("  " + ln.lstrip() for ln in log.splitlines()))
        if churn:
            lines.append(f"  _churn: {len(churn)} commits touched files_")
    return "\n".join(lines) if lines else "\n_No commits in this window._"


def files_section(days):
    lines = []
    prune_expr = []
    for name in PRUNE:
        prune_expr += ["-name", name, "-o"]
    prune_expr = ["("] + prune_expr[:-1] + [")", "-prune", "-o"]

    for root, depth in ROOTS:
        path = Path(os.path.expanduser(root))
        if not path.exists():
            continue
        out = run(
            ["find", "-L", str(path), "-maxdepth", str(depth)]
            + prune_expr
            + ["-type", "f", "-mtime", f"-{days}", "-print"],
            timeout=120,
        )
        if out.startswith("[scan error"):
            lines.append(f"\n### {root}\n  {out}")
            continue
        hits = []
        for f in out.splitlines():
            if Path(f).suffix.lower() in SKIP_EXT or Path(f).name.startswith("."):
                continue
            try:
                mtime = os.path.getmtime(f)
            except OSError:
                continue
            hits.append((mtime, os.path.relpath(f, path)))
        if not hits:
            continue
        hits.sort(reverse=True)
        shown = hits[:MAX_FILES_PER_ROOT]
        lines.append(f"\n### {root}  ({len(hits)} files changed)")
        for mtime, rel in shown:
            stamp = datetime.fromtimestamp(mtime).strftime("%a %m-%d")
            lines.append(f"  - {stamp}  {rel}")
        if len(hits) > len(shown):
            lines.append(f"  - ...and {len(hits) - len(shown)} more")
    return "\n".join(lines) if lines else "\n_No changed files in this window._"


def slurm_section(since, until):
    out = run([
        "sacct", "-S", since, "-E", until, "-X", "-n", "-P",
        "--format=JobID,JobName,Partition,State,Elapsed",
    ])
    if not out or out.startswith("[scan error"):
        return f"\n_{out or 'No jobs in this window.'}_"

    groups = {}
    for row in out.splitlines():
        parts = row.split("|")
        if len(parts) < 5:
            continue
        _, name, part, state, elapsed = parts[:5]
        state = state.split()[0]
        key = (name, part)
        g = groups.setdefault(key, {"n": 0, "states": {}, "secs": 0})
        g["n"] += 1
        g["states"][state] = g["states"].get(state, 0) + 1
        try:
            hms = elapsed.split("-")[-1].split(":")
            secs = sum(int(v) * m for v, m in zip(reversed(hms), (1, 60, 3600)))
            g["secs"] += secs
        except ValueError:
            pass

    lines = [f"\n_{sum(g['n'] for g in groups.values())} jobs across "
             f"{len(groups)} job names._"]
    for (name, part), g in sorted(groups.items(), key=lambda kv: -kv[1]["n"]):
        states = ", ".join(f"{k}:{v}" for k, v in sorted(g["states"].items()))
        hours = g["secs"] / 3600
        lines.append(f"  - **{name}** ({part}) x{g['n']} -- {states} "
                     f"-- {hours:.1f} core-h elapsed")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7, help="lookback window")
    args = ap.parse_args()

    end = datetime.now()
    start = end - timedelta(days=args.days)
    since = start.strftime("%Y-%m-%d")
    until = end.strftime("%Y-%m-%d")

    t0 = time.time()
    out = [
        f"# Activity digest {since} to {until}",
        "",
        "## Git commits",
        git_section(since, until),
        "",
        "## Uncommitted work in progress",
        dirty_section(),
        "",
        "## Changed files",
        files_section(args.days),
        "",
        "## SLURM jobs",
        slurm_section(since, until),
    ]
    print("\n".join(out))
    print(f"\n_scan took {time.time() - t0:.1f}s_")


if __name__ == "__main__":
    main()
