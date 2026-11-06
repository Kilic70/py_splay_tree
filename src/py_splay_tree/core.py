"""A splay tree implementation in pure Python.

The tree stores unique comparable keys and, optionally, associated values.
Splaying is performed bottom-up with a parent pointer, which keeps the
rotations explicit and makes the amortised analysis easy to follow.

Why a parent pointer?  The classic top-down splay is shorter but harder to
extend with operations such as ``split`` and ``merge``.  Bottom-up splaying
costs a little more per operation in constant factors, but the code stays
close to the textbook description and the invariants are obvious.
"""

from __future__ import annotations

from typing import Any, Generic, Iterator, Optional, Tuple, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class EmptyTreeError(IndexError):
    """Raised when an operation requires a non-empty tree."""


class Node(Generic[K, V]):
    """A single node in the splay tree.

    Exposed because callers occasionally want to walk the tree manually
    without paying for the splay operations.  Direct mutation is not part
    of the public contract; use :class:`SplayTree` methods instead.
    """

    __slots__ = ("key", "value", "left", "right", "parent")

    def __init__(
        self,
        key: K,
        value: Optional[V] = None,
        parent: Optional["Node[K, V]"] = None,
    ) -> None:
        self.key = key
        self.value = value
        self.left: Optional[Node[K, V]] = None
        self.right: Optional[Node[K, V]] = None
        self.parent: Optional[Node[K, V]] = parent

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Node(key={self.key!r}, value={self.value!r})"


