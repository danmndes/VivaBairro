from flask import Flask, jsonify, request, render_template, redirect, url_for
from models import db, User, Merchant, Charity
from flask_bcrypt import Bcrypt
from flask_login import login_user, LoginManager, login_required, logout_user, current_user

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["SECRET_KEY"] = "mysecretkey"
db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    models = [User, Merchant, Charity]
    for model in models:
        user = model.query.get(int(user_id))
        if user:
            return user
    return None

with app.app_context():
    db.create_all()  # Run once to create the database

def authenticate_user(username, password):
    models = [User, Merchant, Charity]
    for model in models:
        user = model.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            return user
    return None

def search_user(username):
    models = [User, Merchant, Charity]
    for model in models:
        user = model.query.filter_by(username=username).first()
        if user:
            return user
    return None

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
    page = request.args.get('page', 1, type=int)
    per_page = 12
    paginated_merchants = Merchant.query.paginate(page=page, per_page=per_page, error_out=False)

    template = 'nonuser_dashboard.html' if current_user.tipo != "user" else 'dashboard.html'
    username = current_user.shop_name if current_user.tipo != "user" else current_user.username
    return render_template(
        template,
        username=username,
        merchants=paginated_merchants.items,
        page=paginated_merchants.page,
        pages=paginated_merchants.pages
    )

@app.route('/paginate_merchants')
def paginate_merchants():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    paginated_merchants = Merchant.query.paginate(page, per_page, error_out=False)
    return render_template('merchant_container.html', merchants=paginated_merchants.items)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/get_users', methods=['GET'])
def get_all_users():
    profiles = db.session.query(User).all() + db.session.query(Merchant).all() + db.session.query(Charity).all()
    all_profiles = [{"username": profile.username, "email": profile.email, "tipo": profile.tipo, "shop_name": getattr(profile, 'shop_name', None)} for profile in profiles]
    return jsonify(all_profiles)

@app.route('/profile/<username>')
def profile(username):
    user = search_user(username)
    if user:
        return render_template('profile.html', id=user.id, username=user.username, email=user.email, shop_name=user.shop_name, bairro=user.bairro, tipo=user.tipo)
    return jsonify({"error": "Profile not found"}), 404

@app.route("/create_user", methods=['POST'])
def create_user():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    bairro = request.form.get("bairro")
    tipo = request.form.get("tipo")
    print(f"tipo é: {tipo}")
    atuacao = request.form.get("atuacao_loja") if tipo == "merchant" else request.form.get("atuacao_org")
    nome_local = request.form.get("shop_name") if tipo in ["merchant", "charity"] else None

    if not all([username, email, password, bairro]):
        return jsonify({"error": "Missing username, email, password, or bairro"}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user_model = {'user': User, 'merchant': Merchant, 'charity': Charity}.get(tipo, User)
    user = user_model(username=username, email=email, password=hashed_password, bairro=bairro, tipo=tipo, shop_name=nome_local, atuacao=atuacao)

    db.session.add(user)
    db.session.commit()
    return jsonify({"success": True, "message": "Conta criada com Sucesso"}), 201

@app.route('/edit_user/<int:id>', methods=['POST'])
@login_required
def edit_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user != current_user:
        return jsonify({"error": "You are not authorized to edit this user"}), 403

    user.username = request.form.get("username", user.username)
    user.email = request.form.get("email", user.email)
    user.bairro = request.form.get("bairro", user.bairro)

    db.session.commit()
    return jsonify({"success": True, "message": "User updated successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)
