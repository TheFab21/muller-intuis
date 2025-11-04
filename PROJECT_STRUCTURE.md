# 📦 Muller Intuis Connect - Structure du projet

## 📁 Structure des fichiers

```
muller_intuis/
├── __init__.py                 # Initialisation intégration + API Client + Coordinator
├── config_flow.py              # Configuration via UI Home Assistant
├── const.py                    # Constantes et configuration
├── manifest.json               # Métadonnées de l'intégration
├── strings.json               # Traductions (base)
│
├── translations/
│   ├── en.json                # Traductions anglaises
│   └── fr.json                # Traductions françaises
│
├── README.md                   # Documentation complète
├── QUICKSTART.md              # Guide de démarrage rapide
├── MIGRATION_NODE_RED.md      # Guide de migration
├── FAQ.md                     # Questions fréquentes
├── CORRECTIONS.md             # Explications des corrections
├── .env.example               # Exemple de configuration
└── test_auth.py               # Script de test d'authentification
```

## 📝 Description des fichiers

### Fichiers principaux de l'intégration

#### `__init__.py`
- **Rôle** : Point d'entrée de l'intégration
- **Contient** :
  - `async_setup_entry()` - Configuration initiale
  - `MullerIntuisApiClient` - Client API pour Muller Intuitiv
  - `MullerIntuisDataUpdateCoordinator` - Gestion des mises à jour
- **Fonctionnalités** :
  - Authentification OAuth2 (password grant)
  - Rafraîchissement automatique des tokens
  - Appels API vers Muller Intuitiv
  - Coordination des mises à jour

#### `config_flow.py`
- **Rôle** : Interface de configuration dans Home Assistant
- **Contient** :
  - `ConfigFlow` - Flux de configuration UI
  - `validate_auth()` - Validation des credentials
- **Fonctionnalités** :
  - Formulaire de saisie (4 champs)
  - Validation des identifiants
  - Gestion des erreurs
  - Création de l'entrée de configuration

#### `const.py`
- **Rôle** : Définition des constantes
- **Contient** :
  - URLs de l'API
  - Paramètres OAuth2 Muller
  - Intervalles de mise à jour
  - Mappings des modes
  - Noms des services

#### `manifest.json`
- **Rôle** : Métadonnées de l'intégration
- **Contient** :
  - Domain : `muller_intuis`
  - Version : `1.0.1`
  - Dependencies et requirements
  - Liens documentation et issues

#### `strings.json`
- **Rôle** : Traductions de base
- **Contient** :
  - Labels des champs de configuration
  - Messages d'erreur
  - Messages d'information

### Fichiers de traduction

#### `translations/fr.json` et `translations/en.json`
- **Rôle** : Traductions complètes
- **Contient** :
  - Descriptions détaillées
  - Explications pour chaque champ
  - Messages contextuels

### Documentation

#### `README.md` (4000+ mots)
**Guide complet** couvrant :
- 🔑 Obtention des identifiants (guide pas à pas)
- 📥 Installation (HACS + manuelle)
- ⚙️ Configuration détaillée
- 🎛️ Entités créées
- 🔧 Utilisation et exemples
- 🐛 Dépannage complet
- 📊 Exemples Lovelace
- 🔄 Automatisations

#### `QUICKSTART.md` (500 mots)
**Guide express** pour démarrage en 5 minutes :
- Étapes numérotées
- Format ultra-concis
- Checklist rapide
- Dépannage express

#### `MIGRATION_NODE_RED.md` (3000+ mots)
**Guide de migration** depuis Node-RED :
- 🔄 Analyse du flux Node-RED
- 📋 Récupération des credentials
- 🔧 Équivalences fonctionnelles
- 🚀 Étapes de migration
- 🔍 Comparaisons détaillées
- 📊 Avantages/inconvénients

#### `FAQ.md` (5000+ mots)
**Questions fréquentes** organisées par thème :
- 🔐 Authentification
- 🔄 Fonctionnement
- 🏠 Fonctionnalités
- 🔧 Problèmes courants
- 🔀 Migration
- 🌐 API et technique
- 📊 Performance
- 🆘 Support

#### `CORRECTIONS.md` (2500+ mots)
**Documentation technique** :
- ❌ Problème initial identifié
- ✅ Solution correcte implémentée
- 📝 Changements détaillés dans le code
- 🎯 Avantages de la correction
- 🔍 Preuve de concept (Node-RED)
- 📊 Comparaisons techniques
- 🎓 Leçons apprises

