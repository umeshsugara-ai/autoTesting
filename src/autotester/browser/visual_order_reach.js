// Reachability for visual_order.js — split out (AT-408/AT-416) when the fix
// needed room the 300-line module cap did not have. NOT its own script: this
// file has no wrapper of its own. observe.py splices its text, verbatim, in
// place of the `// AUTOTESTER:REACH_MODULE` marker inside visual_order.js's
// IIFE, so `reachOf`/`isReachable` share that IIFE's closure (`window`,
// `document`) exactly as if this text had never left the file. Edit this file
// for a reachability change; visual_order.js only for anything else.

const SCROLLS = /^(auto|scroll)$/;

// Nearest ancestor that clips its overflow WHERE A READER CANNOT GET AT IT.
// `text-indent:-9999px` and an absolutely-positioned off-screen block both put
// glyphs where no amount of scrolling reveals them.
//
// A genuinely SCROLLABLE pane is the opposite case and was conflated with it
// (AT-379): a reader can scroll an `overflow:auto` pane and read every line,
// so its box is not a boundary. `overflow:hidden` with nothing to scroll still
// is, and the two are told apart by MEASUREMENT — computed overflow is
// `auto`/`scroll` AND the content actually overflows — never by guess.
//
// Per axis, deliberately: `overflow-y:auto; overflow-x:hidden` really does
// hide what runs off its right edge while exposing what runs off its bottom.
//
// TWO running clips, not one (AT-416). A single running clip, narrowed by
// every ancestor's box on the way up and tested against the GLYPH's rect, was
// wrong: a glyph inside a scrollable pane MOVES inside that pane's own box as
// the pane is scrolled, so testing the glyph's CURRENT position against a
// clip an ancestor OUTSIDE the pane contributed made the verdict flip with the
// pane's own scroll offset — reachable only at the instant the glyph happened
// to be coasting through the outer clip band, unreachable a moment earlier or
// later, though nothing about whether a reader can GET there changed. That is
// exactly the scroll-invariance floor this module is charged against (U14a,
// qa/contracts/ui.md): reported=false at rest and reported=true after
// scrolling the SAME pane to the SAME state is two different answers to one
// question, not two different questions.
//
// A reader CAN bring any line inside a genuinely scrollable pane to any
// position within that pane's OWN box by scrolling it — the pane's own box
// does not move when its own content scrolls, only the content does. So the
// question "is this glyph reachable past an ancestor OUTSIDE the pane" does
// not depend on the glyph at all once a scroller has been passed; it depends
// on whether the PANE's own box reaches that ancestor's clip. (Whether a
// SPECIFIC glyph's scroll range actually lands it in the overlap, rather than
// merely somewhere in the pane, is a finer question this does not answer —
// deliberately: U14(b)'s north-star tie-break prefers a reachable glyph
// wrongly kept over a reachable glyph wrongly dropped, and the coarse test is
// the side of that trade this module is built to take.)
//
// `innerClip` is narrowed by every ancestor up to and including the first
// (innermost) genuinely scrollable one, and is tested against the GLYPH's
// rect: nothing between the glyph and that scroller moves relative to the
// glyph when the scroller is scrolled (AT-379's own P2 probe: "the middle box
// is a real boundary"), so that test stays invariant to the scroller's own
// scrolling. `outerClip` is narrowed by every ancestor ABOVE the innermost
// scroller, and is tested against that scroller's OWN box (`scrollerBox`,
// captured once — the innermost only, "carry the innermost scroller's box
// forward"). An outer scroller further up the same chain still adds its own
// offset to `scrollX`/`scrollY` and still narrows `outerClip` like any other
// ancestor; it just never replaces `scrollerBox`. Neither running clip reads
// the glyph's position relative to a scroller that contains it, so neither
// flips with that scroller's own scroll position. The AT-408/AT-393 idea —
// walk all the way up, narrowing — stays; it is just two narrowings now,
// split at the first scroller, instead of one tested against the wrong thing.
//
// Returns `{innerClip, outerClip, scrollerBox, scrollX, scrollY}` —
// `scrollX`/`scrollY` the accumulated scroll offset of the window AND every
// scrollable ancestor (AT-392, AT-408: the walk never stops at the first one).
function reachOf(el) {
  let scrollX = window.scrollX;
  let scrollY = window.scrollY;
  let innerClip = null;
  let outerClip = null;
  let scrollerBox = null;
  const narrow = (clip, box) => (clip === null ? box : {
    left: Math.max(clip.left, box.left),
    right: Math.min(clip.right, box.right),
    top: Math.max(clip.top, box.top),
    bottom: Math.min(clip.bottom, box.bottom),
  });
  for (let node = el; node && node !== document.documentElement; node = node.parentElement) {
    const style = window.getComputedStyle(node);
    if (style.clipPath !== "none") {
      const box = node.getBoundingClientRect();
      if (scrollerBox) outerClip = narrow(outerClip, box);
      else innerClip = narrow(innerClip, box);
      continue;
    }
    if (style.overflow === "visible") continue;
    const box = node.getBoundingClientRect();
    const scrollsY = SCROLLS.test(style.overflowY) && node.scrollHeight > node.clientHeight;
    const scrollsX = SCROLLS.test(style.overflowX) && node.scrollWidth > node.clientWidth;
    if (scrollsX) scrollX += node.scrollLeft;
    if (scrollsY) scrollY += node.scrollTop;
    const clipBox = {
      left: scrollsX ? -Infinity : box.left,
      right: scrollsX ? Infinity : box.right,
      top: scrollsY ? -Infinity : box.top,
      bottom: scrollsY ? Infinity : box.bottom,
    };
    if (scrollerBox) {
      // Already past the innermost scroller: this ancestor's own box narrows
      // the OUTER clip, same shape as any other ancestor above the scroller.
      outerClip = narrow(outerClip, clipBox);
    } else {
      innerClip = narrow(innerClip, clipBox);
      // The FIRST genuinely scrollable ancestor found (innermost, since the
      // walk starts at the glyph). A later one further up only contributes to
      // outerClip/scrollX/scrollY above, per `if (scrollerBox)`.
      if (scrollsX || scrollsY) scrollerBox = box;
    }
  }
  return { innerClip, outerClip, scrollerBox, scrollX, scrollY };
}

