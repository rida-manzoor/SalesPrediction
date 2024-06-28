from flask import Flask, request, render_template, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import os
import pandas as pd
from werkzeug.utils import secure_filename
import pickle

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid user')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        return render_template('dashboard.html', user=user)
    
    return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/login')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'email' not in session:
        return redirect('/login')
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Process the uploaded Excel file
            df = pd.read_excel(filepath)
            # Here you can add your processing logic
            flash('File successfully uploaded and processed')
            return redirect('/dashboard')
    return render_template('upload.html')

@app.route('/single_prediction', methods=['GET', 'POST'])
def single_prediction():
    if 'email' not in session:
        return redirect('/login')
    if request.method == 'POST':
        product_category = request.form['product_category']
        item_id = request.form['item_id']
        season = request.form['season']
        item_price = float(request.form['item_price'])
        promotion = int(request.form['promotion'])
        competitor_activity =int(request.form['competitor_activity'])
        year =int(request.form['year'])
        month =int(request.form['month'])
        day =int(request.form['day'])
        day_of_week =int(request.form['day_of_week'])

        print('Info Rendered')
        
        
    # Create features DataFrame
        features = pd.DataFrame({
                'product_category': [product_category],
                'item_id': [item_id],
                'promotion': [promotion],
                'competitor_activity': [competitor_activity],
                'item_price': [item_price],
                'season': [season],
                'year': [year],
                'month': [month],
                'day': [day],
                'day_of_week': [day_of_week]
            })

        print(features)


        # Load preprocessing and model pickles
        with open('preprocesso.pkl', 'rb') as f:
                preprocessing = pickle.load(f)

        with open('voting_regressor_model.pkl', 'rb') as f:
                model = pickle.load(f)

            # Apply preprocessing
        preprocessed_features = preprocessing.transform(features)

            # Make prediction
        prediction = model.predict(preprocessed_features)[0]

        return render_template('single_prediction.html', prediction=prediction)
    return render_template('single_prediction.html')

@app.route('/bulk_prediction', methods=['GET', 'POST'])
def bulk_prediction():
    if 'email' not in session:
        return redirect('/login')
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Read the uploaded Excel file
            df = pd.read_excel(filepath)

            # Load preprocessing and model pickles
            with open('preprocesso.pkl', 'rb') as f:
                preprocessing = pickle.load(f)

            with open('voting_regressor_model.pkl', 'rb') as f:
                model = pickle.load(f)

            # Apply preprocessing
            preprocessed_df = preprocessing.transform(df)

            # Make predictions
            predictions = model.predict(preprocessed_df)

            # Add predictions to dataframe
            df['Prediction'] = predictions

            # Display the dataframe with predictions
            return render_template('bulk_prediction.html', tables=[df.to_html(classes='data', header="true")], titles=df.columns.values)
    return render_template('bulk_prediction.html')


if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()  # Create tables if they don't exist
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            print("Tables created successfully")
        except Exception as e:
            print(f"Error creating tables: {e}")
    app.run(debug=True)
