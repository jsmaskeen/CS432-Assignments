from typing import Tuple, List, Dict, Any


class BruteForceDB:
    def __init__(self):
        self.data: List[Tuple[int, Dict[str, Any]]] = (
            []
        )  # store values also, hence it had (key, value) tuples (to compare it fairly with B+ tree)

    def insert(self, key: int, value: Dict[str, Any]):
        self.data.append((key, value))

    def search(self, key: int):
        for k, v in self.data:
            if k == key:
                return v
        return None

    def delete(self, key: int):
        for i, (k, _) in enumerate(self.data):
            if k == key:
                self.data.pop(i)
                return True
        return False

    def update(self, key: int, new_value: Dict[str, Any]):
        for i, (k, _) in enumerate(self.data):
            if k == key:
                self.data[i] = (key, new_value)
                return True
        return False

    def range_query(self, start: int, end: int):
        return [v for k, v in self.data if start <= k <= end]
    
    def get_all(self):
        return [v for _,v in self.data]
