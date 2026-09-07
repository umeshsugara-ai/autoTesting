// Enumerate interactive elements on the current page. Loaded by
// browser/observe.py via page.evaluate(). Returns an array of
// {role, name, selector, enabled, visible, href, is_form_submit, in_row,
// target_blank, tag} objects, one per interactive element found.
//
// Selector priority: data-testid > a stable (non-generated-looking) #id >
// [aria-label] > a role+name locator with an nth index > an xpath fallback.
// "in_row" excludes an element from screen-identity's structural signature
// (Track B2) when it sits inside a table row / list item with siblings --
// two list pages differing only in row data should be one screen.
(() => {
  function isVisible(el) {
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) return false;
    const style = window.getComputedStyle(el);
    return style.visibility !== "hidden" && style.display !== "none";
  }

  function roleOf(el) {
    const explicit = el.getAttribute("role");
    if (explicit) return explicit;
    const tag = el.tagName.toLowerCase();
    if (tag === "a" && el.hasAttribute("href")) return "link";
    if (tag === "button") return "button";
    if (tag === "input") {
      const type = (el.getAttribute("type") || "text").toLowerCase();
      if (type === "submit" || type === "button") return "button";
      if (type === "checkbox") return "checkbox";
      if (type === "radio") return "radio";
      return "textbox";
    }
    if (tag === "select") return "combobox";
    if (tag === "textarea") return "textbox";
    if (el.hasAttribute("onclick") || el.tabIndex >= 0) return "button";
    return tag;
  }

  function nameOf(el) {
    const ariaLabel = el.getAttribute("aria-label");
    if (ariaLabel) return ariaLabel.trim();
    const labelledBy = el.getAttribute("aria-labelledby");
    if (labelledBy) {
      const ref = document.getElementById(labelledBy);
      if (ref && ref.innerText) return ref.innerText.trim().slice(0, 60);
    }
    const title = el.getAttribute("title");
    if (title) return title.trim();
    const text = (el.innerText || "").trim();
    if (text) return text.slice(0, 60);
    const alt = el.querySelector && el.querySelector("img[alt]");
    if (alt) return alt.getAttribute("alt").trim();
    const value = el.getAttribute("value");
    if (value) return value.trim();
    return "";
  }

  function isGeneratedId(id) {
    return /^[0-9]+$/.test(id) || /[0-9a-f]{8}/.test(id) || id.length > 40;
  }

  const seen = new Map(); // role|name -> count, for nth disambiguation
  function selectorFor(el, role, name) {
    const testId = el.getAttribute("data-testid");
    if (testId) return `[data-testid="${testId}"]`;
    if (el.id && !isGeneratedId(el.id)) return `#${el.id}`;
    const ariaLabel = el.getAttribute("aria-label");
    if (ariaLabel) return `[aria-label="${ariaLabel}"]`;
    const key = `${role}|${name}`;
    const nth = seen.get(key) || 0;
    seen.set(key, nth + 1);
    if (name) return `role=${role}[name="${name}"] >> nth=${nth}`;
    // last resort: an xpath by tag + index among same-tag siblings
    let path = "";
    let node = el;
    while (node && node.nodeType === 1 && node !== document.body) {
      let index = 1;
      let sibling = node.previousElementSibling;
      while (sibling) {
        if (sibling.tagName === node.tagName) index += 1;
        sibling = sibling.previousElementSibling;
      }
      path = `/${node.tagName.toLowerCase()}[${index}]${path}`;
      node = node.parentElement;
    }
    return `xpath=/html/body${path}`;
  }

  function inRow(el) {
    let node = el.parentElement;
    let depth = 0;
    while (node && depth < 6) {
      const tag = node.tagName.toLowerCase();
      const role = node.getAttribute("role");
      if (tag === "tr" || tag === "li" || role === "row" || role === "listitem") {
        const siblingCount = node.parentElement ? node.parentElement.children.length : 0;
        return siblingCount > 3;
      }
      node = node.parentElement;
      depth += 1;
    }
    return false;
  }

  const SELECTOR = "a, button, input, select, textarea, [onclick], [tabindex]";
  const elements = Array.from(document.querySelectorAll(SELECTOR));
  const out = [];
  for (const el of elements) {
    const role = roleOf(el);
    const name = nameOf(el);
    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute("type") || "").toLowerCase();
    out.push({
      role: role,
      name: name,
      selector: selectorFor(el, role, name),
      enabled: !el.disabled,
      visible: isVisible(el),
      href: el.getAttribute("href") || null,
      is_form_submit: tag === "button" && (type === "" || type === "submit") &&
        !!el.closest("form") || (tag === "input" && type === "submit"),
      in_row: inRow(el),
      target_blank: el.getAttribute("target") === "_blank",
      tag: tag,
    });
  }
  return out;
})();
