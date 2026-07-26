package com.gemma.chat.data

import com.google.gson.annotations.SerializedName

data class OllamaGenerateRequest(
    @SerializedName("model") val model: String,
    @SerializedName("prompt") val prompt: String,
    @SerializedName("stream") val stream: Boolean = true,
    @SerializedName("options") val options: OllamaOptions = OllamaOptions()
)

data class OllamaOptions(
    @SerializedName("temperature") val temperature: Float = 0.7f,
    @SerializedName("num_predict") val numPredict: Int = 2048
)

data class OllamaGenerateResponse(
    @SerializedName("model") val model: String?,
    @SerializedName("created_at") val createdAt: String?,
    @SerializedName("response") val response: String?,
    @SerializedName("done") val done: Boolean = false,
    @SerializedName("context") val context: List<Int>? = null,
    @SerializedName("total_duration") val totalDuration: Long? = null,
    @SerializedName("load_duration") val loadDuration: Long? = null,
    @SerializedName("prompt_eval_count") val promptEvalCount: Int? = null,
    @SerializedName("prompt_eval_duration") val promptEvalDuration: Long? = null,
    @SerializedName("eval_count") val evalCount: Int? = null,
    @SerializedName("eval_duration") val evalDuration: Long? = null
)

data class OllamaChatMessage(
    @SerializedName("role") val role: String,
    @SerializedName("content") val content: String
)

data class OllamaChatRequest(
    @SerializedName("model") val model: String,
    @SerializedName("messages") val messages: List<OllamaChatMessage>,
    @SerializedName("stream") val stream: Boolean = true,
    @SerializedName("options") val options: OllamaOptions = OllamaOptions()
)

data class OllamaChatResponse(
    @SerializedName("model") val model: String?,
    @SerializedName("created_at") val createdAt: String?,
    @SerializedName("message") val message: OllamaChatMessage?,
    @SerializedName("done") val done: Boolean = false
)

data class OllamaModel(
    @SerializedName("name") val name: String,
    @SerializedName("size") val size: Long,
    @SerializedName("digest") val digest: String,
    @SerializedName("modified_at") val modifiedAt: String
)

data class OllamaTagsResponse(
    @SerializedName("models") val models: List<OllamaModel>
)
