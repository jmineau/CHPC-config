#!/usr/bin/env python3
"""Check the account layout for the four kinds of drift the 2026-09 reorg found
by hand: broken symlinks, dead 'cd' aliases, stale backup sources, and code
still pointing at the pruned ~/wkspace shelf.

Plain text to stdout, exit 0 always (report-only). No network. All filesystem
walks are depth-limited and prune known bulk-output directories -- the same
lesson ~/.weekly-log/scan.py already learned: an uncapped find over methane or
stilt takes minutes on NFS, a capped one takes well under a second.

Run by hand: python3 ~/.chpc-config/bin/drift-check.py
Cron: see the crontab entry alongside ~/.weekly-log's Friday job.
"""
import os
import re
import subprocess
from pathlib import Path

HOME = Path.home()

# Same roots/depths ~/.weekly-log/scan.py uses for its changed-file walk, plus a
# couple of shallow ones (~, ~/wkspace, ~/lgs) this script alone needs.
ROOTS = [
    ("~", 2),
    ("~/wkspace", 1),
    ("~/lgs", 3),
    ("~/lgs/jkm/24/methane", 6),
    ("~/lgs/jkm/27/stilt/code", 5),
    ("~/lgs/jkm/27/stilt/validation", 4),
    ("~/lgs/jkm/24/meteorology", 4),
    ("~/lgs/jkm/24/uataq", 7),
    ("~/lgs/jkm/24/inversion-dev", 6),
    ("~/lgs/jkm/24/academic", 5),
    ("~/software/python/pkgs", 4),
    ("~/.chpc-config", 3),
]

# Same PRUNE list as scan.py (bulk output / build junk never worth descending
# into). "archive" is pruned there for speed too -- if you need a thorough check
# of a specific archive/ subtree, point a one-off `find ... -xtype l` at it.
PRUNE = {
    ".git", "__pycache__", ".ipynb_checkpoints", ".venv", "node_modules",
    "_build", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".Rproj.user",
    "site-packages", ".snakemake", ".conda", ".cache",
    "simulations", "chunks", "by-id", "footprints", "particles", "archive",
    "out", "outputs", "_products", "site_libs", "_site", "cache",
}

# .md deliberately excluded: AGENTS.md/README.md files describe the ~/wkspace
# shelf convention in prose (that's their job), which isn't the same as a
# script hardcoding a path that breaks when something comes off the shelf.
CODE_EXT = {".py", ".r", ".R", ".sh", ".ipynb", ".yml", ".yaml", ".toml"}


def find_broken_symlinks():
    """xtype-l walk per root, pruning PRUNE dirs, capped at each root's depth."""
    broken = []
    for root, depth in ROOTS:
        base = Path(os.path.expanduser(root))
        if not base.is_dir():
            continue
        prune_args = []
        for name in PRUNE:
            prune_args += ["-name", name, "-o"]
        prune_args = prune_args[:-1]  # drop trailing -o
        cmd = ["find", str(base), "-maxdepth", str(depth),
               "(", *prune_args, ")", "-prune", "-o", "-xtype", "l", "-print"]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
        except subprocess.TimeoutExpired:
            broken.append(f"  [TIMEOUT after 60s scanning {root} -- widen PRUNE or shrink depth]")
            continue
        for line in out.splitlines():
            broken.append(f"  {line}  -> {os.readlink(line)}")
    return broken


def find_dead_aliases():
    """Parse `alias NAME="cd PATH ..."` lines and check PATH exists."""
    dead = []
    aliases_file = HOME / ".chpc-config" / ".aliases"
    if not aliases_file.is_file():
        return [f"  [.aliases not found at {aliases_file}]"]
    pat = re.compile(r'^alias\s+([\w-]+)="cd\s+([^"&|;]+)')
    for line in aliases_file.read_text().splitlines():
        m = pat.match(line.strip())
        if not m:
            continue
        name, path = m.group(1), m.group(2).strip()
        expanded = os.path.expanduser(os.path.expandvars(path))
        if not os.path.exists(expanded):
            dead.append(f"  {name}: cd {path}  (-> {expanded}, MISSING)")
    return dead


def find_stale_backup_sources():
    """Each non-comment line of directories.txt is `<local> <remote>`. Expand
    $VARS the same way backup.sh's login shell would: source .env, then
    backup.sh's own `LG24=$COMMON/lin-group24` (defined in the script, not
    .env -- a naive .env-only expansion misses it and false-positives every
    $LG24/... entry)."""
    path = HOME / ".chpc-config" / "backup" / "directories.txt"
    if not path.is_file():
        return [f"  [{path} not found]"]
    env = dict(os.environ)
    env_file = HOME / ".env"
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            try:
                env[k.strip()] = subprocess.run(
                    ["bash", "-c", f'echo "{v.strip()}"'], capture_output=True,
                    text=True, env=env, timeout=5,
                ).stdout.strip()
            except Exception:
                pass
    env["LG24"] = f"{env.get('COMMON', '')}/lin-group24"
    stale = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        local = line.split()[0]
        expanded = os.path.expanduser(
            subprocess.run(["bash", "-c", f'echo "{local}"'], capture_output=True,
                            text=True, env=env, timeout=5).stdout.strip()
        )
        if not os.path.exists(expanded):
            stale.append(f"  {local}  (-> {expanded}, MISSING)")
    return stale


def find_wkspace_refs():
    """`~/wkspace/<entry>` in project code is the anti-pattern SLV's own AGENTS.md
    warns about: the shelf is pruned, so a hardcoded reference breaks whenever
    something comes off it (this is exactly how Phase 4 broke 11 links)."""
    hits = []
    pat = re.compile(r"~/wkspace/[A-Za-z0-9._-]+")
    for root, depth in ROOTS:
        base = Path(os.path.expanduser(root))
        if not base.is_dir() or root in ("~", "~/wkspace"):
            continue
        prune_args = []
        for name in PRUNE:
            prune_args += ["-name", name, "-o"]
        prune_args = prune_args[:-1]
        cmd = ["find", str(base), "-maxdepth", str(depth), "(", *prune_args, ")",
               "-prune", "-o", "-type", "f", "-print"]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
        except subprocess.TimeoutExpired:
            hits.append(f"  [TIMEOUT after 60s scanning {root}]")
            continue
        for f in out.splitlines():
            if Path(f).suffix not in CODE_EXT:
                continue
            try:
                text = Path(f).read_text(errors="ignore")
            except OSError:
                continue
            for m in sorted(set(pat.findall(text))):
                hits.append(f"  {f}: {m}")
    return hits


def section(title, items):
    print(f"\n## {title}  ({len(items)} found)")
    if not items:
        print("  (clean)")
    else:
        for i in items:
            print(i)


def main():
    print(f"# Drift check -- {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}")
    section("Broken symlinks", find_broken_symlinks())
    section("Dead 'cd' aliases", find_dead_aliases())
    section("Stale ~/.backup/directories.txt sources", find_stale_backup_sources())
    section("~/wkspace/<entry> refs in project code (pruned-shelf anti-pattern)", find_wkspace_refs())


if __name__ == "__main__":
    main()
