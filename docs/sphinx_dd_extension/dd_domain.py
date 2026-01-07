"""Sphinx plugin to add a data dictionary (DD) domain to sphinx.

Logic is partly based on code in the :external:py:mod:`sphinx.domains` module.
"""

from functools import partial
import logging
from pathlib import Path
import re
from typing import cast, Iterable, Optional, Dict, List, Tuple, Any

from docutils import nodes
from docutils.statemachine import StringList
from docutils.nodes import Element, Node
from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.addnodes import pending_xref
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.domains import Domain, ObjType
from sphinx.environment import BuildEnvironment
from sphinx.roles import XRefRole
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_id, make_refnode
from sphinx.util.typing import OptionSpec


logger = logging.getLogger(__name__)


_bracket_re = re.compile(r"\([^()]*\)")


def remove_brackets(value: str) -> str:
    """Remove brackets (and all contained in it) from value.

    Example:

        >>> remove_brackets("a(bcd)/e(fgh(ijk))/l")
        "a/e/l"
    """
    while True:
        value, substitions_done = _bracket_re.subn("", value)
        if substitions_done == 0:
            return value


def create_xref(node, reftarget, **attributes):
    """Helper to create pending_xref node representing :ref:`{text} <target>`."""
    return pending_xref(
        "",
        node,
        refdomain="std",
        reftype="ref",
        reftarget=reftarget,
        refexplicit=True,
        **attributes,
    )


def get_summary(content: StringList, n_char=60) -> str:
    """Create a summary string from the contents of a DD node"""
    needs_ellipsis = False
    # Get the first line of the contents
    if not content:
        return ""
    text = content[0]
    sentence_end = text.find(". ")
    if sentence_end != -1:
        text = text[: sentence_end + 1]
        needs_ellipsis = True
    # Only display first N_CHAR characters of the first sentence
    if len(text) > n_char:
        break_at_space = text.find(" ", n_char)
        if break_at_space != -1:
            text = text[:break_at_space]
            needs_ellipsis = True
    if needs_ellipsis:
        text = text + " [...]"
    return text


# Custom Sphinx directives
########################################################################################


class DDElement(SphinxDirective):
    """Directive to describe a Data Dictionary node."""

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False

    option_spec: OptionSpec = {
        "data_type": directives.unchanged,
        "has_error": directives.flag,
        "no_summary": directives.flag,
        "type": partial(
            directives.choice, values=("constant", "static", "dynamic", "")
        ),
        "units": directives.unchanged,
    }

    def run(self) -> List[Node]:
        # IDS name:
        prefix = self.env.ref_context.get("dd:ids")

        # Name
        name = self.arguments[0].strip()
        fullname = f"{prefix}/{name}" if prefix else name
        fullname = remove_brackets(fullname)

        # Options
        data_type = self.options.get("data_type")
        has_error = "has_error" in self.options
        typ = self.options.get("type")
        units = self.options.get("units")

        # Generate summary
        summary = ""
        if "no_summary" not in self.options:
            summary = get_summary(self.content)

        # Create DD Node
        node = DDNode(name, data_type, typ, units, summary, has_error)

        # Generate a unique ID:
        node_id = make_id(self.env, self.state.document, "", fullname)
        node["ids"].append(node_id)

        # Register with domain
        objtype = self.name.rsplit(":", 1)[-1]
        domain = cast(DDDomain, self.env.get_domain("dd"))
        domain.note_object(fullname, objtype, node_id, location=node)
        # Create an index node -- this seems not necessary
        # addnodes.index(entries=[("single", fullname, node_id, "", None)])

        # Parse contents
        content_node = nodes.container()
        self.state.nested_parse(self.content, 0, content_node)
        node += content_node.children

        return [node]


