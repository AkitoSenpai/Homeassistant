package com.gemma.chat.model

data class ChatMessage(
    val id: String = java.util.UUID.randomUUID().toString(),
    val content: String,
    val isUser: Boolean,
    val timestamp: Long = System.currentTimeMillis(),
    val isStreaming: Boolean = false
)

data class Conversation(
    val id: String = java.util.UUID.randomUUID().toString(),
    val title: String = "Nouvelle conversation",
    val messages: List<ChatMessage> = emptyList(),
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis()
)

data class OllamaConfig(
    val baseUrl: String = "http://192.168.1.20:11434",
    val model: String = "gemma3n:e4b",
    val temperature: Float = 0.7f,
    val maxTokens: Int = 2048
)
