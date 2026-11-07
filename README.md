# py_splay_tree

A splay tree: a binary search tree that moves the node you just touched to the root, so frequently accessed keys stay near the top.

```python
from py_splay_tree import SplayTree

tree = SplayTree()
tree.insert(10, "ten")
tree.insert(5, "five")
tree.insert(15, "fifteen")

assert tree.find(5) == "five"
assert tree.root_key() == 5

left, right = tree.split(10)
assert list(left) == [5]
assert list(right) == [10, 15]

left.merge(right)
assert list(left) == [5, 10, 15]
```

The module also exports `Node` (the internal node type, useful if you want to walk the tree yourself) and `EmptyTreeError`, raised by `min` and `max` on an empty tree.

## Why this exists

Most balanced trees rebalance on every update, which is the right trade-off when reads and writes are equally common. Splay trees instead do work only when you access a key, and they exploit locality of reference: if you look up the same few keys repeatedly, those keys migrate to the root and the tree stays cheap for that pattern. The cost is that a single unlucky lookup can be O(n), and the tree is not read-only thread-safe — every access mutates the shape.

I picked bottom-up splaying with explicit parent pointers over the shorter top-down formulation. It costs a few extra pointer writes per rotation, but it keeps `split` and `merge` straightforward, which are the operations I actually needed. If you only ever call `find`, a top-down splay would be faster.

## Edge cases worth knowing

`find` on a missing key still splays the last node visited on the search path. That is the standard behaviour and it is usually what you want, but it means a failed lookup is not free and it does change the tree shape. If you need a lookup that leaves the tree alone, walk it yourself starting from `root_key()`.

`split` empties the original tree and returns two new trees. `merge` requires every key in the right-hand tree to be strictly greater than every key in the left-hand tree; it does not check this, and a bad merge will produce a tree that violates the BST invariant. `merge` also refuses to merge a tree with itself.

Keys must be comparable with `<` and `==`. Values default to `None` when you insert without one, so `find` on a key inserted as `tree.insert(k)` returns `None` rather than raising.
