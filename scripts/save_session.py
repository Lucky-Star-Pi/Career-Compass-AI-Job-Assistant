"""Persist a browser session cookie to data/private/session.json.

The cookie is read without echo, written locally, and never printed, logged,
transmitted, or passed on a command line. Only non-reversible metadata is shown.
"""
import argparse
import getpass
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "data" / "private" / "session.json"
CST = timezone(timedelta(hours=8))


def fingerprint(cookie):
    blob = cookie.encode("utf-8")
    return {"bytes": len(blob), "sha256_8": hashlib.sha256(blob).hexdigest()[:8]}


def clean(raw):
    value = (raw or "").strip()
    if value.lower().startswith("cookie:"):
        value = value.split(":", 1)[1].strip()
    value = value.replace("\r", "").replace("\n", "")
    return value


def validate(cookie):
    if not cookie:
        return "Cookie 为空"
    if len(cookie) < 20:
        return "长度过短，可能是复制不完整"
    if "=" not in cookie:
        return "不含 '='，看起来不是 Cookie 请求头"
    if len(cookie) > 8192:
        return "长度异常（>8192），请只复制 Cookie 请求头的值"
    return None


def save(path):
    print("请从浏览器 F12 → Network → 任一 zhidianmijin.com.cn 请求 → 复制请求头 Cookie 的值")
    try:
        cookie = clean(getpass.getpass("粘贴后按回车（输入不回显）: "))
    except (KeyboardInterrupt, EOFError):
        print("\n已取消", file=sys.stderr)
        return 3

    problem = validate(cookie)
    if problem:
        print("FAIL: " + problem, file=sys.stderr)
        return 2

    payload = {
        "cookie": cookie,
        "exported_at": datetime.now(CST).isoformat(timespec="seconds"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)

    print("saved: bytes={bytes} sha256_8={sha256_8} exported_at={exported_at}".format(
        exported_at=payload["exported_at"], **fingerprint(cookie)))
    print("path: " + str(path))
    print("提醒：该文件已被 .gitignore 的 data/private/ 排除；用完请删除。")
    return 0


def verify(path):
    if not path.is_file():
        print("MISSING: " + str(path), file=sys.stderr)
        return 4
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        print("FAIL: 无法解析 " + type(exc).__name__, file=sys.stderr)
        return 5
    cookie = payload.get("cookie") or ""
    info = fingerprint(cookie) if cookie else {"bytes": 0, "sha256_8": "-"}
    print("present: bytes={bytes} sha256_8={sha256_8} exported_at={exported_at}".format(
        exported_at=payload.get("exported_at", "unknown"), **info))
    return 0 if cookie else 6


def main(argv=None):
    parser = argparse.ArgumentParser(description="Save session cookie locally without echoing it.")
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--verify", action="store_true", help="only report metadata of an existing file")
    args = parser.parse_args(argv)
    path = args.path if args.path.is_absolute() else (ROOT / args.path)
    if path.suffix.lower() != ".json":
        print("FAIL: 输出必须是 .json", file=sys.stderr)
        return 7
    return verify(path) if args.verify else save(path)


if __name__ == "__main__":
    raise SystemExit(main())
