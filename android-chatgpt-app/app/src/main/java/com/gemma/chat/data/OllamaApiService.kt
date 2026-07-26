package com.gemma.chat.data

import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Streaming

interface OllamaApiService {
    
    @POST("api/chat")
    @Streaming
    suspend fun chat(@Body request: OllamaChatRequest): Response<ResponseBody>
    
    @POST("api/generate")
    @Streaming
    suspend fun generate(@Body request: OllamaGenerateRequest): Response<ResponseBody>
    
    @GET("api/tags")
    suspend fun getModels(): Response<OllamaTagsResponse>
    
    @POST("api/show")
    suspend fun showModel(@Body request: Map<String, String>): Response<ResponseBody>
}
