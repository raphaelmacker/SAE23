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

> ⚠️ À changer avant tout déploiement en production.

---

## Installation et lancement (VM Ubuntu)

### Étape 1 — Préparer la VM

Le projet tourne sur une **VM Ubuntu** (VirtualBox ou VMware).  
La carte réseau doit être en mode **NAT** pour avoir accès à Internet.

> Dans VirtualBox : clic droit sur la VM → Configuration → Réseau → Mode d'accès réseau : **NAT**

### Étape 2 — Installer Docker

Dans le terminal de la VM :

```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER
```

Fermer et rouvrir le terminal pour appliquer les droits, ou faire :

```bash
newgrp docker
```

### Étape 3 — Récupérer le projet

Copier le fichier `sae23_portfolio_flask.zip` dans la VM, puis :

```bash
unzip sae23_portfolio_flask.zip
cd sae23
```

### Étape 4 — Lancer le projet

```bash
sudo docker-compose up --build
```

La première fois ça prend 2-5 minutes (téléchargement des images Docker).  
Le site est ensuite accessible sur **http://localhost:5000** depuis la VM.

Pour y accéder depuis la machine hôte, trouver l'IP de la VM :

```bash
ip a
```

Puis ouvrir **http://[IP-DE-LA-VM]:5000** dans le navigateur.

### Étape 5 — Arrêter le projet

```bash
# Ctrl+C dans le terminal, puis :
sudo docker-compose down
```

### Relancer après un arrêt (sans rebuild)

```bash
sudo docker-compose up
```

---

## Problèmes rencontrés et solutions

### ❌ Permission denied sur Docker
```
PermissionError: [Errno 13] Permission denied
```
**Solution :**
```bash
sudo usermod -aG docker $USER
# Fermer et rouvrir le terminal, puis relancer avec sudo :
sudo docker-compose up --build
```

---

### ❌ Impossible de télécharger les images (timeout réseau)
```
dial tcp 44.220.103.105:443: i/o timeout
```
**Cause :** La VM n'a pas accès à Internet, ou le réseau de l'IUT utilise un proxy.  
**Solution 1 :** Vérifier que la carte réseau est en mode **NAT** dans VirtualBox.  
**Solution 2 :** Si un proxy est requis, l'ajouter dans `docker-compose.yml` :

```yaml
web:
  build:
    context: .
    args:
      - HTTP_PROXY=http://adresse-proxy:port
      - HTTPS_PROXY=http://adresse-proxy:port
```

Et dans le `Dockerfile`, après `FROM python:3.12-slim` :

```dockerfile
ARG HTTP_PROXY
ARG HTTPS_PROXY
ENV http_proxy=$HTTP_PROXY
ENV https_proxy=$HTTPS_PROXY
```

---

### ❌ Flask démarre avant que MySQL soit prêt
```
sqlalchemy.exc.OperationalError: Can't connect to MySQL server on 'db'
```
**Cause :** Flask essaie de se connecter à MySQL avant qu'il ait fini de démarrer.  
**Solution :** Le bloc d'initialisation dans `app.py` inclut une boucle de retry qui retente la connexion toutes les 3 secondes jusqu'à 10 fois.

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

---

## Sécurité

- **Mots de passe hashés** avec Werkzeug (algorithme bcrypt)
- **Espace admin protégé** par un décorateur `@login_required` sur chaque route sensible
- **Pas d'injection SQL** possible grâce à l'ORM SQLAlchemy (requêtes paramétrées)
- **Validation serveur** des niveaux d'acquisition (whitelist, jamais de valeur libre)
- **Sessions sécurisées** Flask avec clé secrète configurée via variable d'environnement
