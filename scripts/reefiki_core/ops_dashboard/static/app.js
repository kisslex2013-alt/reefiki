/* REEFIKI Ops Dashboard v2 — app.js
   Pure ES2020. No frameworks, no bundler. Renders via <template> + cloneNode +
   textContent (never innerHTML for untrusted data). Diff-friendly: rows are
   keyed by project name, never re-created when the data is the same. */

(() => {
  "use strict";

  // ---------- state ----------
  const state = {
    snapshot: null,
    selected: null,            // project name | null
    tab: "tab.overview",
    language: "en",
    theme: "dark",
    intervalMs: 0,
    i18n: null,
    timer: null,
  };

  const els = {
    body: document.body,
    kpi: document.getElementById("kpi"),
    reefiki: document.getElementById("reefiki-control"),
    currentWork: document.getElementById("current-work"),
    activityList: document.getElementById("activity-list"),
    activityCount: document.getElementById("activity-count"),
    projectsTbody: document.getElementById("projects-tbody"),
    projectsCount: document.getElementById("projects-count"),
    inspectorBody: document.getElementById("inspector-body"),
    inspectorClose: document.getElementById("inspector-close"),
    lastRefresh: document.getElementById("last-refresh"),
    refresh: document.getElementById("refresh"),
    lang: document.getElementById("lang"),
    theme: document.getElementById("theme"),
    interval: document.getElementById("interval"),
  };

  // ---------- i18n ----------
  function t(key) {
    const dict = (state.i18n && state.i18n[state.language]) || {};
    return dict[key] || (state.i18n && state.i18n.en && state.i18n.en[key]) || key;
  }

  function applyLanguage() {
    document.documentElement.lang = state.language;
    els.lang.value = state.language;
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      node.textContent = t(node.dataset.i18n);
    });
    if (state.snapshot) render(state.snapshot);
  }

  // ---------- time ----------
  function relativeTime(iso) {
    if (!iso) return "—";
    const then = new Date(iso);
    if (Number.isNaN(then.getTime())) return "—";
    const now = Date.now();
    const sec = Math.max(0, Math.round((now - then.getTime()) / 1000));
    if (sec < 60) return t("ago.now");
    const min = Math.round(sec / 60);
    if (min < 60) return `${min} ${t("ago.minutes")}`;
    const hr = Math.round(min / 60);
    if (hr < 24) return `${hr} ${t("ago.hours")}`;
    const day = Math.round(hr / 24);
    return `${day} ${t("ago.days")}`;
  }

  // ---------- template helpers ----------
  function cloneTpl(id) {
    const tpl = document.getElementById(id);
    if (!tpl) throw new Error(`missing template #${id}`);
    return tpl.content.firstElementChild.cloneNode(true);
  }

  function fillFields(node, mapping) {
    for (const [selector, value] of Object.entries(mapping)) {
      const target = node.matches(selector) ? node : node.querySelector(selector);
      if (target) target.textContent = value == null || value === "" ? "—" : String(value);
    }
    return node;
  }

  // ---------- header / KPI ----------
  function renderKpi(kpi) {
    const items = [
      { label: t("kpi.total"), value: kpi.total },
      { label: t("kpi.clean"), value: kpi.clean, tone: kpi.dirty ? null : "ok" },
      { label: t("kpi.dirty"), value: kpi.dirty, tone: kpi.dirty ? "warn" : "ok" },
      { label: t("kpi.codex"), value: kpi.codex_branches, tone: kpi.codex_branches ? "accent" : null },
      { label: t("kpi.connected"), value: kpi.connected },
      { label: t("kpi.warnings"), value: kpi.warnings, tone: kpi.warnings ? "warn" : "ok" },
      { label: t("kpi.no_tests"), value: kpi.no_tests, tone: kpi.no_tests ? "warn" : null },
      { label: t("kpi.no_agents"), value: kpi.no_agents_md, tone: kpi.no_agents_md ? "warn" : null },
    ];
    const frag = document.createDocumentFragment();
    for (const item of items) {
      const node = cloneTpl("tpl-kpi-cell");
      fillFields(node, {
        '[data-field="label"]': item.label,
        '[data-field="value"]': item.value,
      });
      if (item.tone) {
        const v = node.querySelector('[data-field="value"]');
        v.classList.add(`tone-${item.tone}`);
      }
      frag.appendChild(node);
    }
    els.kpi.replaceChildren(frag);
  }

  // ---------- control plane: REEFIKI ----------
  function renderReefiki(control) {
    const activeTask = (control.active_tasks && control.active_tasks[0]) || null;
    const nextTask = (control.next_tasks && control.next_tasks[0]) || null;
    const node = cloneTpl("tpl-reefiki");
    fillFields(node, {
      '[data-field="phase"]': control.roadmap_phase || "—",
      '[data-field="sprint"]': control.current_sprint || "—",
      '[data-field="active-task"]': activeTask ? `${activeTask.id} ${activeTask.title}` : "—",
      '[data-field="next-task"]': nextTask ? `${nextTask.id} ${nextTask.title}` : "—",
      '[data-field="health"]': control.health_outcome || "unknown",
      '[data-field="t111"]': control.t111_status || "—",
      '[data-field="last-log"]': control.last_log_heading
        ? `${control.last_log_heading} (${control.last_log_iso || "—"})`
        : "—",
    });
    els.reefiki.replaceChildren(node);
  }

  // ---------- control plane: current work ----------
  function renderCurrentWork(items, selectedName) {
    els.currentWork.replaceChildren();
    if (!items.length) {
      const p = document.createElement("p");
      p.className = "muted";
      p.textContent = t("current-work-empty");
      els.currentWork.appendChild(p);
      return;
    }
    const frag = document.createDocumentFragment();
    for (const p of items) {
      const card = cloneTpl("tpl-work-card");
      const isSelected = selectedName === p.name;
      if (isSelected) card.classList.add("is-selected");
      const stateLabel = p.dirty
        ? `${t("state.dirty")} ${p.dirty_paths_count}`
        : t("state.clean");
      fillFields(card, {
        '[data-field="name"]': p.name,
        '[data-field="state"]': stateLabel,
        '[data-field="branch"]': p.branch || "—",
        '[data-field="ago"]': relativeTime(p.last_activity && p.last_activity.iso),
        '[data-field="detail"]':
          p.detected_stack && p.detected_stack.length
            ? p.detected_stack.join(", ")
            : (p.readiness || "—"),
      });
      const stateBadge = card.querySelector('[data-field="state"]');
      stateBadge.classList.add(p.dirty ? "tone-warn" : "tone-ok");
      card.addEventListener("click", () => select(p.name));
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(p.name); }
      });
      card.dataset.project = p.name;
      frag.appendChild(card);
    }
    els.currentWork.appendChild(frag);
  }

  // ---------- activity feed ----------
  function renderActivity(events) {
    els.activityCount.textContent = `${events.length}`;
    if (!events.length) {
      const li = document.createElement("li");
      li.className = "muted";
      li.textContent = t("activity-empty");
      els.activityList.replaceChildren(li);
      return;
    }
    const frag = document.createDocumentFragment();
    for (const e of events) {
      const node = cloneTpl("tpl-activity-item");
      const kindNode = node.querySelector('[data-field="kind"]');
      kindNode.textContent = e.kind;
      kindNode.classList.add(`tone-${e.kind}`);
      fillFields(node, {
        '[data-field="title"]': e.title || "—",
        '[data-field="project"]': e.project || "—",
        '[data-field="ago"]': relativeTime(e.iso),
      });
      node.addEventListener("click", () => {
        if (e.project && e.project !== "reefiki") select(e.project, "tab.logs");
      });
      frag.appendChild(node);
    }
    els.activityList.replaceChildren(frag);
  }

  // ---------- projects table ----------
  function renderProjects(projects, selectedName) {
    els.projectsCount.textContent = `${projects.length}`;
    const prev = new Map();
    for (const tr of els.projectsTbody.children) {
      if (tr.dataset && tr.dataset.name) prev.set(tr.dataset.name, tr);
    }
    const frag = document.createDocumentFragment();
    for (const p of projects) {
      let tr = prev.get(p.name);
      if (!tr) {
        tr = cloneTpl("tpl-project-row");
        tr.dataset.name = p.name;
      }
      const isSelected = selectedName === p.name;
      tr.classList.toggle("is-selected", isSelected);
      const mappingStatus = (p.reefiki_mapping && p.reefiki_mapping.mapping_status) || "missing";
      const stateCell = tr.querySelector('[data-field="state"]');
      const stateLabel = p.dirty
        ? `${t("state.dirty")} ${p.dirty_paths_count}`
        : t("state.clean");
      fillFields(tr, {
        '[data-field="name"]': p.name,
        '[data-field="branch"]': p.branch || "—",
        '[data-field="state"]': stateLabel,
        '[data-field="ahead-behind"]': `${p.ahead ?? "—"}/${p.behind ?? "—"}`,
        '[data-field="ago"]': relativeTime(p.last_activity && p.last_activity.iso),
        '[data-field="mapping"]': t(`mapping.${mappingStatus}`),
      });
      stateCell.classList.toggle("tone-warn", !!p.dirty);
      stateCell.classList.toggle("tone-ok", !p.dirty);
      tr.onclick = () => select(p.name);
      tr.onkeydown = (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(p.name); }
      };
      frag.appendChild(tr);
      prev.delete(p.name);
    }
    els.projectsTbody.replaceChildren(frag);
  }

  // ---------- inspector ----------
  function select(name, tab) {
    if (!name) {
      state.selected = null;
      state.tab = "tab.overview";
    } else {
      state.selected = state.selected === name && !tab ? null : name;
      if (tab) state.tab = tab;
    }
    els.inspectorClose.hidden = state.selected == null;
    if (state.snapshot) {
      renderProjects(state.snapshot.projects, state.selected);
      renderCurrentWork(state.snapshot.current_work, state.selected);
      renderInspector(state.snapshot.projects, state.selected);
    }
  }

  function renderInspector(projects, name) {
    if (!name) {
      els.inspectorBody.replaceChildren();
      const p = document.createElement("p");
      p.className = "muted";
      p.textContent = t("empty");
      els.inspectorBody.appendChild(p);
      return;
    }
    const p = projects.find((x) => x.name === name);
    if (!p) {
      els.inspectorBody.replaceChildren();
      return;
    }
    const tabs = ["tab.overview", "tab.files", "tab.readiness", "tab.logs", "tab.warnings"];
    const tabsRow = document.createElement("div");
    tabsRow.className = "tabs";
    for (const tabId of tabs) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = t(tabId);
      if (tabId === state.tab) btn.classList.add("is-active");
      btn.addEventListener("click", () => { state.tab = tabId; renderInspector(projects, name); });
      tabsRow.appendChild(btn);
    }

    const body = document.createElement("div");
    body.className = "kv-block";
    if (state.tab === "tab.overview") renderOverview(p, body);
    else if (state.tab === "tab.files") renderFiles(p, body);
    else if (state.tab === "tab.readiness") renderReadiness(p, body);
    else if (state.tab === "tab.logs") renderLogs(p, body);
    else if (state.tab === "tab.warnings") renderWarnings(p, body);

    els.inspectorBody.replaceChildren(tabsRow, body);
  }

  function appendKv(parent, label, value) {
    const row = cloneTpl("tpl-detail-kv");
    fillFields(row, {
      '[data-field="label"]': label,
      '[data-field="value"]': value == null || value === "" ? "—" : String(value),
    });
    parent.appendChild(row);
  }

  function renderOverview(p, body) {
    const la = p.last_activity || {};
    appendKv(body, t("label.branch"), p.branch);
    appendKv(body, t("label.head"), la.short_sha || "—");
    appendKv(body, t("label.dirty"), p.dirty ? `${t("state.dirty")} (${p.dirty_paths_count})` : t("state.clean"));
    appendKv(body, t("label.ahead-behind"), `${p.ahead ?? "—"}/${p.behind ?? "—"}`);
    appendKv(body, t("label.worktrees"), p.worktree_count);
    appendKv(body, t("label.stack"), (p.detected_stack || []).join(", ") || "—");
    appendKv(body, t("label.last"), la.heading ? `${la.short_sha || ""} ${la.subject || ""}` : "—");
    const mapping = p.reefiki_mapping || {};
    appendKv(body, t("label.mapping"),
      mapping.mapping_status === "connected" && mapping.project
        ? `${t("mapping.connected")}: ${mapping.project}`
        : t(`mapping.${mapping.mapping_status || "missing"}`));
    appendKv(body, t("label.readiness"), p.readiness);
  }

  function renderFiles(p, body) {
    const f = p.detected_files || {};
    appendKv(body, t("label.manifests"), (f.manifests || []).length);
    appendKv(body, t("label.ci"), (f.ci || []).length);
    appendKv(body, t("label.tests"), (f.test_markers || []).length);
    appendKv(body, t("label.agents"), (f.agent || []).length);
    appendKv(body, t("label.remotes"),
      (p.remotes || []).map((r) => r.name).join(", ") || "—");
    const list = document.createElement("details");
    list.className = "warn-list";
    const summary = document.createElement("summary");
    summary.textContent = `${t("label.manifests")} / ${t("label.ci")} / ${t("label.tests")} / ${t("label.agents")}`;
    list.appendChild(summary);
    const ul = document.createElement("ul");
    for (const group of [f.manifests || [], f.ci || [], f.test_markers || [], f.agent || []]) {
      for (const path of group) {
        const li = document.createElement("li");
        li.textContent = path;
        ul.appendChild(li);
      }
    }
    list.appendChild(ul);
    body.appendChild(list);
  }

  function renderReadiness(p, body) {
    const g = p.gates || {};
    appendKv(body, t("label.manifests"), g.package_manifest ? t("yes") : t("no"));
    appendKv(body, t("label.ci"), g.ci ? t("yes") : t("no"));
    appendKv(body, t("label.tests"), g.tests ? t("yes") : t("no"));
    appendKv(body, t("label.agents"), g.agents_md ? t("yes") : t("no"));
    appendKv(body, t("label.readiness"), p.readiness);
  }

  function renderLogs(p, body) {
    const entries = (p.latest_log_entries || []).slice().reverse();
    if (!entries.length) {
      const span = document.createElement("span");
      span.className = "muted";
      span.textContent = t("activity-empty");
      body.appendChild(span);
      return;
    }
    const ul = document.createElement("ul");
    ul.className = "log-list";
    for (const e of entries) {
      const li = cloneTpl("tpl-log-entry");
      fillFields(li, {
        '[data-field="heading"]': e.heading || "—",
        '[data-field="body"]': (e.lines && e.lines[0]) || "",
      });
      ul.appendChild(li);
    }
    body.appendChild(ul);
  }

  function renderWarnings(p, body) {
    const warnings = p.warnings || [];
    appendKv(body, t("label.warnings"), warnings.length);
    appendKv(body, t("label.dirty-paths"), p.dirty_paths_count);
    if (warnings.length) {
      const det = document.createElement("details");
      det.className = "warn-list";
      const summary = document.createElement("summary");
      summary.textContent = `${t("label.warnings")}: ${warnings.length}`;
      det.appendChild(summary);
      const ul = document.createElement("ul");
      for (const w of warnings) {
        const li = document.createElement("li");
        li.textContent = `${w.code}: ${w.message || ""}`;
        ul.appendChild(li);
      }
      det.appendChild(ul);
      body.appendChild(det);
    }
  }

  // ---------- top-level render ----------
  function render(snap) {
    state.snapshot = snap;
    renderKpi(snap.kpi || {});
    renderReefiki(snap.reefiki || {});
    renderCurrentWork(snap.current_work || [], state.selected);
    renderActivity(snap.activity_feed || []);
    renderProjects(snap.projects || [], state.selected);
    renderInspector(snap.projects || [], state.selected);
    const ts = snap.generated_at;
    els.lastRefresh.textContent = ts ? `${t("ago-relative-prefix")}${relativeTime(ts)}` : "—";
    els.lastRefresh.classList.remove("stale");
  }

  // ---------- fetch ----------
  async function fetchSnapshot() {
    try {
      const r = await fetch("/api/snapshot", { cache: "no-store" });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const snap = await r.json();
      render(snap);
    } catch (err) {
      els.lastRefresh.classList.add("stale");
      els.lastRefresh.textContent = `${t("fetch-failed")}: ${err.message || err}`;
    }
  }

  function startTimer(ms) {
    if (state.timer) clearInterval(state.timer);
    state.timer = null;
    if (ms > 0) state.timer = setInterval(fetchSnapshot, ms);
  }

  // ---------- init ----------
  async function init() {
    state.theme = (localStorage.getItem("reefiki.opsDashboard.theme") === "light") ? "light" : "dark";
    state.language = (localStorage.getItem("reefiki.opsDashboard.language") === "ru") ? "ru" : "en";
    state.intervalMs = Number(localStorage.getItem("reefiki.opsDashboard.interval") || 0);

    els.theme.value = state.theme;
    els.lang.value = state.language;
    els.interval.value = String(state.intervalMs);

    document.documentElement.dataset.theme = state.theme;

    els.theme.addEventListener("change", (e) => {
      state.theme = e.target.value;
      localStorage.setItem("reefiki.opsDashboard.theme", state.theme);
      document.documentElement.dataset.theme = state.theme;
    });
    els.lang.addEventListener("change", (e) => {
      state.language = e.target.value;
      localStorage.setItem("reefiki.opsDashboard.language", state.language);
      applyLanguage();
    });
    els.interval.addEventListener("change", (e) => {
      state.intervalMs = Number(e.target.value);
      localStorage.setItem("reefiki.opsDashboard.interval", String(state.intervalMs));
      startTimer(state.intervalMs);
    });
    els.refresh.addEventListener("click", fetchSnapshot);
    els.inspectorClose.addEventListener("click", () => select(null));
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && state.selected) select(null);
    });

    try {
      const r = await fetch("/static/i18n.json", { cache: "no-store" });
      state.i18n = await r.json();
    } catch {
      state.i18n = { en: {}, ru: {} };
    }
    applyLanguage();
    startTimer(state.intervalMs);
    fetchSnapshot();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
