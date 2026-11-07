#!/usr/bin/env bash
# 一键部署 C6A 仪表盘到 GitHub Pages（仅 Git 提交 + 推送；Pages 开关在网页端点一下）
# 用法：bash deploy.sh 你的GitHub用户名 [仓库名]
set -e
USERNAME="${1:?用法: bash deploy.sh 你的GitHub用户名 [仓库名]}"
REPO="${2:-elite20-submission-dashboard}"

cd "$(dirname "$0")"
git init -b main 2>/dev/null || git checkout -q -B main
git add -A
git commit -q -m "feat: Elite20 提交数据仪表盘 C6A（纯前端，零依赖）" || echo "（无新改动，跳过提交）"
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/${USERNAME}/${REPO}.git"
git push -u origin main

echo ""
echo "✅ 已推送到 https://github.com/${USERNAME}/${REPO}"
echo "下一步：浏览器打开该仓库 → Settings → Pages → Source 选 main / root → Save"
echo "约 2 分钟后访问：https://${USERNAME}.github.io/${REPO}/"
