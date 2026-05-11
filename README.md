# SAE 2.3 — Portfolio Dynamique Flask

### Raphaël Macker · BUT R&T · IUT de Béthune

-----

# PARTIE 1 — PRÉSENTATION DU PROJET

## C’est quoi ce projet ?

Au départ j’avais un portfolio en HTML/CSS pur (statique). La SAE 2.3 demandait de le rendre **dynamique** avec Flask et une base de données.

Concrètement ça veut dire :

- Avant : les compétences étaient écrites en dur dans le HTML, impossible à modifier sans retoucher le code
- Après : les compétences sont stockées dans une **base de données MySQL**, et on peut les modifier via une interface web

## Ce que fait le site

|Page            |Qui peut y accéder|Ce qu’elle fait                    |
|----------------|------------------|-----------------------------------|
|`/`             |Tout le monde     |Affiche le profil et les stats     |
|`/competences`  |Tout le monde     |Tableau de toutes les compétences  |
|`/login`        |Tout le monde     |Formulaire de connexion            |
|`/admin`        |Admin connecté    |Voir et supprimer les compétences  |
|`/admin/valider`|Admin connecté    |Modifier le niveau d’une compétence|
|`/logout`       |Admin connecté    |Se déconnecter                     |

## Technologies utilisées

- **Flask** (Python) — le framework web qui gère les pages et les routes
- **MySQL** — la base de données qui stocke les compétences
- **SQLAlchemy** — sert à parler à MySQL depuis Python sans écrire du SQL brut
- **Jinja2** — le système de templates HTML intégré à Flask
- **Docker** — permet de lancer l’application sur n’importe quel serveur facilement

-----

# PARTIE 2 — STRUCTURE DU PROJET (fichier par fichier)

```
SAE23/
├── app.py                      ← Le cœur de l'application
├── requirements.txt            ← Liste des bibliothèques Python nécessaires
├── Dockerfile                  ← Instructions pour créer le conteneur Flask
├── docker-compose.yml          ← Lance les deux serveurs (MySQL + Flask)
├── templates/
│   ├── base.html               ← Template parent (navbar + footer communs)
│   ├── index.html              ← Page d'accueil / profil
│   ├── competences.html        ← Tableau public des compétences
│   ├── login.html              ← Formulaire de connexion
│   └── admin/
│       ├── dashboard.html      ← Interface admin (voir/supprimer)
│       └── valider.html        ← Formulaire pour modifier une compétence
└── static/
    ├── css/style.css           ← Le style visuel du site
    └── img/                    ← Les images (photo de profil, etc.)
```

### Pourquoi cette organisation ?

- `templates/` : Flask cherche les fichiers HTML dans ce dossier automatiquement
- `static/` : tout ce qui est CSS, images, JS va ici (fichiers servis directement au navigateur)
- `admin/` dans templates : je sépare les pages admin des pages publiques pour que ce soit plus clair
- `app.py` seul à la racine : c’est le point d’entrée de l’application, Flask doit le trouver facilement

-----

# PARTIE 3 — EXPLICATION DU CODE (app.py)

## 3.1 — Les imports et la configuration

```python
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os, time
```

**Ce que j’importe et pourquoi :**

- `Flask` : la classe principale pour créer l’application
- `render_template` : pour afficher un fichier HTML depuis templates/
- `request` : pour récupérer ce que l’utilisateur a soumis dans un formulaire
- `redirect` / `url_for` : pour rediriger vers une autre page
- `session` : pour mémoriser qu’un utilisateur est connecté (comme un cookie)
- `flash` : pour afficher des messages de succès/erreur à l’utilisateur
- `SQLAlchemy` : pour gérer la base de données avec des objets Python
- `generate_password_hash` / `check_password_hash` : pour ne jamais stocker un mot de passe en clair

```python
app = Flask(__name__)
app.secret_key = 'ma_cle_secrete_sae23'
```

**Pourquoi `secret_key` ?** Flask l’utilise pour signer les sessions. Sans ça, n’importe qui pourrait falsifier une session et se connecter en admin.

```python
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.environ.get('MYSQL_USER')}:..."
)
```

**Pourquoi `os.environ.get()` ?** Pour ne pas écrire le mot de passe en dur dans le code. Les vraies valeurs sont dans `docker-compose.yml` sous forme de variables d’environnement.

-----

## 3.2 — Les modèles (tables de la base de données)

```python
class Semestre(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False)   # ex: S1
    nom  = db.Column(db.String(100), nullable=False)
    blocs = db.relationship('Bloc', backref='semestre', lazy=True)
```

