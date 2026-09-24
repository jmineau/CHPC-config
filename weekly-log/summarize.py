#!/usr/bin/env python3
"""Summarize an activity digest into a weekly research log.

Reads the digest on stdin (or --digest FILE) and POSTs it to the CHPC-hosted
vLLM endpoint on nimbus. Prompts stay on CHPC hardware; no external API, no
API key, no per-token cost.

Usage:
    python3 scan.py | python3 summarize.py -o weeks/2026-09-15.md
    python3 summarize.py --digest d.md --dry-run   # print the prompt, call nothing
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ENDPOINT = "http://nimbus.chpc.utah.edu:44242/v1/chat/completions"
MODEL = "Qwen/Qwen3.8-27B-FP8"
TIMEOUT = 600
# The nimbus server hard-caps completions at 2048 tokens regardless of what we
# ask for, so there is no point requesting more.
MAX_TOKENS = 2048

SYSTEM = (
    "You are summarizing a researcher's week from machine-collected activity "
    "data. The researcher is an atmospheric science PhD student estimating "
    "methane emissions in the Salt Lake Valley. They maintain Python packages "
    "(slv, fips, pystilt/stilt, lair, uataq, arlmet) and run the STILT "
    "atmospheric transport model on a SLURM cluster. Write plainly and "
    "concretely. Never invent work that is not evidenced in the data."
)

PROMPT = """Below is an automated digest of my activity for the past week:
git commits, files I modified, and SLURM jobs I ran.

Write my weekly log in markdown with these sections:

## Summary
Two or three sentences on what the week was actually about.

## What moved forward
Group the work by project or theme, not by repository. Each bullet should say
what changed and why it matters. Merge related commits into one bullet rather
than restating the commit list. Skip pure release/chore/CI noise unless it was
the point of the work.

## Compute
One short paragraph on the SLURM jobs: what was being run, and note any
failures (OUT_OF_MEMORY, CANCELLED, TIMEOUT) as things that may need attention.

## Open threads
What looks in progress or unfinished. Lean on the "Uncommitted work in
progress" section -- those are edits I have not committed, so they are the
strongest evidence of what I was mid-way through. Note the branch if it is not
main. Also flag SLURM failures worth chasing. If something is ambiguous, say so
rather than guessing. Keep this short.

Rules:
- Only use what is in the digest. Do not speculate about motivation.
- Refer to code by package and module name where the digest gives it.
- The "Changed files" section is file paths only -- you cannot see file
  contents, so do not describe what the code in them does. Commit messages are
  the reliable description of the work; file paths only show where it happened.
- A file appearing under "Changed files" may just have been touched by a git
  operation rather than edited. Do not build a claim on a file path alone.
- No preamble, no closing remarks. Start with the `## Summary` heading.

--- DIGEST ---
{digest}
"""


def strip_thinking(text):
    """Qwen models can emit <think>...</think> preambles; drop them."""
    while "<think>" in text and "</think>" in text:
        head, _, rest = text.partition("<think>")
        _, _, tail = rest.partition("</think>")
        text = head + tail
    return text.strip()


def summarize(digest):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": PROMPT.format(digest=digest)},
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.3,
        # Qwen3 defaults to thinking mode, which spends the whole 2048-token
        # budget on a `reasoning` field and returns empty content. Off.
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        body = json.load(resp)
    choice = body["choices"][0]
    msg = choice["message"]
    text = strip_thinking(msg.get("content") or "")
    if not text:
        # Empty content with a populated reasoning channel means thinking mode
        # ate the token budget -- see chat_template_kwargs above.
        reasoning = msg.get("reasoning") or msg.get("reasoning_content") or ""
        raise RuntimeError(
            f"empty completion (finish_reason={choice.get('finish_reason')}, "
            f"reasoning_chars={len(reasoning)}); usage={body.get('usage')}"
        )
    return text, body.get("usage", {})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--digest", type=Path, help="digest file (default: stdin)")
    ap.add_argument("-o", "--out", type=Path, help="write log here (default: stdout)")
    ap.add_argument("--dry-run", action="store_true", help="print prompt, no call")
    args = ap.parse_args()

    digest = args.digest.read_text() if args.digest else sys.stdin.read()
    if not digest.strip():
        sys.exit("error: empty digest")

    if args.dry_run:
        print(PROMPT.format(digest=digest))
        return

    try:
        log, usage = summarize(digest)
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError,
            RuntimeError, TimeoutError) as err:
        sys.exit(f"error: summarization failed ({type(err).__name__}: {err})")

    header = (
        f"# Weekly log -- generated {datetime.now():%Y-%m-%d %H:%M}\n\n"
        f"_Model: {MODEL} on nimbus. "
        f"{usage.get('prompt_tokens', '?')} in / "
        f"{usage.get('completion_tokens', '?')} out._\n\n"
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(header + log + "\n")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(header + log)


if __name__ == "__main__":
    main()
