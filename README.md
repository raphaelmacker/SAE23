# SAE 2.3 — Portfolio Dynamique Flask

### Raphaël Macker · BUT R&T · IUT de Béthune

-----

# PARTIE 1 — PRÉSENTATION DU PROJET

## C’est quoi ce projet ?

Au départ j’avais un portfolio en HTML/CSS pur (statique). La SAE 2.3 demandait de le rendre **dynamique** avec Flask et une base de données.

Concrètement ça veut dire :

- **Avant** : les compétences étaient écrites en dur dans le HTML, impossible à modifier sans retoucher le code
- **Après** : les compétences sont stockées dans une **base de données MySQL**, et on peut les modifier via une interface web

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
├── config.py                   ← Informations du profil étudiant
├── requirements.txt            ← Liste des bibliothèques Python nécessaires
├── Dockerfile                  ← Instructions pour créer le conteneur Flask
├── docker-compose.yml          ← Lance les deux serveurs (MySQL + Flask)
├── database.sql                ← Sauvegarde complète de la base de données
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
- `admin/` dans templates : sépare les pages admin des pages publiques pour plus de clarté
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
- `render_template` : pour afficher un fichier HTML depuis `templates/`
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

Toutes les autres pages **héritent** de `base.html` avec `{% extends "base.html" %}`. Ça évite de réécrire la navbar et le footer dans chaque page.

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

# PARTIE 5 — FICHIERS DE CONFIGURATION ET DOCKER

## requirements.txt

```
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
PyMySQL==1.1.1
cryptography==42.0.8
Werkzeug==3.0.3
```

C’est la liste de toutes les bibliothèques Python dont le projet a besoin. Quand Docker construit le conteneur Flask, il lit ce fichier et installe tout avec `pip install -r requirements.txt`.

**Chaque ligne :**

- `Flask` : le framework web principal
- `Flask-SQLAlchemy` : l’extension qui connecte Flask à la base de données
- `PyMySQL` : le driver Python qui permet de parler à MySQL (c’est lui qui fait la vraie connexion)
- `cryptography` : requis par PyMySQL pour les connexions sécurisées à MySQL
- `Werkzeug` : fourni avec Flask, on l’utilise pour hasher les mots de passe

**Pourquoi fixer les versions (ex: `==3.0.3`) ?** Pour que le projet fonctionne toujours de la même façon, même dans 6 mois. Si on ne fixe pas les versions, une mise à jour automatique pourrait casser quelque chose.

-----

## config.py

```python
PROFILE = {
    "nom":         "Raphaël Macker",
    "formation":   "BUT Réseaux & Télécommunications",
    "email":       "raphael.macker@example.com",
    ...
}
```

Ce fichier regroupe toutes les informations personnelles du profil en un seul endroit. La consigne demande explicitement un *“fichier de configuration facile à manipuler”* — si je veux changer mon email ou ma description, je modifie juste ce fichier sans toucher au code ou aux templates.

**Comment il est utilisé ?** Dans `app.py` :

```python
from config import PROFILE
```

Puis on passe `PROFILE` aux templates pour afficher les infos sur la page d’accueil.

-----

## Dockerfile

```dockerfile
FROM python:3.12-slim
```

Image Docker officielle Python légère. `slim` veut dire qu’elle ne contient que le strict minimum, ce qui rend le conteneur plus petit.

```dockerfile
ARG HTTP_PROXY
ARG HTTPS_PROXY
ENV http_proxy=$HTTP_PROXY
ENV https_proxy=$HTTPS_PROXY
```

Configure le proxy de l’IUT **pendant la construction** du conteneur. Sans ça, `pip install` ne peut pas télécharger les bibliothèques depuis le réseau de l’IUT.

- `ARG` : reçoit la valeur passée depuis `docker-compose.yml`
- `ENV` : la rend disponible pour toutes les commandes qui suivent

```dockerfile
WORKDIR /app
```

Définit `/app` comme dossier de travail dans le conteneur.

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

On copie d’abord **seulement** `requirements.txt` et on installe les dépendances. Pourquoi pas tout copier d’un coup ? Pour optimiser le cache Docker : si le code change mais pas les dépendances, Docker ne réinstalle pas tout.

```dockerfile
COPY . .
```

Copie tout le reste du projet (app.py, templates, static…) dans `/app`.

```dockerfile
EXPOSE 5000
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
```

