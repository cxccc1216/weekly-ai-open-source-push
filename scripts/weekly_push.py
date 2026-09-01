#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每周 AI 开源项目精选推送（GitHub Actions 定时运行）
数据源：GitHub Trending (weekly)
推送：Server酱（微信「方糖」服务号）
"""

import os
import re
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

SENDKEY = os.environ.get("SERVERCHAN_SENDKEY", "")
REPORT_FILE = "weekly-report.md"

# 翻译缓存（避免同一项目重复请求）
_TRANSLATE_CACHE = {}


def translate_zh(text: str) -> str:
    """调用 Google Translate 免费接口把英文描述翻译为中文；失败时回退英文原文"""
    if not text:
        return ""
    if text in _TRANSLATE_CACHE:
        return _TRANSLATE_CACHE[text]
    try:
        q = urllib.parse.quote(text[:500])
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q={q}"
        req = urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"]})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", "ignore"))
        parts = []
        for seg in data[0]:
            if seg and seg[0]:
                parts.append(seg[0])
        result = "".join(parts).strip() or text
        _TRANSLATE_CACHE[text] = result
        return result
    except Exception:
        _TRANSLATE_CACHE[text] = text
        return text

# AI 项目关键词（匹配仓库名/描述）
AI_PATTERN = re.compile(
    r"\b(ai|llm|gpt|agent|claude|openai|anthropic|diffusion|chat|assistant|copilot|neural|rag|whisper|llama|qwen|deepseek|gemini|model|intelligence|pipeline|image|video|audio|speech|vision|translate|ocr)\b",
    re.I,
)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "ignore")


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def parse_trending(html: str) -> list:
    """解析 GitHub Trending 页面，返回仓库列表"""
    items = []
    blocks = re.findall(r'<article class="Box-row">(.*?)</article>', html, re.S)
    for b in blocks:
        name_m = re.search(r'<h2[^>]*>\s*<a[^>]*href="/([^"]+)"', b)
        if not name_m:
            continue
        full_name = name_m.group(1).strip("/")
        desc_m = re.search(r'<p class="col-9[^"]*"[^>]*>(.*?)</p>', b, re.S)
        desc = clean(re.sub(r"<[^>]+>", "", desc_m.group(1))) if desc_m else ""
        lang_m = re.search(r'itemprop="programmingLanguage">([^<]+)<', b)
        lang = lang_m.group(1).strip() if lang_m else ""
        stars_m = re.search(r"repo-stars-counter-star[^>]*>([\d,]+)<", b)
        total = int(stars_m.group(1).replace(",", "")) if stars_m else 0
        week_m = re.search(r"([\d,]+)\s+stars?\s+(?:this week|today)", b)
        week = int(week_m.group(1).replace(",", "")) if week_m else 0
        items.append(
            {
                "name": full_name,
                "desc": desc,
                "lang": lang,
                "stars": total,
                "week": week,
            }
        )
    return items


def is_ai(item: dict) -> bool:
    text = f"{item['name']} {item['desc']}".lower()
    return bool(AI_PATTERN.search(text))


def build_markdown(ai_items: list, top_items: list, week_range: str) -> str:
    lines = [
        f"# 🤖 本周 AI 开源项目精选（{week_range}）",
        "",
        "数据来源：GitHub Trending（每周榜）",
        "",
        "## 🔥 AI 相关 · 本周精选",
        "",
    ]
    for i, it in enumerate(ai_items[:12], 1):
        url = f"https://github.com/{it['name']}"
        star = f"⭐本周 +{it['week']:,}" if it["week"] else f"⭐{it['stars']:,}"
        lines.append(f"{i}. **[{it['name']}]({url})** {star}")
        desc_zh = translate_zh(it["desc"]) if it["desc"] else ""
        if desc_zh:
            lines.append(f"   {desc_zh[:90]}")
        lines.append("")
    if top_items:
        lines += ["---", "", "## 📈 本周总榜 Top 5", ""]
        for i, it in enumerate(top_items[:5], 1):
            url = f"https://github.com/{it['name']}"
            desc_zh = translate_zh(it["desc"]) if it["desc"] else ""
            lines.append(f"{i}. [{it['name']}]({url}) ⭐{it['stars']:,} — {desc_zh[:60]}")
        lines.append("")
    lines.append("> 完整榜单见 GitHub Trending：https://github.com/trending?since=weekly")
    return "\n".join(lines)


def push_wechat(title: str, desp: str) -> bool:
    if not SENDKEY:
        print("[SKIP] 未配置 SERVERCHAN_SENDKEY，跳过推送（仅生成报告）")
        return False
    data = urllib.parse.urlencode({"title": title, "desp": desp}).encode()
    url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA["User-Agent"]})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8", "ignore"))
    ok = result.get("code") == 0
    if ok:
        print("[PUSH] 微信推送成功")
    else:
        print(f"[PUSH] 推送失败: {json.dumps(result, ensure_ascii=False)}")
    return ok


def main():
    cn_tz = timezone(timedelta(hours=8))
    now = datetime.now(cn_tz)
    start = (now - timedelta(days=6)).strftime("%m/%d")
    end = now.strftime("%m/%d")
    week_range = f"{start}-{end}"

    try:
        html = fetch("https://github.com/trending?since=weekly")
        items = parse_trending(html)
    except Exception as e:
        print(f"[ERROR] 抓取失败: {e}")
        sys.exit(1)

    if not items:
        print("[ERROR] 未解析到任何项目")
        sys.exit(1)

    ai_items = [it for it in items if is_ai(it)]
    top_items = sorted(items, key=lambda x: x["stars"], reverse=True)
    md = build_markdown(ai_items, top_items, week_range)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[OK] 报告已生成: {REPORT_FILE}（AI 相关 {len(ai_items)} 条 / 总 {len(items)} 条）")

    title = f"🤖 AI开源周报 {week_range}"
    push_wechat(title, md)


if __name__ == "__main__":
    main()
