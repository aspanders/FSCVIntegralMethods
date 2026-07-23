package com.beadsnap.app.ui.screens.studio

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.beadsnap.app.data.model.CreatorType
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.data.model.PatternCategory
import com.beadsnap.app.data.store.PatternStore
import com.beadsnap.app.services.AIPatternService
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.util.UUID

class StudioViewModel(
    private val service: AIPatternService,
    private val store: PatternStore
) : ViewModel() {

    private val _prompt = MutableStateFlow("")
    val prompt: StateFlow<String> = _prompt.asStateFlow()

    private val _selectedCategory = MutableStateFlow<PatternCategory?>(PatternCategory.geometric)
    val selectedCategory: StateFlow<PatternCategory?> = _selectedCategory.asStateFlow()

    private val _selectedGridSize = MutableStateFlow(GridSize.large)
    val selectedGridSize: StateFlow<GridSize> = _selectedGridSize.asStateFlow()

    private val _isGenerating = MutableStateFlow(false)
    val isGenerating: StateFlow<Boolean> = _isGenerating.asStateFlow()

    private val _generatedPattern = MutableStateFlow<FusePattern?>(null)
    val generatedPattern: StateFlow<FusePattern?> = _generatedPattern.asStateFlow()

    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage: StateFlow<String?> = _errorMessage.asStateFlow()

    private val _hasAPIKey = MutableStateFlow(service.hasAPIKey)
    val hasAPIKey: StateFlow<Boolean> = _hasAPIKey.asStateFlow()

    val apiKey: String get() = service.apiKey

    private var generationJob: Job? = null
    private var isSaving = false

    fun setPrompt(p: String) { _prompt.value = p }
    fun setCategory(c: PatternCategory?) { _selectedCategory.value = c }
    fun setGridSize(gs: GridSize) { _selectedGridSize.value = gs }
    fun clearError() { _errorMessage.value = null }

    fun generate() {
        val text = _prompt.value.trim()
        if (text.isBlank()) return
        _isGenerating.value = true
        _errorMessage.value = null
        val job = viewModelScope.launch {
            try {
                val pattern = service.generate(text, _selectedCategory.value, _selectedGridSize.value)
                if (isActive) _generatedPattern.value = pattern
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                if (isActive) _errorMessage.value = e.message
            } finally {
                // only the still-current job may clear the progress flag
                if (generationJob === coroutineContext[Job]) _isGenerating.value = false
            }
        }
        generationJob = job
    }

    fun cancelGeneration() {
        generationJob?.cancel()
        generationJob = null
        _isGenerating.value = false
    }

    fun iterate(instruction: String) {
        val pattern = _generatedPattern.value ?: return
        _isGenerating.value = true
        _errorMessage.value = null
        val job = viewModelScope.launch {
            try {
                val updated = service.iterate(pattern, instruction)
                if (isActive) _generatedPattern.value = updated
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                if (isActive) _errorMessage.value = e.message
            } finally {
                if (generationJob === coroutineContext[Job]) _isGenerating.value = false
            }
        }
        generationJob = job
    }

    fun saveAPIKey(key: String) {
        service.apiKey = key
        _hasAPIKey.value = service.hasAPIKey
    }

    fun saveGenerated(): FusePattern? {
        if (isSaving) return null
        val pattern = _generatedPattern.value ?: return null
        isSaving = true
        return try {
            val saved = pattern.copy(
                id = UUID.randomUUID().toString(),
                createdBy = CreatorType.user
            )
            store.save(saved)
            saved
        } finally {
            isSaving = false
        }
    }
}