class _TopLevel(SphinxDirective):
    """Directive to mark the description of a Data Dictionary IDS/utility."""

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False

    refname = ""

    def run(self) -> List[Node]:
        """Run this directive.

        - Set the dd:ids context in the current document to the IDS name.
        - If :noindex: is not provided, an index entry for the IDS name is added that
          can be referred to with :dd:ids:`<ids_name>`.
        """
        domain = cast(DDDomain, self.env.get_domain("dd"))
        ids_name = self.arguments[0].strip()
        noindex = "noindex" in self.options
        self.env.ref_context["dd:ids"] = ids_name

        content_node = nodes.section()
        self.state.nested_parse(self.content, 0, content_node)

        ret = []
        if not noindex:
            # note ids to the domain
            node_id = make_id(self.env, self.state.document, self.refname, ids_name)
            target = nodes.target("", "", ids=[node_id])
            self.set_source_info(target)
            self.state.document.note_explicit_target(target)

            domain.note_object(ids_name, self.refname, node_id, location=target)
            ret.append(target)
            indextext = f"{self.refname}; {ids_name}"
            inode = addnodes.index(entries=[("pair", indextext, node_id, "", None)])
            ret.append(inode)
        ret.append(ExpandCollapseNode())
        ret.extend(content_node.children)
        return ret


class IDS(_TopLevel):
    """Directive to mark the description of a Data Dictionary IDS."""

    refname = "ids"


class Util(_TopLevel):
    """Directive to mark the description of a Data Dictionary utility node."""

    refname = "util"


class UtilReference(DDElement):
    """Directive to mark that a node is a reference to a utility struct."""

    has_content = False
    required_arguments = 2

    def run(self):
        self.options["data_type"] = "structure"
        self.options["no_summary"] = True
        self.content = StringList()
        reference = self.arguments.pop()
        self.content.append(
            f"See common IDS structure reference: :dd:util:`{reference}`.",
            *self.get_source_info(),
        )
        return super().run()


class DDIdentifier(SphinxDirective):
    """Directive to mark an identifier."""

    has_content = False
    required_arguments = 1
    optional_arguments = 0

    def run(self) -> List[Node]:
        """Run this directive."""
        domain = cast(DDDomain, self.env.get_domain("dd"))
        identifier_fname = self.arguments[0].strip()

        # note identifier to the domain
        node_id = make_id(self.env, self.state.document, "identifier", identifier_fname)
        target = nodes.target("", "", ids=[node_id])
        self.set_source_info(target)
        self.state.document.note_explicit_target(target)

        domain.note_object(identifier_fname, "identifier", node_id, location=target)
        indextext = f"identifier; {identifier_fname}"
        inode = addnodes.index(entries=[("pair", indextext, node_id, "", None)])

        return [target, inode]


class IDSXRefRole(XRefRole):
    """Extend standard cross-reference role to process tildes.

    :dd:node:`a/b/c` will display as "a/b/c", whereas :dd:node:`~a/b/c` will
    display as "c".
    """

    def process_link(
        self,
        env: BuildEnvironment,
        refnode: Element,
        has_explicit_title: bool,
        title: str,
        target: str,
    ) -> Tuple[str, str]:
        refnode["dd:ids"] = env.ref_context.get("dd:ids")
        # Process tildes, similar to the Python domain
        if not has_explicit_title:
            target = target.lstrip("~")  # only has a meaning for the title
            # if the first character is a tilde, only display the name
            if title.startswith("~"):
                title = title[1:].rsplit("/")[-1]
        return title, target


class IdentifierXRefRole(XRefRole):
    """Extend standard cross-reference role to process identifiers correctly."""

    def process_link(
        self,
        env: BuildEnvironment,
        refnode: Element,
        has_explicit_title: bool,
        title: str,
        target: str,
    ) -> Tuple[str, str]:
        if not has_explicit_title:
            title = Path(target).stem
        return title, target


# Custom Sphinx Domain
########################################################################################


