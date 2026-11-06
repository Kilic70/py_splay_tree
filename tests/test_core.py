import unittest

from py_splay_tree import SplayTree, Node, EmptyTreeError


class TestSplayTree(unittest.TestCase):
    def test_empty_tree_behaviour(self):
        tree = SplayTree()
        self.assertEqual(len(tree), 0)
        self.assertFalse(tree)
        self.assertTrue(tree.is_empty())
        self.assertIsNone(tree.root_key())
        self.assertEqual(tree.height(), -1)
        with self.assertRaises(EmptyTreeError):
            tree.min()
        with self.assertRaises(EmptyTreeError):
            tree.max()
        with self.assertRaises(KeyError):
            tree.find(1)

    def test_insert_and_find(self):
        tree = SplayTree()
        tree.insert(10, "ten")
        tree.insert(5, "five")
        tree.insert(15, "fifteen")
        self.assertEqual(len(tree), 3)
        self.assertEqual(tree.find(10), "ten")
        self.assertEqual(tree.find(5), "five")
        self.assertEqual(tree.find(15), "fifteen")
        self.assertEqual(tree.root_key(), 15)
        self.assertIn(10, tree)
        self.assertNotIn(99, tree)

    def test_insert_replaces_existing_value(self):
        tree = SplayTree()
        tree.insert(1, "one")
        tree.insert(1, "uno")
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree.find(1), "uno")

    def test_insert_without_value_defaults_to_none(self):
        tree = SplayTree()
        tree.insert(7)
        self.assertIsNone(tree.find(7))

    def test_ordered_iteration(self):
        tree = SplayTree()
        for key in [5, 3, 8, 1, 4, 7, 9]:
            tree.insert(key, key * 10)
        self.assertEqual(list(tree), [1, 3, 4, 5, 7, 8, 9])

    def test_min_and_max_splay(self):
        tree = SplayTree()
        for key in [5, 3, 8, 1, 4, 7, 9]:
            tree.insert(key, key)
        self.assertEqual(tree.min(), (1, 1))
        self.assertEqual(tree.root_key(), 1)
        self.assertEqual(tree.max(), (9, 9))
        self.assertEqual(tree.root_key(), 9)

    def test_delete_returns_value_and_shrinks(self):
        tree = SplayTree()
        for key in [5, 3, 8, 1, 4, 7, 9]:
            tree.insert(key, key * 100)
        self.assertEqual(tree.delete(4), 400)
        self.assertEqual(len(tree), 6)
        self.assertNotIn(4, tree)
        self.assertEqual(list(tree), [1, 3, 5, 7, 8, 9])

    def test_delete_missing_key_raises(self):
        tree = SplayTree()
        tree.insert(1, "one")
        with self.assertRaises(KeyError):
            tree.delete(2)
        self.assertEqual(len(tree), 1)

    def test_discard(self):
        tree = SplayTree()
        tree.insert(1, "one")
        self.assertTrue(tree.discard(1))
        self.assertFalse(tree.discard(1))
        self.assertTrue(tree.is_empty())

    def test_delete_all_nodes(self):
        tree = SplayTree()
        for key in range(10):
            tree.insert(key, key)
        for key in range(10):
            tree.delete(key)
        self.assertTrue(tree.is_empty())
        self.assertEqual(len(tree), 0)

    def test_split(self):
        tree = SplayTree()
        for key in [1, 2, 3, 4, 5]:
            tree.insert(key, key)
        left, right = tree.split(3)
        self.assertEqual(list(left), [1, 2])
        self.assertEqual(list(right), [3, 4, 5])
        self.assertTrue(tree.is_empty())

    def test_split_below_all(self):
        tree = SplayTree()
        for key in [10, 20, 30]:
            tree.insert(key, key)
        left, right = tree.split(5)
        self.assertEqual(list(left), [])
        self.assertEqual(list(right), [10, 20, 30])

    def test_split_above_all(self):
        tree = SplayTree()
        for key in [10, 20, 30]:
            tree.insert(key, key)
        left, right = tree.split(99)
        self.assertEqual(list(left), [10, 20, 30])
        self.assertEqual(list(right), [])

    def test_merge(self):
        left = SplayTree()
        for key in [1, 2, 3]:
            left.insert(key, key)
        right = SplayTree()
        for key in [4, 5, 6]:
            right.insert(key, key)
        left.merge(right)
        self.assertEqual(list(left), [1, 2, 3, 4, 5, 6])
        self.assertTrue(right.is_empty())

    def test_merge_with_empty(self):
        left = SplayTree()
        left.insert(1, "one")
        right = SplayTree()
        left.merge(right)
        self.assertEqual(list(left), [1])
        self.assertTrue(right.is_empty())

    def test_merge_into_empty(self):
        left = SplayTree()
        right = SplayTree()
        right.insert(2, "two")
        left.merge(right)
        self.assertEqual(list(left), [2])
        self.assertTrue(right.is_empty())

    def test_merge_self_raises(self):
        tree = SplayTree()
        tree.insert(1, "one")
        with self.assertRaises(ValueError):
            tree.merge(tree)

    def test_clear(self):
        tree = SplayTree()
        for key in range(5):
            tree.insert(key, key)
        tree.clear()
        self.assertTrue(tree.is_empty())
        self.assertEqual(len(tree), 0)

    def test_get(self):
        tree = SplayTree()
        tree.insert(1, "one")
        self.assertEqual(tree.get(1), "one")
        self.assertIsNone(tree.get(2))
        self.assertEqual(tree.get(2, "missing"), "missing")

    def test_height(self):
        tree = SplayTree()
        self.assertEqual(tree.height(), -1)
        tree.insert(1, "one")
        self.assertEqual(tree.height(), 0)
        tree.insert(2, "two")
        self.assertEqual(tree.height(), 1)

    def test_node_repr(self):
        node = Node(1, "one")
        self.assertEqual(repr(node), "Node(key=1, value='one')")


if __name__ == "__main__":
    unittest.main()
