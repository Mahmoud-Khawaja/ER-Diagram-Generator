from graphviz import Digraph
import os
import subprocess
import pydot

def generate_er_diagram_pydot(parsed_sql, output_path='er_diagram', format='png', orientation='LR'):
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
        
        for src, tgt, fk, rel, rel_type in foreign_keys:
            rel_node = pydot.Node(rel, shape='diamond', style='filled', fillcolor='white')
            graph.add_node(rel_node)
            
            if rel_type == "1:1":
                edge1 = pydot.Edge(src, rel, label='1')
                edge2 = pydot.Edge(rel, tgt, label='1')
            elif rel_type == "1:N":
                edge1 = pydot.Edge(src, rel, label='N')
                edge2 = pydot.Edge(rel, tgt, label='1')
            elif rel_type == "N:1":
                edge1 = pydot.Edge(src, rel, label='1')
                edge2 = pydot.Edge(rel, tgt, label='N')
            elif rel_type == "M:N":
                edge1 = pydot.Edge(src, rel, label='M')
                edge2 = pydot.Edge(rel, tgt, label='N')
            else:
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
        raise Exception(f"Error: {str(e)}")

def generate_er_diagram_graphviz(parsed_sql, output_path='er_diagram', format='png', orientation='LR'):
    try:
        try:
            subprocess.run(['dot', '-V'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (subprocess.SubprocessError, FileNotFoundError):
            raise Exception("Graphviz not installed.")
            
        tables = parsed_sql.get('tables', {})
        foreign_keys = parsed_sql.get('foreign_keys', [])
        
        g = Digraph('ER', filename=output_path, engine='dot', format=format)
        g.attr(rankdir=orientation, 
               splines='ortho', 
               nodesep='0.8', 
               ranksep='1.0',
               concentrate='true')
        
        for tbl in tables:
            g.node(tbl, 
                  shape='box', 
                  style='filled',
                  fillcolor='lightblue',
                  fontname='Arial',
                  fontsize='16',
                  margin='0.3,0.1')
        
        for tbl, cols in tables.items():
            for col, is_pk, is_fk in cols:
                node_id = f"{tbl}_{col}"
                
                if col in ('CONSTRAINT', 'PRIMARY', 'FOREIGN', 'UNIQUE'):
                    continue
                    
                if is_pk and is_fk:
                    label = f"PK/FK: {col}"
                    style = 'filled,dashed'
                    fillcolor = 'lightyellow'
                elif is_pk:
                    label = f"PK: {col}"
                    style = 'filled'
                    fillcolor = 'lightgreen'
                elif is_fk:
                    label = f"FK: {col}"
                    style = 'filled,dashed'
                    fillcolor = 'lightpink'
                else:
                    label = col
                    style = 'solid'
                    fillcolor = 'white'
                
                g.node(node_id, 
                      label=label, 
                      shape='ellipse', 
                      style=style, 
                      fillcolor=fillcolor,
                      fontname='Arial',
                      fontsize='14')
                      
                g.edge(node_id, tbl, style='solid')
        
        for src, tgt, fk, rel, rel_type in foreign_keys:
            if src not in tables or tgt not in tables:
                continue
                
            g.node(rel, 
                  shape='diamond', 
                  style='filled', 
                  fillcolor='lightsalmon',
                  fontname='Arial',
                  fontsize='12',
                  height='1',
                  width='1')
                  
            if rel_type == "1:1":
                g.edge(src, rel, label='1', fontsize='10', fontname='Arial')
                g.edge(rel, tgt, label='1', fontsize='10', fontname='Arial')
            elif rel_type == "1:N":
                g.edge(src, rel, label='N', fontsize='10', fontname='Arial')
                g.edge(rel, tgt, label='1', fontsize='10', fontname='Arial')
            elif rel_type == "N:1":
                g.edge(src, rel, label='1', fontsize='10', fontname='Arial')
                g.edge(rel, tgt, label='N', fontsize='10', fontname='Arial')
            elif rel_type == "M:N":
                g.edge(src, rel, label='M', fontsize='10', fontname='Arial')
                g.edge(rel, tgt, label='N', fontsize='10', fontname='Arial')
            else:
                g.edge(src, rel, label='N', fontsize='10', fontname='Arial')
                g.edge(rel, tgt, label='1', fontsize='10', fontname='Arial')
        
        diagram_path = g.render(cleanup=True)
        return diagram_path
        
    except Exception as e:
        raise Exception(f"Error: {str(e)}")

def generate_er_diagram(parsed_sql, output_path='er_diagram', format='png', orientation='LR', engine='graphviz'):
    if engine == 'pydot':
        return generate_er_diagram_pydot(parsed_sql, output_path, format, orientation)
    else:
        return generate_er_diagram_graphviz(parsed_sql, output_path, format, orientation)
