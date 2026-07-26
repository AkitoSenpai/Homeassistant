# 📱 Gemma Chat - Application Android

Application Android native pour converser avec votre IA locale (Ollama) - Interface style ChatGPT.

## 🎯 Démarrage rapide

### Pré-requis
- Serveur Ollama avec modèle installé
- Android Studio (Hedgehog ou plus récent)
- Téléphone Android (API 24+)

### Installation

1. **Configurer Ollama** sur votre serveur :
```bash
ollama pull gemma3n:e4b
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

2. **Ouvrir dans Android Studio** :
```bash
cd android-chatgpt-app
# Ouvrir le dossier dans Android Studio
```

3. **Build & Run** :
```bash
./gradlew assembleDebug
```

## 📱 Fonctionnalités

| Fonctionnalité | Description |
|----------------|-------------|
| 💬 Chat en temps réel | Streaming des réponses Ollama |
| 🎨 Interface moderne | Bulles de chat style ChatGPT |
| 🌙 Thème adaptatif | Sombre/clair automatique |
| ⚙️ Configuration | URL, modèle, température |
| 🔒 100% local | Aucune donnée envoyée sur Internet |

## 📡 Configuration

Dans l'app, allez dans Paramètres et configurez :
- **URL Ollama** : `http://IP_SERVEUR:11434`
- **Modèle** : `gemma3n:e4b` (ou autre)
- **Température** : 0.7 (recommandé)
- **Tokens max** : 2048

## 🏗️ Architecture

```
android-chatgpt-app/
├── app/
│   ├── build.gradle.kts          # Configuration Gradle
│   └── src/main/
│       ├── AndroidManifest.xml
│       └── java/com/gemma/chat/
│           ├── MainActivity.kt
│           ├── model/            # Modèles de données
│           ├── data/             # API Ollama + DataStore
│           ├── viewmodel/        # ChatViewModel
│           └── ui/
│               ├── theme/        # Material 3 Theme
│               └── screens/      # ChatScreen + SettingsScreen
└── build.gradle.kts
```

## 📜 Licence

MIT
