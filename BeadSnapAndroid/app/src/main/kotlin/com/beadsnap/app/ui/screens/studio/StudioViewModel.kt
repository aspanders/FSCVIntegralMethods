package com.beadsnap.app.ui.screens.studio

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.beadsnap.app.data.model.CreatorType
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.data.model.PatternCategory
import com.beadsnap.app.data.store.PatternStore
import com.beadsnap.app.services.AIPatternService
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.UUID

class StudioViewModel(
    private val service: AIPatternService,
    private val store: PatternStore
) : ViewModel() {

    private val _prompt = MutableStateFlow("")
    val prompt: StateFlow<String> = _prompt.asStateFlow()

    private val _selectedCategory = MutableStateFlow<PatternCategory?>(PatternCategory.animals)
    val selectedCategory: StateFlow<PatternCategory?> = _selectedCategory.asStateFlow()

    private val _selectedGridSize = MutableStateFlow(GridSize.large)
    val selectedGridSize: StateFlow<GridSize> = _selectedGridSize.asStateFlow()

    private val _isGenerating = MutableStateFlow(false)
    val isGenerating: StateFlow<Boolean> = _isGenerating.asStateFlow()

    private val _generatedPattern = MutableStateFlow<FusePattern?>(null)
    val generatedPattern: StateFlow<FusePattern?> = _generatedPattern.asStateFlow()

    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage: StateFlow<String?> = _errorMessage.asStateFlow()

    val hasAPIKey: Boolean get() = service.hasAPIKey
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
        generationJob = viewModelScope.launch {
            try {
                val pattern = withContext(Dispatchers.IO) {
                    service.generateBlocking(text, _selectedCategory.value, _selectedGridSize.value)
                }
                if (isActive) _generatedPattern.value = pattern
            } catch (e: Exception) {
                if (isActive) _errorMessage.value = e.message
            } finally {
                _isGenerating.value = false
            }
        }
    }

    fun cancelGeneration() {
        generationJob?.cancel()
        _isGenerating.value = false
    }

    fun iterate(instruction: String) {
        val pattern = _generatedPattern.value ?: return
        _isGenerating.value = true
        _errorMessage.value = null
        generationJob = viewModelScope.launch {
            try {
                val updated = withContext(Dispatchers.IO) {
                    service.iterateBlocking(pattern, instruction)
                }
                if (isActive) _generatedPattern.value = updated
            } catch (e: Exception) {
                if (isActive) _errorMessage.value = e.message
            } finally {
                _isGenerating.value = false
            }
        }
    }

    fun saveAPIKey(key: String) {
        service.apiKey = key
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
