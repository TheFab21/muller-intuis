# 🎨 Schéma visuel des corrections

## 📊 Architecture de l'intégration

```
┌─────────────────────────────────────────────────────────────────┐
│                    HOME ASSISTANT                               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │           Interface utilisateur                         │  │
│  │                                                         │  │
│  │  [OFF] [AUTO] [HEAT]  ← Modes HVAC                    │  │
│  │                                                         │  │
│  │  Presets: [schedule] [away] [frost_protection]        │  │
│  │                                                         │  │
│  │  🌡️ Température: 19.5°C                              │  │
│  │  📊 Puissance: 45%                                    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                            ↕                                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │        climate.py (Entités thermostat)                  │  │
│  │                                                         │  │
│  │  • async_set_hvac_mode()                              │  │
│  │  • async_set_temperature()                            │  │
│  │  • async_set_preset_mode()                            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                            ↕                                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │    __init__.py (Coordinateur) ⭐ CORRIGÉ               │  │
│  │                                                         │  │
│  │  • async_set_home_mode()                              │  │
│  │  • _validate_endtime() ← NOUVEAU                      │  │
│  │    ├─ Vérifie min 5 min futur                        │  │
│  │    ├─ Vérifie max 1 an                                │  │
│  │    └─ Fallback 3h si invalide                         │  │
│  │                                                         │  │
│  │  • async_ensure_token_valid()                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                            ↕                                   │
└─────────────────────────────────────────────────────────────────┘
                             ↕
          ┌──────────────────────────────────────┐
          │   API Muller Intuitiv / Netatmo      │
          │   https://app.muller-intuitiv.net    │
          │                                      │
          │   POST /api/setthermmode             │
          │   {                                  │
          │     "mode": "off|schedule|away|hg",  │
          │     "endtime": <validated_timestamp> │
          │   }                                  │
          └──────────────────────────────────────┘
                             ↕
          ┌──────────────────────────────────────┐
          │      Radiateurs Muller Intuis        │
          │         🔥 🔥 🔥 🔥 🔥                │
          └──────────────────────────────────────┘
```

---

## 🔄 Flux de validation endtime

### AVANT (avec erreur)
```
User clique OFF
       ↓
climate.py envoie mode="off" + endtime=<any_timestamp>
       ↓
API rejette: "endtime in past" ❌
```

### APRÈS (corrigé)
```
User clique OFF
       ↓
climate.py → async_set_hvac_mode("off")
       ↓
coordinator → async_set_home_mode("off", endtime=None)
       ↓
_validate_endtime(None, "off")
├─ Mode "off" → return None ✅
└─ Pas d'endtime dans payload
       ↓
API accepte ✅
       ↓
Radiateurs OFF 🔥➡️❄️
```

---

## 🎯 Mapping des modes

### Interface HA → API
```
┌──────────────────┐
│  HVAC Modes      │
├──────────────────┤
│  OFF    ────────┼──→  "off"      (arrêt complet)
│  AUTO   ────────┼──→  "schedule" (planning)
│  HEAT   ────────┼──→  "manual"   (température)
└──────────────────┘

┌──────────────────┐
│  Presets         │
├──────────────────┤
│  schedule ──────┼──→  "schedule"
│  manual ────────┼──→  "manual"
│  away ──────────┼──→  "away"
│  frost_protect ─┼──→  "hg"       (hors-gel)
└──────────────────┘
```

---

## ⏰ Logique de validation endtime

```
┌─────────────────────────────────────────────────────────┐
│              _validate_endtime(endtime, mode)           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Si endtime is None:                                   │
│    ├─ Mode in ["off", "schedule", "hg"]               │
│    │    └─→ return None (pas d'endtime nécessaire)    │
│    │                                                    │
│    └─ Mode in ["away", "manual"]                      │
│         └─→ return now + 3 heures (défaut)            │
│                                                         │
│  Si endtime fourni:                                    │
│    ├─ now = timestamp actuel                          │
│    ├─ min_time = now + 5 min                          │
│    ├─ max_time = now + 1 an                           │
│    │                                                    │
│    ├─ Si endtime < min_time:                          │
│    │    └─→ return now + 3h (trop tôt)                │
│    │                                                    │
│    ├─ Si endtime > max_time:                          │
│    │    └─→ return now + 3h (trop tard)               │
│    │                                                    │
│    └─ Sinon:                                           │
│         └─→ return endtime (valide ✅)                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔀 Comparaison Node-RED vs HA

### Node-RED (actuel)
```
input_select.mode
       ↓
Transco ("Home" → "schedule", "Away" → "away", "Hors Gel" → "hg")
       ↓
