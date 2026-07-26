package com.gemma.chat.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.gemma.chat.data.OllamaChatMessage
import com.gemma.chat.data.OllamaRepository
import com.gemma.chat.data.SettingsRepository
import com.gemma.chat.model.ChatMessage
import com.gemma.chat.model.OllamaConfig
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

class ChatViewModel(application: Application) : AndroidViewModel(application) {
    
    private val settingsRepository = SettingsRepository(application)
    private var ollamaRepository: OllamaRepository
    
    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()
    
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()
    
    private val _config = MutableStateFlow(OllamaConfig())
    val config: StateFlow<OllamaConfig> = _config.asStateFlow()
    
    private val _availableModels = MutableStateFlow<List<String>>(emptyList())
    val availableModels: StateFlow<List<String>> = _availableModels.asStateFlow()
    
    private val _connectionStatus = MutableStateFlow<ConnectionStatus>(ConnectionStatus.Unknown)
    val connectionStatus: StateFlow<ConnectionStatus> = _connectionStatus.asStateFlow()
    
    private val conversationHistory = mutableListOf<OllamaChatMessage>()
    
    init {
        viewModelScope.launch {
            val savedConfig = settingsRepository.configFlow.first()
            _config.value = savedConfig
            ollamaRepository = OllamaRepository(savedConfig)
            loadModels()
        }
        
        viewModelScope.launch {
            settingsRepository.configFlow.collect { newConfig ->
                _config.value = newConfig
                ollamaRepository.updateConfig(newConfig)
            }
        }
    }
    
    fun sendMessage(content: String) {
        if (content.isBlank() || _isLoading.value) return
        
        val userMessage = ChatMessage(content = content, isUser = true)
        _messages.value = _messages.value + userMessage
        
        val assistantMessage = ChatMessage(content = "", isUser = false, isStreaming = true)
        _messages.value = _messages.value + assistantMessage
        
        _isLoading.value = true
        
        conversationHistory.add(OllamaChatMessage(role = "user", content = content))
        
        viewModelScope.launch {
            val responseBuilder = StringBuilder()
            
            ollamaRepository.chat(conversationHistory).collect { chunk ->
                responseBuilder.append(chunk)
                val updatedContent = responseBuilder.toString()
                
                _messages.value = _messages.value.map { msg ->
                    if (msg.id == assistantMessage.id) {
                        msg.copy(content = updatedContent)
                    } else msg
                }
            }
            
            val finalContent = responseBuilder.toString()
            conversationHistory.add(OllamaChatMessage(role = "assistant", content = finalContent))
            
            _messages.value = _messages.value.map { msg ->
                if (msg.id == assistantMessage.id) {
                    msg.copy(isStreaming = false)
                } else msg
            }
            
            _isLoading.value = false
        }
    }
    
    fun clearConversation() {
        _messages.value = emptyList()
        conversationHistory.clear()
    }
    
    fun updateConfig(newConfig: OllamaConfig) {
        viewModelScope.launch {
            settingsRepository.saveConfig(newConfig)
            _config.value = newConfig
            ollamaRepository.updateConfig(newConfig)
            loadModels()
        }
    }
    
    fun loadModels() {
        viewModelScope.launch {
            val result = ollamaRepository.getAvailableModels()
            result.onSuccess { models ->
                _availableModels.value = models.map { it.name }
                _connectionStatus.value = ConnectionStatus.Connected
            }.onFailure { error ->
                _connectionStatus.value = ConnectionStatus.Error(error.message ?: "Unknown error")
            }
        }
    }
    
    fun testConnection() {
        viewModelScope.launch {
            _connectionStatus.value = ConnectionStatus.Testing
            val result = ollamaRepository.testConnection()
            result.onSuccess { success ->
                _connectionStatus.value = if (success) {
                    ConnectionStatus.Connected
                } else {
                    ConnectionStatus.Error("Connection failed")
                }
            }.onFailure { error ->
                _connectionStatus.value = ConnectionStatus.Error(error.message ?: "Unknown error")
            }
        }
    }
    
    sealed class ConnectionStatus {
        object Unknown : ConnectionStatus()
        object Testing : ConnectionStatus()
        object Connected : ConnectionStatus()
        data class Error(val message: String) : ConnectionStatus()
    }
}
