from typing import List, Dict, Any, Union, Tuple, Optional, overload, Literal


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


# def delete(self, key):
#     """
#     Delete key from the B+ tree.
#     Handle underflow by borrowing from siblings or merging nodes.
#     Update the root if it becomes empty.
#     Return True if deletion succeeded, False otherwise.
#     """
#     pass


# def _delete(self, node, key):
#     # Recursive helper for deletion. Handle leaf and internal nodes .
#     # Ensure all nodes maintain minimum keys after deletion.
#     pass


# def visualize_tree(self):
#     # Generate Graphviz representation of the B+ tree structure .
#     pass


# def _add_nodes(self, dot, node):
#     # Recursively add nodes to Graphviz object (for visualisation.
#     pass


# def _add_edges(self, dot, node):
#     # Add edges between nodes and dashed lines for leaf connections (for visualisation
#     pass
