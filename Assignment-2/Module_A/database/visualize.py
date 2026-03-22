import graphviz # type:ignore
from typing import Set
from database.bplustree import BPlusTreeNode

def make_label(node:BPlusTreeNode, degree:int):
    top_row = '<TD BORDER="0" WIDTH="15"></TD>' 
    for i in range(degree - 1):
        key_val = node.keys[i] if i < len(node.keys) else ""
        top_row += f'<TD COLSPAN="2" WIDTH="30" HEIGHT="30">{key_val}</TD>'
    top_row += '<TD WIDTH="15" BORDER="0" HEIGHT="30" ></TD>'

    bottom_row = ""
    for i in range(degree):
        bottom_row += f'<TD PORT="p{i}" COLSPAN="2" WIDTH="30" HEIGHT="20" BGCOLOR="#eeeeee"></TD>'

    return f"""<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
  <TR>{top_row}</TR>
  <TR>{bottom_row}</TR>
</TABLE>>"""

def visualize(bptree_root: BPlusTreeNode, degree: int):
    dot = graphviz.Digraph(
        comment='B+ Tree',
        node_attr={'shape': 'plaintext', 'fontname': 'Courier'},
        edge_attr={'fontname': 'Courier', 'arrowsize': '0.6'}
    )
    
    visited:Set[str] = set()

    def make(node:BPlusTreeNode):
        node_id = str(id(node))
        if node_id in visited:
            return node_id
        visited.add(node_id)

        dot.node(name=node_id, label=make_label(node, degree)) #type:ignore

        if not node.leaf:
            for i, child in enumerate(node.children):
                child_id = make(child)
                dot.edge(f"{node_id}:p{i}", child_id) #type:ignore
        
        else:
            for i, val in enumerate(node.values):
                data_id = f"data_{id(val)}"
                data_label = " | ".join([f"{k}: {v}" for k, v in val.items()])
                
                dot.node(data_id, label=f"{{ {data_label} }}", shape="record", color="gray") #type:ignore
                
                dot.edge(f"{node_id}:p{i}", data_id, color="red", style="dotted") #type:ignore

            if node.next:
                next_id = str(id(node.next))
                dot.edge(node_id, next_id, constraint='false', color="blue", style="dashed") #type:ignore
                dot.edge(next_id, node_id, constraint='false', color="teal", style="dashed") #type:ignore
            
        return node_id

    make(bptree_root)
    return dot