class DDDomain(Domain):
    """Sphinx domain for the Data Dictionary."""

    name = "dd"
    label = "IMAS DD"
    object_types = {
        # IDSs
        "ids": ObjType("IDS", "ids"),
        # Utility structures
        "util": ObjType("utility", "util"),
        "util-ref": ObjType("utility", "util"),
        # IDS nodes
        "node": ObjType("node", "node"),
        # Data types
        "data_type": ObjType("data_type", "data_type"),
        # Identifiers
        "identifier": ObjType("identifier", "identifier"),
    }
    directives = {
        "ids": IDS,
        "util": Util,
        "util-ref": UtilReference,
        "node": DDElement,
        "data_type": DDElement,
        "identifier": DDIdentifier,
    }
    roles = {
        "ids": IDSXRefRole(),
        "util": IDSXRefRole(),
        "node": IDSXRefRole(),
        "data_type": IDSXRefRole(),
        "identifier": IdentifierXRefRole(),
    }
    initial_data = {
        "objects": {},  # fullname -> docname, node_id, objtype
    }

    @property
    def objects(self) -> Dict[str, Tuple[str, str, str]]:
        """Get all objects in the DD domain encountered so far.

        Returns:
            Dictionary mapping fullname -> document_name, node_id, object_type
        """
        return self.data.setdefault("objects", {})

    def note_object(
        self, fullname: str, objtype: str, node_id: str, location: Any = None
    ) -> None:
        """Register a new object to the DD domain."""
        fullname = fullname
        if fullname in self.objects:
            docname = self.objects[fullname][0]
            logger.warning(
                "duplicate object description of %s, other instance in %s"
                ", use :noindex: for one of them",
                fullname,
                docname,
            )
        self.objects[fullname] = (self.env.docname, node_id, objtype)
        if objtype == "identifier":
            # Allow to refer to the short name as well for identifiers
            shortname = Path(fullname).stem
            if shortname not in self.objects:
                self.objects[shortname] = (self.env.docname, node_id, objtype)

    # Implement methods that should be overwritten

    def clear_doc(self, docname: str) -> None:
        for fullname, (obj_docname, _node_id, _l) in list(self.objects.items()):
            if obj_docname == docname:
                del self.objects[fullname]

    def merge_domaindata(self, docnames: List[str], otherdata: dict) -> None:
        for fullname, (fn, node_id, objtype) in otherdata["objects"].items():
            if fn in docnames:
                self.objects[fullname] = (fn, node_id, objtype)

    def find_obj(
        self, ids_name: Optional[str], name: str, typ: Optional[str]
    ) -> Tuple[str, Optional[Tuple[str, str, str]]]:
        """Find the DD object for "name", using the given context IDS name."""
        name = remove_brackets(name)
        newname = f"{ids_name}/{name}" if ids_name and typ != "util" else name
        if newname in self.objects:
            obj = self.objects[newname]
        else:
            obj = self.objects.get(name)

        if obj is not None and typ is not None:
            objtypes = self.objtypes_for_role(typ)
            if objtypes is None or obj[2] not in objtypes:
                obj = None  # No match for this role

        return newname, obj

    def resolve_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        typ: str,
        target: str,
        node: pending_xref,
        contnode: Element,
    ) -> Optional[Element]:
        ids_name = node.get("dd:ids")
        name, obj = self.find_obj(ids_name, target, typ)
        if not obj:
            return None
        return make_refnode(builder, fromdocname, obj[0], obj[1], contnode, name)

    def resolve_any_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        target: str,
        node: pending_xref,
        contnode: Element,
    ) -> List[Tuple[str, Element]]:
        ids_name = node.get("dd:ids")
        name, obj = self.find_obj(ids_name, target, None)
        if not obj:
            return []
        return [
            f"dd:{self.role_for_objtype(obj[2])}",
            make_refnode(builder, fromdocname, obj[0], obj[1], contnode, name),
        ]

    def get_objects(self) -> Iterable[Tuple[str, str, str, str, str, int]]:
        for refname, (docname, node_id, typ) in list(self.objects.items()):
            # TODO: check which priority to use, currently 1 (default prio)
            yield refname, refname, typ, docname, node_id, 1

    def get_full_qualified_name(self, node: Element) -> Optional[str]:
        ids_name = node.get("dd:ids")
        target = node.get("reftarget")
        if target is None:
            return None
        return f"{ids_name}/{target}" if ids_name else target


