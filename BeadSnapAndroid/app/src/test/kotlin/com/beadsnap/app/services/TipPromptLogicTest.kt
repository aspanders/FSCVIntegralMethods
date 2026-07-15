package com.beadsnap.app.services

import org.junit.Assert.*
import org.junit.Test

class TipPromptLogicTest {

    private val threshold = TipPromptLogic.PROMPT_THRESHOLD

    @Test
    fun `no prompt before the tenth use`() {
        for (count in 0 until threshold) {
            assertFalse(TipPromptLogic.shouldPrompt(count, false, false, threshold))
        }
    }

    @Test
    fun `prompts on the tenth use`() {
        assertTrue(TipPromptLogic.shouldPrompt(threshold, false, false, threshold))
    }

    @Test
    fun `never prompts after permanent dismissal`() {
        assertFalse(TipPromptLogic.shouldPrompt(100, true, false, threshold))
    }

    @Test
    fun `never prompts after a tip has been given`() {
        assertFalse(TipPromptLogic.shouldPrompt(100, false, true, threshold))
    }

    @Test
    fun `maybe later defers until the retry point`() {
        val retryAt = threshold + TipPromptLogic.LATER_RETRY_USES
        assertFalse(TipPromptLogic.shouldPrompt(retryAt - 1, false, false, retryAt))
        assertTrue(TipPromptLogic.shouldPrompt(retryAt, false, false, retryAt))
    }
}
