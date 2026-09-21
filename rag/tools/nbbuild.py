"""Tiny helper: build and execute a notebook from (kind, source) pairs."""
import os
import sys
import nbformat
from nbclient import NotebookClient


def build(cells, path, run_dir):
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_markdown_cell(src) if kind == "md"
        else nbformat.v4.new_code_cell(src)
        for kind, src in cells
    ]
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3", "language": "python", "name": "python3"}
    client = NotebookClient(nb, timeout=1800, kernel_name="python3",
                            resources={"metadata": {"path": run_dir}})
    client.execute()
    with open(path, "w") as fh:
        nbformat.write(nb, fh)
    # surface failures loudly
    bad = []
    for i, c in enumerate(nb.cells):
        for o in (c.get("outputs") or []):
            if o.get("output_type") == "error":
                bad.append((i, o.get("ename"), (o.get("evalue") or "")[:400]))
    return bad
