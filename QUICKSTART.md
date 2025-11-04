# 🚀 Guide de démarrage rapide - Muller Intuis Connect

## En 5 minutes chrono ⏱️

### 1️⃣ Créer une application Netatmo (2 min)

1. Allez sur **[dev.netatmo.com](https://dev.netatmo.com)**
2. Connectez-vous avec vos identifiants **Muller Intuitiv**
3. Cliquez sur **"Create"**
4. Remplissez les champs requis (nom, description, etc.)
5. **Notez** votre **Client ID** et **Client Secret**

### 2️⃣ Installer l'intégration (1 min)

#### Via HACS (recommandé)
```
HACS → Intégrations → Menu ⋮ → Dépôts personnalisés
→ Ajouter : https://github.com/TheFab21/muller-intuis
→ Télécharger → Redémarrer HA
```

#### Manuellement
```bash
# Copier le dossier muller_intuis dans custom_components/
# Redémarrer Home Assistant
```

### 3️⃣ Configurer (2 min)

```
Paramètres → Appareils et services → + Ajouter une intégration
→ Rechercher "Muller Intuis Connect"
→ Entrer vos 4 identifiants :
   • Client ID (de dev.netatmo.com)
   • Client Secret (de dev.netatmo.com)  
   • Email (de l'app Muller Intuitiv)
   • Mot de passe (de l'app Muller Intuitiv)
→ Soumettre
```

### ✅ C'est terminé !

Vos radiateurs apparaissent maintenant comme entités `climate.*` dans Home Assistant.

## 🎯 Premiers pas

### Contrôler un radiateur

Via l'interface :
```
Developer Tools → Services → climate.set_temperature
Entity: climate.muller_salon
Temperature: 21
→ Call Service
```

Via une automation :
```yaml
service: climate.set_temperature
target:
  entity_id: climate.muller_salon
data:
  temperature: 21
```

### Changer de planning

```yaml
service: select.select_option
target:
  entity_id: select.muller_intuis_active_schedule
data:
  option: "Planning Jour"
```

## 📱 Carte Lovelace rapide

```yaml
type: thermostat
entity: climate.muller_salon
name: Salon
```

## ❓ Problème ?

### Test rapide d'authentification

```bash
python3 test_auth.py
```

### Vérifier les logs

```
Paramètres → Système → Journaux
Rechercher : "muller_intuis"
```

## 📚 Documentation complète

- [README.md](README.md) - Documentation complète
- [MIGRATION_NODE_RED.md](MIGRATION_NODE_RED.md) - Migration depuis Node-RED

## 🆘 Erreurs courantes

| Erreur | Solution |
|--------|----------|
| `invalid_auth` | Vérifiez email/password Muller Intuitiv |
| `cannot_connect` | Vérifiez votre connexion internet |
| `already_configured` | Supprimez l'ancienne config et recommencez |
| `No homes found` | Vérifiez que vos radiateurs sont bien dans l'app Muller |

---

**Besoin d'aide ?** → Ouvrez une [issue sur GitHub](https://github.com/TheFab21/muller-intuis/issues)