**Comment lire ça ?** Chaque classe = une table dans MySQL. Chaque `db.Column` = une colonne.

- `primary_key=True` : c’est l’identifiant unique de chaque ligne
- `nullable=False` : ce champ est obligatoire
- `db.relationship` : crée le lien entre Semestre et ses Blocs (comme une clé étrangère)

**La hiérarchie des tables :**

```
Semestre  →  Bloc  →  Competence
  (S1)      (ADMIN)    (AC11.01)
```

Chaque compétence appartient à un bloc, chaque bloc appartient à un semestre.

-----

## 3.3 — Les routes (pages du site)

**C’est quoi une route ?** C’est l’URL qui déclenche une fonction Python.

```python
@app.route('/')
def index():
    semestres = Semestre.query.all()
    total    = Competence.query.count()
    acquises = Competence.query.filter(
        Competence.niveau.in_(['acquis', 'expert'])
    ).count()
    return render_template('index.html', semestres=semestres, total=total, acquises=acquises)
```

**Ligne par ligne :**

- `@app.route('/')` : quand quelqu’un va sur `/`, Flask appelle la fonction `index()`
- `Semestre.query.all()` : récupère tous les semestres depuis MySQL
- `Competence.query.count()` : compte le nombre total de compétences
- `.filter(...)` : compte seulement celles qui sont acquises ou expert
- `render_template(...)` : affiche le fichier `index.html` en lui passant les données

-----

## 3.4 — La connexion / authentification

```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Connexion réussie !', 'success')
            return redirect(url_for('dashboard'))
        flash('Identifiant ou mot de passe incorrect.', 'error')
    return render_template('login.html')
```

**Ce qui se passe quand on se connecte :**

1. L’utilisateur soumet le formulaire → `request.method == 'POST'`
1. On cherche l’utilisateur dans la BDD par son nom
1. `check_password_hash` compare le mot de passe saisi avec le hash stocké en BDD
1. Si c’est bon → on stocke l’`user_id` dans la session (il est “connecté”)
1. Si c’est faux → message d’erreur, on reste sur la page login

**Pourquoi stocker dans `session` ?** La session Flask est chiffrée côté serveur. Tant que `session['user_id']` existe, l’utilisateur est considéré connecté sur toutes les pages.

-----

## 3.5 — Protection de l’espace admin

```python
def connecte():
    return 'user_id' in session

@app.route('/admin')
def dashboard():
    if not connecte():
        flash('Vous devez être connecté.', 'warning')
        return redirect(url_for('login'))
    ...
```

**Pourquoi cette vérification ?** Sans ça, n’importe qui pourrait aller sur `/admin` directement dans l’URL. La fonction `connecte()` vérifie que la session contient bien un `user_id` avant d’afficher la page.

-----

## 3.6 — Le formulaire de validation

```python
@app.route('/admin/valider', methods=['GET', 'POST'])
def valider():
    if request.method == 'POST':
        comp_id = request.form.get('competence_id')
        niveau  = request.form.get('niveau')

        niveaux_valides = [n[0] for n in NIVEAUX]
        if niveau not in niveaux_valides:
            flash('Données invalides.', 'error')
            return redirect(url_for('valider'))

        comp = Competence.query.get_or_404(int(comp_id))
        comp.niveau = niveau
        db.session.commit()
        flash(f'Compétence {comp.code} mise à jour !', 'success')
        return redirect(url_for('dashboard'))
```

**Ce qui se passe :**

1. L’admin choisit une compétence et un niveau dans le formulaire
1. On vérifie que le niveau est bien dans la liste autorisée (sécurité)
1. On récupère la compétence depuis la BDD
1. On modifie son niveau et on sauvegarde avec `db.session.commit()`

**Pourquoi vérifier le niveau ?** Pour éviter qu’un utilisateur malveillant envoie une valeur personnalisée dans le formulaire (sécurité contre la falsification de requêtes).

-----

# PARTIE 4 — EXPLICATION DES TEMPLATES (Jinja2)

## C’est quoi Jinja2 ?

C’est le système de templates de Flask. Il permet d’écrire du HTML avec des variables Python dedans.

## base.html — Le template parent

```html
{% block content %}{% endblock %}
```

Toutes les autres pages **héritent** de `base.html` avec `{% extends "base.html" %}`.
Ça évite de réécrire la navbar et le footer dans chaque page.

**Pourquoi c’est bien ?** Si je veux changer la navbar, je le fais une seule fois dans `base.html` et ça se répercute partout.

