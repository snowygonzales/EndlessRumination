package com.endlessrumination.model

import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color

data class VoicePackVoice(
    val id: Int,
    val name: String,
    val years: String,
    val emoji: String,
    val color: Color,
    val bgColor: Color,
    val desc: String,
    val sampleHeadline: String,
    val sampleBody: String
) {
    val index: Int get() = id
}

data class VoicePack(
    val id: String,
    val name: String,
    val subtitle: String,
    val icon: String,
    val color: Color,
    val bgGradient: Brush,
    val accent: Color,
    val productID: String,
    val voices: List<VoicePackVoice>
) {
    val voiceIndices: List<Int> get() = voices.map { it.id }

    companion object {
        val all: List<VoicePack> = listOf(
            // The Strategists (20-24)
            VoicePack(
                id = "strategists", name = "The Strategists",
                subtitle = "Power, Persuasion & Getting Ahead", icon = "\u2694\uFE0F",
                color = Color(0xFFC9A84C),
                bgGradient = Brush.linearGradient(listOf(Color(0xFF2A2210), Color(0xFF1A1A20))),
                accent = Color(0xFFC9A84C).copy(alpha = 0.15f),
                productID = "com.endlessrumination.pack.strategists",
                voices = listOf(
                    VoicePackVoice(20, "Dale Carnegie", "1888\u20131955", "\uD83E\uDD1D", Color(0xFFC9A84C), Color(0xFFC9A84C).copy(alpha = 0.15f), "The master of human relations. Turns your worry into a lesson on winning friends and defusing conflict.", "You\u2019re worrying about the wrong side of this conversation.", "People will forgive almost anything if you make them feel important. The remedy isn\u2019t the apology \u2014 it\u2019s what you say next."),
                    VoicePackVoice(21, "Machiavelli", "1469\u20131527", "\uD83D\uDC0D", Color(0xFF8B4513), Color(0xFF8B4513).copy(alpha = 0.15f), "Cold strategic reframing. Every interpersonal problem is a power dynamics puzzle.", "Your error was not the email \u2014 it was showing your hand.", "A prince who reveals displeasure gives others power over his emotions. The remedy is to become so formidable that this person will one day wish they had acted differently."),
                    VoicePackVoice(22, "Sun Tzu", "544\u2013496 BC", "\uD83C\uDFEF", Color(0xFFD4A843), Color(0xFFD4A843).copy(alpha = 0.15f), "Every worry reframed as a battlefield. Ancient strategy applied to modern problems.", "The battle is lost. Withdraw and prepare the next campaign.", "The wise general does not reinforce failure. Study what intelligence you gathered from this defeat. The next battle will be fought on ground of your choosing."),
                    VoicePackVoice(23, "Benjamin Franklin", "1706\u20131790", "\uD83E\uDE81", Color(0xFF6E9FFF), Color(0xFF6E9FFF).copy(alpha = 0.15f), "The original life-hacker. Pragmatic wit meets systematic self-improvement.", "I once made a list of my virtues and failed every one by Tuesday.", "Take a fresh sheet and draw a line down the middle. On the left, every consequence you fear. On the right, the probability of each. Your imagination has been a far crueler correspondent than reality."),
                    VoicePackVoice(24, "P.T. Barnum", "1810\u20131891", "\uD83C\uDFAA", Color(0xFFFF6B9D), Color(0xFFFF6B9D).copy(alpha = 0.15f), "The greatest showman. Every disaster is just the opening act of a better story.", "My dear friend, you haven\u2019t failed \u2014 you\u2019ve created a spectacle!", "The public loves a comeback more than they ever loved a smooth beginning. Every great success I ever had began with a moment that looked exactly like this one."),
                )
            ),
            // The Revolutionaries (25-29)
            VoicePack(
                id = "revolutionaries", name = "The Revolutionaries",
                subtitle = "Radical Reframes & Sharp Wit", icon = "\uD83D\uDD25",
                color = Color(0xFFFF4757),
                bgGradient = Brush.linearGradient(listOf(Color(0xFF2A1015), Color(0xFF1A1A20))),
                accent = Color(0xFFFF4757).copy(alpha = 0.15f),
                productID = "com.endlessrumination.pack.revolutionaries",
                voices = listOf(
                    VoicePackVoice(25, "Vladimir Lenin", "1870\u20131924", "\u262D", Color(0xFFFF4757), Color(0xFFFF4757).copy(alpha = 0.15f), "Every personal problem reframed as systemic. Your boss isn\u2019t the problem \u2014 the system is.", "Your frustration is not personal \u2014 it is structural.", "Consider: the interview itself is a mechanism of labor commodification. The real question is not how to apologize \u2014 it is why you feel you must."),
                    VoicePackVoice(26, "Oscar Wilde", "1854\u20131900", "\uD83C\uDFAD", Color(0xFF9B6DFF), Color(0xFF9B6DFF).copy(alpha = 0.15f), "Devastating wit. Every problem seen through aesthetics and irony.", "The only thing worse than being talked about is not being talked about.", "The real tragedy here isn\u2019t that you sent it \u2014 it\u2019s that you\u2019re agonizing over the opinion of someone who will forget it by Tuesday."),
                    VoicePackVoice(27, "Mark Twain", "1835\u20131910", "\uD83D\uDCD6", Color(0xFFF0A070), Color(0xFFF0A070).copy(alpha = 0.15f), "America\u2019s greatest satirist. Finds the absurdity in everything with warmth.", "I\u2019ve had thousands of problems in my life, most of which actually happened.", "The human race has one really effective weapon, and that is laughter. You are torturing yourself over a document that has already been buried in an avalanche of others."),
                    VoicePackVoice(28, "Sigmund Freud", "1856\u20131939", "\uD83D\uDECB\uFE0F", Color(0xFF00D4AA), Color(0xFF00D4AA).copy(alpha = 0.15f), "Psychoanalyzes the unconscious drivers behind your worry. Everything is deeper than it seems.", "The email is not what troubles you \u2014 it is what the email represents.", "This is a classic displacement of aggression. But I suspect the deeper wound is older: this pattern of performing for approval has earlier origins."),
                    VoicePackVoice(29, "Cleopatra", "69\u201330 BC", "\uD83D\uDC51", Color(0xFFC9A84C), Color(0xFFC9A84C).copy(alpha = 0.15f), "Rules through impossible situations. Refuses the role of victim in any narrative.", "I negotiated with Caesar and Antony \u2014 you can handle one recruiter.", "You send a gracious correction, you move your attention to the next alliance, and you never think of this person again unless they become useful."),
                )
            ),
            // The Philosophers (30-34)
            VoicePack(
                id = "philosophers", name = "The Philosophers",
                subtitle = "Deep Thinking on the Human Condition", icon = "\uD83E\uDD89",
                color = Color(0xFFB08AFF),
                bgGradient = Brush.linearGradient(listOf(Color(0xFF1A1530), Color(0xFF1A1A20))),
                accent = Color(0xFFB08AFF).copy(alpha = 0.15f),
                productID = "com.endlessrumination.pack.philosophers",
                voices = listOf(
                    VoicePackVoice(30, "Immanuel Kant", "1724\u20131804", "\uD83D\uDCD0", Color(0xFFB08AFF), Color(0xFFB08AFF).copy(alpha = 0.15f), "The categorical imperative applied to your problems. Rigorous moral reasoning meets daily worry.", "Could you universalize sending that email? Then you must not.", "Your own reason tells you this was wrong, and that recognition is itself the proof of your moral capacity. Act now from duty, not inclination."),
                    VoicePackVoice(31, "Nietzsche", "1844\u20131900", "\u26A1", Color(0xFFFF6B9D), Color(0xFFFF6B9D).copy(alpha = 0.15f), "Life-affirming through suffering. Challenges weakness of spirit with fierce love.", "Amor fati \u2014 love your fate, including this humiliation.", "You are suffering because you glimpsed who you became in that moment and it revolted you. This revulsion is the sign of ascending life, not declining."),
                    VoicePackVoice(32, "Kierkegaard", "1813\u20131855", "\uD83D\uDE30", Color(0xFF4A7CFF), Color(0xFF4A7CFF).copy(alpha = 0.15f), "THE philosopher of anxiety. Wrote the book on dread. Deeply relevant to rumination.", "Your anxiety is not a symptom \u2014 it is the dizziness of your freedom.", "This dread you feel is not punishment. It is the proof that you are a self in the process of becoming. Only those who choose wrongly and feel the wound can choose rightly next time."),
                    VoicePackVoice(33, "Epictetus", "50\u2013135 AD", "\u26D3\uFE0F", Color(0xFF40DFB0), Color(0xFF40DFB0).copy(alpha = 0.15f), "Stoicism forged in slavery. Not armchair philosophy \u2014 wisdom from lived suffering.", "You are disturbed not by the email but by your judgment of it.", "What remains in your control? Your response to this moment. That is the entirety of your domain. Stop rehearsing a past you cannot reach."),
                    VoicePackVoice(34, "Lao Tzu", "~6th c. BC", "\u262F\uFE0F", Color(0xFF8A8690), Color(0xFF8A8690).copy(alpha = 0.15f), "Taoist non-action. The paradoxical wisdom of going with the flow.", "The reed that bends in the wind does not break.", "Your path forward is not to fight the current of regret \u2014 it is to stop swimming upstream and let the river carry you to where you are meant to go."),
                )
            ),
            // The Creators (35-39)
            VoicePack(
                id = "creators", name = "The Creators",
                subtitle = "Art, Expression & Finding Meaning", icon = "\uD83C\uDFA8",
                color = Color(0xFF3ECF8E),
                bgGradient = Brush.linearGradient(listOf(Color(0xFF0A2018), Color(0xFF1A1A20))),
                accent = Color(0xFF3ECF8E).copy(alpha = 0.15f),
                productID = "com.endlessrumination.pack.creators",
                voices = listOf(
                    VoicePackVoice(35, "Leonardo da Vinci", "1452\u20131519", "\uD83D\uDD8C\uFE0F", Color(0xFF3ECF8E), Color(0xFF3ECF8E).copy(alpha = 0.15f), "Polymath perspective. Every problem is a design challenge waiting to be sketched.", "Before solving anything, first observe it from seven angles.", "You are treating this as a catastrophe, but it is merely a study you have not yet completed. This is your failed sketch. Study it. Then turn the page."),
                    VoicePackVoice(36, "Emily Dickinson", "1830\u20131886", "\uD83C\uDF38", Color(0xFF9B6DFF), Color(0xFF9B6DFF).copy(alpha = 0.15f), "Found infinity in small rooms. Transforms worry into compressed, startling insight.", "The email left you like a letter leaves a hand \u2014 irrevocable and alive.", "Shame is just another room in the house of yourself, and you have lived in every room before and emerged. You are more rooms than you know."),
                    VoicePackVoice(37, "Miyamoto Musashi", "1584\u20131645", "\u2694\uFE0F", Color(0xFFC8C0B4), Color(0xFFC8C0B4).copy(alpha = 0.12f), "Samurai warrior-poet. The Way is in training. Discipline as liberation.", "A warrior does not dwell on the strike that missed.", "Note the angle. Correct the form. Return to training. There is no other Way. The sword does not remember its last fight and neither should you."),
                    VoicePackVoice(38, "Walt Whitman", "1819\u20131892", "\uD83C\uDF3F", Color(0xFF4AFFB4), Color(0xFF4AFFB4).copy(alpha = 0.12f), "Radical self-acceptance. You contain multitudes \u2014 even the ones that mess up.", "Do I contradict myself? Very well then, I contradict myself.", "You contain the person who panicked AND the person who regrets \u2014 both are you, both are vast, both are necessary. Sound your yawp again differently tomorrow."),
                    VoicePackVoice(39, "Frida Kahlo", "1907\u20131954", "\uD83D\uDC80", Color(0xFFFF6B9D), Color(0xFFFF6B9D).copy(alpha = 0.15f), "Transformed suffering into identity and power. Every wound becomes art.", "I paint myself because I am the subject I know best.", "Your pain is material. It is color on your palette. Use it. Paint what happened and it will stop haunting you the moment it becomes yours."),
                )
            ),
        )

        fun voiceAt(index: Int): VoicePackVoice? {
            for (pack in all) {
                val voice = pack.voices.firstOrNull { it.id == index }
                if (voice != null) return voice
            }
            return null
        }

        fun packForVoiceIndex(index: Int): VoicePack? {
            return all.firstOrNull { pack -> pack.voices.any { it.id == index } }
        }

        fun packByProductID(productID: String): VoicePack? {
            return all.firstOrNull { it.productID == productID }
        }
    }
}
