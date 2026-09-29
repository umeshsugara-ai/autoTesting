import tempfile, pathlib
from crawl_fake import crawl_it, make_project
from autotester.schema.enums import WritePolicy
from autotester.schema.crawl import SafetyPolicy
from autotester.stages.explore_safety import is_destructive
for wp in (WritePolicy.ALLOW_WRITES,):
    tmp = pathlib.Path(tempfile.mkdtemp())
    proj = make_project(wp)
    crawl, store, page = crawl_it(tmp, project=proj, policy=SafetyPolicy(write_policy=wp))
    nodes = {n.id: n for n in store.list_nodes(crawl.id)}
    els = {(n.id, e.selector): e for n in nodes.values() for e in n.elements}
    print("policy", wp.value)
    for i, e in enumerate(store.list_edges(crawl.id)):
        el = els.get((e.from_node, e.target))
        d = is_destructive(el, SafetyPolicy()) if el else None
        print(i, nodes[e.from_node].url_template, e.target, e.outcome.value, "DESTRUCTIVE" if d else "")
