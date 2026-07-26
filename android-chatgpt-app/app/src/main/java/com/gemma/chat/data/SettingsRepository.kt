package com.gemma.chat.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.gemma.chat.model.OllamaConfig
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")

class SettingsRepository(private val context: Context) {
    
    companion object {
        val BASE_URL = stringPreferencesKey("base_url")
        val MODEL = stringPreferencesKey("model")
        val TEMPERATURE = floatPreferencesKey("temperature")
        val MAX_TOKENS = intPreferencesKey("max_tokens")
    }
    
    val configFlow: Flow<OllamaConfig> = context.dataStore.data.map { preferences ->
        OllamaConfig(
            baseUrl = preferences[BASE_URL] ?: "http://192.168.1.20:11434",
            model = preferences[MODEL] ?: "gemma3n:e4b",
            temperature = preferences[TEMPERATURE] ?: 0.7f,
            maxTokens = preferences[MAX_TOKENS] ?: 2048
        )
    }
    
    suspend fun saveConfig(config: OllamaConfig) {
        context.dataStore.edit { preferences ->
            preferences[BASE_URL] = config.baseUrl
            preferences[MODEL] = config.model
            preferences[TEMPERATURE] = config.temperature
            preferences[MAX_TOKENS] = config.maxTokens
        }
    }
    
    suspend fun resetConfig() {
        context.dataStore.edit { preferences ->
            preferences.clear()
        }
    }
}
