"""Sphinx plugin to generate a changelog of the DD and add it to sphinx.
Logic is partly based on code in the :external:py:mod:`sphinx.domains` module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from git import Repo, Tag
from packaging.version import Version

import os

from sphinx.application import Sphinx
from sphinx.util import logging

logger = logging.getLogger(__name__)
try:
    is_gitrepo = True
    repo = Repo("..")
except Exception as _:
    logger.error(
        "git repo is not present, Data Dictionary changelog will not be generated"
    )
    is_gitrepo = False

try:
    from imas import IDSFactory
    from imas.dd_zip import dd_xml_versions
    from imas.ids_convert import DDVersionMap

    has_imaspy = True
except ImportError:
    logger.error("IMASPy is not available, IDS migration guide will not be generated")
    has_imaspy = False


def heading(s: str, style="-"):
    return f"{s}\n{style * len(s)}\n\n"


def tag_sort_helper(tag: Tag):
    parts = tag.name.split(".")
    return tuple(map(int, parts))


def sort_tags(list_of_tags: List[Tag]):
    return sorted(list_of_tags, key=tag_sort_helper)


def ids_changes(ids_name: str, from_factory, to_factory):
    added: list[str] = []
    removed: list[str] = []
    renamed: list[tuple[str, str]] = []
    retyped: list[tuple[str, str, str]] = []
    version_map = DDVersionMap(
        ids_name, from_factory._etree, to_factory._etree, Version(from_factory.version)
    )
    for f, t in version_map.old_to_new.path.items():
        if f.endswith(("_error_index", "_error_upper", "_error_lower")):
            continue
        if t is None:
            removed.append(f)
        elif f in version_map.old_to_new.type_change:
            # DD3 -> DD4 specific conversion
            if f == "ids_properties/source" and t == "ids_properties/provenance":
                renamed.append((f, t))
                continue
            from_data_type = from_factory._etree.find(f".//field[@path='{f}']").get(
                "data_type"
            )
            to_data_type = to_factory._etree.find(f".//field[@path='{t}']").get(
                "data_type"
            )
            retyped.append((f, from_data_type, to_data_type))
        else:
            renamed.append((f, t))

    for f, t in version_map.new_to_old.path.items():
        if f.endswith(("_error_index", "_error_upper", "_error_lower")):
            continue
        if t is None and f not in version_map.new_to_old.type_change:
            added.append(f)
    return added, removed, renamed, retyped


def indent(s, i):
    output = ""
    for line in s.split("\n"):
        if len(line) > 0:
            output += f"{' ' * i}{line}\n"
        else:
            output += "\n"
    return output


class TreeNode:
    def __init__(self, name="root_node"):
        self.children: dict[str, TreeNode] = {}
        self.name = name

    def add_path(self, path: str, postfix=""):
        split_path = path.split("/", maxsplit=1)
        if len(split_path) == 2:
            name, remaining_path = split_path
            self.children.setdefault(name, TreeNode(name))
            self.children[name].add_path(remaining_path, postfix)
        else:
            name = split_path[0]
            self.children.setdefault(name, TreeNode(name + postfix))

    def __repr__(self) -> str:
        return self.__str__()

    def _str(self, output="", prefix="", child_prefix=""):
        output = prefix + self.name + "\n"
        if self.name == "root_node":
            output = ""
        for i, child in enumerate(self.children.values()):
            if i == len(self.children) - 1:
                gen_prefix = child_prefix + "└─"
                gen_child_prefix = child_prefix + "  "
            else:
                gen_prefix = child_prefix + "├─"
                gen_child_prefix = child_prefix + "│ "
            output += child._str(output, gen_prefix, child_prefix=gen_child_prefix)
        return output

    def __str__(self):
        return self._str()


def get_relative_path(a: str, b: str):
    return os.path.relpath(b, a)


def to_tree_renamed(a: list[str]):
    output = ".. code-block:: \n\n"
    t = TreeNode()
    for i, j in sorted(a):
        t.add_path(i, f" → {'/'.join(get_relative_path(i, j).split('/')[1:])}")
    output += indent(str(t), 4)
    return output


def to_tree_retyped(a: list[str]):
    output = ".. code-block:: \n\n"
    t = TreeNode()
    for i, j, k in sorted(a):
        t.add_path(i, f": {j} → {k}")
    output += indent(str(t), 4)
    return output


def to_tree(a: list[str]):
    output = ".. code-block:: \n\n"
    t = TreeNode()
    a.sort()
    for i in a:
        t.add_path(i)
    output += indent(str(t), 4)
    return output


def format_renamed(renamed):
    output = ".. code-block:: \n\n"
    for f, t in renamed:
        output += indent(f"{f} -> {t}", 4)
    return output


def generate_dd_changelog(app: Sphinx):
    if not app.config.dd_changelog_generate:
        logger.warning(
            "Not generating DD changelog sources (dd_changelog_generate=False)"
        )
        return

    docfile = Path("generated/changelog/ids.rst")
    docfile.unlink(True)

    if not has_imaspy:
        docfile.write_text(
            heading("IDS migration guide <MISSING>", "=")
            + "ImportError: Could not import ``imaspy``."
        )

    logger.info("Generating DD ids migration guide sources.")

    # Ensure output folders exist
    (Path("generated/changelog/ids_changes")).mkdir(parents=True, exist_ok=True)

    my_ids_xml = "../IDSDef.xml"

    factory = IDSFactory(xml_path=my_ids_xml)

    versions = [
        x.name
        for x in reversed(sort_tags(repo.tags))
        if x.name != factory.version and x.name in dd_xml_versions()
    ]

    output = heading("IDS migration guide", "#")
    output += heading(f"IDS migration guide to: {factory.version}", "=")
    output += f"Below you can find all changes the current ({factory.version})"
    output += " and a specific old DD version\n\n"

    output += ".. toctree::\n   :maxdepth: 1\n   :caption: DD versions\n\n"

    for version in versions:
        version_docfile = Path(f"generated/changelog/ids_changes/{version}.rst")

        version_docfile.unlink(True)

        text = ""

        from_factory = IDSFactory(version)

        added_ids = set(factory).difference(from_factory)
        removed_ids = set(from_factory).difference(factory)

        text += heading(version, style="=")
        text += (
            f"On this page, all IDS changes between DD version {from_factory.version}"
            f" and version {factory.version} are shown\n\n"
        )
        for i in added_ids:
            text += heading(f"NEW IDS: {i}")
        for i in removed_ids:
            text += heading(f"REMOVED IDS: {i}")

        for i in set(factory).intersection(set(from_factory)):
            added, removed, renamed, retyped = ids_changes(i, from_factory, factory)
            if (
                len(added) > 0
                or len(removed) > 0
                or len(renamed) > 0
                or len(retyped) > 0
            ):
                text += heading(i)
            if len(added) > 0:
                text += heading("Added", "*")
                text += to_tree(added)
                text += "\n"
            if len(removed) > 0:
                text += heading("Removed", "*")
                text += to_tree(removed)
                text += "\n"
            if len(renamed) > 0:
                text += heading("Renamed", "*")
                text += to_tree_renamed(renamed)
                text += "\n"
            if len(retyped) > 0:
                text += heading("Type changed", "*")
                text += to_tree_retyped(retyped)
                text += "\n"

        with open(version_docfile, "w") as f:
            f.write(text)

        output += f"   ids_changes/{version}\n"

    with open(docfile, "w") as f:
        f.write(output)


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_config_value("dd_changelog_generate", True, "env", [bool])
    if has_imaspy:
        app.connect("builder-inited", generate_dd_changelog)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
