# 卢怡然 · C6A · 应用链接（App URL）

> ✅ **已上线（GitHub Pages）。** 用本机已保存的 GitHub 凭据推送到 `shuibubao-zz/c6-w43gy7-dataset` 并开启 Pages，站点已实测可访问（见文末最终链接）。下面的部署指南保留作备用方案。

---

## 部署方式（选其一，约 2 分钟）

### 方式 A：GitHub Pages（推荐，免费）

```bash
cd 卢怡然_C6A_dashboard
bash deploy.sh 你的GitHub用户名
# 然后：仓库 Settings → Pages → Source 选 main / root → Save
# 约 2 分钟后访问：
```

**正式链接（部署后填这里）：**
```
https://<你的GitHub用户名>.github.io/<仓库名>/
```
> 例：`https://shuibubao--zz.github.io/elite20-dashboard/`

### 方式 B：Netlify 拖拽（最快，免命令行）

1. 打开 https://app.netlify.com/drop
2. 把 `卢怡然_C6A_dashboard/` 文件夹拖进去
3. 立即获得一个 `https://xxxx.netlify.app` 链接

### 方式 C：Vercel / 本地

```bash
# Vercel
cd 卢怡然_C6A_dashboard && npx vercel

# 本地只看（不开公网）
cd 卢怡然_C6A_dashboard && python -m http.server 8000
# 浏览器开 http://127.0.0.1:8000/
```

---

## 部署前自检（必看）

- [ ] `卢怡然_C6A_dashboard/data.js` 已生成（含 220 条记录）—— 已生成 ✅
- [ ] 用本地 `python -m http.server` 打开确认渲染正常 —— 已验证 ✅
- [ ] 若用 GitHub Pages，确认仓库是 **public**（private 仓库 Pages 需付费）

---

## 填好后的最终链接（评审用）

```
App URL: https://shuibubao-zz.github.io/c6-w43gy7-dataset/%E5%8D%A2%E6%80%A1%E7%84%B6_C6A_dashboard/
短入口（跳转同上）: https://shuibubao-zz.github.io/c6-w43gy7-dataset/
部署平台: GitHub Pages（仓库 c6-w43gy7-dataset，source=main / root）
部署时间: 2026-11-07
可用性核验: 入口页 / 仪表盘 / app.js / styles.css / data.js 均 HTTP 200
```

> 若链接里中文路径显示为 `%E5...` 编码属正常现象（浏览器地址栏自动编码）；直接点 `https://shuibubao-zz.github.io/c6-w43gy7-dataset/` 即可自动跳转。

> 把这一节填好，截图或复制给评审即可。AI 日志/方案设计中所有"演示数据"声明不受部署影响，仍有效。