input_datetime.away_until_date
       ↓
moment (convertir en timestamp)
       ↓
Fonction validation (5 min min, 1 an max, fallback 3h)
       ↓
Set payload JSON
       ↓
HTTP POST /api/setthermmode
```

### Home Assistant (nouveau)
```
climate.muller_salon
       ↓
set_hvac_mode("off")  ou  set_preset_mode("away")
       ↓
coordinator.async_set_home_mode(mode, endtime)
       ↓
_validate_endtime() ← MÊME LOGIQUE QUE NODE-RED
       ↓
HTTP POST /api/setthermmode
```

✅ **Même résultat, mais intégré nativement dans HA**

---

## 📊 Modes disponibles - Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    MODES DISPONIBLES                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔴 OFF (HVAC Mode)                                        │
│     └─→ API: "off"                                         │
│     └─→ Endtime: aucun                                     │
│     └─→ Action: Arrêt complet                             │
│                                                             │
│  🔵 AUTO (HVAC Mode)                                       │
│     └─→ API: "schedule"                                    │
│     └─→ Endtime: aucun                                     │
│     └─→ Action: Suit le planning                          │
│                                                             │
│  🟢 HEAT (HVAC Mode)                                       │
│     └─→ API: "manual"                                      │
│     └─→ Endtime: 3h (auto)                                │
│     └─→ Action: Température manuelle                       │
│                                                             │
│  🟡 away (Preset)                                          │
│     └─→ API: "away"                                        │
│     └─→ Endtime: 3h (auto)                                │
│     └─→ Action: Mode absent                               │
│                                                             │
│  ❄️  frost_protection (Preset)                            │
│     └─→ API: "hg"                                          │
│     └─→ Endtime: aucun                                     │
│     └─→ Action: Hors-gel ~7°C                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 Scénarios de test

### Test 1: Mode OFF
```
[User] Clique sur OFF
   ↓
[HA] set_hvac_mode("off")
   ↓
[Code] async_set_home_mode("off", endtime=None)
   ↓
[Validation] mode="off" → endtime reste None
   ↓
[API] POST {"mode": "off"}  (PAS d'endtime)
   ↓
[Résultat] ✅ Radiateurs complètement éteints
```

### Test 2: Mode hors-gel
```
[User] Sélectionne preset "frost_protection"
   ↓
[HA] set_preset_mode("frost_protection")
   ↓
[Code] async_set_home_mode("hg", endtime=None)
   ↓
[Validation] mode="hg" → endtime reste None
   ↓
[API] POST {"mode": "hg"}  (PAS d'endtime)
   ↓
[Résultat] ✅ Hors-gel activé (~7°C)
```

### Test 3: Mode absent
```
[User] Sélectionne preset "away"
   ↓
[HA] set_preset_mode("away")
   ↓
[Code] async_set_home_mode("away", endtime=None)
   ↓
[Validation] mode="away" + endtime=None → endtime = now + 3h
   ↓
[API] POST {"mode": "away", "endtime": <timestamp+3h>}
   ↓
[Résultat] ✅ Mode absent pour 3 heures
```

### Test 4: Endtime invalide (dans le passé)
```
[User] Tente de définir endtime dans le passé
   ↓
[Code] async_set_home_mode("away", endtime=1699000000)
   ↓
[Validation] endtime < (now + 5min) → endtime = now + 3h
   ↓
[API] POST {"mode": "away", "endtime": <timestamp+3h>}
   ↓
[Résultat] ✅ Pas d'erreur, fallback automatique
```

---

## 🎉 Résumé visuel

```
┌────────────────────────────────────────────────────────────┐
│                    AVANT                                   │
├────────────────────────────────────────────────────────────┤
│  ❌ "endtime in past" errors                              │
│  ❌ OFF = hors-gel seulement                              │
│  ❌ Pas de vrai arrêt                                     │
│  ❌ Validation manuelle nécessaire (Node-RED)             │
└────────────────────────────────────────────────────────────┘
                         ↓
                  📦 CORRECTION
                         ↓
┌────────────────────────────────────────────────────────────┐
│                    APRÈS                                   │
├────────────────────────────────────────────────────────────┤
│  ✅ Validation automatique endtime                        │
│  ✅ OFF = arrêt complet                                   │
│  ✅ Hors-gel = preset distinct                            │
│  ✅ Compatible Node-RED                                   │
│  ✅ Automatisations HA simplifiées                        │
└────────────────────────────────────────────────────────────┘
```

---

**Ce schéma résume visuellement toutes les corrections apportées !** 🎨
