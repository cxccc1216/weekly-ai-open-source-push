# 🤖 每周 AI 开源项目微信推送（云端定时 + 永久存档）

**不用打开电脑，每周日自动把 GitHub 本周最受欢迎的 AI 开源项目推送到你微信，报告永久存档、随时可下载可搜索。**

## 工作原理

```
GitHub Actions（云端免费定时器）
   ↓ 每周日 20:35（北京时间）
抓取 GitHub Trending 每周榜
   ↓
筛选 AI 相关项目，生成摘要
   ↓
① 报告写入 reports/ 并提交回本仓库（永久存档）
② 调用 Server酱 API，推送「摘要 + 两个永久链接」到微信
```

- 定时任务跑在 **GitHub 云端服务器**，与你的电脑无关，电脑关机照常推送
- 免费：GitHub Actions 免费额度 + Server酱免费版（每天 5 条，每周 1 条绰绰有余）

## 为什么报告要存回仓库

方糖（Server酱）的**推送内容保留时间很短：免费会员只有 1 天，订阅会员 3–7 天**。
也就是说，如果正文只存在方糖服务器上，过一两天点开就是空的。

所以改成：**正文存进本仓库（永久），推送只带链接**。

- 在线阅读（带 Download 按钮）：`reports/weekly-ai-YYYY-MM-DD.md`
- 纯文本直链（手机可直接保存）：`raw.githubusercontent.com/...`

两个链接都是永久地址，方糖过期也不影响。

## 文件结构

```
weekly-push/
├── .github/workflows/weekly-push.yml   # 定时任务（每周日 20:35）
├── scripts/weekly_push.py              # 抓取 + 筛选 + 生成报告 + 推送
└── reports/                            # 每周报告存档（由 Action 自动生成提交）
    ├── INDEX.md                        # 总目录（按周列出，方便检索）
    └── weekly-ai-YYYY-MM-DD.md         # 每周报告
```

## 首次配置（一次性，5 分钟）

### 1. 获取 Server酱 SendKey（已完成则跳过）

1. 手机微信搜索关注「**方糖**」服务号
2. 电脑浏览器打开 https://sct.ftqq.com ，用 GitHub 账号登录（或微信扫码）
3. 进入「SendKey」页面 https://sct.ftqq.com/sendkey ，复制 `SCT...` 开头的 Key

### 2. 配置 GitHub Secret

在仓库页面打开：**Settings → Secrets and variables → Actions → New repository secret**

| 字段 | 值 |
|---|---|
| Name | `SERVERCHAN_SENDKEY` |
| Secret | 你复制的 SendKey（SCT...） |

### 3. 手动测试一次

仓库页面 → **Actions** → 左侧 `Weekly AI Open Source Push` → **Run workflow** → 绿色按钮

几秒后微信「方糖」服务号应收到推送；失败可在该运行日志里查看原因。

## 验证自动推送

- 下次自动运行：**每周日 20:35（北京时间）**
- 运行后仓库 `reports/` 目录会新增一份报告，并更新 `reports/INDEX.md` 总目录
- 微信推送里点「在线阅读」即为永久地址，不会过期

## 注意

- `permissions: contents: write` 是回写存档所必需的
- Actions 里的 artifact 只用于排查问题（30 天自动清理），**不要当作长期存档**
- 仓库为 Public，报告内容均为公开的开源项目信息，不含隐私数据
