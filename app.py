from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.sqlite import JSON
from dotenv import load_dotenv
import os

load_dotenv() 
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
ADMIN_USERNAME = 'YAMIN'
app = Flask(__name__)

db_path = os.path.join(app.instance_path, "chulas.db")
os.makedirs(app.instance_path, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Fix: Move SECRET_KEY to environment variable
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey-change-this-in-production')

db = SQLAlchemy(app)

class Chula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    head = db.Column(db.String(100))
    members = db.Column(JSON, default=list)

with app.app_context():
    db.create_all()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Fix: Handle both JSON (from JS) and form data (from template)
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            if request.is_json:
                return jsonify({"success": True}), 200
            else:
                return redirect(url_for('index'))
        else:
            if request.is_json:
                return jsonify({"error": "Invalid credentials"}), 401
            else:
                return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Test route
@app.route('/api/ping')
def ping():
    return jsonify({"message": "API is working!"})

@app.route('/api/chulas', methods=['GET'])
def get_all_chulas():
    chulas = Chula.query.all()

    result = []
    for chula in chulas:
        result.append({
            "id": chula.id,
            "name": chula.name,
            "head": chula.head,
            "members": chula.members if chula.members else []
        })

    return jsonify(result), 200

@app.route('/api/chulas', methods=['POST'])
def add_chula():
    try:
        data = request.get_json()
        
        # Fix: Add validation
        if not data or not data.get('name'):
            return jsonify({"error": "Name is required"}), 400
        
        name = data.get('name')
        head = data.get('head')
        
        # Fix: Process members string into array
        members_input = data.get('members', '')
        if isinstance(members_input, str):
            members = [m.strip() for m in members_input.split(',') if m.strip()]
        else:
            members = members_input if members_input else []

        new_chula = Chula(name=name, head=head, members=members)
        db.session.add(new_chula)
        db.session.commit()
        return jsonify({"message": "Chula added successfully!"})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to add chula"}), 500

@app.route('/api/chulas/<int:chula_id>', methods=['GET'])
def get_chula(chula_id):
    chula = Chula.query.get(chula_id)

    if not chula:
        return jsonify({"error": "Chula not found"}), 404

    result = {
        "id": chula.id,
        "name": chula.name,
        "head": chula.head,
        "members": chula.members if chula.members else []
    }

    return jsonify(result), 200

@app.route('/api/chulas/<int:chula_id>', methods=['PUT'])
def update_chula(chula_id):
    try:
        chula = Chula.query.get(chula_id)

        if not chula:
            return jsonify({"error": "Chula not found"}), 404

        data = request.get_json()
        chula.name = data.get('name', chula.name)
        chula.head = data.get('head', chula.head)
        
        # Fix: Process members string into array
        members_input = data.get('members', chula.members)
        if isinstance(members_input, str):
            chula.members = [m.strip() for m in members_input.split(',') if m.strip()]
        else:
            chula.members = members_input

        db.session.commit()
        return jsonify({"message": "Chula updated successfully"}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update chula"}), 500

# Fix: Add DELETE endpoint
@app.route('/api/chulas/<int:chula_id>', methods=['DELETE'])
def delete_chula(chula_id):
    try:
        chula = Chula.query.get(chula_id)
        if not chula:
            return jsonify({"error": "Chula not found"}), 404
        
        db.session.delete(chula)
        db.session.commit()
        return jsonify({"message": "Chula deleted successfully"}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete chula"}), 500

@app.route('/')
def index():
    return render_template('index.html', is_admin=session.get('logged_in', False))

if __name__ == '__main__':
    app.run(debug=True, port=5001)