function isReachable(rect, reach) {
  // Off the DOCUMENT's left edge or above its top cannot be scrolled to.
  // Further down or right can be, so those stay.
  //
  // THIS LINE HAS BEEN WRONG FIVE TIMES, always the same way: a fix for false
  // POSITIVES that manufactured a false NEGATIVE of the AT-355 shape — a
  // credential rendering in plain type while this returns a clean string.
  // AT-373 (viewport-relative test), AT-379 (a scrollable pane read as a
  // clip), AT-392 (window offset only), AT-408 (walk stopped at the first
  // one-axis scroller), AT-416 (the outer clip tested the glyph's own MOVING
  // rect instead of the scroller's FIXED box, so the verdict flipped with the
  // scroller's own scroll position). Each asked "can a reader SEE this right
  // now?" where the question is "can a reader REACH it, ever?". Details in
  // those ledger rows; the rule here:
  //
  //   a glyph is unreachable only if it sits before the document origin after
  //   everything scrollable has been scrolled back, OR it sits outside a hard
  //   clip that no scroll moves, OR the scroller carrying it sits outside a
  //   hard clip further out that no scroll of THAT scroller moves either.
  //
  // `reach.scrollX/scrollY` carry the first part — window plus every
  // scrollable ancestor — and are already scroll-position invariant (moving a
  // scroller by `d` moves `rect` by `-d` and `scrollY` by `+d`). `innerClip`
  // is the second part, tested against the glyph itself because nothing
  // between it and the first scroller moves relative to it when that scroller
  // is scrolled. `outerClip` is the third part, tested against
  // `reach.scrollerBox` rather than `rect` because a scroller's own box does
  // NOT move when its own content is scrolled — only the glyph inside it does
  // — so testing the scroller's box is what keeps this invariant too (AT-416).
  if (rect.right + reach.scrollX <= 0) return false;
  if (rect.bottom + reach.scrollY <= 0) return false;
  if (reach.innerClip) {
    const c = reach.innerClip;
    if (!(rect.right > c.left && rect.left < c.right &&
          rect.bottom > c.top && rect.top < c.bottom)) return false;
  }
  if (reach.outerClip) {
    const c = reach.outerClip;
    const box = reach.scrollerBox;
    if (!(box.right > c.left && box.left < c.right &&
          box.bottom > c.top && box.top < c.bottom)) return false;
  }
  return true;
}
