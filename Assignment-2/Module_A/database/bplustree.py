def search ( self, key ) :
    # Search for a key in the B+ tree. Return the associated value if found, else None.
    # Traverse from root to appropriate leaf node.
    pass

def insert ( self , key , value ) :
    """
    Insert key-value pair into the B+ tree.
    Handle root splitting if necessary
    Maintain sorted order and balance properties.
    """
    pass

def _insert_non_full ( self , node , key , value ) :
    # Recursive helper to insert into a non-full node.
    # Split child nodes if they become full during insertion.
    pass

def _split_child ( self , parent , index ) :
    """
    Split the arentchild at the given index
    For leaves:preserve the linked list structure and copy the middle key to the parent.
    For internal nodes: promote the middle key and split the children
    """
    pass

def delete ( self, key ) :
    """
    Delete key from the B+ tree.
    Handle underflow by borrowing from siblings or merging nodes.
    Update the root if it becomes empty.
    Return True if deletion succeeded, False otherwise.
    """
    pass

def _delete ( self , node , key ) :
    # Recursive helper for deletion. Handle leaf and internal nodes .
    # Ensure all nodes maintain minimum keys after deletion.
    pass

def _fill_child ( self , node , index ) :
    # Ensure child at given index has enough keys by borrowing from siblings or merging.
    pass

def _borrow_from_prev ( self , node , index ) :
    # Borrow a key from the left sibling to prevent underflow.
    pass

def _borrow_from_next ( self , node , index ) :
    # Borrow a key from the right sibling to prevent underflow
    pass

def _merge ( self , node , index ) :
    # Merge child at index with its right sibling. Update parent keys
    pass

def update ( self , key , new_value ) :
    # Update value associated with an existing key. Return True if successful.
    pass

def range_query ( self , start_key , end_key ):
    """
    Return all key-value pairs where start_key <= key <= end_key.
    Traverse leaf nodes using the following pointers for efficient range scans.
    """
    pass

def get_all ( self ) :
    # Return all key-value pairs in the tree using in-order traversal.
    pass

def visualize_tree ( self ):
    # Generate Graphviz representation of the B+ tree structure .
    pass

def _add_nodes ( self , dot , node ) :
    # Recursively add nodes to Graphviz object (for visualisation.
    pass

def _add_edges ( self , dot , node ) :
    # Add edges between nodes and dashed lines for leaf connections (for visualisation
    pass
