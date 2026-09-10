#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每周 AI 开源项目精选推送（GitHub Actions 定时运行）

数据源：GitHub Trending (weekly)
推送：Server酱（微信「方糖」服务号）
存档：报告写入 reports/ 目录并提交回仓库，推送里只带永久链接

为什么这么改：方糖推送内容免费版只保留 1 天、会员 3–7 天，
过期后正文就查不到了。所以正文不放在方糖，改成存进本仓库，
推送只给「在线阅读」和「下载」两个永久链接。
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

# 仓库信息（Actions 里由 GITHUB_REPOSITORY / GITHUB_REF_NAME 自动注入，本地跑用默认值）
REPO_SLUG = (os.environ.get("GITHUB_REPOSITORY") or "").strip() or "cxccc1216/weekly-ai-open-source-push"
BRANCH = (os.environ.get("GITHUB_REF_NAME") or "").strip() or "main"

REPORT_DIR = "reports"
INDEX_FILE = os.path.join(REPORT_DIR, "INDEX.md")

# 翻译缓存（避免同一项目重复请求）
_TRANSLATE_CACHE = {}


def translate_zh(text: str) -> str:
    """调用 MyMemory 免费接口把英文描述翻译为中文；失败时回退英文原文

    MyMemory 是免费公开翻译服务（api.mymemory.translated.net），无 key、不限 datacenter IP，
    比 Google Translate gtx 适合 GitHub Actions 云端使用。"""
    if not text:
        return ""
    if text in _TRANSLATE_CACHE:
        return _TRANSLATE_CACHE[text]
    try:
        q = urllib.parse.quote(text[:500])
        url = f"https://api.mymemory.translated.net/get?q={q}&langpair=en|zh-CN&de=workbuddy@users.noreply.github.com"
        req = urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"]})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", "ignore"))
        translated = data.get("responseData", {}).get("translatedText", "").strip()
        status = data.get("responseStatus")
        if status == 200 and translated and translated.lower() != text.lower():
            _TRANSLATE_CACHE[text] = translated
            return translated
        print(f"[WARN] 翻译未返回有效结果: status={status} text={translated[:60]!r}")
        _TRANSLATE_CACHE[text] = text
        return text
    except Exception as e:
        print(f"[WARN] 翻译失败 ({type(e).__name__}: {e})，回退原文")
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


def build_markdown(ai_items: list, top_items: list, week_range: str, blob_url: str, raw_url: str) -> str:
    lines = [
        f"# 🤖 本周 AI 开源项目精选（{week_range}）",
        "",
        "## 📄 永久存档",
        "",
        f"- **在线阅读（含下载按钮）**：{blob_url}",
        f"- **纯文本直链（手机可直接保存）**：{raw_url}",
        "",
        "> 方糖推送正文只保留 1 天（会员 3–7 天），之后请从上面链接查看，永久有效。",
        "",
        "---",
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


def write_report(report_path: str, content: str) -> None:
    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)


def update_index(week_date: str, report_filename: str, ai_items: list) -> None:
    """维护 reports/INDEX.md 总目录：最新一周在最上面，重复日期先覆盖"""
    os.makedirs(REPORT_DIR, exist_ok=True)

    blob_url = f"https://github.com/{REPO_SLUG}/blob/{BRANCH}/{REPORT_DIR}/{report_filename}"
    raw_url = f"https://raw.githubusercontent.com/{REPO_SLUG}/{BRANCH}/{REPORT_DIR}/{report_filename}"
    names = ", ".join(it["name"] for it in ai_items[:12])
    row = f"| {week_date} | [查看]({blob_url}) · [下载]({raw_url}) | {len(ai_items)} | {names} |"

    rows = []
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line.startswith("|"):
                    continue
                if line.startswith("| 周次") or set(line) <= set("|-: "):
                    continue
                if line.startswith(f"| {week_date} "):
                    continue
                rows.append(line)

    rows.insert(0, row)

    lines = [
        "# 📚 AI 开源周报总目录",
        "",
        f"共 {len(rows)} 期 ｜ 仓库：https://github.com/{REPO_SLUG}",
        "",
        "| 周次 | 报告 | AI 项目数 | 本周收录项目 |",
        "|---|---|---|---|",
    ] + rows + [
        "",
        "> 每期报告永久保存在本目录，方糖推送过期后仍可从这里查阅与下载。",
        "",
    ]
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] 总目录已更新: {INDEX_FILE}（共 {len(rows)} 期）")


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
    week_date = now.strftime("%Y-%m-%d")
    start = (now - timedelta(days=6)).strftime("%m/%d")
    end = now.strftime("%m/%d")
    week_range = f"{start}-{end}"

    report_filename = f"weekly-ai-{week_date}.md"
    # URL 里必须用正斜杠（Windows 的 os.path.join 会给出反斜杠，链接会失效）
    report_rel = f"{REPORT_DIR}/{report_filename}"
    report_path = os.path.join(REPORT_DIR, report_filename)
    blob_url = f"https://github.com/{REPO_SLUG}/blob/{BRANCH}/{report_rel}"
    raw_url = f"https://raw.githubusercontent.com/{REPO_SLUG}/{BRANCH}/{report_rel}"

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
    md = build_markdown(ai_items, top_items, week_range, blob_url, raw_url)

    write_report(report_path, md)
    print(f"[OK] 报告已生成: {report_path}（AI 相关 {len(ai_items)} 条 / 总 {len(items)} 条）")

    update_index(week_date, report_filename, ai_items)

    title = f"🤖 AI开源周报 {week_range}"
    push_wechat(title, md)


if __name__ == "__main__":
    main()
