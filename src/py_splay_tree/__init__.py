"""Public API for py_splay_tree.

Only a handful of names are re-exported here so that ``from
py_splay_tree import SplayTree`` is enough for typical usage.
"""

from .core import SplayTree, Node, EmptyTreeError

__all__ = ["SplayTree", "Node", "EmptyTreeError"]
