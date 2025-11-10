# 🔄 Mise à jour rapide v1.5.1

## ⚠️ Correction urgente : KeyError 'name'

Cette version corrige l'erreur :
```
KeyError: 'name'
File climate.py, line 98
```

---

## 📦 Fichiers à remplacer

Tu as **2 options** selon ta préférence :

### Option 1 : Remplacement rapide (Recommandé)

Remplace uniquement ces 3 fichiers dans `custom_components/muller_intuis/` :

1. **climate.py** ⭐ (correction principale)
2. **sensor.py** ⭐ (correction capteurs)
3. **manifest.json** (mise à jour version)

### Option 2 : Réinstallation complète

Remplace tout le dossier `muller_intuis` par le nouveau.

---

## 🚀 Procédure (Option 1 - 2 minutes)

### Étape 1 : Arrêter Home Assistant (optionnel mais recommandé)

```
Paramètres → Système → Arrêter Home Assistant
```

### Étape 2 : Via Samba/SSH

```bash
# Remplacer les fichiers
cd /config/custom_components/muller_intuis/

# Backup (optionnel)
cp climate.py climate.py.backup
cp sensor.py sensor.py.backup

# Copier les nouveaux fichiers
# (depuis le dossier muller_intuis_fixed)
```

### Étape 3 : Redémarrer Home Assistant

```
Paramètres → Système → Redémarrer
```

### Étape 4 : Vérifier

1. Va dans **Paramètres → Appareils et services**
2. Clique sur **Muller Intuis Connect**
3. Vérifie que les entités apparaissent sans erreur

---

## 🔍 Vérification de la version

Après redémarrage, vérifie dans les logs :

```
Paramètres → Système → Journaux
```

Tu devrais voir :
```
[custom_components.muller_intuis] Found X rooms
[custom_components.muller_intuis] Room data: {...}
```

---

## 🐛 Si le problème persiste

Active les logs debug pour identifier la structure exacte :

**Dans `configuration.yaml` :**
```yaml
logger:
  default: info
  logs:
    custom_components.muller_intuis: debug
```

Redémarre et partage-moi la ligne `"Room data:"` des logs.

---

## ✅ Correction appliquée

**Avant :**
```python
self._attr_name = f"Muller {room['name']}"  # ❌ Crash si 'name' absent
```

**Après :**
```python
room_name = room.get("name") or room.get("module_name") or room.get("id")
self._attr_name = f"Muller {room_name}"  # ✅ Toujours un nom
```

---

## 📊 Compatibilité

Cette version est compatible avec toutes les structures API Muller/Netatmo :
- ✅ room['name']
- ✅ room['module_name']
- ✅ room['id'] (fallback)

---

## 🎯 Résumé

1. ⬇️ Télécharger les 3 fichiers corrigés
2. 📁 Remplacer dans `custom_components/muller_intuis/`
3. 🔄 Redémarrer Home Assistant
4. ✅ Vérifier que tout fonctionne

**C'est tout ! 🚀**

---

**Version** : 1.5.1  
**Date** : 6 novembre 2024  
**Correction** : KeyError 'name'
