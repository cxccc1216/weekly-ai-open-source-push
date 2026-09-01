# 🤖 每周 AI 开源项目微信推送（云端定时）

**不用打开电脑，每周日自动把 GitHub 本周最受欢迎的 AI 开源项目推送到你微信。**

## 工作原理

```
GitHub Actions（云端免费定时器）
   ↓ 每周日 20:35（北京时间）
抓取 GitHub Trending 每周榜
   ↓
筛选 AI 相关项目，生成摘要
   ↓ 调用 Server酱 API
微信「方糖」服务号收到推送
```

- 定时任务跑在 **GitHub 云端服务器**，与你的电脑无关，电脑关机照常推送
- 免费：GitHub Actions 免费额度 + Server酱免费版（每天 5 条，每周 1 条绰绰有余）

## 文件结构

```
weekly-push/
├── .github/workflows/weekly-push.yml   # 定时任务（每周日 20:35）
└── scripts/weekly_push.py              # 抓取 + 筛选 + 推送脚本
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

几秒后微信「方糖」服务号应收到测试推送；失败可在该运行日志里查看原因。

## 验证自动推送

- 下次自动运行：**每周日 20:35（北京时间）**
- 每次运行都会在 Actions 页面生成一份 `weekly-report.md` 报告（可下载查看原始内容）