### Fichiers utilitaires

#### `test_auth.py`
- **Rôle** : Script de test d'authentification
- **Utilisation** : `python3 test_auth.py`
- **Fonctionnalités** :
  - Test de connexion à l'API
  - Validation des credentials
  - Affichage des tokens (masqués)
  - Diagnostics détaillés
  - Conseils en cas d'erreur

#### `.env.example`
- **Rôle** : Template de configuration
- **Contient** :
  - Variables d'environnement nécessaires
  - Exemples de valeurs
  - Documentation inline

## 🔑 Points clés de l'implémentation

### Authentification OAuth2 (grant type: password)

```python
# Paramètres spécifiques à Muller Intuitiv
auth_data = {
    "client_id": "...",                    # De dev.netatmo.com
    "client_secret": "...",                # De dev.netatmo.com
    "username": "user@email.com",          # Email Muller Intuitiv
    "password": "...",                     # Mot de passe Muller
    "grant_type": "password",              # ← Resource Owner Password
    "user_prefix": "muller",               # ← Spécifique Muller !
    "scope": "read_muller write_muller",   # ← Scopes Muller !
}

# Endpoint spécifique
url = "https://app.muller-intuitiv.net/oauth2/token"
```

### Rafraîchissement automatique des tokens

```python
# Rafraîchissement 5 minutes avant expiration
if time.time() >= (self._token_expires_at - 300):
    await self._refresh_token()
```

### Gestion des erreurs

```python
# Erreur 401 → Re-authentification
if response.status == 401:
    self._access_token = None
    raise ConfigEntryAuthFailed("Authentication failed")
```

## 🎯 Workflow de l'intégration

```
1. Utilisateur configure l'intégration
   ↓
2. config_flow.py valide les credentials
   ↓
3. __init__.py initialise l'API client
   ↓
4. Premier appel : récupération du home_id
   ↓
5. DataUpdateCoordinator démarre
   ↓
6. Mises à jour toutes les 5 minutes
   ↓
7. Rafraîchissement auto des tokens
```

## 📊 Statistiques du projet

- **Lignes de code Python** : ~800 lignes
- **Lignes de documentation** : ~15,000 mots
- **Fichiers de traduction** : 2 langues (FR, EN)
- **Guides utilisateur** : 5 documents
- **Scripts utilitaires** : 1 script de test

## 🚀 Installation pour développement

```bash
# Cloner le projet
git clone https://github.com/TheFab21/muller-intuis.git

# Copier dans custom_components
cp -r muller-intuis/custom_components/muller_intuis \
      ~/.homeassistant/custom_components/

# Redémarrer Home Assistant
```

## 🧪 Tests

### Test manuel d'authentification
```bash
python3 test_auth.py
```

### Test dans Home Assistant
```yaml
# Activer les logs debug
logger:
  logs:
    custom_components.muller_intuis: debug
```

## 📦 Déploiement

### Via HACS
1. Ajouter le repository custom
2. Installer via HACS
3. Redémarrer HA

### Manuel
1. Copier le dossier dans `custom_components/`
2. Redémarrer HA

## 🔮 Roadmap future

- [ ] Platform `climate` (thermostats) - **Priority 1**
- [ ] Platform `sensor` (température, puissance, énergie) - **Priority 1**
- [ ] Platform `select` (plannings) - **Priority 1**
- [ ] Services de gestion des plannings - Priority 2
- [ ] Platform `switch` (boost mode) - Priority 3
- [ ] Support des scènes Muller - Priority 3
- [ ] Statistiques avancées - Priority 4

## 🤝 Contribution

### Prérequis
- Python 3.11+
- Home Assistant 2024.1+
- Accès à un système Muller Intuitiv

### Process
1. Fork le projet
2. Créer une branche feature
3. Développer et tester
4. Ouvrir une Pull Request

## 📄 Licence

MIT License - Voir LICENSE pour détails

## 👏 Remerciements

- **TheFab21** - Auteur original
- **Netatmo** - API Energy
- **Muller** - Système Intuitiv
- **Communauté Home Assistant** - Support et feedback

---

**Version** : 1.0.1  
**Date** : Novembre 2025  
**Basé sur** : Flux Node-RED Muller Intuitiv  
**Testé avec** : Home Assistant 2024.11
