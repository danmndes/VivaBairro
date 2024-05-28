from flask import Flask, jsonify, request, render_template,redirect, url_for
from models import db, User, Merchant, Charity
from flask_bcrypt import bcrypt
from flask_login import login_user, LoginManager, login_required,logout_user, current_user

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["SECRET_KEY"] = "mysecretkey"
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    merchant = Merchant.query.filter_by(id=user_id).first()
    charity = Charity.query.filter_by(id=user_id).first()
    if user != None:
        return User.query.get(int(user_id))
    if merchant != None:
        return Merchant.query.get(int(user_id))
    if charity != None:
        return Charity.query.get(int(user_id))

with app.app_context():
    db.create_all() #usa so a 1x para criar o db
    

def authenticate_user(username, password):
    models = [User, Merchant, Charity]
    for model in models:
        user = model.query.filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode(), user.password):
            return user
    return None

def search_user(username):
    user = User.query.filter_by(username=username).first()
    merchant = Merchant.query.filter_by(username=username).first()
    charity = Charity.query.filter_by(username=username).first()
    if user:
        return user
    if merchant:
        return merchant
    if charity:
        return charity

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        form_remember = 'remember' in request.form
        
        user = authenticate_user(username, password)
        
        if user:
            login_user(user, remember=form_remember)
            return jsonify({"redirect": url_for('dashboard')})
        else:
            return jsonify({"error": "Usuário não encontrado ou senha incorreta"}), 403
    
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    merchants = Merchant.query.all()
    if current_user.tipo != "user":
           return render_template('nonuser_dashboard.html', username=current_user.shop_name, user=current_user.username) 
    return render_template('dashboard.html', username=current_user.username, merchants=merchants)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/get_users', methods=['GET'])
def getAllUsers():
    profiles = db.session.query(User).all() + db.session.query(Merchant).all() + db.session.query(Charity).all()
    all_profiles = [{"username": profile.username, "email": profile.email, "tipo": profile.tipo, "shop_name": getattr(profile, 'shop_name', None)} for profile in profiles]
    return jsonify(all_profiles)

@app.route('/profile/<username>')
def profile(username):
    user = search_user(username)
    return render_template('profile.html', id=user.id, username=user.username, email=user.email, shop_name=user.shop_name,bairro=user.bairro, tipo=user.tipo)

@app.route("/create_user", methods=['GET','POST'])
def create_user():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    bairro = request.form.get("bairro")
    tipo = request.form.get("tipo")
    if tipo == "merchant":
        nome_local = request.form.get("shop_name")
    elif tipo == "charity":
        nome_local = request.form.get("charity_name")
    else:
        nome_local = None

    if not all(username and email and password and bairro):
        return jsonify({"error": "Missing username, email, password, or bairro"}), 400
    
    existing_user = User.query.filter_by(username=username).first()
    
    if existing_user:
        return jsonify({"success": False, "error": "Username already exists"}), 400
    hashed_password = bcrypt.hashpw(password=password.encode(), salt=bcrypt.gensalt())
    if tipo == 'user':
        user = User(username=username, email=email, password=hashed_password, bairro=bairro, tipo=tipo)
    elif tipo == 'merchant':
        user = Merchant(username=username, email=email, password=hashed_password, bairro=bairro, tipo=tipo, shop_name=nome_local)
    elif tipo == 'charity':
        user = Charity(username=username, email=email, password=hashed_password, bairro=bairro, tipo=tipo, shop_name=nome_local) 
    
    db.session.add(user)
    db.session.commit()
    return jsonify({"success": True,"message": "Conta criada com Sucesso"}), 201

@app.route('/edit_user/<int:id>', methods=['POST'])
@login_required
def edit_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user != current_user:  # Ensure that only the user can edit their own profile
        return jsonify({"error": "You are not authorized to edit this user"}), 403

    # Update user information
    user.username = request.form.get("username", user.username)
    user.email = request.form.get("email", user.email)
    user.bairro = request.form.get("bairro", user.bairro)

    db.session.commit()
    return jsonify({"success": True, "message": "User updated successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)
