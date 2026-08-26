package com.beadsnap.app.services

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The library update channel used to be one hardcoded URL pinned to a git
 * branch. Deleting that branch would have silently stopped pattern updates for
 * every installed copy of the app, with no fix short of shipping a new build.
 * These tests pin the two properties that make that unfixable-in-the-field
 * failure impossible.
 */
class LibrarySourcesTest {

    @Test
    fun `more than one source is configured`() {
        // One source is one branch away from a dead update channel.
        assertTrue("need a fallback host", LibrarySources.BASES.size >= 2)
    }

    @Test
    fun `every source is an absolute https url with no trailing slash`() {
        for (base in LibrarySources.BASES) {
            assertTrue("$base must be https", base.startsWith("https://"))
            assertTrue("$base must not end in /", !base.endsWith("/"))
        }
    }

    @Test
    fun `manifest url is the library manifest under the base`() {
        assertEquals(
            "https://example.com/library/manifest.json",
            LibrarySources.manifestUrl("https://example.com")
        )
    }

    @Test
    fun `a trailing slash on the base does not double up`() {
        assertEquals(
            "https://example.com/library/manifest.json",
            LibrarySources.manifestUrl("https://example.com/")
        )
    }

    @Test
    fun `the sibling patterns file is preferred over the recorded url`() {
        // This ordering is the fix. A manifest copied to a new host still names
        // the OLD patternsUrl inside it, so trusting the file would send the app
        // straight back to the host it just moved off.
        val urls = LibrarySources.patternUrls(
            "https://new-host.example.com",
            "https://old-host.example.com/library/patterns.json"
        )
        assertEquals(
            listOf(
                "https://new-host.example.com/library/patterns.json",
                "https://old-host.example.com/library/patterns.json"
            ),
            urls
        )
    }

    @Test
    fun `the recorded url is kept as a fallback, not discarded`() {
        val urls = LibrarySources.patternUrls("https://a.example.com", "https://b.example.com/p.json")
        assertTrue("must still try the manifest's own url",
            urls.contains("https://b.example.com/p.json"))
    }

    @Test
    fun `a manifest that names the same file does not produce a duplicate fetch`() {
        val urls = LibrarySources.patternUrls(
            "https://example.com",
            "https://example.com/library/patterns.json"
        )
        assertEquals(listOf("https://example.com/library/patterns.json"), urls)
    }

    @Test
    fun `a blank patterns url is dropped rather than fetched`() {
        val urls = LibrarySources.patternUrls("https://example.com", "")
        assertEquals(listOf("https://example.com/library/patterns.json"), urls)
    }
}