# Custom docutils nodes
########################################################################################


class DDNode(nodes.Element):
    """Docutils node to represent a DD Element (structure, AoS, data element)."""

    def __init__(self, name, data_type, typ, units, summary, has_error):
        super().__init__("", classes=["dd"])
        # Create summary node
        self += DDSummary(self, name, data_type, typ, units, summary, has_error)


# Visitors of DDNode for HTML documentation:
def visit_ddnode(self, node: Element) -> None:
    self.body.append(self.starttag(node, "details"))


def depart_ddnode(self, node: Element) -> None:
    self.body.append("</details>\n\n")


class DDSummary(nodes.TextElement):
    """Docutils node to represent the summary of a DD Element."""

    def __init__(self, parent, name, data_type, typ, units, summary, has_error):
        super().__init__("", classes=["dd"])

        parts = name.rsplit("/", 1)
        if len(parts) > 1:
            self += nodes.Text(parts[0] + "/")
        self += nodes.inline(text=parts[-1], classes=["name"])

        if has_error:
            self += create_xref(nodes.Text(" ⇹"), "errorbars", classes=["errorbar"])

        if typ:
            # Note: actual text is added with CSS (::before)
            self += create_xref(nodes.inline(), f"type-{typ}", classes=[f"dd-{typ}"])

        if units:
            self += nodes.inline(text=units, classes=["dd_unit"])

        if data_type:
            if data_type in ("structure", "struct_array"):
                parent["classes"].append("dd-struct")
            data_type = {
                "str_type": "STR_0D",
                "str_1d_type": "STR_1D",
                "int_type": "INT_0D",
                "flt_type": "FLT_0D",
                "flt_1d_type": "FLT_1D",
                "cpx_type": "CPX_0D",
                "struct_array": "AoS",  # IMAS-5058: AoS in doc instead of struct_array
            }.get(data_type, data_type)
            self += pending_xref(
                "",
                nodes.Text(data_type),
                refdomain="dd",
                reftype="data_type",
                reftarget=data_type,
                classes=["dd_data_type"],
            )

        self += DDPermaLink()

        if summary:
            self += nodes.inline(text=summary, classes=["dd-summary"])


# Visitors of DDSummary for HTML documentation:
def visit_ddsummary(self, node: Element) -> None:
    self.body.append(self.starttag(node, "summary"))


def depart_ddsummary(self, node: Element) -> None:
    self.body.append("</summary>\n")


class DDPermaLink(nodes.Inline, nodes.Element):
    """Placeholder node for a permalink."""


# Visitors of DDPermaLink for HTML documentation:
def visit_ddpermalink(self, node: Element) -> None:
    self.add_permalink_ref(node.parent.parent, "Permalink to this node")


def depart_ddpermalink(self, node: Element) -> None:
    pass  # nothing to be done


class ExpandCollapseNode(nodes.Inline, nodes.Element):
    """Placeholder for expand/collapse all buttons."""


def visit_expandcollapsenode(self, node: Element) -> None:
    self.body.append(
        "<div class='dd-toggle'><a class='dd-expand' "
        'onclick=\'document.querySelectorAll("details").forEach('
        "(ele) => {ele.open = true;})'><span>+</span> Expand all</a>"
        "<a class='dd-collapse' "
        'onclick=\'document.querySelectorAll("details").forEach('
        "(ele) => {ele.open = false;})'><span>-</span> Collapse all</a></div>"
    )


def depart_expandcollapsenode(self, node: Element) -> None:
    pass  # nothing to be done


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_domain(DDDomain)
    app.add_node(DDNode, html=(visit_ddnode, depart_ddnode))
    app.add_node(DDSummary, html=(visit_ddsummary, depart_ddsummary))
    app.add_node(DDPermaLink, html=(visit_ddpermalink, depart_ddpermalink))
    app.add_node(
        ExpandCollapseNode, html=(visit_expandcollapsenode, depart_expandcollapsenode)
    )
    return {
        "version": "0.2",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
