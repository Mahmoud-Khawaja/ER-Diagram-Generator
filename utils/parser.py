import re

def parse_sql_ddl(sql_text):
    tables = {}
    foreign_keys = []
    unique_constraints = {}
    
    def remove_comments(sql_text):
        sql_text = re.sub(r'--.*?$', '', sql_text, flags=re.MULTILINE)
        sql_text = re.sub(r'/\*.*?\*/', '', sql_text, flags=re.DOTALL)
        return sql_text
    
    def split_columns(table_body):
        parts = []
        bracket_level = 0
        current = []
        
        for char in table_body:
            if char == '(':
                bracket_level += 1
            elif char == ')':
                bracket_level -= 1
            
            if char == ',' and bracket_level == 0:
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(char)
                
        if current:
            parts.append(''.join(current).strip())
            
        return parts
    
    sql_text = remove_comments(sql_text)
    print(sql_text)
    
    create_table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\[]?(\w+)[`"\]]?\s*\((.*?)\);'
    table_matches = re.finditer(create_table_pattern, sql_text, re.IGNORECASE | re.DOTALL)
    
    for match in table_matches:
        table_name = match.group(1)
        table_body = match.group(2)
        tables[table_name] = []
        unique_constraints[table_name] = []
        
        parts = split_columns(table_body)
        
        primary_keys = set()
        
        for part in parts:
            pk_match = re.search(r'PRIMARY\s+KEY\s*\(([^)]+)\)', part, re.IGNORECASE)
            if pk_match:
                pk_cols = [col.strip(' `"[]') for col in pk_match.group(1).split(',')]
                primary_keys.update(pk_cols)
            
            unique_match = re.search(r'UNIQUE\s*\(([^)]+)\)', part, re.IGNORECASE)
            if unique_match:
                unique_cols = [col.strip(' `"[]') for col in unique_match.group(1).split(',')]
                unique_constraints[table_name].extend(unique_cols)
        
        for part in parts:
            part = part.strip()
            
            if re.match(r'(?:CONSTRAINT|PRIMARY\s+KEY|FOREIGN\s+KEY|UNIQUE|CHECK)', part, re.IGNORECASE):
                continue
                
            col_match = re.match(r'[`"\[]?(\w+)[`"\]]?', part)
            if not col_match:
                continue
                
            col_name = col_match.group(1)
            
            is_pk = col_name in primary_keys or 'PRIMARY KEY' in part.upper()
            
            if 'UNIQUE' in part.upper():
                unique_constraints[table_name].append(col_name)
            
            is_fk = False
            fk_match = re.search(r'REFERENCES\s+[`"\[]?(\w+)[`"\]]?\s*\(\s*[`"\[]?(\w+)[`"\]]?\s*\)', part, re.IGNORECASE)
            if fk_match:
                is_fk = True
                target_table = fk_match.group(1)
                target_column = fk_match.group(2)
                relationship_name = f"rel_{table_name}_{target_table}_{col_name}"
                foreign_keys.append((table_name, target_table, col_name, relationship_name))
            
            tables[table_name].append((col_name, is_pk, is_fk))
        
        # foreign keys stuff
        for part in parts:
            fk_match = re.search(r'FOREIGN\s+KEY\s*\(\s*[`"\[]?(\w+)[`"\]]?\s*\)\s*REFERENCES\s+[`"\[]?(\w+)[`"\]]?\s*\(\s*[`"\[]?(\w+)[`"\]]?\s*\)', part, re.IGNORECASE)
            if fk_match:
                source_column = fk_match.group(1)
                target_table = fk_match.group(2)
                target_column = fk_match.group(3)
                
                for idx, (col, is_pk, _) in enumerate(tables[table_name]):
                    if col == source_column:
                        tables[table_name][idx] = (col, is_pk, True)
                
                relationship_name = f"rel_{table_name}_{target_table}_{source_column}"
                foreign_keys.append((table_name, target_table, source_column, relationship_name))
    
    typed_foreign_keys = []
    for src, tgt, fk, rel in foreign_keys:
        is_pk_in_source = False
        for col, is_pk, _ in tables.get(src, []):
            if col == fk and is_pk:
                is_pk_in_source = True
                break
        
        is_unique_in_source = fk in unique_constraints.get(src, [])
        
        # TODO: work to be done here
        '''
        1->1: foreign key with a unique constraint linking one record in each table
        1->N: default relationship where multiple records in one table reference a single record in another
        N->1: foreign key that is part of the pk commonly seen in associative tables

        I've no clue how to do N->M we can consider this as a limitation but the current implemenetation will work fine for most 
        common cases
        '''
        if is_pk_in_source and is_unique_in_source:
            rel_type = "1:1"  
        elif is_pk_in_source:
            rel_type = "N:1" 
        elif is_unique_in_source:
            rel_type = "1:1"  
        else:
            rel_type = "1:N" 
        
        typed_foreign_keys.append((src, tgt, fk, rel, rel_type))
    
    typed_foreign_keys = list(set(typed_foreign_keys))
    
    return {
        'tables': tables,
        'foreign_keys': typed_foreign_keys
    }
