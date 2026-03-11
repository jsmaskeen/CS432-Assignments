class BruteForceDB:
    def __init__(self):
        self.data = []  # store values also, hence it had (key, value) tuples (to compare it farly with B+ tree)

    def insert(self, key, value=None):
        self.data.append((key, value))

    def search(self, key):
        for k, v in self.data:
            if k == key:
                return v
        return None

    def delete(self, key):
        for i, (k, _) in enumerate(self.data):
            if k == key:
                self.data.pop(i)
                return True
        return False

    def update(self, key, new_value):
        for i, (k, _) in enumerate(self.data):
            if k == key:
                self.data[i] = (key, new_value)
                return True
        return False

    def range_query(self, start, end):
        return [(k, v) for k, v in self.data if start <= k <= end]
