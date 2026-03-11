from typing import List, Dict, Any, Union, Tuple, Optional, overload, Literal
from math import ceil


class BPlusTreeNode:
    def __init__(self, leaf: bool = False) -> None:
        self.leaf: bool = leaf
        self.values: List[Dict[str, Any]] = []
        self.children: List[BPlusTreeNode] = []
        self.keys: List[int] = []  # stored in sorted order.
        self.next: Union[BPlusTreeNode, None] = None
        self.prev: Union[BPlusTreeNode, None] = None
        self.parent: Optional[BPlusTreeNode] = None
        """
        Eg. degree = 5
        keys:     [   k1    k2    k3    k4   ]
        children: [c1    c2    c3    c4    c5]
        """


"""
Assumption:
our b+tree has a doubly linked list to traverse in both directions.
"""


class BPlusTree:
    def __init__(self, primary_key: str, degree: int) -> None:
        self.degree = degree
        self.root = BPlusTreeNode(leaf=True)
        self.primary_key = primary_key

    def search(self, key: int):
        return self._search(key, False)

    @overload
    def _search(
        self, key: int, get_node: Literal[False]
    ) -> Optional[Dict[str, Any]]: ...

    @overload
    def _search(
        self, key: int, get_node: Literal[True]
    ) -> Tuple["BPlusTreeNode", Union[int, None]]: ...
    def _search(self, key: int, get_node: bool = False) -> Any:
        cur = self.root
        while not cur.leaf:
            loc = self._find_index(key, cur.keys)
            cur = cur.children[loc]

        for idx, k in enumerate(cur.keys):
            if k == key:
                return cur.values[idx] if not get_node else (cur, idx)

        return None if not get_node else (cur, None)

    def _find_index(self, key: int, keys: List[int]):
        for i, k in enumerate(keys):
            if k >= key:
                return (i + 1) if k == key else i
        return len(keys)

    def update(self, key: int, new_value: Dict[str, Any]):
        cur, idx = self._search(key, get_node=True)
        if idx is None:
            raise ValueError("No such primary key entry found")
        if new_value[self.primary_key] != key:
            raise ValueError("Tried to change the primary key???")
        cur.values[idx] = new_value
        return

    def insert(self, key: int, value: Dict[str, Any]):
        cur, idx = self._search(key, get_node=True)
        if idx is not None:
            raise ValueError("Tried to modify an existing primary key")
        else:
            j = len(cur.keys)
            for i in range(len(cur.keys)):
                if cur.keys[i] > key:
                    j = i
                    break
            cur.keys.insert(j, key)
            cur.values.insert(j, value)
            if len(cur.keys) >= self.degree:
                # need to split -> split at middle, recursive splittt!!!1 need to handle linked ist too.
                self._split_node(cur)

    def _split_node(self, node: BPlusTreeNode):
        if node.leaf:
            left_node = BPlusTreeNode(True)
            right_node = BPlusTreeNode(True)
            left_node.prev = node.prev
            left_node.next = right_node
            right_node.next = node.next
            right_node.prev = left_node
            if node.prev is not None:
                node.prev.next = left_node
            if node.next is not None:
                node.next.prev = right_node
            mid = len(node.keys) // 2
            left_node.keys = node.keys[:mid]
            left_node.values = node.values[:mid]
            right_node.keys = node.keys[mid:]
            right_node.values = node.values[mid:]

            if node.parent is None:
                # this is the root
                new_root = BPlusTreeNode(False)
                new_root.children = [left_node, right_node]
                new_root.keys = [node.keys[mid]]
                left_node.parent = new_root
                right_node.parent = new_root
                self.root = new_root
            else:
                parent = node.parent
                node_idx = parent.children.index(node)
                parent.children[node_idx] = left_node
                parent.children.insert(node_idx + 1, right_node)
                parent.keys.insert(node_idx, right_node.keys[0])
                left_node.parent = parent
                right_node.parent = parent
                if len(parent.keys) >= self.degree:
                    self._split_node(parent)
        else:

            left_node = BPlusTreeNode(False)
            right_node = BPlusTreeNode(False)
            mid = len(node.keys) // 2

            left_node.keys = node.keys[:mid]
            left_node.children = node.children[: mid + 1]
            for child in left_node.children:
                child.parent = left_node

            right_node.keys = node.keys[mid + 1 :]
            right_node.children = node.children[mid + 1 :]
            for child in right_node.children:
                child.parent = right_node

            if node.parent is None:
                # root will split
                new_root = BPlusTreeNode(False)
                new_root.keys = [node.keys[mid]]
                new_root.children = [left_node, right_node]
                left_node.parent = new_root
                right_node.parent = new_root
                self.root = new_root
            else:
                parent = node.parent
                left_node.parent = parent
                right_node.parent = parent

                node_idx = parent.children.index(node)
                parent.keys.insert(node_idx, node.keys[mid])
                parent.children[node_idx] = left_node
                parent.children.insert(node_idx + 1, right_node)
                if len(parent.keys) >= self.degree:
                    self._split_node(parent)

    def range_query(self, start_key: int, end_key: int):
        # find the node where start key will be/just bigger than this, then trraverse the linked list
        (cur, idx) = self._search(start_key, True)
        result: List[Tuple[int, Dict[str, Any]]] = []
        if idx is None:
            idx = len(cur.keys)
            for i, val in enumerate(cur.keys):
                if val >= start_key:
                    idx = i
                    break

        while cur is not None:
            while idx < len(cur.keys):
                k = cur.keys[idx]
                if k > end_key:
                    return result
                result.append((k, cur.values[idx]))
                idx += 1

            cur = cur.next
            idx = 0

        return result

    def get_all(self):
        #  need to find ledtmost leaf and traverse hrough the linked list.
        cur = self.root
        res: List[Tuple[int, Dict[str, Any]]] = []
        while not cur.leaf:
            if not cur.children:
                return res
            cur = cur.children[0]

        while cur is not None:
            for i in range(len(cur.keys)):
                res.append((cur.keys[i], cur.values[i]))
            cur = cur.next

        return res

    def delete(self, key: int):
        min_keys = (
            ceil(self.degree / 2) - 1
        )  # minimum keys for non leaf nodes except root
        cur = self.root
        nodes_having_key: List[Tuple[BPlusTreeNode, int]] = []  # last one is the leaf
        while not cur.leaf:
            loc = len(cur.keys)
            for i, k in enumerate(cur.keys):
                if k >= key:
                    if k == key:
                        loc = i + 1
                        nodes_having_key.append((cur, i))
                    else:
                        loc = i
                    break
            cur = cur.children[loc]

        leaf_idx = None
        for idx, k in enumerate(cur.keys):
            if k == key:
                leaf_idx = idx
                break

        if leaf_idx is None:
            return False  # key not found

        nodes_having_key.append((cur, leaf_idx))
        leaf_node = cur

        leaf_node.keys.pop(leaf_idx)
        leaf_node.values.pop(leaf_idx)

        # if key was present in internal nodes, we neeed to replace it with the new first key of this leaf
        if len(nodes_having_key) > 1 and len(leaf_node.keys) > 0:
            internal_key = leaf_node.keys[0]
            for ancestor, anc_idx in nodes_having_key[:-1]:  # all except the leaf
                ancestor.keys[anc_idx] = internal_key

        if leaf_node is self.root:
            return True

        if len(leaf_node.keys) >= min_keys:
            return True

        self._fix_underflow(leaf_node, min_keys)
        return True

    def _fix_underflow(self, node: BPlusTreeNode, min_keys: int):
        # if node is root, the tree height will shrink
        if node.parent is None:
            if len(node.keys) == 0 and len(node.children) == 1:
                self.root = node.children[0]
                self.root.parent = None
            return

        parent = node.parent
        idx_in_parent = parent.children.index(node)

        if node.leaf:
            left_neigh = (
                node.prev
                if (node.prev is not None and node.prev.parent is parent)
                else None
            )
            right_neigh = (
                node.next
                if (node.next is not None and node.next.parent is parent)
                else None
            )
        else:
            # internal nodes aren't in a linked list.
            left_neigh = (
                parent.children[idx_in_parent - 1] if idx_in_parent > 0 else None
            )
            right_neigh = (
                parent.children[idx_in_parent + 1]
                if idx_in_parent < len(parent.children) - 1
                else None
            )

        if left_neigh is not None and len(left_neigh.keys) > min_keys:
            self._take_from_left(node, left_neigh, parent, idx_in_parent)
            return

        if right_neigh is not None and len(right_neigh.keys) > min_keys:
            self._take_from_right(node, right_neigh, parent, idx_in_parent)
            return

        # if we cannot take from either neighbors

        if left_neigh is not None:
            self._merge_nodes(left_neigh, node, parent, idx_in_parent - 1)
        elif right_neigh is not None:
            self._merge_nodes(node, right_neigh, parent, idx_in_parent)
        else:
            raise Exception("idk what happened :cries:")

        # parent underflow check
        if parent.parent is None:  # parent is root
            if len(parent.keys) == 0:
                # root has no keys, its first child becomes root
                self.root = parent.children[0]
                self.root.parent = None
        elif len(parent.keys) < min_keys:
            self._fix_underflow(parent, min_keys)

    def _take_from_left(
        self,
        node: BPlusTreeNode,
        left_neigh: BPlusTreeNode,
        parent: BPlusTreeNode,
        idx_in_parent: int,
    ):
        # idx_in_parent - 1  =======>>> parent key between left_neigh and node

        if node.leaf:
            # take last key-value from left neigh, put at start of node
            borrowed_key = left_neigh.keys.pop(-1)
            borrowed_val = left_neigh.values.pop(-1)
            node.keys.insert(0, borrowed_key)
            node.values.insert(0, borrowed_val)
            # update parent's middle key to be the new first key of node
            parent.keys[idx_in_parent - 1] = node.keys[0]
        else: # non leaf node
            #  pull middle key down from parent, push last key of left_neigh up
            node.keys.insert(0, parent.keys[idx_in_parent - 1])
            parent.keys[idx_in_parent - 1] = left_neigh.keys.pop(-1)
            # make the last child of left_neigh,  the first child of node
            child = left_neigh.children.pop(-1)
            node.children.insert(0, child)
            child.parent = node

    def _take_from_right(
        self,
        node: BPlusTreeNode,
        right_neigh: BPlusTreeNode,
        parent: BPlusTreeNode,
        idx_in_parent: int,
    ):
        # idx_in_parent - 1  =======>>> parent key between node and right_neigh

        if node.leaf:
            # take first key-value from right neihbor, append to node
            borrowed_key = right_neigh.keys.pop(0)
            borrowed_val = right_neigh.values.pop(0)
            node.keys.append(borrowed_key)
            node.values.append(borrowed_val)
            # make parent's middle key to be the new first key of right neighbor
            parent.keys[idx_in_parent] = right_neigh.keys[0]
        else:
            # pull middle key down, push first key of right_neigh up
            node.keys.append(parent.keys[idx_in_parent])
            parent.keys[idx_in_parent] = right_neigh.keys.pop(0)
            # make the first child of right_neigh, the last child of node
            child = right_neigh.children.pop(0)
            node.children.append(child)
            child.parent = node

    def _merge_nodes(
        self,
        left_node: BPlusTreeNode,
        right_node: BPlusTreeNode,
        parent: BPlusTreeNode,
        middle_idx: int,
    ):
        if left_node.leaf:
            left_node.keys.extend(right_node.keys)
            left_node.values.extend(right_node.values)

            left_node.next = right_node.next
            if right_node.next is not None:
                right_node.next.prev = left_node
        else:
            left_node.keys.append(parent.keys[middle_idx])
            left_node.keys.extend(right_node.keys)
            left_node.children.extend(right_node.children)

            for child in right_node.children:
                child.parent = left_node

        parent.keys.pop(middle_idx)
        parent.children.remove(right_node)
