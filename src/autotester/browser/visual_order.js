// The page's text in VISUAL reading order — what a human actually takes off
// the screen, which is NOT document order whenever direction is overridden.
// Loaded by browser/observe.py via page.evaluate(). Returns a string.
//
// AT-355/AT-358: a credential written backwards behind U+202E is stored
// reversed and rendered forwards. Every instrument the crawler had read the
// DOM — innerText, textContent, element names — and every one of them reports
// the stored order, so all of them said the page was clean while a reader
// could see the secret in plain type. A checker caught it only by measuring
// where the glyphs actually landed.
//
// Method: one Range per character, its client rect taken, glyphs bucketed into
// rows by y and sorted by x within a row. Characters that occupy no box, or
// that paint nothing a reader can see, are dropped.
//
// WHAT THIS DOES NOT SEE (AT-362). Each is a page where a credential could render
// in plain type while this returns a clean string:
//   - text in an open shadow root, or in a same-origin <iframe>;
//   - CSS generated content, the WHOLE class: ::before, ::after, ::marker (an
//     <ol>'s own "1."), ::first-letter / ::first-line (AT-371: naming two members
//     and stopping under-named the class);
//   - a <select>'s option text, including <select size="4">, shown permanently;
//   - text painted into <canvas>;
//   - a `title` tooltip (hover) or an `alt` string (image failure).
// Extending into shadow roots and frames is a unit, not a line.
//
// SEEN BY ACCIDENT, NOT BY DESIGN (AT-374): <svg><text> IS reported — SVG text
// nodes are ordinary text nodes to the walker. Nothing pins it, so it is not
// claimed as a capability; listing it above as unseen was a false statement.
(() => {
  const ROW_TOLERANCE = 4; // px; sub-pixel and font-metric jitter within a line
  const BULLET = "•";

  // ---- what a reader can actually see ------------------------------------

  function effectiveOpacity(el) {
    let opacity = 1;
    for (let node = el; node && node !== document.documentElement; node = node.parentElement) {
      const value = parseFloat(window.getComputedStyle(node).opacity);
      if (!Number.isNaN(value)) opacity *= value;
      if (opacity === 0) return 0;
    }
    return opacity;
  }

  // `-webkit-text-security` turns a run into bullets with no `type=password`
  // anywhere — on a plain <span> as readily as on an input (AT-372). Reporting
  // the characters would put in cleartext exactly what the screen masks, which
  // is the password defect one property to the left.
  function masksText(el) {
    const style = window.getComputedStyle(el);
    const value = style.webkitTextSecurity ||
      style.getPropertyValue("-webkit-text-security");
    return Boolean(value) && value !== "none";
  }

  // display:contents has no box, so checkVisibility() on it is false though its text
  // paints (AT-438). Ask the nearest BOX in the FLAT tree (slots, shadow hosts) and how
  // a visible box hides its own contents. <details> is judged by `::details-content`,
  // never its tag: authors restyle it (AT-449). NEVER insert a probe (AT-442/443).
  function flatParent(node) {
    return node.assignedSlot || node.parentElement || (node.parentNode && node.parentNode.host) || null;
  }

  function contentsRenders(el) {
    if (window.getComputedStyle(el).display !== "contents") return false;
    let child = el;
    for (let box = flatParent(el); box; child = box, box = flatParent(box)) {
      const s = window.getComputedStyle(box);
      // AT-453: the pseudo's own contentVisibility is not enough -- an author
      // `::details-content{display:contents|inline}` etc. means content-visibility
      // does not apply and the body still paints (AT-437's HIDES_ON allow-list,
      // now applied to the PSEUDO's display instead of assuming block). Measured
      // against 26 details-shaped pages incl. A3/A4:
      // qa/evidence/browser-at438-display-contents-2026-09-16-checker-c3/fixdir3.py.
      if (box.tagName === "DETAILS" && child !== box.querySelector(":scope > summary") &&
          (p => p.contentVisibility === "hidden" && HIDES_ON.test(p.display))(window.getComputedStyle(box, "::details-content"))) return false;
      if (s.display === "contents") continue;
      if (!box.checkVisibility()) return false;
      return !(s.contentVisibility === "hidden" && HIDES_ON.test(s.display));
    }
    return false;
  }

  const HIDES_ON = /^(block|inline-block|flex|inline-flex|grid|inline-grid|flow-root|list-item|table-cell|table-caption)$/;

  function paintsInk(el) {
    const style = window.getComputedStyle(el);
    if (style.visibility === "hidden") return false;
    // A CLOSED <details> lays its body out and shows nothing (AT-372): the
    // browser holds it at `content-visibility:hidden` so find-in-page can still
    // reach it, which is precisely a reader NOT seeing it.
    //
    // DEFAULT options on purpose: opacity/visibility flags would subsume the rules
    // below, and a rule another rule covers cannot be falsified (C7).
    if (el.checkVisibility && !el.checkVisibility() && !contentsRenders(el)) return false;
    // checkVisibility() misses text whose own PARENT is content-visibility:hidden
    // (AT-429). Computed style says `hidden` even where Chromium still PAINTS (inline,
    // ruby, table rows, `table`, `contents`: AT-437), so HIDES_ON is a MEASURED allow-list
    // (at429 groundtruth.py): an unmeasured display is reported, never a missed credential.
    if (style.contentVisibility === "hidden" && HIDES_ON.test(style.display)) return false;
    // A zero alpha paints a box and shows nothing (AT-363). Anchored to the
    // FOUR-component form on purpose: the first regex also matched `rgb(0,0,0)`
    // and read the BLUE channel as alpha, so black text counted as transparent
    // and every page came back empty — caught only by a same-page positive control.
    const alpha = style.color.match(
      /^rgba\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*,\s*([\d.]+)\s*\)$/);
    if (alpha && parseFloat(alpha[1]) === 0) return false;
    return effectiveOpacity(el) !== 0;
  }

  // ---- reachability (AT-408/AT-416; split into visual_order_reach.js) -----
  // Moved out to its own file when the fix needed room this module's 300-line
  // cap did not have. Spliced back in HERE by observe.py (string replace on
  // the marker below) so `reachOf`/`isReachable` share this IIFE's closure and
  // `page.evaluate()` still receives ONE script shaped exactly as before —
  // never two top-level scripts, which risks Playwright's expression-vs-
  // function parsing of the string differently than today's `(() => {...})();`.
  // AUTOTESTER:REACH_MODULE

  // ---- measurement --------------------------------------------------------

  function glyphsOf(node, reach, checkReachable, mask) {
    const text = node.nodeValue;
    const out = [];
    // Measure the whole node once and DISCARD the result (AT-410). Inside a
    // subtree the browser has skipped — `content-visibility:auto` off-screen,
    // with an intrinsic placeholder size — the FIRST rect query returns all
    // zeros and itself forces the layout, so every later query is right. The
    // per-glyph loop below took that first query on character 0, the width
    // guard dropped it, and `CVAUTO_SENTINEL_91` came back as
    // `VAUTO_SENTINEL_91` on the first call and correct on the second. Callers
    // call once. This throwaway query is the one that absorbs the zeros.
    const warm = document.createRange();
    warm.selectNodeContents(node);
    warm.getBoundingClientRect();
    for (let i = 0; i < text.length; i += 1) {
      const range = document.createRange();
      range.setStart(node, i);
      range.setEnd(node, i + 1);
      const rect = range.getBoundingClientRect();
      // Zero WIDTH means nothing was painted: a zero-width space, a dropped NUL,
      // a variation selector, the direction override itself. Width ALONE, on
      // purpose — `width === 0 && height === 0` is right for an element but a
      // one-character Range keeps the full line height, so that form kept every
      // U+200B: the exact blindness this instrument exists to remove.
      if (rect.width === 0) continue;
      if (checkReachable && !isReachable(rect, reach)) continue;
      const ch = mask ? BULLET : text[i];
      out.push({ ch, text: ch, x: rect.left, y: rect.top });
    }
    return out;
  }

  // A form control's value is not a text node, so the walker below is blind to
  // it — and a case title renders ONLY inside `input[name=title]` (AT-361).
  // The value is mirrored into an offscreen span carrying the control's own
  // font, direction and unicode-bidi, measured, and removed. The mirror is what
  // makes this a measurement rather than a DOM read: a value spelled with a
  // direction override reorders inside the span exactly as it does inside the
  // control, and so does a control reversed by CSS alone.
  //
  // This is the one place the detector writes to the page. The span is
  // positioned far offscreen, never interacted with, and removed in a
  // `finally` — a deliberate trade, not an oversight.
  function mirrorGlyphs(control) {
    // A password field shows bullets. Reporting its value would put a
    // credential in cleartext into an observation string (AT-363) — the
    // opposite of this module's job — so what a reader sees is what is
    // reported. An empty control shows its placeholder, which renders.
    // `-webkit-text-security` masks a control with no `type=password` on it at
    // all (AT-372), so the two cases are one rule. A placeholder is NEVER
    // masked: a masked field still shows its placeholder in plain type.
    const hasValue = Boolean(control.value);
    const masked = control.type === "password" || masksText(control);
    const shown = hasValue && masked
      ? BULLET.repeat(control.value.length)
      : (control.value || control.placeholder || "");
    if (!shown) return [];
    const at = control.getBoundingClientRect();
    if (at.width === 0 && at.height === 0) return [];
    const style = window.getComputedStyle(control);
    const span = document.createElement("span");
    span.textContent = shown;
    span.style.cssText = "position:absolute;left:-99999px;top:0;white-space:pre;";
    span.style.font = style.font;
    span.style.direction = style.direction;
    span.style.unicodeBidi = style.unicodeBidi;
    document.body.appendChild(span);
    try {
      // Reachability is NOT checked inside the mirror: it sits at
      // left:-99999px by design, which is exactly what `isReachable`
      // rejects. The control's OWN position is what decides whether a
      // reader can reach it, and that is tested by the caller.
      const local = glyphsOf(span.firstChild, null, false);
      // ONE item, not one per glyph. Re-seating each glyph at its own x and
      // letting the global sort take over interleaved two adjacent inputs into
      // `PLACEHOLDER_SENTINEL_8*8*****...`: a long value overflows its box in
      // the mirror, where the control itself would have clipped it, so the runs
      // overlap in x. The control's value is one run at one position; only its
      // INTERNAL order is a measurement.
      local.sort((a, b) => a.x - b.x);
      return [{ text: local.map((g) => g.ch).join(""), x: at.left, y: at.top }];
    } finally {
      span.remove();
    }
  }

  const items = [];  // {text, x, y}; a text-node glyph or a whole control value
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node = walker.nextNode();
  while (node) {
    const parent = node.parentElement;
    if (node.nodeValue && node.nodeValue.trim() && parent && paintsInk(parent)) {
      const glyphs = glyphsOf(node, reachOf(parent), true, masksText(parent));
      for (const item of glyphs) items.push(item);
    }
    node = walker.nextNode();
  }

  for (const control of document.querySelectorAll("input, textarea")) {
    if (!paintsInk(control)) continue;
    if (!isReachable(control.getBoundingClientRect(), reachOf(control))) continue;
    for (const item of mirrorGlyphs(control)) items.push(item);
  }

  items.sort((a, b) => {
    const rowA = Math.round(a.y / ROW_TOLERANCE);
    const rowB = Math.round(b.y / ROW_TOLERANCE);
    return rowA === rowB ? a.x - b.x : rowA - rowB;
  });

  return items.map((item) => item.text).join("");
})();
