package com.beadsnap.app.ui.screens.library

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.beadsnap.app.data.model.Difficulty
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.PatternCategory
import com.beadsnap.app.data.store.PatternStore
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.stateIn

enum class LibrarySortOrder(val displayName: String) {
    TITLE("Name"),
    DIFFICULTY("Difficulty"),
    NEWEST("Newest First")
}

@OptIn(FlowPreview::class, ExperimentalCoroutinesApi::class)
class LibraryViewModel(private val store: PatternStore) : ViewModel() {

    private val _selectedCategory = MutableStateFlow<PatternCategory?>(null)
    val selectedCategory: StateFlow<PatternCategory?> = _selectedCategory.asStateFlow()

    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()

    private val _sortOrder = MutableStateFlow(LibrarySortOrder.TITLE)
    val sortOrder: StateFlow<LibrarySortOrder> = _sortOrder.asStateFlow()

    val patterns: StateFlow<List<FusePattern>> = combine(
        store.systemPatterns,
        store.userPatterns,
        _selectedCategory,
        _searchQuery.debounce(80),
        _sortOrder
    ) { system, user, category, query, sort ->
        filter(system + user, category, query, sort)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    val categoryCounts: StateFlow<Map<PatternCategory, Int>> = combine(
        store.systemPatterns, store.userPatterns
    ) { system, user ->
        (system + user).groupingBy { it.category }.eachCount()
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyMap())

    fun setCategory(cat: PatternCategory?) { _selectedCategory.value = cat }
    fun setQuery(q: String) { _searchQuery.value = q }
    fun setSortOrder(order: LibrarySortOrder) { _sortOrder.value = order }

    private fun filter(
        all: List<FusePattern>,
        category: PatternCategory?,
        query: String,
        sort: LibrarySortOrder
    ): List<FusePattern> {
        var result = if (category != null) all.filter { it.category == category } else all
        val q = query.trim().lowercase()
        if (q.isNotEmpty()) {
            result = result.filter {
                it.title.lowercase().contains(q) || it.tags.any { t -> t.lowercase().contains(q) }
            }
        }
        return when (sort) {
            LibrarySortOrder.TITLE      -> result.sortedBy { it.title.lowercase() }
            LibrarySortOrder.DIFFICULTY -> result.sortedBy { difficultyOrder(it.difficulty) }
            LibrarySortOrder.NEWEST     -> result.reversed()
        }
    }

    private fun difficultyOrder(d: Difficulty) = when (d) {
        Difficulty.easy -> 0; Difficulty.medium -> 1; Difficulty.hard -> 2
    }
}
