# 🎮 Motdle — Bot Discord Wordle Français

Un bot Discord pour jouer au **Wordle en français** avec vos amis ! Chaque jour, un nouveau mot à deviner en 6 essais maximum, avec comparaisons de résultats et système de notifications.

## 🌟 Fonctionnalités

### Gameplay
- **Jeu quotidien** : un mot différent chaque jour, identique pour tous
- **6 essais** : trouvez le mot en maximum 6 tentatives
- **Feedback visuels** : tiles colorées (vert = correct, jaune = présent, gris = absent)
- **Clavier AZERTY** : état des lettres mis à jour au fur et à mesure

### Système de Classement & Partage
- **Challenge du jour** (`/classement`) : voir les résultats de tous les joueurs
  - Affichage **en deux temps** : d'abord masqué, puis bouton "Voir les détails" pour révéler les grilles des joueurs qui ont activé le partage
  - Chaque joueur ne voit ses propres lettres que s'il a terminé la partie
- **Message de partage** (`/partage`) : afficher publiquement les résultats du jour sans spolier
  - Bouton "Jouer" pour permettre aux autres de lancer une partie
  - Les grilles sont toujours masquées (aucune lettre visible)

### Notifications & Préférences
- **Message quotidien à 9h** : rappel dans le salon, avec deux toggles
  - 🔔 **Pingez-moi** : reçoit un DM privé à 16h si pas encore joué
  - 👁 **Partage d'activité** : autorise les autres à voir ses mots dans le classement
- **DM automatique à 16h** : rappel pour les joueurs qui ont activé le ping

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.12+
- `uv` (gestionnaire de paquets : https://github.com/astral-sh/uv)
- Un serveur Discord (ou accès à en modifier les paramètres)
- Un bot Discord créé dans le [Discord Developer Portal](https://discord.com/developers/applications)

### Installation

1. **Cloner/télécharger le projet**
   ```bash
   git clone https://github.com/Omegalpha44/motdle
   ```

2. **Créer/reconstruire le virtualenv**
   ```bash
   uv venv --clear
   uv sync
   ```

3. **Configurer les variables d'environnement**

   Créer un fichier `.env` à la racine :
   ```env
   DISCORD_TOKEN=votre_token_bot
   SALON=1234567890
   ```

   - `DISCORD_TOKEN` : token du bot (Developer Portal → Bot → TOKEN)
   - `SALON` : ID du canal où le bot envoie les messages (clic droit → Copier l'ID du salon)

4. **Configurer les permissions Discord**

   Dans le Developer Portal, pour votre bot :
   - **Permissions requises** :
     - Envoyer des messages
     - Envoyer des messages privés
     - Utiliser les commandes slash
     - Lire les historiques de messages
   - **Intents requis** :
     - ✅ **Server Members Intent** (obligatoire pour les DM de rappel)
     - ✅ Intents par défaut

5. **Lancer le bot**
   ```bash
   uv run python -m motdle
   ```

## 📋 Commandes

### Joueur
- **`/motdle`** — Démarrer/reprendre une partie du jour
- **`/classement`** — Voir les résultats du Challenge du jour
  - Affiche d'abord les grilles masquées
  - Bouton "Voir les détails" pour révéler les grilles (si partage activé)
- **`/partage`** — Afficher les résultats publiquement dans le salon (auto-déclenché à la fin d'une partie)

### Admin
- **`/admin reset`** — Vider complètement la base de données
- **`/admin populate`** — Générer 20 joueurs fictifs pour tester l'affichage
- **`/admin daily`** — Forcer l'envoi du message quotidien maintenant

## 🗄️ Base de Données

SQLite, deux tables :

| Table | Colonnes | Rôle |
|-------|----------|------|
| `game_results` | user_id, date, attempts, won, grid | Résultats quotidiens |
| `user_preferences` | user_id, ping_enabled, share_activity | Préférences (ping, partage) |

La DB est auto-nettoyée : les résultats antérieurs à aujourd'hui sont supprimés automatiquement.

## 🛠️ Architecture

```
src/motdle/
├── core/
│   ├── words.py          # Dictionnaire 5-lettres, sélection du mot du jour
│   ├── evaluator.py      # Algo Wordle (2-pass pour les doublons)
│   ├── game.py           # GameState, validation, logique du jeu
│   └── database.py       # SQLite, requêtes, gestion prefs
├── bot/
│   ├── client.py         # MotdleBot, setup des cogs/vues
│   ├── cogs/
│   │   ├── wordle.py     # Slash commands (/motdle, /classement, /partage, /admin)
│   │   └── scheduler.py  # Tâches planifiées (9h, 16h)
│   └── views/
│       ├── game_view.py           # Boutons Deviner + Classement
│       ├── guess_modal.py         # Modal pour entrer un mot
│       ├── daily_view.py          # Toggles Ping + Partage
│       ├── play_button.py         # Bouton Jouer (sur /partage)
│       ├── classement_view.py     # Bouton Voir les détails
│       ├── image_renderer.py      # Rendu PNG des grilles
│       └── renderer.py            # (non utilisé)
└── __main__.py           # Entrée, mode terminal/bot
```

## 🎨 Affichage

### Grille de Jeu
- 5×6 plateau avec lettres et couleurs
- Clavier AZERTY avec état des lettres
- Embed coloré : vert (gagné), rouge (perdu), blurple (en cours)

### Challenge du Jour
- Image multi-cartes : chaque joueur = 1 carte (32×209px)
- Mini-grilles 5×6, statut (✓ Réussi / ✗ Perdu), rang
- **Lettres visibles** : seulement si joueur a fini sa partie + partage activé
- **Lettres masquées** : couleurs uniquement sinon

## 🔒 Sécurité & Permissions

- Toutes les commandes sont restreintes au **canal SALON** (`#motdle` généralement)
- Les commandes admin requièrent le statut **Administrateur** Discord
- Les messages éphémères (privés) ne sont visibles que par l'utilisateur cible
- Le bot a besoin de **Server Members Intent** pour envoyer des DM (activé en code + Developer Portal)

## 🧪 Tests

```bash
uv run python -m pytest tests/ -v
```

19 tests ; tous les modules core sont couverts (evaluator, game, database).

## 📝 Notes de Développement

### Mot du jour
Sélectionné **déterministiquement** selon la date :
```python
sha256(date_iso) % nb_mots  # Même mot pour tous, même jour
```

### Révélation des grilles
- Par défaut : **caché** (couleurs uniquement)
- Révélé si : joueur a **fini** ET joueur a **activé partage d'activité**
- `/partage` public : **jamais de lettres** (seules les couleurs)

### Scheduler
Tâches à heures fixes (fuseau horaire **Europe/Paris**) :
- **9h00** : message quotidien avec toggles
- **16h00** : DM rappel aux joueurs avec ping activé (si pas fini)

## 🐛 Troubleshooting

### Le bot ne démarre pas
- Vérifier `DISCORD_TOKEN` dans `.env`
- Vérifier que le bot **Server Members Intent** est ✅ dans Developer Portal
- Reconstruire le venv : `uv venv --clear && uv sync`

### 403 Forbidden sur `/admin daily`
- Le bot n'a pas la permission **Envoyer des messages** dans le salon
- **Paramètres du salon → Permissions → [Bot] → Envoyer des messages : ✅**

### Pas de DM à 16h
- Vérifier que l'utilisateur a activé le toggle "Pingez-moi"
- Vérifier que bot n'est pas bloqué (paramètres confidentialité Discord)

## 📄 Licence

Libre d'usage. Développé pour une Rasberry pi 5 8go.

---

**Amusez-vous bien ! 🎮**
