#!/usr/bin/env python3
"""Send screenshots to a vision model on OpenRouter and get back structured UI findings.

    python3 ~/.claude/skills/ui-review/scripts/review.py review \
        --brief brief.json --rubric ~/.claude/skills/ui-review/references/rubric.md \
        [--context .claude/ui-review.md] \
        --image .ui-review/run1/01-record.png [--image ...] [--pair mock.png build.png ...] \
        [--model google/gemini-2.5-flash-lite] [--out .ui-review/run1]

    uv run python …/review.py ask --image shot.png "Is there a backspace key on the keypad?"
    uv run python …/review.py models                  # candidate vision models + live price

Claude never opens the image: the model's text is what comes back. Every image must sit next to
the `<name>.src.json` sidecar that capture.sh writes, and its url must be a localhost stack —
a cloud screenshot holds real participant PII. Every request is price-sorted and
`data_collection: deny`. The run directory keeps request (minus image bytes), response and cost.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import pathlib
import re
import sys
import time

import httpx
from PIL import Image

API = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = os.environ.get("UI_REVIEW_MODEL", "google/gemini-2.5-flash-lite")
MAX_EDGE = int(os.environ.get("UI_REVIEW_MAX_EDGE", "1568"))  # px, long edge after downscale
JPEG_Q = int(os.environ.get("UI_REVIEW_JPEG_QUALITY", "80"))
LOCAL = re.compile(
    r"^(https?://(localhost|127\.0\.0\.1|[a-z0-9.-]+\.localhost)(:\d+)?(/|$)|file:///)", re.I
)
CANDIDATES = (  # the bake-off shortlist; `models` prints live prices for these
    "google/gemini-2.5-flash-lite",
    "google/gemini-2.5-flash",
    "qwen/qwen3-vl-32b-instruct",
    "qwen/qwen3-vl-8b-instruct",
    "openai/gpt-5-nano",
    "openai/gpt-5-mini",
    "openai/gpt-4o-mini",
    "mistralai/mistral-small-3.2-24b-instruct",
    "z-ai/glm-5.3-flash",
)


def die(msg: str, code: int = 2) -> None:
    print(f"✗ {msg}", file=sys.stderr)
    sys.exit(code)


def key() -> str:
    k = os.environ.get("OPENROUTER_API_KEY")
    if not k:
        die("OPENROUTER_API_KEY is not set")
    return k


def sidecar(png: pathlib.Path, *, optional: bool = False) -> dict:
    """The provenance capture.sh wrote. Missing or non-local ⇒ refuse (PII rule).

    A MOCK image may come straight from a design folder with no sidecar (optional=True): it is
    a design asset, not a screenshot of anyone's data.
    """
    sc = png.with_suffix(".src.json")
    if not sc.exists():
        if optional:
            return {"url": f"file://{png.resolve()}", "viewport": None}
        die(f"{png}: no {sc.name} sidecar — capture with capture.sh, never a bare screenshot")
    meta = json.loads(sc.read_text())
    if not LOCAL.match(meta.get("url") or ""):
        die(f"{png}: source {meta.get('url')!r} is not local — never sent (PII)")
    return meta


def encode(png: pathlib.Path) -> tuple[str, tuple[int, int], int]:
    """Downscale + JPEG: the single biggest cost lever (images bill as input tokens by size)."""
    im = Image.open(png)
    im = im.convert("RGB")
    w, h = im.size
    scale = MAX_EDGE / max(w, h)
    if scale < 1:
        im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=JPEG_Q, optimize=True)
    data = buf.getvalue()
    return base64.b64encode(data).decode(), im.size, len(data)


def legend_text(png: pathlib.Path) -> str:
    """The annotate legend capture.sh saved: `data.annotations[]` with number/ref/role/name."""
    lg = png.with_suffix(".legend.json")
    if not lg.exists():
        return ""
    try:
        d = json.loads(lg.read_text())
    except json.JSONDecodeError:
        return ""
    ann = ((d.get("data") or {}).get("annotations")) or d.get("annotations") or []
    lines = [
        f"[{a.get('number')}] @{a.get('ref')} {a.get('role', '')} {a.get('name', '')}".rstrip()
        for a in ann[:150]
        if a.get("number")
    ]
    return "Element labels in this image ([N] = element ref):\n" + "\n".join(lines) if lines else ""


def image_part(b64: str) -> dict:
    return {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}


def call(model: str, messages: list, max_tokens: int, out: pathlib.Path | None, label: str) -> dict:
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "usage": {"include": True},
        "provider": {"sort": "price", "data_collection": "deny"},
    }
    t0 = time.time()
    with httpx.Client(timeout=180) as c:
        r = c.post(
            f"{API}/chat/completions",
            json=body,
            headers={
                "Authorization": f"Bearer {key()}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/saccacare",
                "X-Title": "saccacare ui-review",
            },
        )
    try:
        resp = r.json()
    except ValueError:
        die(f"OpenRouter returned non-JSON ({r.status_code}): {r.text[:300]}")
    if out:
        out.mkdir(parents=True, exist_ok=True)
        slim = json.loads(json.dumps(body))
        for m in slim["messages"]:
            if isinstance(m.get("content"), list):
                for p in m["content"]:
                    if p.get("type") == "image_url":
                        p["image_url"] = {"url": "<image bytes omitted>"}
        (out / f"{label}.request.json").write_text(json.dumps(slim, indent=1))
        (out / f"{label}.response.json").write_text(json.dumps(resp, indent=1))
    if "error" in resp:
        die(f"OpenRouter error {resp['error'].get('code')}: {resp['error'].get('message')}", 4)
    u = resp.get("usage") or {}
    cost = u.get("cost")
    print(
        f"· {model} via {resp.get('provider')} · {u.get('prompt_tokens')} in"
        f" / {u.get('completion_tokens')} out"
        f" · {f'${cost:.4f}' if cost is not None else 'cost n/a'} · {time.time() - t0:.1f}s",
        file=sys.stderr,
    )
    return resp


def content_text(resp: dict) -> str:
    return ((resp.get("choices") or [{}])[0].get("message") or {}).get("content") or ""


def parse_json(text: str) -> dict | None:
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S) or re.search(
        r"(\{.*\})", text, re.S
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def reviewer_context(profile: pathlib.Path) -> str:
    """The `## Reviewer context` section of a project profile, or the whole file if it has none."""
    text = profile.read_text()
    m = re.search(r"^## Reviewer context\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    return (m.group(1) if m else text).strip()


def cmd_review(a: argparse.Namespace) -> int:
    rubric = pathlib.Path(a.rubric).read_text()
    if a.context:
        rubric += "\n\n## Reviewer context (this project)\n\n" + reviewer_context(
            pathlib.Path(a.context)
        )
    brief = json.loads(pathlib.Path(a.brief).read_text())
    for k in ("feature", "userGoal", "stateShown", "surface", "viewport"):
        if k not in brief:
            die(f"brief is missing '{k}' — fixed fields only, no free text (see SKILL.md)")
    parts: list[dict] = [
        {"type": "text", "text": "BRIEF (fixed fields):\n" + json.dumps(brief, indent=1)}
    ]
    manifest = []
    n = 0
    for png in a.image or []:
        p = pathlib.Path(png)
        meta = sidecar(p)
        b64, size, nbytes = encode(p)
        n += 1
        parts.append(
            {
                "type": "text",
                "text": (
                    f"IMAGE {n}: build — {p.stem} — {meta['url']}"
                    f" — viewport {meta.get('viewport')}\n{legend_text(p)}"
                ).rstrip(),
            }
        )
        parts.append(image_part(b64))
        manifest.append(
            {
                "n": n,
                "kind": "build",
                "file": str(p),
                "sent": f"{size[0]}x{size[1]} {nbytes // 1024}KB",
            }
        )
    for mock, build in a.pair or []:
        for kind, png in (("mock", mock), ("build", build)):
            p = pathlib.Path(png)
            meta = sidecar(p, optional=(kind == "mock"))
            b64, size, nbytes = encode(p)
            n += 1
            parts.append(
                {
                    "type": "text",
                    "text": (
                        f"IMAGE {n}: {kind.upper()} of pair '{pathlib.Path(build).stem}'"
                        f" — {meta['url']}\n{legend_text(p) if kind == 'build' else ''}"
                    ).rstrip(),
                }
            )
            parts.append(image_part(b64))
            manifest.append(
                {
                    "n": n,
                    "kind": kind,
                    "file": str(p),
                    "sent": f"{size[0]}x{size[1]} {nbytes // 1024}KB",
                }
            )
    if n == 0:
        die("no images given")
    parts.append({"type": "text", "text": "Return ONLY the JSON object the rubric specifies."})
    messages = [{"role": "system", "content": rubric}, {"role": "user", "content": parts}]
    out = pathlib.Path(a.out) if a.out else None
    resp = call(a.model, messages, a.max_tokens, out, "review")
    text = content_text(resp)
    data = parse_json(text)
    if data is None:
        print(text)
        die("model did not return the JSON object; raw text printed above", 5)
    data["_manifest"] = manifest
    data["_model"] = resp.get("model")
    data["_usage"] = resp.get("usage")
    if out:
        (out / "findings.json").write_text(json.dumps(data, indent=1))
    findings = data.get("findings") or []
    order = {"blocker": 0, "major": 1, "minor": 2, "note": 3}
    findings.sort(key=lambda f: order.get(str(f.get("severity")).lower(), 9))
    print(f"\nverdict: {data.get('verdict', '?')} — {len(findings)} findings\n")
    print("| # | severity | label | where | what | expected | fix |\n|---|---|---|---|---|---|---|")
    for i, f in enumerate(findings, 1):
        row = [str(i)] + [
            str(f.get(k, "") or "").replace("|", "\\|").replace("\n", " ")
            for k in ("severity", "label", "where", "what", "expected", "fix")
        ]
        print("| " + " | ".join(row) + " |")
    if data.get("openQuestion"):
        print(f"\nopen question: {data['openQuestion']}")
    return 0


def cmd_ask(a: argparse.Namespace) -> int:
    p = pathlib.Path(a.image)
    sidecar(p)
    b64, _, _ = encode(p)
    parts = [
        {
            "type": "text",
            "text": a.question + "\nAnswer in at most three sentences, from the image only.",
        },
        image_part(b64),
    ]
    lg = legend_text(p)
    if lg:
        parts.insert(0, {"type": "text", "text": lg})
    resp = call(
        a.model,
        [{"role": "user", "content": parts}],
        300,
        pathlib.Path(a.out) if a.out else None,
        f"ask-{int(time.time())}",
    )
    print(content_text(resp).strip())
    return 0


def cmd_models(a: argparse.Namespace) -> int:
    with httpx.Client(timeout=30) as c:
        data = c.get(f"{API}/models").json()["data"]
    by_id = {m["id"]: m for m in data}
    print(f"{'$/M in':>7} {'$/M out':>7}  id   (default {DEFAULT_MODEL}; env UI_REVIEW_MODEL)")
    for mid in CANDIDATES:
        m = by_id.get(mid)
        if not m:
            print(f"{'?':>7} {'?':>7}  {mid}  (not listed)")
            continue
        p = m["pricing"]
        print(f"{float(p['prompt']) * 1e6:7.2f} {float(p['completion']) * 1e6:7.2f}  {mid}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("review", help="review build screenshots (and mock/build pairs)")
    r.add_argument("--brief", required=True, help="JSON with the fixed brief fields")
    r.add_argument("--rubric", required=True, help="references/rubric.md (the system prompt)")
    r.add_argument(
        "--context", help="project profile (.claude/ui-review.md); its Reviewer context is appended"
    )
    r.add_argument("--image", action="append", help="a build screenshot (repeatable)")
    r.add_argument(
        "--pair",
        nargs=2,
        action="append",
        metavar=("MOCK", "BUILD"),
        help="a mock/build pair (repeatable)",
    )
    r.add_argument("--model", default=DEFAULT_MODEL)
    r.add_argument("--max-tokens", type=int, default=2500)
    r.add_argument("--out", help="run directory for request/response/findings (default: none)")
    r.set_defaults(fn=cmd_review)
    q = sub.add_parser("ask", help="one question about one image")
    q.add_argument("--image", required=True)
    q.add_argument("question")
    q.add_argument("--model", default=DEFAULT_MODEL)
    q.add_argument("--out")
    q.set_defaults(fn=cmd_ask)
    m = sub.add_parser("models", help="candidate vision models with live prices")
    m.set_defaults(fn=cmd_models)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
