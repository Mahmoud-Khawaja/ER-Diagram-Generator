import pydot
import os

def generate_er_diagram(parsed_sql, output_path='er_diagram', format='png', orientation='LR'):
    try:
        tables = parsed_sql.get('tables', {})
        foreign_keys = parsed_sql.get('foreign_keys', [])
        
        graph = pydot.Dot(graph_type='digraph', rankdir=orientation, splines='ortho')
        
        table_nodes = {}
        for tbl in tables:
            node = pydot.Node(tbl, shape='box', style='filled', fillcolor='lightgrey')
            graph.add_node(node)
            table_nodes[tbl] = node
        
        for tbl, cols in tables.items():
            for col, is_pk, is_fk in cols:
                node_id = f"{tbl}_{col}"
                label = f"PK: {col}" if is_pk else col
                style = 'dashed' if is_fk else 'solid'
                node = pydot.Node(node_id, label=label, shape='ellipse', style=style)
                graph.add_node(node)
                edge = pydot.Edge(node_id, tbl)
                graph.add_edge(edge)
        
        for src, tgt, fk, rel in foreign_keys:
            rel_node = pydot.Node(rel, shape='diamond', style='filled', fillcolor='white')
            graph.add_node(rel_node)
            edge1 = pydot.Edge(src, rel, label='N')
            edge2 = pydot.Edge(rel, tgt, label='1')
            graph.add_edge(edge1)
            graph.add_edge(edge2)
        
        full_output_path = f"{output_path}.{format}"
        
        if format == 'png':
            graph.write_png(full_output_path)
        elif format == 'svg':
            graph.write_svg(full_output_path)
        elif format == 'pdf':
            graph.write_pdf(full_output_path)
        else:
            full_output_path = f"{output_path}.png"
            graph.write_png(full_output_path)
        
        return full_output_path
    
    except Exception as e:
        raise Exception(f"Error generating diagram: {str(e)}")