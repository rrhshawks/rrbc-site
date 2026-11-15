/* Reads the "What We've Funded" Google Sheet (published as CSV) and fills any
   element with data-funded. Columns: Date, School year, Program, Area,
   What it paid for, Amount, Show on website. Only rows marked Yes are shown. */
(function () {
  var cfg = window.RRBC || {};

  function parseCSV(text) {
    var rows = [], row = [], cell = "", q = false;
    for (var i = 0; i < text.length; i++) {
      var c = text[i];
      if (q) {
        if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
        else if (c === '"') q = false;
        else cell += c;
      } else if (c === '"') q = true;
      else if (c === ",") { row.push(cell); cell = ""; }
      else if (c === "\n" || c === "\r") {
        if (c === "\r" && text[i + 1] === "\n") i++;
        row.push(cell); rows.push(row); row = []; cell = "";
      } else cell += c;
    }
    if (cell || row.length) { row.push(cell); rows.push(row); }
    return rows;
  }

  function toRecords(rows) {
    if (!rows.length) return [];
    var head = rows[0].map(function (h) { return h.trim().toLowerCase(); });
    function col(name) { return head.indexOf(name); }
    var c = { date: col("date"), year: col("school year"), program: col("program"), area: col("area"),
      what: col("what it paid for"), amount: col("amount"), show: col("show on website") };
    return rows.slice(1).map(function (r) {
      function g(k) { return c[k] < 0 ? "" : (r[c[k]] || "").trim(); }
      return { date: g("date"), year: g("year"), program: g("program"), area: g("area"),
        what: g("what"), amount: g("amount"), show: g("show") };
    }).filter(function (r) { return r.program && /^y/i.test(r.show); });
  }

  function money(v) {
    var n = parseFloat(String(v).replace(/[^0-9.]/g, ""));
    return isNaN(n) ? null : n;
  }
  function fmt(n) { return "$" + n.toLocaleString("en-US", { maximumFractionDigits: 0 }); }
  function fmtDate(s) {
    var d = new Date(s + "T12:00:00");
    return isNaN(d) ? s : d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function render(box, data, isSample) {
    var limit = parseInt(box.getAttribute("data-limit"), 10) || 0;
    var list = box.querySelector("[data-list]");
    var summary = box.querySelector("[data-summary]");
    var filters = box.querySelector("[data-filters]");
    var empty = box.querySelector("[data-empty]");
    // Newest school year first; within a year, newest date first, otherwise keep the sheet's order.
    data.forEach(function (r, i) { r._i = i; });
    data.sort(function (a, b) {
      if (a.year !== b.year) return a.year < b.year ? 1 : -1;
      if (a.date && b.date && a.date !== b.date) return a.date < b.date ? 1 : -1;
      return a._i - b._i;
    });

    if (!data.length) { empty.hidden = false; return; }

    if (isSample) {
      var note = el("p", "sample-note", "Sample entries. The real list appears once the Google Sheet is connected.");
      box.insertBefore(note, box.firstChild);
    }

    var year = data[0].year;
    var inYear = data.filter(function (r) { return r.year === year; });
    var total = inYear.reduce(function (s, r) { return s + (money(r.amount) || 0); }, 0);
    var areas = {};
    inYear.forEach(function (r) { if (r.area) areas[r.area] = 1; });
    var nAreas = Object.keys(areas).length;
    var missing = inYear.some(function (r) { return money(r.amount) == null; });
    summary.textContent = (year ? "In " + year + ", " : "") + "the club funded " + inYear.length +
      (inYear.length === 1 ? " request" : " requests") +
      (nAreas ? " across " + nAreas + (nAreas === 1 ? " area" : " areas") : "") + "." +
      (total ? (missing ? " Listed amounts total " : " Total: ") + fmt(total) + "." : "");

    var current = "All";
    function draw() {
      list.textContent = "";
      var rows = data.filter(function (r) { return current === "All" || r.area === current; });
      if (limit) rows = rows.slice(0, limit);
      var lastYear = null;
      rows.forEach(function (r) {
        if (!limit && r.year && r.year !== lastYear) {
          lastYear = r.year;
          var h = el("li", "ledger-year");
          h.appendChild(el("h3", null, r.year + " school year"));
          list.appendChild(h);
        }
        var li = el("li", r.date ? "ledger-row" : "ledger-row no-date");
        if (r.date) li.appendChild(el("span", "ledger-date", fmtDate(r.date)));
        var mid = el("span", "ledger-main");
        mid.appendChild(el("strong", "ledger-program", r.program));
        mid.appendChild(el("span", "ledger-what", r.what));
        li.appendChild(mid);
        if (r.area) li.appendChild(el("span", "ledger-area", r.area));
        var m = money(r.amount);
        li.appendChild(el("span", "ledger-amount", m ? fmt(m) : ""));
        list.appendChild(li);
      });
    }

    if (!limit && filters) {
      var names = ["All"].concat(Object.keys(data.reduce(function (o, r) { if (r.area) o[r.area] = 1; return o; }, {})).sort());
      var bar = el("div", "filters");
      bar.setAttribute("role", "group");
      bar.setAttribute("aria-label", "Filter by area");
      names.forEach(function (n) {
        var b = el("button", "filter", n);
        b.type = "button";
        b.setAttribute("aria-pressed", n === current ? "true" : "false");
        b.addEventListener("click", function () {
          current = n;
          bar.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
          draw();
        });
        bar.appendChild(b);
      });
      filters.appendChild(bar);
    }
    draw();
  }

  function start() {
    var boxes = document.querySelectorAll("[data-funded]");
    if (!boxes.length) return;
    function each(data, sample) { boxes.forEach(function (b) { render(b, data.slice(), sample); }); }
    function fallback() {
      if (cfg.sample) each(cfg.sample, true);
      else each([], false);
    }
    function useText(t) { each(toRecords(parseCSV(t)), false); }
    if (!cfg.csv) return cfg.csvText ? useText(cfg.csvText) : fallback();
    fetch(cfg.csv, { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (t) { each(toRecords(parseCSV(t)), false); })
      .catch(function () {
        if (cfg.csvText) { useText(cfg.csvText); } else { fallback(); }
      });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
