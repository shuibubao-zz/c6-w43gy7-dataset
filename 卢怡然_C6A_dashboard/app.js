/* app.js —— 纯前端仪表盘逻辑（零依赖，离线可用） */
(function () {
  "use strict";
  var D = window.DASHBOARD_DATA;
  if (!D) { document.body.innerHTML = "<p style='padding:20px'>未找到 data.js，请先运行 build_site_data.py</p>"; return; }
  var S = D.stats;
  var records = D.records;
  var students = D.students;
  var challenges = D.challenges;
  var chTitles = D.ch_titles;

  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function sym(st) { return st === "complete" ? "✅" : st === "partial" ? "⚠️" : "❌"; }
  function cellClass(st) { return st === "complete" ? "cell-c" : st === "partial" ? "cell-p" : "cell-m"; }
  function findRec(stu, ch) {
    for (var i = 0; i < records.length; i++)
      if (records[i].student === stu && records[i].challenge === ch) return records[i];
    return null;
  }
  function fileHref(stu, file) {
    return "../卢怡然_C6A_data/submissions/" + encodeURIComponent(stu) + "/" + encodeURIComponent(file);
  }

  /* ---------- 顶部卡片 ---------- */
  function renderCards() {
    var c = $("cards");
    var ailogRate = Math.round(S.ailog_missing_rate * 100);
    var avg = Math.round(S.avg_completeness * 100);
    var items = [
      ["学生总数", students.length, "人"],
      ["挑战总数", challenges.length, "个"],
      ["实际提交", S.submission_count, "条"],
      ["平均齐备率", avg, "%"],
      ["缺AI日志占比", ailogRate, "%"]
    ];
    c.innerHTML = items.map(function (it) {
      return '<div class="card"><div class="k">' + it[0] + '</div><div class="v">' + it[1] +
        ' <small>' + it[2] + '</small></div></div>';
    }).join("");
  }

  /* ---------- 口径徽章 ---------- */
  function renderBadge() {
    $("caliberBadge").textContent =
      "数据口径：卢怡然(真实记录) + 19 名合成样本 · " + S.record_count + " 条矩阵记录 · 生成于 " +
      (D.generated_at || "").slice(0, 10);
  }

  /* ---------- 甜甜圈：全量记录状态分布（含未提交，与矩阵一致） ---------- */
  function drawDonut() {
    var cv = $("donut"), ctx = cv.getContext("2d");
    var cnt = { complete: 0, partial: 0, missing: 0 };
    records.forEach(function (r) { cnt[r.status]++; });
    var data = [
      { v: cnt.complete, c: "#2e9e5b", t: "完整" },
      { v: cnt.partial, c: "#c9901b", t: "部分" },
      { v: cnt.missing, c: "#d64545", t: "缺失/未提交" }
    ];
    var total = data.reduce(function (a, b) { return a + b.v; }, 0) || 1;
    var r = 80, cx = 110, cy = 110, start = -Math.PI / 2;
    ctx.clearRect(0, 0, cv.width, cv.height);
    data.forEach(function (d) {
      var ang = d.v / total * Math.PI * 2;
      ctx.beginPath(); ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, r, start, start + ang); ctx.closePath();
      ctx.fillStyle = d.c; ctx.fill(); start += ang;
    });
    ctx.beginPath(); ctx.arc(cx, cy, 42, 0, Math.PI * 2); ctx.fillStyle = "#fff"; ctx.fill();
    ctx.fillStyle = "#1f2733"; ctx.font = "bold 20px sans-serif"; ctx.textAlign = "center";
    ctx.fillText(total, cx, cy - 4);
    ctx.fillStyle = "#6b7785"; ctx.font = "12px sans-serif";
    ctx.fillText("提交条数", cx, cy + 16);
    // 图例
    var lx = 210, ly = 50;
    data.forEach(function (d) {
      ctx.fillStyle = d.c; ctx.fillRect(lx, ly - 10, 14, 14);
      ctx.fillStyle = "#1f2733"; ctx.textAlign = "left"; ctx.font = "13px sans-serif";
      ctx.fillText(d.t + " " + d.v, lx + 20, ly + 2); ly += 28;
    });
  }

  /* ---------- 横向条形：各挑战完整率 ---------- */
  function drawBars() {
    var cv = $("bars"), ctx = cv.getContext("2d");
    var items = challenges.map(function (ch) {
      return { ch: ch, rate: (S.ch_stats[ch] ? S.ch_stats[ch].complete_rate : 0) };
    }).sort(function (a, b) { return b.rate - a.rate; });
    ctx.clearRect(0, 0, cv.width, cv.height);
    var x0 = 46, y0 = 14, bw = 300, bh = 16, gap = 18;
    ctx.font = "12px sans-serif"; ctx.textAlign = "right"; ctx.fillStyle = "#1f2733";
    items.forEach(function (it, i) {
      var y = y0 + i * (bh + gap);
      ctx.fillText(it.ch, x0 - 6, y + bh - 3);
      ctx.fillStyle = "#e3e8ef"; ctx.fillRect(x0, y, bw, bh);
      ctx.fillStyle = it.rate >= 0.5 ? "#2e9e5b" : it.rate >= 0.25 ? "#c9901b" : "#d64545";
      ctx.fillRect(x0, y, bw * it.rate, bh);
      ctx.fillStyle = "#1f2733"; ctx.textAlign = "left";
      ctx.fillText(Math.round(it.rate * 100) + "%", x0 + bw + 6, y + bh - 3);
    });
  }

  /* ---------- 热力矩阵 ---------- */
  function renderMatrix() {
    var t = $("matrix");
    var head = "<tr><th>学生</th>" + challenges.map(function (ch) {
      return "<th>" + ch + "</th>"; }).join("") + "</tr>";
    var rows = students.map(function (stu) {
      var isReal = stu === "卢怡然";
      var cells = challenges.map(function (ch) {
        var r = findRec(stu, ch);
        if (!r || r.status === "missing") return '<td class="cell-m">❌</td>';
        var pct = Math.round(r.completeness * 100);
        return '<td class="' + cellClass(r.status) + '">' + sym(r.status) + pct + "%</td>";
      }).join("");
      return '<tr><td class="name' + (isReal ? ' real' : '') + '">' + esc(stu) +
        (isReal ? '<span class="tag-real">真实</span>' : '') + "</td>" + cells + "</tr>";
    }).join("");
    t.innerHTML = head + rows;
  }

  /* ---------- 时间线 ---------- */
  function renderTimeline() {
    var ul = $("timeline");
    ul.innerHTML = S.timeline.map(function (r) {
      var dt = (r.submitted_at || "").replace("T", " ").slice(0, 16);
      return "<li><span class='dt'>" + dt + "</span> ｜ <b>" + esc(r.student) +
        "</b> 提交 <b>" + r.challenge + "</b> " + sym(r.status) + " 齐备 " +
        Math.round(r.completeness * 100) + "%</li>";
    }).join("");
  }

  /* ---------- 学生列表（含筛选/排序/搜索） ---------- */
  function getFilters() {
    return {
      q: ($("search").value || "").trim().toLowerCase(),
      status: $("statusFilter").value,
      sort: $("sortBy").value
    };
  }
  function renderStudentList() {
    var f = getFilters();
    var list = students.filter(function (s) {
      if (f.q && s.toLowerCase().indexOf(f.q) < 0) return false;
      if (f.status) {
        var recs = records.filter(function (r) { return r.student === s && r.status === f.status; });
        if (!recs.length) return false;
      }
      return true;
    });
    if (f.sort === "comp") list.sort(function (a, b) {
      return (S.stu_stats[b] ? S.stu_stats[b].avg_completeness : 0) - (S.stu_stats[a] ? S.stu_stats[a].avg_completeness : 0); });
    else if (f.sort === "complete") list.sort(function (a, b) {
      return (S.stu_stats[b] ? S.stu_stats[b].complete_rate : 0) - (S.stu_stats[a] ? S.stu_stats[a].complete_rate : 0); });

    var html = list.map(function (s) {
      var st = S.stu_stats[s] || { n: 0, complete: 0, complete_rate: 0, avg_completeness: 0 };
      var real = s === "卢怡然" ? '<span class="tag-real">真实</span>' : "";
      return '<div class="tile" data-stu="' + esc(s) + '"><div class="t">' + esc(s) + real +
        '</div><div class="m">提交 ' + st.n + ' ｜ 完整率 ' + Math.round(st.complete_rate * 100) +
        '% ｜ 平均齐备 ' + Math.round(st.avg_completeness * 100) + '%</div></div>';
    }).join("");
    $("stuList").innerHTML = html;
    $("stuDetail").style.display = "none";
    $("stuList").style.display = "grid";
    Array.prototype.forEach.call(document.querySelectorAll(".tile[data-stu]"), function (el) {
      el.onclick = function () { renderStudentDetail(el.getAttribute("data-stu")); };
    });
  }

  function renderStudentDetail(stu) {
    $("stuList").style.display = "none";
    var box = $("stuDetail");
    box.style.display = "block";
    var recs = records.filter(function (r) { return r.student === stu; })
      .sort(function (a, b) { return challenges.indexOf(a.challenge) - challenges.indexOf(b.challenge); });
    var real = stu === "卢怡然" ? ' <span class="tag-real">真实记录</span>' : "";
    var body = recs.map(function (r) {
      if (r.status === "missing") {
        return '<div class="detail" style="margin-bottom:10px;padding:12px"><b>' + r.challenge +
          " · " + esc(r.title) + '</b> <span class="pill m">❌ 未提交</span></div>';
      }
      var pct = Math.round(r.completeness * 100);
      var files = (r.present_files || []).map(function (f) {
        return '<li><a href="' + fileHref(stu, f) + '" target="_blank">' + esc(f) + "</a></li>";
      }).join("");
      var miss = (r.missing || []).map(function (m) { return '<li class="miss">' + esc(m) + "</li>"; }).join("");
      var review = r.review_passed
        ? '<span class="pill c">评审通过</span>'
        : '<span class="pill p">评审需补</span>';
      return '<div class="detail" style="margin-bottom:10px;padding:12px">' +
        "<b>" + r.challenge + " · " + esc(r.title) + "</b> " +
        '<span class="pill ' + (r.status === "complete" ? "c" : "p") + '">' + sym(r.status) +
        (r.status === "complete" ? "完整" : "部分") + "</span> " + review +
        '<div class="barline"><i style="width:' + pct + '%"></i></div>' +
        '<div class="note">齐备率 ' + pct + "% ｜ 已交 " + r.required_present + "/" + r.required_total +
        " ｜ " + (r.submitted_at || "").slice(0, 16).replace("T", " ") + "</div>" +
        (miss ? '<div class="note" style="color:#d64545">缺失必填：' + esc(r.missing.join("、")) + "</div>" : "") +
        (files ? '<ul class="files">' + files + "</ul>" : "") +
        '<div class="note">评审备注：' + esc(r.review_note) + "</div>" +
        "</div>";
    }).join("");
    box.innerHTML = '<span class="back" onclick="renderStudentList()">← 返回学生列表</span>' +
      "<h2>" + esc(stu) + " 的提交" + real + "</h2>" + body;
  }

  /* ---------- 挑战列表 ---------- */
  function renderChallengeList() {
    var f = getFilters();
    var list = challenges.filter(function (ch) {
      if (f.q && ch.toLowerCase().indexOf(f.q) < 0 && (chTitles[ch] || "").toLowerCase().indexOf(f.q) < 0) return false;
      if (f.status) {
        var recs = records.filter(function (r) { return r.challenge === ch && r.status === f.status; });
        if (!recs.length) return false;
      }
      return true;
    });
    var html = list.map(function (ch) {
      var st = S.ch_stats[ch] || { n: 0, complete_rate: 0, avg_completeness: 0 };
      return '<div class="tile" data-ch="' + ch + '"><div class="t">' + ch + "</div>" +
        '<div class="m">' + esc(chTitles[ch]) + " ｜ 提交 " + st.n + " ｜ 完整率 " +
        Math.round(st.complete_rate * 100) + "%</div></div>";
    }).join("");
    $("chList").innerHTML = html;
    $("chDetail").style.display = "none";
    $("chList").style.display = "grid";
    Array.prototype.forEach.call(document.querySelectorAll(".tile[data-ch]"), function (el) {
      el.onclick = function () { renderChallengeDetail(el.getAttribute("data-ch")); };
    });
  }

  function renderChallengeDetail(ch) {
    $("chList").style.display = "none";
    var box = $("chDetail");
    box.style.display = "block";
    var recs = records.filter(function (r) { return r.challenge === ch && r.status !== "missing"; })
      .sort(function (a, b) { return b.completeness - a.completeness; });
    var rows = recs.map(function (r) {
      var pct = Math.round(r.completeness * 100);
      var real = r.student === "卢怡然" ? ' <span class="tag-real">真实</span>' : "";
      return "<tr><td class='name" + (r.student === "卢怡然" ? " real" : "") + "'>" +
        "<a href='javascript:void(0)' onclick=\"renderStudentDetail('" + esc(r.student) + "')\">" +
        esc(r.student) + "</a>" + real + "</td><td class='" + cellClass(r.status) + "'>" +
        sym(r.status) + pct + "%</td><td>" + r.required_present + "/" + r.required_total +
        "</td><td>" + (r.missing.join("、") || "—") + "</td><td>" +
        (r.submitted_at || "").slice(0, 16).replace("T", " ") + "</td></tr>";
    }).join("");
    box.innerHTML = '<span class="back" onclick="renderChallengeList()">← 返回挑战列表</span>' +
      "<h2>" + ch + " · " + esc(chTitles[ch]) + "</h2>" +
      '<table><tr><th>学生</th><th>状态</th><th>已交</th><th>缺失必填</th><th>提交时间</th></tr>' +
      rows + "</table>";
  }

  /* ---------- 页脚口径声明 ---------- */
  function renderFoot() {
    $("foot").innerHTML =
      "口径与权威源：本仪表盘数据由 scan_submissions.py 对 submissions/ 目录真实磁盘扫描得到，" +
      "识别规则为唯一权威口径（文件名匹配 &lt;学生&gt;_&lt;挑战&gt;_&lt;后缀&gt;）。" +
      "卢怡然记录基于本会话真实工作；其余 19 名为确定性合成样本（seed=42），仅用于演示管线，不代表真实同学。" +
      "completeness = 必填已交/必填总数；level_achieved 为文件齐备度近似，非质量评级；评审列为 C4A 文件名级初筛。";
  }

  /* ---------- 绑定 ---------- */
  function bind() {
    Array.prototype.forEach.call(document.querySelectorAll(".tab"), function (t) {
      t.onclick = function () {
        document.querySelectorAll(".tab").forEach(function (x) { x.classList.remove("active"); });
        document.querySelectorAll(".panel").forEach(function (x) { x.classList.remove("active"); });
        t.classList.add("active");
        $("panel-" + t.getAttribute("data-tab")).classList.add("active");
      };
    });
    ["search", "statusFilter", "sortBy"].forEach(function (id) {
      $(id).addEventListener("input", function () {
        renderStudentList(); renderChallengeList();
      });
      $(id).addEventListener("change", function () {
        renderStudentList(); renderChallengeList();
      });
    });
    window.renderStudentList = renderStudentList;
    window.renderChallengeList = renderChallengeList;
    window.renderStudentDetail = renderStudentDetail;
  }

  /* ---------- init ---------- */
  renderCards();
  renderBadge();
  drawDonut();
  drawBars();
  renderMatrix();
  renderTimeline();
  renderStudentList();
  renderChallengeList();
  renderFoot();
  bind();

  /* ---------- deep-link：支持 #stu=姓名 / #ch=编号 直达详情 ---------- */
  function handleHash() {
    var h = (location.hash || "").replace(/^#/, "");
    var m = h.match(/(stu|ch)=([^&]+)/);
    if (!m) return;
    if (m[1] === "stu") {
      document.querySelector('.tab[data-tab="students"]').click();
      renderStudentDetail(decodeURIComponent(m[2]));
    } else if (m[1] === "ch") {
      document.querySelector('.tab[data-tab="challenges"]').click();
      renderChallengeDetail(decodeURIComponent(m[2]));
    }
  }
  window.addEventListener("hashchange", handleHash);
  handleHash();
})();
