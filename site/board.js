/* Reads the "Board Officers" Google Sheet (published as CSV) and fills [data-board].
   Columns: Order, Name, Title, Bio, Headshot link, Show on website. Only rows marked Yes show. */
(function () {
  var cfg = window.RRBC_BOARD || {};

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
    function col(n) { return head.indexOf(n); }
    var c = { order: col("order"), name: col("name"), title: col("title"), bio: col("bio"),
      photo: col("headshot link"), show: col("show on website") };
    return rows.slice(1).map(function (r) {
      function g(k) { return c[k] < 0 ? "" : (r[c[k]] || "").trim(); }
      return { order: parseFloat(g("order")) || 999, name: g("name"), title: g("title"),
        bio: g("bio"), photo: g("photo"), show: g("show") };
    }).filter(function (r) { return r.name && /^y/i.test(r.show); });
  }

  // Turns a Google Drive share link into a direct image address. Other image links pass through.
  function photoUrl(link) {
    if (!link) return "";
    var m = link.match(/\/d\/([A-Za-z0-9_-]{20,})/) || link.match(/[?&]id=([A-Za-z0-9_-]{20,})/);
    if (m && /google\.com/.test(link)) return "https://drive.google.com/thumbnail?id=" + m[1] + "&sz=w640";
    return /^https:\/\//.test(link) ? link : "";
  }

  function initials(name) {
    return name.split(/\s+/).filter(Boolean).slice(0, 2).map(function (w) { return w[0].toUpperCase(); }).join("");
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function render(box, people, isSample) {
    var list = box.querySelector("[data-list]");
    var fallback = box.querySelector("[data-fallback]");
    if (!people.length) { fallback.hidden = false; return; }
    if (isSample) box.insertBefore(el("p", "sample-note", "Sample officers. The real board appears once the Google Sheet is connected."), box.firstChild);
    people.sort(function (a, b) { return a.order - b.order; });
    people.forEach(function (p) {
      var li = el("li", "officer");
      var fig = el("div", "officer-photo");
      var src = photoUrl(p.photo);
      var mono = el("span", "officer-initials", initials(p.name));
      mono.setAttribute("aria-hidden", "true");
      fig.appendChild(mono);
      if (src) {
        var img = new Image();
        img.alt = "Photo of " + p.name;
        img.loading = "lazy";
        img.onload = function () { fig.classList.add("has-photo"); };
        img.onerror = function () { img.remove(); };
        img.src = src;
        fig.appendChild(img);
      }
      li.appendChild(fig);
      var body = el("div", "officer-body");
      body.appendChild(el("h3", "officer-name", p.name));
      if (p.title) body.appendChild(el("p", "officer-title", p.title));
      if (p.bio) body.appendChild(el("p", "officer-bio", p.bio));
      li.appendChild(body);
      list.appendChild(li);
    });
  }

  function start() {
    var box = document.querySelector("[data-board]");
    if (!box) return;
    function fallback() { render(box, cfg.sample ? cfg.sample.slice() : [], !!cfg.sample); }
    function useText(t) { render(box, toRecords(parseCSV(t)), false); }
    if (!cfg.csv) return cfg.csvText ? useText(cfg.csvText) : fallback();
    fetch(cfg.csv, { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (t) { render(box, toRecords(parseCSV(t)), false); })
      .catch(function () {
        if (cfg.csvText) { useText(cfg.csvText); } else { fallback(); }
      });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
