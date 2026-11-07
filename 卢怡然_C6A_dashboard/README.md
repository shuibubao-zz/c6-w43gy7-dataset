# Elite20 提交数据仪表盘（C6A）

纯前端、零依赖、离线可用：把散落的提交变成可浏览 / 可筛选 / 可追踪的结构化看板。

## 直接运行
```bash
# 方式 A：起一个本地静态服务（推荐，文件链接可点开）
cd 卢怡然_C6A_dashboard
python -m http.server 8080
# 浏览器打开 http://127.0.0.1:8080/index.html

# 方式 B：直接双击 index.html（file:// 也能跑，文件链接需与数据目录同包）
```

## 功能
- 📊 总览：5 张统计卡 + 状态分布甜甜圈 + 各挑战完整率条形图 + 学生×挑战热力矩阵 + 最近提交
- 👤 按学生：点击学生查看其全部提交（状态/齐备率/缺失项/文件链接/评审备注）
- 🎯 按挑战：点击挑战查看全体完成情况
- 🔍 筛选/排序：按名称、状态、齐备率筛选排序
- 🔗 文件链接：点击文件名打开对应提交物（相对路径指向 `../卢怡然_C6A_data/submissions/`）
- 📌 缺失高亮：缺必填项 / 评审未过 的条目显式标红

## 数据从哪来（口径）
数据由 `卢怡然_C6A_data/scan_submissions.py` 对 `submissions/` 目录真实磁盘扫描得到，
再经 `build_site_data.py` 转成 `data.js` 内嵌。要刷新数据：
```bash
cd 卢怡然_C6A_data
python gen_sample_submissions.py   # 仅首次/换样本时需要
python scan_submissions.py
python build_report.py             # 生成 Excel
cd ../卢怡然_C6A_dashboard
python build_site_data.py          # 重新生成 data.js
```
**权威口径**：卢怡然记录=本会话真实工作；其余 19 名为确定性合成样本（seed=42），仅用于演示管线。详见 Excel「口径说明」Sheet 与各文档。

## 部署（Level 4）
```bash
bash deploy.sh 你的GitHub用户名        # 推到 GitHub，再在 Settings→Pages 开 main/root
# 或：把本文件夹拖到 Netlify / 运行 npx vercel
```
