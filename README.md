# Portfolio Dynamique — SAE 2.3
### Raphaël Macker · BUT Réseaux & Télécommunications · IUT de Béthune

---

## Présentation du projet

Dans le cadre de la SAE 2.3, j'ai transformé mon portfolio statique (HTML/CSS) en une application web dynamique développée avec **Flask** et **MySQL**, hébergée via **Docker**.

Le site permet de consulter publiquement les compétences acquises durant la formation BUT RT, et d'en gérer le niveau d'acquisition depuis un espace d'administration protégé.

---

## Technologies utilisées

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3.12 · Flask 3.0 |
| Base de données | MySQL 8.4 · SQLAlchemy (ORM) |
| Frontend | Jinja2 · HTML/CSS · JavaScript |
| Hébergement | Docker · Docker Compose |
| Sécurité | Werkzeug (hash bcrypt) · Sessions Flask |

---

## Fonctionnalités

- **Page profil** — Présentation de l'étudiant, stats dynamiques (compétences acquises / total)
- **Récapitulatif des compétences** — Tableau public organisé par semestre et bloc de compétences
- **Espace admin protégé** — Connexion requise pour accéder aux actions de gestion
- **Formulaire de validation** — Choisir un apprentissage critique et lui attribuer un niveau (non acquis → expert)
- **Suppression de compétence** — Depuis le dashboard admin avec confirmation
- **Base de données relationnelle** — Modèles Semestre → Bloc → Compétence liés par clés étrangères

---

## Modèle de base de données

```
Semestre (id, code, nom)
    └── Bloc (id, code, nom, semestre_id)
            └── Competence (id, code, nom, niveau, bloc_id)

User (id, username, password)
```

Chaque entité possède un **code** (ex : `S1`, `ADMIN`, `AC11.01`), un **nom**, et un **lien vers l'entité parente** via clé étrangère — conformément au cahier des charges.

---

## Structure du projet

```
sae23/
├── app.py               # Application Flask principale (routes, modèles, auth)
├── config.py            # Profil étudiant — facile à modifier
├── requirements.txt     # Dépendances Python
├── Dockerfile           # Image Docker pour Flask
├── docker-compose.yml   # Orchestration : MySQL + Flask
├── templates/
│   ├── base.html        # Template parent (navbar, footer, flash messages)
│   ├── index.html       # Page profil
│   ├── competences.html # Récapitulatif public des compétences
│   ├── login.html       # Page de connexion
│   └── admin/
│       ├── dashboard.html  # Dashboard admin (voir, supprimer)
│       └── valider.html    # Formulaire de validation d'une compétence
└── static/
    ├── css/
    │   ├── style.css    # Design système hérité du portfolio statique
    │   └── app.css      # Styles spécifiques à l'application Flask
    └── img/             # Photos et images du portfolio
```

---

## Lancement avec Docker (recommandé)

```bash
# Cloner le repo
git clone https://github.com/raphael-macker/sae23-portfolio-flask
cd sae23-portfolio-flask

# Construire et démarrer les deux conteneurs (MySQL + Flask)
docker-compose up --build

# Le site est accessible sur http://localhost:5000
```

## Lancement en local (développement)

```bash
# Installer les dépendances
pip install -r requirements.txt

# Variables d'environnement pour la base de données
export MYSQL_HOST=localhost
export MYSQL_USER=raphael
export MYSQL_PASSWORD=password
export MYSQL_DATABASE=portfolio

# Lancer Flask
python app.py
```

---

## Pages du site

| URL | Description | Accès |
|-----|-------------|-------|
| `/` | Page profil avec stats dynamiques | Public |
| `/competences` | Tableau récapitulatif des compétences | Public |
| `/login` | Connexion à l'espace admin | Public |
| `/admin` | Dashboard — consulter et supprimer | 🔒 Protégé |
| `/admin/valider` | Formulaire de validation d'une compétence | 🔒 Protégé |
| `/logout` | Déconnexion | — |

---

## Compte administrateur par défaut

| Identifiant | Mot de passe |
|-------------|-------------|
| `admin` | `admin123` |

> ⚠️ À changer avant tout déploiement en production via la variable `SECRET_KEY` dans `docker-compose.yml`.

---

## Sécurité

- **Mots de passe hashés** avec Werkzeug (algorithme bcrypt)
- **Espace admin protégé** par un décorateur `@login_required` sur chaque route sensible
- **Pas d'injection SQL** possible grâce à l'ORM SQLAlchemy (requêtes paramétrées)
- **Validation serveur** des niveaux d'acquisition (whitelist, jamais de valeur libre)
- **Sessions sécurisées** Flask avec clé secrète configurée via variable d'environnement

---

## Barème couvert

| Critère | Points | Couvert |
|---------|--------|---------|
| Système de templates Flask | 10 | ✅ `base.html` + héritage Jinja2 |
| Code organisé et lisible | 10 | ✅ Routes, modèles, helpers séparés |
| Base de données + modèles | 10 | ✅ SQLAlchemy, 3 entités + User |
| Intégration BDD/Flask | 10 | ✅ Requêtes ORM, jointures |
| Authentification + espace protégé | 10 | ✅ Session + `@login_required` |
| Formulaire ajout/validation | 10 | ✅ `/admin/valider` avec filtre JS |
| Interface affichage/suppression | 10 | ✅ Dashboard admin |
| Docker | 10 | ✅ `Dockerfile` + `docker-compose.yml` |
| Sécurité | 10 | ✅ Hash, ORM, whitelist, sessions |
| Présentation | 10 | — |
