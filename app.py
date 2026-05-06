from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')

# ── Base de données ──
db_user     = os.environ.get('MYSQL_USER', 'raphael')
db_password = os.environ.get('MYSQL_PASSWORD', 'password')
db_host     = os.environ.get('MYSQL_HOST', 'localhost')
db_name     = os.environ.get('MYSQL_DATABASE', 'portfolio')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ────────────────────────────────────────────────
#  MODÈLES
# ────────────────────────────────────────────────

class Semestre(db.Model):
    __tablename__ = 'semestres'
    id   = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)   # ex: S1
    nom  = db.Column(db.String(100), nullable=False)               # ex: Semestre 1
    blocs = db.relationship('Bloc', backref='semestre', lazy=True, cascade='all, delete-orphan')

class Bloc(db.Model):
    __tablename__ = 'blocs'
    id          = db.Column(db.Integer, primary_key=True)
    code        = db.Column(db.String(20), nullable=False)          # ex: ADMIN
    nom         = db.Column(db.String(200), nullable=False)         # ex: Administrer
    semestre_id = db.Column(db.Integer, db.ForeignKey('semestres.id'), nullable=False)
    competences = db.relationship('Competence', backref='bloc', lazy=True, cascade='all, delete-orphan')

class Competence(db.Model):
    __tablename__ = 'competences'
    id      = db.Column(db.Integer, primary_key=True)
    code    = db.Column(db.String(30), nullable=False)              # ex: AC11.01
    nom     = db.Column(db.String(300), nullable=False)
    niveau  = db.Column(db.String(50), nullable=False, default='non_acquis')
    bloc_id = db.Column(db.Integer, db.ForeignKey('blocs.id'), nullable=False)

NIVEAUX = [
    ('non_acquis',      'Non acquis',         'niveau-na'),
    ('en_cours',        'En cours d\'acquisition', 'niveau-ec'),
    ('presque_acquis',  'Presque acquis',     'niveau-pa'),
    ('acquis',          'Acquis',             'niveau-ac'),
    ('expert',          'Expert',             'niveau-ex'),
]

class User(db.Model):
    __tablename__ = 'users'
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

# ────────────────────────────────────────────────
#  DONNÉES INITIALES
# ────────────────────────────────────────────────

def seed_data():
    """Peuple la BDD si elle est vide."""
    if Semestre.query.first():
        return

    semestres_data = [
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
    ]
    blocs_data = [
        ('ADMIN',    'Administrer les réseaux et les systèmes'),
        ('CONNECT',  'Connecter les entreprises et les usagers'),
        ('PROG',     'Programmer les équipements du réseau'),
        ('SECU',     'Sécuriser les réseaux et les systèmes'),
        ('SURVEILL', 'Surveiller les réseaux et les systèmes'),
    ]
    competences_data = {
        'ADMIN': [
            ('AC11.01', 'Maîtriser les lois fondamentales de l\'électricité afin d\'intervenir sur des équipements de réseaux et télécommunications'),
            ('AC11.02', 'Comprendre les systèmes de numération et les caractéristiques des signaux électriques'),
            ('AC11.03', 'Configurer les fonctions de base du réseau local'),
        ],
        'CONNECT': [
            ('AC12.01', 'Maîtriser les technologies xDSL, fibre optique et radio pour les accès'),
            ('AC12.02', 'Tester les accès au réseau local et à Internet'),
        ],
        'PROG': [
            ('AC13.01', 'Utiliser un système informatique et ses outils'),
            ('AC13.02', 'Lire, exécuter, corriger et écrire du code'),
        ],
        'SECU': [
            ('AC14.01', 'Maîtriser les principes de la cryptographie et de la sécurisation des réseaux'),
            ('AC14.02', 'Identifier les risques de sécurité et les contre-mesures appropriées'),
        ],
        'SURVEILL': [
            ('AC15.01', 'Identifier les différentes solutions de supervision réseau'),
            ('AC15.02', 'Déployer des outils de surveillance et analyser les données collectées'),
        ],
    }

    for s_code, s_nom in semestres_data:
        sem = Semestre(code=s_code, nom=s_nom)
        db.session.add(sem)
        db.session.flush()
        for b_code, b_nom in blocs_data:
            bloc = Bloc(code=b_code, nom=b_nom, semestre_id=sem.id)
            db.session.add(bloc)
            db.session.flush()
            for c_code, c_nom in competences_data.get(b_code, []):
                comp = Competence(code=c_code, nom=c_nom, niveau='non_acquis', bloc_id=bloc.id)
                db.session.add(comp)

    db.session.commit()

# ────────────────────────────────────────────────
#  AUTH HELPER
# ────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ────────────────────────────────────────────────
#  ROUTES PUBLIQUES
# ────────────────────────────────────────────────

@app.route('/')
def index():
    semestres = Semestre.query.all()
    # Stats globales
    total = Competence.query.count()
    acquises = Competence.query.filter(Competence.niveau.in_(['acquis', 'expert'])).count()
    return render_template('index.html', semestres=semestres, total=total, acquises=acquises)

@app.route('/competences')
def competences():
    semestres = Semestre.query.options(
        db.joinedload(Semestre.blocs).joinedload(Bloc.competences)
    ).all()
    niveaux_map = {code: (label, css) for code, label, css in NIVEAUX}
    return render_template('competences.html', semestres=semestres, niveaux_map=niveaux_map)

# ────────────────────────────────────────────────
#  ROUTES AUTH
# ────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Connexion réussie.', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Identifiants incorrects.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))

# ────────────────────────────────────────────────
#  ROUTES ADMIN (PROTÉGÉES)
# ────────────────────────────────────────────────

@app.route('/admin')
@login_required
def admin_dashboard():
    semestres = Semestre.query.options(
        db.joinedload(Semestre.blocs).joinedload(Bloc.competences)
    ).all()
    niveaux_map = {code: (label, css) for code, label, css in NIVEAUX}
    return render_template('admin/dashboard.html', semestres=semestres, niveaux_map=niveaux_map)

@app.route('/admin/valider', methods=['GET', 'POST'])
@login_required
def valider_competence():
    semestres = Semestre.query.options(
        db.joinedload(Semestre.blocs).joinedload(Bloc.competences)
    ).all()
    if request.method == 'POST':
        comp_id = request.form.get('competence_id')
        niveau  = request.form.get('niveau')
        # Validation
        valid_niveaux = [n[0] for n in NIVEAUX]
        if not comp_id or niveau not in valid_niveaux:
            flash('Données invalides.', 'error')
            return redirect(url_for('valider_competence'))
        comp = Competence.query.get_or_404(int(comp_id))
        comp.niveau = niveau
        db.session.commit()
        flash(f'Compétence « {comp.code} » mise à jour : {dict((n[0], n[1]) for n in NIVEAUX)[niveau]}.', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/valider.html', semestres=semestres, niveaux=NIVEAUX)

@app.route('/admin/supprimer/<int:comp_id>', methods=['POST'])
@login_required
def supprimer_competence(comp_id):
    comp = Competence.query.get_or_404(comp_id)
    db.session.delete(comp)
    db.session.commit()
    flash(f'Compétence « {comp.code} » supprimée.', 'info')
    return redirect(url_for('admin_dashboard'))

# ────────────────────────────────────────────────
#  INIT APP
# ────────────────────────────────────────────────

with app.app_context():
    db.create_all()
    seed_data()
    # Crée un compte admin par défaut si aucun utilisateur n'existe
    if not User.query.first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123')
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
