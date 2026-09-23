#!/usr/bin/env python3
"""Rebuild the rule sets from MetaCubeX/meta-rules-dat.

Runs locally or in CI (GitHub Actions). Stdlib only.

  python3 scripts/build.py            # rebuild rules/*.json in place
  python3 scripts/build.py --check    # fail if any file would change (CI dry-run)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
RULES = ROOT / "rules"

MIRRORS = (
    "https://cdn.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@sing/geo/geosite/{}.json",
    "https://fastly.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@sing/geo/geosite/{}.json",
    "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/{}.json",
)
FIELDS = ("domain", "domain_suffix", "domain_keyword", "domain_regex")

# Hosts that must always resolve direct. Kept here so a rebuild never drops them.
EXTRA_DIRECT_HOSTS = ("molin.myds.me", "smalin.myds.me")

TARGETS = {
    # `cn` is required: geolocation-cn alone misses taobao/weibo/alipay/alibaba/alicdn/sina.
    "direct-cn.json": (["private", "cn", "geolocation-cn", "apple-cn", "microsoft@cn", "google-cn"], True),
    "ads.json": (["category-ads-all"], False),
    "proxy-cn.json": (["geolocation-!cn", "gfw"], False),
}

FOREIGN_PROBES = (
    "google.com", "youtube.com", "facebook.com", "twitter.com", "x.com", "instagram.com",
    "github.com", "openai.com", "chatgpt.com", "anthropic.com", "claude.ai", "netflix.com",
    "telegram.org", "t.me", "wikipedia.org", "reddit.com", "stackoverflow.com", "npmjs.com",
    "docker.com", "pypi.org", "cloudflare.com", "amazon.com", "apple.com", "microsoft.com",
    "spotify.com", "discord.com",
)


def fetch(name: str) -> dict:
    last = None
    for tpl in MIRRORS:
        url = tpl.format(name)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if "rules" not in data:
                raise ValueError("missing 'rules'")
            return data
        except Exception as exc:  # noqa: BLE001 - fall through to the next mirror
            last = exc
    raise RuntimeError(f"all mirrors failed for {name}: {last}")


def build(sources, with_hosts):
    acc = {f: [] for f in FIELDS}
    for name in sources:
        for rule in fetch(name).get("rules") or []:
            for field in FIELDS:
                values = rule.get(field)
                if isinstance(values, list):
                    acc[field].extend(values)
    for field in acc:
        acc[field] = sorted(set(acc[field]))
    if with_hosts:
        # Both fields: `domain` is exact, `domain_suffix` is suffix. Guarantees a hit.
        for host in EXTRA_DIRECT_HOSTS:
            for field in ("domain", "domain_suffix"):
                if host not in acc[field]:
                    acc[field].append(host)
        for field in ("domain", "domain_suffix"):
            acc[field] = sorted(set(acc[field]))
    return {"version": 2, "rules": [{k: v for k, v in acc.items() if v}]}


def verify(direct: dict) -> list[str]:
    problems = []
    rule = direct["rules"][0]
    domain, suffix = set(rule.get("domain", [])), set(rule.get("domain_suffix", []))
    for host in EXTRA_DIRECT_HOSTS:
        if host not in domain and host not in suffix:
            problems.append(f"required host missing: {host}")
    # True suffix semantics — substring matching false-positives on dl.google.com.
    captured = [
        f for f in FOREIGN_PROBES
        if any(f == x or f.endswith("." + x) for x in domain | suffix)
    ]
    if captured:
        problems.append(f"foreign domains captured by direct list: {captured}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit 1 if any file would change")
    args = ap.parse_args()

    RULES.mkdir(parents=True, exist_ok=True)
    changed = False

    for filename, (sources, with_hosts) in TARGETS.items():
        data = build(sources, with_hosts)
        text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        json.loads(text)

        if with_hosts:
            problems = verify(data)
            if problems:
                for p in problems:
                    print(f"  FAIL {filename}: {p}", file=sys.stderr)
                return 1

        path = RULES / filename
        old = path.read_text(encoding="utf-8") if path.exists() else None
        total = sum(len(v) for v in data["rules"][0].values())
        if old != text:
            changed = True
            if not args.check:
                path.write_text(text, encoding="utf-8")
            print(f"  {'would update' if args.check else 'updated'} {filename}: {total} entries, {len(text) // 1024} KB")
        else:
            print(f"  unchanged {filename}: {total} entries")

    if args.check and changed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
