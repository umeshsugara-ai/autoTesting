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
// rows by y and sorted by x within a row. Characters that occupy no box are
// dropped, because they are what a reader does not see.
(() => {
  const ROW_TOLERANCE = 4; // px; sub-pixel and font-metric jitter within a line

  function glyphsOf(node) {
    const text = node.nodeValue;
    const out = [];
    for (let i = 0; i < text.length; i += 1) {
      const range = document.createRange();
      range.setStart(node, i);
      range.setEnd(node, i + 1);
      const rect = range.getBoundingClientRect();
      // Zero WIDTH means nothing was painted where a reader would look: a
      // zero-width space, a NUL the parser dropped, a variation selector, the
      // direction override itself. Excluding them is the point -- the string
      // this returns is what a reader can see, not what was stored.
      //
      // The test is width alone, deliberately. `width === 0 && height === 0`
      // was the first version, copied from `enumerate.js::isVisible` where it
      // is right for an ELEMENT; for a one-character Range it is wrong, because
      // a zero-width character still reports the full LINE HEIGHT. It kept
      // every U+200B and reproduced, inside the new instrument, exactly the
      // blindness the instrument exists to remove.
      if (rect.width === 0) continue;
      out.push({ ch: text[i], x: rect.left, y: rect.top });
    }
    return out;
  }

  function isVisibleElement(el) {
    return window.getComputedStyle(el).visibility !== "hidden";
  }

  function isRendered(node) {
    // `visibility: hidden` is the case this exists for, and it is the ONLY one.
    // Measured against a real Chromium: `display:none`, `<script>` and
    // `<style>` text all report zero-width rects, so the width filter above
    // already excludes them and a tag check was dead code. `visibility:hidden`
    // does NOT -- it preserves layout, so its glyphs report a real width, and
    // without this the detector reports text nobody can see as if a reader saw
    // it. A tag allow/deny list was the intuitive guard and the wrong one.
    const parent = node.parentElement;
    return parent ? isVisibleElement(parent) : false;
  }

  // AT-361. A form control's value is not a text node, so the walker below is
  // structurally blind to it -- and a case title renders ONLY inside
  // `input[name=title]`, which is the single field U8 is written about. A
  // text-node-only detector therefore returns a clean string for that page
  // whatever the field holds: a guaranteed false negative exactly where it
  // matters most.
  //
  // Each value is mirrored into an offscreen span carrying the control's own
  // font, direction and unicode-bidi, measured per character, and removed. The
  // mirror is what makes the measurement real rather than a DOM read: a value
  // spelled with a direction override reorders inside the span exactly as it
  // does inside the control.
  //
  // This is the one place the detector touches the page. The span is absolutely
  // positioned far offscreen, is never interacted with, and is removed in a
  // `finally`, so the page under test keeps its own state -- but it IS a write,
  // and that is a deliberate trade, not an oversight.
  function mirrorGlyphs(control) {
    const value = control.value;
    if (!value) return [];
    const at = control.getBoundingClientRect();
    if (at.width === 0 && at.height === 0) return [];
    const style = window.getComputedStyle(control);
    const span = document.createElement("span");
    span.textContent = value;
    span.style.cssText = "position:absolute;left:-99999px;top:0;white-space:pre;";
    span.style.font = style.font;
    span.style.direction = style.direction;
    span.style.unicodeBidi = style.unicodeBidi;
    document.body.appendChild(span);
    try {
      const node = span.firstChild;
      const local = glyphsOf(node);
      const origin = local.length ? Math.min(...local.map((g) => g.x)) : 0;
      // Re-seated onto the control's own position so page-level ordering holds.
      return local.map((g) => ({ ch: g.ch, x: at.left + (g.x - origin), y: at.top }));
    } finally {
      span.remove();
    }
  }

  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const glyphs = [];
  let node = walker.nextNode();
  while (node) {
    if (node.nodeValue && node.nodeValue.trim() && isRendered(node)) {
      for (const glyph of glyphsOf(node)) glyphs.push(glyph);
    }
    node = walker.nextNode();
  }

  for (const control of document.querySelectorAll("input, textarea")) {
    if (!isVisibleElement(control)) continue;
    for (const glyph of mirrorGlyphs(control)) glyphs.push(glyph);
  }

  glyphs.sort((a, b) => {
    const rowA = Math.round(a.y / ROW_TOLERANCE);
    const rowB = Math.round(b.y / ROW_TOLERANCE);
    return rowA === rowB ? a.x - b.x : rowA - rowB;
  });

  return glyphs.map((g) => g.ch).join("");
})();
