import os
import sys
import uuid
import threading
import subprocess
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Task storage: {task_id: {status: 'running', logs: '', series: '', chapter: ''}}
tasks = {}

def run_production(task_id, series, chapter, script_content):
    tasks[task_id]['status'] = 'running'
    
    # Create temp script file
    safe_series = "".join([c if c.isalnum() else "_" for c in series.lower()])
    temp_script_path = f"tmp_script_{task_id}.txt"
    with open(temp_script_path, "w", encoding="utf-8") as f:
        f.write(script_content)
    
    # Run process_chapter.py
    cmd = [
        sys.executable, "process_chapter.py",
        "--series", series,
        "--chapter", str(chapter),
        "--script", temp_script_path
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        for line in process.stdout:
            tasks[task_id]['logs'] += line
            print(f"[{task_id}] {line.strip()}") # Mirror to local console
            
        process.wait()
        
        if process.returncode == 0:
            tasks[task_id]['status'] = 'completed'
        else:
            tasks[task_id]['status'] = 'failed'
            
    except Exception as e:
        tasks[task_id]['logs'] += f"\nCRITICAL ERROR: {str(e)}"
        tasks[task_id]['status'] = 'failed'
    finally:
        # Cleanup
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/publish', methods=['POST'])
def publish():
    data = request.json
    series = data.get('series')
    chapter = data.get('chapter')
    script = data.get('script')
    
    if not all([series, chapter, script]):
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
        
    task_id = str(uuid.uuid4())[:8]
    tasks[task_id] = {
        'status': 'queued',
        'logs': f"> Initiating build for {series} Ch.{chapter}...\n",
        'series': series,
        'chapter': chapter
    }
    
    thread = threading.Thread(target=run_production, args=(task_id, series, chapter, script))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'started',
        'task_id': task_id
    })

@app.route('/status/<task_id>')
def status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'status': 'error', 'message': 'Task not found'}), 404
        
    return jsonify({
        'status': task['status'],
        'logs': task['logs']
    })

if __name__ == '__main__':
    print("REELS LABS Engine starting at http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
