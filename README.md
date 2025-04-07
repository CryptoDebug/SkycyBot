# SkycyBot

Un bot Discord polyvalent avec des fonctionnalités de modération, de jeux et de statistiques.

## Fonctionnalités

### Système de modération
- Protection anti-spam
- Protection anti-liens
- Système de sanctions (avertissements, exclusions temporaires, bannissements)

### Système de jeux
- Jeu du pendu
- Système de points pour les utilisateurs
- Classement des meilleurs joueurs

### Système de statistiques
- Suivi des messages, commandes et réactions
- Statistiques par utilisateur et par serveur
- Commandes pour afficher les statistiques

### Système de bienvenue
- Message de bienvenue personnalisable
- Système de vérification pour les nouveaux membres
- Attribution automatique de rôles

## Installation

1. Clonez ce dépôt
2. Installez les dépendances avec `pip install -r requirements.txt`
3. Configurez votre fichier `.env` avec vos tokens Discord
4. Lancez le bot avec `python main.py`

## Configuration

Le bot peut être configuré via des commandes slash:
- `/welcome` - Configure le système de bienvenue
- `/welcomeinfo` - Affiche la configuration actuelle du système de bienvenue
- `/serverinfo` - Affiche les statistiques du serveur

## Licence

Ce projet est sous licence MIT. 