# 🤖 Gemma Chat - Application Android

Application Android native pour converser avec votre IA locale via Ollama. Interface moderne inspirée de ChatGPT.

## ✨ Fonctionnalités

- 💬 **Interface chat moderne** avec bulles de conversation style ChatGPT
- 🔄 **Streaming en temps réel** - voyez la réponse se construire mot par mot
- 🎨 **Thème sombre/clair** automatique selon les préférences système
- ⚙️ **Configuration flexible** - URL Ollama, modèle, température, tokens
- 📱 **Support complet du clavier** et du redimensionnement
- 🔒 **Connexion locale** - vos données restent sur votre réseau

## 📋 Pré-requis

- **Android Studio** Hedgehog (2023.1.1) ou plus récent
- **SDK Android** : API 24+ (Android 7.0 Nougat)
- **Serveur Ollama** avec modèle installé (ex: `gemma3n:e4b`)
- **Réseau** : téléphone et serveur Ollama sur le même réseau local

## 🚀 Installation

### 1. Cloner le projet

```bash
cd android-chatgpt-app
```

### 2. Ouvrir dans Android Studio

- File > Open > Sélectionner le dossier `android-chatgpt-app`
- Attendre la synchronisation Gradle

### 3. Configurer votre serveur Ollama

Lancez Ollama sur votre serveur avec le modèle Gemma :

```bash
# Installer Ollama si pas déjà fait
curl -fsSL https://ollama.com/install.sh | sh

# Télécharger le modèle
ollama pull gemma3n:e4b

# Démarrer Ollama (écoute sur 0.0.0.0:11434)
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

### 4. Compiler et installer

```bash
./gradlew assembleDebug
```

Ou utilisez Android Studio : Build > Build Bundle(s) / APK(s) > Build APK(s)

L'APK sera dans : `app/build/outputs/apk/debug/app-debug.apk`

## 📱 Configuration dans l'app

1. Ouvrez l'app et allez dans **Paramètres** (icône ⚙️)
2. Entrez l'URL de votre serveur Ollama :
   - Format : `http://IP_SERVEUR:11434`
   - Exemple : `http://192.168.1.20:11434`
3. Appuyez sur **Tester** pour vérifier la connexion
4. Sélectionnez votre modèle dans la liste déroulante
5. Ajustez la température et les tokens si besoin
6. **Enregistrez** et revenez au chat

## 🏗️ Architecture

```
app/
├── src/main/
│   ├── java/com/gemma/chat/
│   │   ├── MainActivity.kt          # Point d'entrée
│   │   ├── model/                   # Modèles de données
│   │   │   └── Models.kt
│   │   ├── data/                    # Couche données
│   │   │   ├── OllamaApiModels.kt   # Modèles API Ollama
│   │   │   ├── OllamaApiService.kt  # Interface Retrofit
│   │   │   ├── OllamaRepository.kt  # Repository avec streaming
│   │   │   └── SettingsRepository.kt # Préférences DataStore
│   │   ├── viewmodel/               # ViewModel
│   │   │   └── ChatViewModel.kt
│   │   └── ui/
│   │       ├── theme/               # Thème Material 3
│   │       └── screens/             # Écrans Compose
│   │           ├── ChatScreen.kt    # Écran principal
│   │           └── SettingsScreen.kt
│   └── res/                         # Ressources Android
└── build.gradle.kts
```

## 🔧 Technologies utilisées

| Technologie | Usage |
|-------------|-------|
| **Kotlin** | Langage principal |
| **Jetpack Compose** | UI déclarative native |
| **Material 3** | Design system Google |
| **Retrofit + OkHttp** | Client HTTP pour Ollama |
| **Kotlin Coroutines** | Programmation asynchrone |
| **DataStore** | Persistance des paramètres |
| **Navigation Compose** | Navigation entre écrans |

## 📡 API Ollama utilisée

L'application utilise l'endpoint **Chat** d'Ollama :

```
POST /api/chat
Content-Type: application/json

{
  "model": "gemma3n:e4b",
  "messages": [
    {"role": "user", "content": "Bonjour !"}
  ],
  "stream": true,
  "options": {
    "temperature": 0.7,
    "num_predict": 2048
  }
}
```

Le streaming est activé pour afficher la réponse en temps réel.

## 🔒 Sécurité

- `android:usesCleartextTraffic="true"` est activé pour permettre les connexions HTTP locales
- Ajoutez `network_security_config.xml` pour plus de sécurité si besoin
- L'application ne fait AUCUN appel externe - tout reste sur votre réseau local

## 🐛 Dépannage

| Problème | Solution |
|----------|----------|
| "Hors ligne" | Vérifiez que Ollama tourne et que l'URL est correcte |
| "Aucun modèle" | Lancez `ollama pull gemma3n:e4b` sur le serveur |
| Connexion refusée | Vérifiez le pare-feu (port 11434) |
| Streaming ne marche pas | Vérifiez que `stream: true` dans la requête |

## 📜 Licence

MIT - Faites-en ce que vous voulez !
