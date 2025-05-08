from flask import Flask, request, render_template, send_file, flash, redirect, url_for
import os
import uuid
from datetime import datetime
from utils.parser import parse_sql_ddl
from utils.diagram import generate_er_diagram

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-for-flask')
app.config['UPLOAD_FOLDER'] = 'output'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        sql_text = request.form.get('sql_text')
        if not sql_text:
            flash('are you gay or smthn? pass the sql code', 'error')
            return redirect(url_for('index'))
        
        orientation = request.form.get('orientation', 'LR')
        format_type = request.form.get('format', 'png')
        engine = request.form.get('engine', 'graphviz')
        
        try:
            file_id = str(uuid.uuid4())
            
            parsed_sql = parse_sql_ddl(sql_text)  
            print(parsed_sql)
            
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], f'diagram_{file_id}')
            diagram_path = generate_er_diagram(
                parsed_sql, 
                output_path, 
                format=format_type, 
                orientation=orientation,
                engine=engine
            )
            
            tables_count = len(parsed_sql.get('tables', {}))
            relationships_count = len(parsed_sql.get('foreign_keys', []))
            
            download_name = os.path.basename(diagram_path)
            
            return render_template('result.html', 
                                  diagram_url=url_for('serve_diagram', filename=download_name),
                                  download_name=download_name,
                                  tables_count=tables_count,
                                  relationships_count=relationships_count,
                                  sql_text=sql_text,
                                  now=datetime.now())
        except Exception as e:
            flash(f'Error generating:{str(e)}', 'error')
            return render_template('index.html', sql_text=sql_text)
    
    return render_template('index.html')

@app.route('/diagram/<path:filename>')
def serve_diagram(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(file_path, mimetype='image/png')

@app.route('/download/<path:filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(file_path, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
