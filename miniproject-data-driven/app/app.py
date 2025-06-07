
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory, flash
import os
import pandas as pd
from werkzeug.utils import secure_filename
from utils import analyze_sales_dataset, validate_sales_csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'

# In-memory storage
users = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'retailer1': {'password': 'retail123', 'role': 'retailer'},
    'retailer2': {'password': 'retail456', 'role': 'retailer'}

}

analyzed_datasets = {}  # {'dataset_name': {'filename': ..., 'link': ..., 'suggestions': ..., 'uploaded_by': ...}}


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = users.get(username)
    if user and user['password'] == password:
        session['username'] = username
        session['role'] = user['role']
        return redirect(url_for(f"{user['role']}_dashboard"))
    flash("Invalid credentials")
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/')
    return render_template('admin_dashboard.html', datasets=analyzed_datasets)

@app.route('/retailer')
def retailer_dashboard():
    if session.get('role') != 'retailer':
        return redirect('/')
    user_datasets = {name: data for name, data in analyzed_datasets.items()
                 if data.get('uploaded_by') == session['username']}
    return render_template('retailer_dashboard.html', username=session['username'], datasets=user_datasets)

    
@app.route('/upload_sales', methods=['POST'])
def upload_sales():
    if session.get('role') != 'retailer':
        return redirect('/')
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('retailer_dashboard'))
    if file and file.filename.endswith('.csv'):
        df = pd.read_csv(file)
        if not validate_sales_csv(df):
            flash('Invalid Sales Dataset Format')
            return redirect(url_for('retailer_dashboard'))
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df.to_csv(path, index=False)
        analyzed_name = os.path.splitext(filename)[0]
        analyze_sales_dataset(df, analyzed_name)
        analyzed_datasets[analyzed_name] = {
    'filename': filename,
    'link': '',
    'suggestions': '',
    'uploaded_by': session['username']
}

        flash('Dataset uploaded successfully')
    return redirect(url_for('retailer_dashboard'))

@app.route('/admin/update/<name>', methods=['POST'])
def update_dataset(name):
    if session.get('role') != 'admin':
        return redirect('/')
    link = request.form['power_link']
    suggestion = request.form['suggestion']
    if name in analyzed_datasets:
        analyzed_datasets[name]['link'] = link
        analyzed_datasets[name]['suggestions'] = suggestion
    flash('Report link and suggestions updated')
    return redirect(url_for('admin_dashboard'))
    
@app.route('/download/<filename>')
def download_file(filename):
    if session.get('role') != 'admin':
        return redirect('/')
    
    # Get dataset name without .csv
    analyzed_name = os.path.splitext(filename)[0]
    processed_filename = f"{analyzed_name}_summary.csv"
    processed_path = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
    
    if os.path.exists(processed_path):
        return send_from_directory(app.config['UPLOAD_FOLDER'], processed_filename, as_attachment=True)
    else:
        flash("Processed file not found.")
        return redirect(url_for('admin_dashboard'))


@app.route('/retailer/view/<name>')

def view_analysis(name):
    if session.get('role') != 'retailer':
        return redirect('/')
    data = analyzed_datasets.get(name)
    if not data or data.get('uploaded_by') != session['username']:
        flash("Unauthorized access or dataset not found.")
        return redirect(url_for('retailer_dashboard'))
    return render_template('retailer_view.html', name=name, data=data)


if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)