## Les boucles et conditions dans les templates

```html
{% for semestre in semestres %}
  <h2>{{ semestre.nom }}</h2>
  {% for bloc in semestre.blocs %}
    ...
  {% endfor %}
{% endfor %}
```

- `{{ variable }}` : affiche la valeur d’une variable Python
- `{% for ... %}` : boucle sur une liste
- `{% if ... %}` : condition

## Les messages flash

```html
{% with messages = get_flashed_messages(with_categories=true) %}
  {% for categorie, message in messages %}
    <div class="flash flash-{{ categorie }}">{{ message }}</div>
  {% endfor %}
{% endwith %}
```

Ce bloc dans `base.html` affiche automatiquement les messages de succès/erreur envoyés depuis Python avec `flash(...)`.

-----

# PARTIE 5 — DOCKER

## C’est quoi Docker ?

Docker permet de **mettre une application dans une boîte isolée** (conteneur) avec tout ce dont elle a besoin. L’avantage : ça marche sur n’importe quel serveur, sans avoir à installer Python, MySQL, etc. manuellement.

## Dockerfile — Comment construire le conteneur Flask

```dockerfile
FROM python:3.12-slim          # On part d'une image Python légère
WORKDIR /app                   # Le dossier de travail dans le conteneur
COPY requirements.txt .        # On copie la liste des dépendances
RUN pip install -r requirements.txt  # On les installe
COPY . .                       # On copie tout le code
EXPOSE 5000                    # On ouvre le port 5000
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]  # On lance Flask
```

## docker-compose.yml — Les deux serveurs

```yaml
services:
  db:        # Serveur MySQL
    image: mysql:8.4
    ...
  web:       # Serveur Flask
    build: .
    depends_on:
      db:
        condition: service_healthy   # Flask attend que MySQL soit prêt
```

**Pourquoi deux services ?** La consigne demande un serveur BDD et un serveur HTTP séparés. `depends_on` avec `service_healthy` assure que MySQL est complètement démarré avant que Flask essaie de s’y connecter.

-----

# PARTIE 6 — INSTALLATION ET LANCEMENT

## Étape 1 — Préparer la VM Ubuntu

La carte réseau doit être en mode **NAT** dans VirtualBox :

> Clic droit sur la VM → Configuration → Réseau → Mode d’accès réseau : **NAT**

## Étape 2 — Installer Docker

```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER
```

Fermer et rouvrir le terminal, ou faire `newgrp docker`.

## Étape 3 — Configurer le proxy de l’IUT

Le proxy de l’IUT Artois est : `http://cache-etu.univ-artois.fr:3128`

**3a. Proxy pour le terminal (permanent) :**

```bash
nano ~/.bashrc
```

Ajouter à la fin :

```bash
export http_proxy=http://cache-etu.univ-artois.fr:3128
export https_proxy=http://cache-etu.univ-artois.fr:3128
```

Puis :

```bash
source ~/.bashrc
```

**3b. Proxy pour Docker :**

```bash
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo nano /etc/systemd/system/docker.service.d/proxy.conf
```

Coller :

```
[Service]
Environment="HTTP_PROXY=http://cache-etu.univ-artois.fr:3128"
Environment="HTTPS_PROXY=http://cache-etu.univ-artois.fr:3128"
```

Puis :

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

> ⚠️ Le proxy dans `docker-compose.yml` et `Dockerfile` est déjà configuré dans les fichiers du projet.

## Étape 4 — Lancer le projet

```bash
unzip SAE23.zip
cd SAE23
sudo docker-compose up --build
```

Première fois : 2-5 minutes (téléchargement des images).  
Le site est sur **http://localhost:5000**

## Étape 5 — Arrêter / Relancer

```bash
# Arrêter
sudo docker-compose down

# Relancer (sans rebuild, plus rapide)
sudo docker-compose up
```

-----

# PARTIE 7 — PROBLÈMES RENCONTRÉS

### Permission denied sur Docker

```
PermissionError: [Errno 13] Permission denied
```

**Solution :** `sudo usermod -aG docker $USER` puis fermer/rouvrir le terminal.

### Timeout réseau (images Docker)

```
dial tcp: i/o timeout
```

**Solution :** Vérifier mode NAT dans VirtualBox + configurer le proxy (Partie 6 Étape 3).

### Flask démarre avant MySQL

```
Can't connect to MySQL server on 'db'
```

**Solution :** Déjà géré dans `app.py` avec une boucle qui retente la connexion 10 fois toutes les 3 secondes.
