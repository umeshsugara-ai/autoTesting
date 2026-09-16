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
// WHAT THIS DOES NOT SEE (AT-362 — named here rather than left to be
// discovered). The claim is "text a reader can see", and these are the places
// that claim does not hold. Each is a page where a credential could render in
// plain type while this returns a clean string:
//   - text inside an open shadow root, and text in a same-origin <iframe>;
//   - CSS generated content, the WHOLE class and not two members of it:
//     ::before, ::after, ::marker — an ordinary <ol>'s own "1." / "2."
//     numbering is generated content and is not reported — and ::first-letter
//     / ::first-line when they inject or transform. AT-371 was filed because
//     this line named ::before/::after and stopped, which under-named the
//     class it was disclosing;
//   - a <select>'s rendered option text — including a <select size="4">, which
//     shows its options permanently with no interaction at all;
//   - text painted into <canvas>;
//   - a `title` tooltip (renders on hover) or an `alt` string (renders only
//     when the image fails).
// Extending the walk into shadow roots and frames is real work with its own
// failure modes — a unit, not a line. Until then the limit is written down, so
// a clean result is read for what it is.
//
// SEEN, BUT BY ACCIDENT RATHER THAN BY DESIGN (AT-374). <svg><text> IS
// reported. It sat in the list above for one cycle and that was a false
// statement in a limits block, which is worse than no block: the sentence
// above promises each entry is a page where a credential renders while this
// returns clean, and that was never true of SVG text. It works because SVG
// text nodes are text nodes like any other, so the walker finds them without
// knowing what they are. Nothing pins it, so it is not claimed as a capability
// either — it is recorded here, under a heading that does not lie about it.
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

  function paintsInk(el) {
    const style = window.getComputedStyle(el);
    if (style.visibility === "hidden") return false;
    // A CLOSED <details> lays its body out and shows nothing (AT-372): the
    // browser holds it at `content-visibility:hidden` so find-in-page can still
    // reach it, which is precisely a reader NOT seeing it.
    //
    // Called with DEFAULT options on purpose — display and content-visibility
    // only. `{opacityProperty: true, visibilityProperty: true}` would subsume
    // the two rules below, and a rule whose failure another rule covers cannot
    // be falsified: the opacity and visibility mutations would survive and C7's
    // kills would become vacuous. Each rule answers for itself.
    if (el.checkVisibility && !el.checkVisibility()) return false;
    // A zero alpha paints a box and shows nothing — reporting it is the
    // DOM-order error pointed the other way (AT-363).
    //
    // Anchored to the FOUR-component form on purpose. `rgba?\([^)]*,\s*([\d.]+)\s*\)`
    // was the first version and it matched plain `rgb(0, 0, 0)` too, capturing
    // the BLUE channel as the alpha — so ordinary black text was read as
    // transparent and this returned an empty string for every page. Every
    // "is not reported" assertion in the suite would have passed on a detector
    // that saw nothing at all; the same-page positive control is what caught it.
    const alpha = style.color.match(
      /^rgba\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*,\s*([\d.]+)\s*\)$/);
    if (alpha && parseFloat(alpha[1]) === 0) return false;
    return effectiveOpacity(el) !== 0;
  }

  // Nearest ancestor that clips its overflow. `text-indent:-9999px` and an
  // absolutely-positioned off-screen block both put glyphs where no amount of
  // scrolling reveals them.
  function clipRect(el) {
    for (let node = el; node && node !== document.documentElement; node = node.parentElement) {
      const style = window.getComputedStyle(node);
      if (style.overflow !== "visible" || style.clipPath !== "none") {
        return node.getBoundingClientRect();
      }
    }
    return null;
  }

  function isReachable(rect, clip) {
    // Off the DOCUMENT's left edge or above its top cannot be scrolled to.
    // Further down or right can be, so those stay.
    //
    // The scroll offsets are load-bearing (AT-373). The first version of this
    // rule tested `rect.right <= 0` against the VIEWPORT, and a client rect is
    // viewport-relative, so on a scrolled page everything above the fold tested
    // as unreachable and silently vanished from the result. That is a false
    // NEGATIVE of the AT-355 shape — a credential rendering in plain type while
    // this returns a clean string — manufactured by the fix for the false
    // positives. The next unit wires this into a crawl that scrolls, so it
    // would have shipped straight into the one caller that triggers it.
    //
    // The clip intersection below stays viewport-relative and is correct that
    // way: a clipping ancestor and its content scroll together.
    if (rect.right + window.scrollX <= 0) return false;
    if (rect.bottom + window.scrollY <= 0) return false;
    if (!clip) return true;
    return rect.right > clip.left && rect.left < clip.right &&
           rect.bottom > clip.top && rect.top < clip.bottom;
  }

  // ---- measurement --------------------------------------------------------

  function glyphsOf(node, clip, checkReachable, mask) {
    const text = node.nodeValue;
    const out = [];
    for (let i = 0; i < text.length; i += 1) {
      const range = document.createRange();
      range.setStart(node, i);
      range.setEnd(node, i + 1);
      const rect = range.getBoundingClientRect();
      // Zero WIDTH means nothing was painted where a reader would look: a
      // zero-width space, a NUL the parser dropped, a variation selector, the
      // direction override itself.
      //
      // The test is width alone, deliberately. `width === 0 && height === 0`
      // was the first version, copied from `enumerate.js::isVisible` where it
      // is right for an ELEMENT; for a one-character Range it is wrong, because
      // a zero-width character still reports the full LINE HEIGHT. It kept
      // every U+200B and reproduced, inside this instrument, exactly the
      // blindness the instrument exists to remove.
      if (rect.width === 0) continue;
      if (checkReachable && !isReachable(rect, clip)) continue;
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
      const glyphs = glyphsOf(node, clipRect(parent), true, masksText(parent));
      for (const item of glyphs) items.push(item);
    }
    node = walker.nextNode();
  }

  for (const control of document.querySelectorAll("input, textarea")) {
    if (!paintsInk(control)) continue;
    if (!isReachable(control.getBoundingClientRect(), clipRect(control))) continue;
    for (const item of mirrorGlyphs(control)) items.push(item);
  }

  items.sort((a, b) => {
    const rowA = Math.round(a.y / ROW_TOLERANCE);
    const rowB = Math.round(b.y / ROW_TOLERANCE);
    return rowA === rowB ? a.x - b.x : rowA - rowB;
  });

  return items.map((item) => item.text).join("");
})();
