// DriveTTO video player — resolves ?v= or ?src= against media-selection.json
(function () {
  "use strict";

  var DATA_URL = "assets/data/media-selection.json";
  var BASE = "https://rtwotwo.github.io/DriveTTO/";

  var videoEl = document.getElementById("player-video");
  var titleEl = document.getElementById("player-title");
  var metaEl = document.getElementById("player-meta");
  var descEl = document.getElementById("player-desc");
  var relatedEl = document.getElementById("related");
  var locEl = document.getElementById("player-loc");

  // Robust param extraction: handles ?v=ID, ?src=..., ?id=ID,
  // hash forms (#v=ID) and URLs where "=" got percent-encoded.
  function qs(name) {
    var raw = decodeURIComponent(window.location.search + "&" + window.location.hash.replace(/^#/, ""));
    var pairs = raw.split(/[?&#;]+/);
    for (var i = 0; i < pairs.length; i++) {
      var pos = pairs[i].indexOf("=");
      if (pos < 0) continue;
      if (pairs[i].slice(0, pos) === name) {
        return pairs[i].slice(pos + 1);
      }
    }
    // Fallback: when the key itself was embedded (e.g. "v=nuscenes..." as first pair)
    for (var j = 0; j < pairs.length; j++) {
      var pos2 = pairs[j].indexOf("=");
      if (pos2 > 0) return pairs[j].slice(pos2 + 1);
    }
    return null;
  }

  function abs(p) {
    if (!p) return "";
    return /^https?:/.test(p) ? p : p.replace(/^\//, BASE).replace(/^\.\//, BASE);
  }

  function buildCatalog(d) {
    var items = [];
    function push(id, title, src, poster, meta, desc) {
      items.push({
        id: id,
        title: title,
        src: abs(src),
        poster: poster ? abs(poster) : "",
        meta: meta,
        desc: desc || ""
      });
    }
    (d.videos || []).forEach(function (v, i) {
      var diff = (v.difficulty || "").toUpperCase();
      var meta = [
        "HUGSIM · " + (v.dataset || ""),
        diff,
        "RC " + (v.rc != null ? Number(v.rc).toFixed(1) : "—"),
        "HD " + (v.hd != null ? Number(v.hd).toFixed(1) : "—")
      ];
      push(v.id, v.title || v.id, v.src, v.poster, meta, v.description);
    });
    (d.navsim_animations || []).forEach(function (a) {
      push(a.token, "NAVSIM plan animation", a.src, "", ["PDMS " + a.pdms, "4 s prediction horizon"], a.scope);
    });
    if (d.intro) {
      push("intro", "DriveTTO introduction", d.intro.src, "assets/images/intro-poster.jpg",
        ["1 min 54 s", "Method · Planning · Closed-loop driving"], d.intro.selection);
    }
    if (d.algorithm_animation) {
      push("algorithm", "DriveTTO algorithm animation", d.algorithm_animation.src, d.algorithm_animation.poster,
        ["72 s", "Search. Compare. Select."], d.algorithm_animation.scope + ". " + (d.algorithm_animation.note || ""));
    }
    return items;
  }

  function findItem(catalog, param) {
    if (!param) return null;
    if (!/^https?:/.test(param)) {
      for (var i = 0; i < catalog.length; i++) {
        if (catalog[i].id === param) return catalog[i];
      }
      var norm = param.split("/").pop().replace(/\.mp4$/, "");
      for (var j = 0; j < catalog.length; j++) {
        if (catalog[j].src.split("/").pop().replace(/\.mp4$/, "") === norm) return catalog[j];
      }
      return null;
    }
    var norm2 = param.split("/").pop().replace(/\.mp4$/, "");
    for (var k = 0; k < catalog.length; k++) {
      if (catalog[k].src.split("/").pop().replace(/\.mp4$/, "") === norm2) return catalog[k];
    }
    return null;
  }

  function render(item, catalog) {
    document.title = item.title + " — DriveTTO";
    videoEl.src = item.src;
    if (item.poster) videoEl.poster = item.poster;
    titleEl.textContent = item.title;
    metaEl.innerHTML = item.meta.map(function (m) {
      return '<span class="player-chip">' + m.replace(/ /g, "&nbsp;") + "</span>";
    }).join("");
    descEl.textContent = item.desc || "";
    locEl.textContent = item.src.replace(BASE, "");

    // related: other clips in the same group of up to 8
    var others = catalog.filter(function (c) { return c.id !== item.id; });
    if (others.length) {
      var head = document.createElement("div");
      head.className = "related-head";
      head.textContent = "More videos";
      relatedEl.appendChild(head);
      others.slice(0, 8).forEach(function (c) {
        var a = document.createElement("a");
        a.className = "related-item";
        a.href = "player.html?v=" + encodeURIComponent(c.id);
        var img = document.createElement("img");
        img.src = c.poster || "assets/images/intro-poster.jpg";
        img.loading = "lazy";
        img.alt = c.title;
        img.onerror = function () { img.src = "assets/images/intro-poster.jpg"; };
        var t = document.createElement("span");
        t.textContent = c.title;
        var e = document.createElement("em");
        e.textContent = c.meta.join(" · ");
        a.appendChild(img); a.appendChild(t); a.appendChild(e);
        relatedEl.appendChild(a);
      });
    }
  }

  function showError(msg) {
    document.body.innerHTML =
      '<div class="player-error"><h1>Video not found</h1><p>' + msg + "</p>" +
      '<p><a class="player-back" href="index.html">← Back to the DriveTTO project page</a></p></div>';
  }

  fetch(DATA_URL)
    .then(function (r) { if (!r.ok) throw new Error("data fetch failed"); return r.json(); })
    .then(function (d) {
      var catalog = buildCatalog(d);
      var param = qs("v") || qs("src") || qs("id");
      var item = findItem(catalog, param);
      if (!item) {
        showError("The requested video could not be matched. Please pick one from the project page.");
        return;
      }
      render(item, catalog);
    })
    .catch(function (err) {
      showError("Unable to load video catalog. " + err.message);
    });
})();