class SplayTree(Generic[K, V]):
    """A self-adjusting binary search tree.

    Keys must be comparable with ``<`` and ``==``.  Values are optional; if
    no value is supplied the stored value is simply the key itself, which
    makes the tree usable as a plain ordered set.

    All mutating methods splay the accessed node to the root, so the most
    recently touched key is always at the root.  This is the property that
    gives splay trees their amortised logarithmic behaviour on skewed
    access patterns.
    """

    __slots__ = ("_root", "_size")

    def __init__(self) -> None:
        self._root: Optional[Node[K, V]] = None
        self._size = 0

    # ------------------------------------------------------------------
    # Basic container protocol
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: object) -> bool:
        try:
            self.find(key)  # type: ignore[arg-type]
            return True
        except KeyError:
            return False

    def __iter__(self) -> Iterator[K]:
        """Yield keys in ascending order.

        Iteration does not splay; otherwise a full scan would reorganise
        the tree in surprising ways.  The iterator is a generator over the
        ordinary in-order traversal.
        """
        stack: list[Node[K, V]] = []
        node = self._root
        while stack or node is not None:
            while node is not None:
                stack.append(node)
                node = node.left
            node = stack.pop()
            yield node.key
            node = node.right

    def __bool__(self) -> bool:
        return self._root is not None

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def find(self, key: K) -> V:
        """Return the value stored under *key*.

        Raises :class:`KeyError` if the key is absent.  The last node
        visited on the search path is splayed to the root even on a miss,
        which is the standard splay-tree behaviour and keeps the tree
        responsive to near-miss accesses.
        """
        node = self._find_node(key)
        if node is None or node.key != key:
            raise KeyError(key)
        self._splay(node)
        return node.value  # type: ignore[return-value]

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Return the value for *key*, or *default* if absent."""
        try:
            return self.find(key)
        except KeyError:
            return default

    def min(self) -> Tuple[K, V]:
        """Return the smallest key and its value."""
        if self._root is None:
            raise EmptyTreeError("min() on empty tree")
        node = self._root
        while node.left is not None:
            node = node.left
        self._splay(node)
        return node.key, node.value  # type: ignore[return-value]

    def max(self) -> Tuple[K, V]:
        """Return the largest key and its value."""
        if self._root is None:
            raise EmptyTreeError("max() on empty tree")
        node = self._root
        while node.right is not None:
            node = node.right
        self._splay(node)
        return node.key, node.value  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def insert(self, key: K, value: Optional[V] = None) -> None:
        """Insert *key* with *value*.

        If the key already exists its value is replaced.  The inserted or
        updated node is splayed to the root.
        """
        if self._root is None:
            self._root = Node(key, value)
            self._size = 1
            return

        node = self._find_node(key)
        assert node is not None
        if node.key == key:
            node.value = value
            self._splay(node)
            return

        new_node = Node(key, value, parent=node)
        if key < node.key:
            node.left = new_node
        else:
            node.right = new_node
        self._size += 1
        self._splay(new_node)

    def delete(self, key: K) -> V:
        """Remove *key* and return its value.

        Raises :class:`KeyError` if the key is absent.  The parent of the
        removed node is splayed, which is the conventional replacement for
        splaying the deleted node itself.
        """
        node = self._find_node(key)
        if node is None or node.key != key:
            if node is not None:
                self._splay(node)
            raise KeyError(key)

        value = node.value
        self._splay(node)
        self._delete_root()
        return value  # type: ignore[return-value]

    def discard(self, key: K) -> bool:
        """Remove *key* if present.  Returns whether anything was removed."""
        try:
            self.delete(key)
            return True
        except KeyError:
            return False

    def clear(self) -> None:
        """Remove every node."""
        self._root = None
        self._size = 0

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def split(self, key: K) -> Tuple["SplayTree[K, V]", "SplayTree[K, V]"]:
        """Split into a tree of keys ``< key`` and a tree of keys ``>= key``.

        The original tree is emptied.  The split is performed by splaying
        the largest key strictly less than *key* (or the smallest key
        otherwise) and detaching the appropriate child.
        """
        left_tree: SplayTree[K, V] = SplayTree()
        right_tree: SplayTree[K, V] = SplayTree()

        if self._root is None:
            return left_tree, right_tree

        # Splay the node with the largest key < key, if any.
        node = self._root
        candidate: Optional[Node[K, V]] = None
        while node is not None:
            if node.key < key:
                candidate = node
                node = node.right
            else:
                node = node.left

        if candidate is None:
            # Every key is >= key.
            right_tree._root = self._root
            right_tree._size = self._size
            self._root = None
            self._size = 0
            return left_tree, right_tree

        self._splay(candidate)
        assert self._root is candidate
        right_child = candidate.right
        candidate.right = None
        if right_child is not None:
            right_child.parent = None

        left_tree._root = candidate
        left_tree._size = self._size - self._count(right_child)
        right_tree._root = right_child
        right_tree._size = self._count(right_child)

        self._root = None
        self._size = 0
        return left_tree, right_tree

    def merge(self, other: "SplayTree[K, V]") -> None:
        """Merge *other* into this tree, emptying *other*.

        All keys in *other* must be strictly greater than every key in
        this tree.  The merge splays the maximum of this tree and attaches
        *other* as its right child.
        """
        if other is self:
            raise ValueError("cannot merge a tree with itself")
        if other._root is None:
            return
        if self._root is None:
            self._root = other._root
            self._size = other._size
            other._root = None
            other._size = 0
            return

        node = self._root
        while node.right is not None:
            node = node.right
        self._splay(node)
        assert self._root is node
        node.right = other._root
        other._root.parent = node
        self._size += other._size
        other._root = None
        other._size = 0

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    def root_key(self) -> Optional[K]:
        """Return the key at the root, or ``None`` for an empty tree."""
        return None if self._root is None else self._root.key

    def height(self) -> int:
        """Return the height of the tree (0 for a single node, -1 for empty)."""
        return self._height(self._root)

    def is_empty(self) -> bool:
        return self._root is None

    # ------------------------------------------------------------------
    # Internal machinery
    # ------------------------------------------------------------------

    def _find_node(self, key: K) -> Optional[Node[K, V]]:
        """Return the last node visited while searching for *key*.

        The returned node may not match *key*; callers must compare.
        """
        node = self._root
        last: Optional[Node[K, V]] = None
        while node is not None:
            last = node
            if key < node.key:
                node = node.left
            elif node.key < key:
                node = node.right
            else:
                return node
        return last

    def _splay(self, node: Node[K, V]) -> None:
        """Rotate *node* to the root using bottom-up splaying."""
        while node.parent is not None:
            parent = node.parent
            grand = parent.parent
            if grand is None:
                if node is parent.left:
                    self._rotate_right(parent)
                else:
                    self._rotate_left(parent)
            elif node is parent.left and parent is grand.left:
                self._rotate_right(grand)
                self._rotate_right(parent)
            elif node is parent.right and parent is grand.right:
                self._rotate_left(grand)
                self._rotate_left(parent)
            elif node is parent.right and parent is grand.left:
                self._rotate_left(parent)
                self._rotate_right(grand)
            else:  # node is parent.left and parent is grand.right
                self._rotate_right(parent)
                self._rotate_left(grand)
        self._root = node

    def _rotate_left(self, node: Node[K, V]) -> None:
        right = node.right
        assert right is not None
        node.right = right.left
        if right.left is not None:
            right.left.parent = node
        right.parent = node.parent
        if node.parent is None:
            self._root = right
        elif node is node.parent.left:
            node.parent.left = right
        else:
            node.parent.right = right
        right.left = node
        node.parent = right

    def _rotate_right(self, node: Node[K, V]) -> None:
        left = node.left
        assert left is not None
        node.left = left.right
        if left.right is not None:
            left.right.parent = node
        left.parent = node.parent
        if node.parent is None:
            self._root = left
        elif node is node.parent.left:
            node.parent.left = left
        else:
            node.parent.right = left
        left.right = node
        node.parent = left

    def _delete_root(self) -> None:
        """Remove the current root, which is assumed to be splayed."""
        root = self._root
        assert root is not None
        left = root.left
        right = root.right
        if left is None:
            self._root = right
            if right is not None:
                right.parent = None
        elif right is None:
            self._root = left
            left.parent = None
        else:
            # Splay the maximum of the left subtree, then attach the right
            # subtree as its right child.  This keeps the BST invariant
            # without needing a separate join routine.
            node = left
            while node.right is not None:
                node = node.right
            self._root = left
            left.parent = None
            self._splay(node)
            assert self._root is node
            node.right = right
            right.parent = node
        self._size -= 1

    @staticmethod
    def _count(node: Optional[Node[K, V]]) -> int:
        if node is None:
            return 0
        return 1 + SplayTree._count(node.left) + SplayTree._count(node.right)

    @staticmethod
    def _height(node: Optional[Node[K, V]]) -> int:
        if node is None:
            return -1
        return 1 + max(SplayTree._height(node.left), SplayTree._height(node.right))