- `EXPOSE 5000` : documente que le conteneur utilise le port 5000
- `CMD` : commande lancée au démarrage. `--host=0.0.0.0` est important : sans ça, Flask n’écoute que sur `localhost` à l’intérieur du conteneur et n’est pas accessible de l’extérieur.

-----

## docker-compose.yml

Ce fichier définit et orchestre les **deux serveurs** du projet.

### Le serveur de base de données

```yaml
db:
  image: mysql:8.4
  container_name: portfolio_db
  restart: unless-stopped
  environment:
    MYSQL_ROOT_PASSWORD: rootpassword
    MYSQL_DATABASE: portfolio
    MYSQL_USER: raphael
    MYSQL_PASSWORD: password
```

- `image: mysql:8.4` : image officielle MySQL 8.4, pas besoin de l’installer manuellement
- `restart: unless-stopped` : si MySQL plante, Docker le redémarre automatiquement
- `environment` : variables utilisées par MySQL pour créer la base et l’utilisateur au premier démarrage

```yaml
  volumes:
    - mysql_data:/var/lib/mysql
```

Les données MySQL sont sauvegardées dans un **volume Docker**. Sans ça, toutes les données seraient perdues à chaque `docker-compose down`.

```yaml
  healthcheck:
    test: ["CMD", "mysqladmin", "ping", ...]
    interval: 10s
    retries: 5
```

Docker vérifie toutes les 10 secondes si MySQL répond vraiment. Tant qu’il n’est pas “healthy”, Flask ne démarre pas.

### Le serveur Flask

```yaml
web:
  build:
    context: .
    args:
      - HTTP_PROXY=http://cache-etu.univ-artois.fr:3128
      - HTTPS_PROXY=http://cache-etu.univ-artois.fr:3128
```

- `build: context: .` : Docker construit l’image en lisant le `Dockerfile` dans le dossier actuel
- `args` : passe le proxy au Dockerfile pour que `pip install` puisse accéder à Internet à l’IUT

```yaml
  environment:
    FLASK_APP: app.py
    MYSQL_HOST: db
    MYSQL_USER: raphael
    MYSQL_PASSWORD: password
```

- `FLASK_APP` : dit à Flask quel fichier lancer
- `MYSQL_HOST: db` : le nom `db` correspond au nom du service MySQL défini plus haut. Docker Compose crée un réseau interne entre les conteneurs, donc `db` est l’adresse de MySQL vue depuis Flask.

```yaml
  ports:
    - "5000:5000"
```

Redirige le port 5000 de la VM vers le port 5000 du conteneur. Format : `PORT_VM:PORT_CONTENEUR`.

```yaml
  depends_on:
    db:
      condition: service_healthy
```

Flask attend que MySQL soit complètement prêt (healthcheck OK) avant de démarrer.

-----

## database.sql

C’est une **sauvegarde complète** de la base de données générée avec `mysqldump`. Elle contient les instructions `CREATE TABLE` pour créer toutes les tables et les instructions `INSERT INTO` pour remettre toutes les données.

**À quoi ça sert ?** Restaurer la BDD si besoin, ou montrer la structure exacte des tables avec les vraies contraintes SQL.

**Par exemple, la table `competences` :**

```sql
CREATE TABLE `competences` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(30) NOT NULL,
  `nom` varchar(300) NOT NULL,
  `niveau` varchar(50) NOT NULL,
  `bloc_id` int NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`bloc_id`) REFERENCES `blocs` (`id`)
);
```

On voit clairement la clé étrangère `bloc_id` qui pointe vers la table `blocs` — exactement ce que demande la consigne.

-----

## static/css/style.css

C’est le fichier CSS qui gère tout l’aspect visuel du site : couleurs, polices, mise en page, boutons, tableaux…

**Pourquoi il est dans `static/` ?** Flask sert les fichiers de ce dossier directement au navigateur, sans les traiter. C’est le bon endroit pour tout ce qui ne change pas dynamiquement.

**Comment il est chargé ?** Dans `base.html` :

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
```

`url_for('static', ...)` génère automatiquement le bon chemin vers le fichier, peu importe où le site est hébergé.

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

Première fois : 2–5 minutes (téléchargement des images).  
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


### Flask démarre avant MySQL

**Symptôme :** Flask crash au démarrage avec une erreur de connexion BDD.

**Solution :** Le `healthcheck` + `depends_on: condition: service_healthy` dans `docker-compose.yml` règle ce problème — Flask attend que MySQL soit vraiment prêt avant de démarrer.
