# Portfolio Raphaël Macker — SAE 2.3 Flask

Portfolio dynamique avec Flask, MySQL et Docker.

## Structure du projet

```
sae23/
├── app.py               # Application Flask principale
├── config.py            # Profil étudiant (à modifier)
├── requirements.txt     # Dépendances Python
├── Dockerfile           # Image Docker Flask
├── docker-compose.yml   # Orchestration MySQL + Flask
├── templates/
│   ├── base.html        # Template de base (navbar, footer)
│   ├── index.html       # Page profil
│   ├── competences.html # Récapitulatif public
│   ├── login.html       # Page de connexion
│   └── admin/
│       ├── dashboard.html  # Dashboard admin protégé
│       └── valider.html    # Formulaire de validation
└── static/
    ├── css/
    │   ├── style.css    # Design système du portfolio
    │   └── app.css      # Styles spécifiques Flask
    ├── js/
    └── img/             # Photos et images
```

## Lancement avec Docker (recommandé)

```bash
# Construire et démarrer les conteneurs
docker-compose up --build

# Le site est accessible sur http://localhost:5000
```

## Lancement en local (développement)

```bash
# Installer les dépendances
pip install -r requirements.txt

# Configurer MySQL local dans app.py ou variables d'env
export MYSQL_HOST=localhost
export MYSQL_USER=raphael
export MYSQL_PASSWORD=password
export MYSQL_DATABASE=portfolio

# Lancer Flask
python app.py
```

## Compte administrateur par défaut

- **Identifiant :** `admin`
- **Mot de passe :** `admin123`

⚠️ Changez le mot de passe en production !

## Pages

| URL | Description | Accès |
|-----|-------------|-------|
| `/` | Page profil avec stats | Public |
| `/competences` | Tableau récapitulatif | Public |
| `/login` | Connexion admin | Public |
| `/admin` | Dashboard — voir et supprimer | 🔒 Protégé |
| `/admin/valider` | Valider une compétence | 🔒 Protégé |
| `/logout` | Déconnexion | — |

## Sécurité

- Mots de passe hashés avec Werkzeug (bcrypt)
- Protection CSRF via sessions Flask sécurisées
- Requêtes SQL via ORM SQLAlchemy (pas d'injection possible)
- Espace admin protégé par décorateur `@login_required`
- Validation des données côté serveur (niveaux whitelist)
