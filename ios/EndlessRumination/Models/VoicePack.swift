import SwiftUI

struct VoicePackVoice: Identifiable {
    let id: Int
    let name: String
    let years: String
    let emoji: String
    let color: Color
    let bgColor: Color
    let desc: String
    let sampleHeadline: String
    let sampleBody: String

    var index: Int { id }
}

struct VoicePack: Identifiable {
    let id: String
    let name: String
    let subtitle: String
    let icon: String
    let color: Color
    let bgGradient: LinearGradient
    let accent: Color
    let productID: String
    let voices: [VoicePackVoice]

    var voiceIndices: [Int] { voices.map(\.id) }
}

extension VoicePack {
    static let all: [VoicePack] = [
        // MARK: - The Revolutionaries (25-29)
        VoicePack(
            id: "revolutionaries",
            name: "The Revolutionaries",
            subtitle: "Radical Reframes & Sharp Wit",
            icon: "\u{1F525}",
            color: Color(hex: 0xFF4757),
            bgGradient: LinearGradient(colors: [Color(hex: 0x2A1015), Color(hex: 0x1A1A20)], startPoint: .topLeading, endPoint: .bottomTrailing),
            accent: Color(hex: 0xFF4757).opacity(0.15),
            productID: "com.endlessrumination.pack.revolutionaries",
            voices: [
                VoicePackVoice(id: 25, name: "Vladimir Lenin", years: "1870\u{2013}1924", emoji: "\u{262D}", color: Color(hex: 0xFF4757), bgColor: Color(hex: 0xFF4757).opacity(0.15), desc: "Every personal problem reframed as systemic. Your boss isn't the problem -- the system is.", sampleHeadline: "Your frustration is not personal -- it is structural.", sampleBody: "Consider: the interview itself is a mechanism of labor commodification. The real question is not how to apologize -- it is why you feel you must."),
                VoicePackVoice(id: 26, name: "Oscar Wilde", years: "1854\u{2013}1900", emoji: "\u{1F3AD}", color: Color(hex: 0x9B6DFF), bgColor: Color(hex: 0x9B6DFF).opacity(0.15), desc: "Devastating wit. Every problem seen through aesthetics and irony.", sampleHeadline: "The only thing worse than being talked about is not being talked about.", sampleBody: "The real tragedy here isn't that you sent it -- it's that you're agonizing over the opinion of someone who will forget it by Tuesday."),
                VoicePackVoice(id: 27, name: "Mark Twain", years: "1835\u{2013}1910", emoji: "\u{1F4D6}", color: Color(hex: 0xF0A070), bgColor: Color(hex: 0xF0A070).opacity(0.15), desc: "America's greatest satirist. Finds the absurdity in everything with warmth.", sampleHeadline: "I've had thousands of problems in my life, most of which actually happened.", sampleBody: "The human race has one really effective weapon, and that is laughter. You are torturing yourself over a document that has already been buried in an avalanche of others."),
                VoicePackVoice(id: 28, name: "Sigmund Freud", years: "1856\u{2013}1939", emoji: "\u{1F6CB}\u{FE0F}", color: Color(hex: 0x00D4AA), bgColor: Color(hex: 0x00D4AA).opacity(0.15), desc: "Psychoanalyzes the unconscious drivers behind your worry. Everything is deeper than it seems.", sampleHeadline: "The email is not what troubles you -- it is what the email represents.", sampleBody: "This is a classic displacement of aggression. But I suspect the deeper wound is older: this pattern of performing for approval has earlier origins."),
                VoicePackVoice(id: 29, name: "Cleopatra", years: "69\u{2013}30 BC", emoji: "\u{1F451}", color: Color(hex: 0xC9A84C), bgColor: Color(hex: 0xC9A84C).opacity(0.15), desc: "Rules through impossible situations. Refuses the role of victim in any narrative.", sampleHeadline: "I negotiated with Caesar and Antony -- you can handle one recruiter.", sampleBody: "You send a gracious correction, you move your attention to the next alliance, and you never think of this person again unless they become useful."),
            ]
        ),
        // MARK: - The Creators (35-39)
        VoicePack(
            id: "creators",
            name: "The Creators",
            subtitle: "Art, Expression & Finding Meaning",
            icon: "\u{1F3A8}",
            color: Color(hex: 0x3ECF8E),
            bgGradient: LinearGradient(colors: [Color(hex: 0x0A2018), Color(hex: 0x1A1A20)], startPoint: .topLeading, endPoint: .bottomTrailing),
            accent: Color(hex: 0x3ECF8E).opacity(0.15),
            productID: "com.endlessrumination.pack.creators",
            voices: [
                VoicePackVoice(id: 35, name: "Leonardo da Vinci", years: "1452\u{2013}1519", emoji: "\u{1F58C}\u{FE0F}", color: Color(hex: 0x3ECF8E), bgColor: Color(hex: 0x3ECF8E).opacity(0.15), desc: "Polymath perspective. Every problem is a design challenge waiting to be sketched.", sampleHeadline: "Before solving anything, first observe it from seven angles.", sampleBody: "You are treating this as a catastrophe, but it is merely a study you have not yet completed. This is your failed sketch. Study it. Then turn the page."),
                VoicePackVoice(id: 36, name: "Emily Dickinson", years: "1830\u{2013}1886", emoji: "\u{1F338}", color: Color(hex: 0x9B6DFF), bgColor: Color(hex: 0x9B6DFF).opacity(0.15), desc: "Found infinity in small rooms. Transforms worry into compressed, startling insight.", sampleHeadline: "The email left you like a letter leaves a hand -- irrevocable and alive.", sampleBody: "Shame is just another room in the house of yourself, and you have lived in every room before and emerged. You are more rooms than you know."),
                VoicePackVoice(id: 37, name: "Miyamoto Musashi", years: "1584\u{2013}1645", emoji: "\u{2694}\u{FE0F}", color: Color(hex: 0xC8C0B4), bgColor: Color(hex: 0xC8C0B4).opacity(0.12), desc: "Samurai warrior-poet. The Way is in training. Discipline as liberation.", sampleHeadline: "A warrior does not dwell on the strike that missed.", sampleBody: "Note the angle. Correct the form. Return to training. There is no other Way. The sword does not remember its last fight and neither should you."),
                VoicePackVoice(id: 38, name: "Walt Whitman", years: "1819\u{2013}1892", emoji: "\u{1F33F}", color: Color(hex: 0x4AFFB4), bgColor: Color(hex: 0x4AFFB4).opacity(0.12), desc: "Radical self-acceptance. You contain multitudes -- even the ones that mess up.", sampleHeadline: "Do I contradict myself? Very well then, I contradict myself.", sampleBody: "You contain the person who panicked AND the person who regrets -- both are you, both are vast, both are necessary. Sound your yawp again differently tomorrow."),
                VoicePackVoice(id: 39, name: "Frida Kahlo", years: "1907\u{2013}1954", emoji: "\u{1F480}", color: Color(hex: 0xFF6B9D), bgColor: Color(hex: 0xFF6B9D).opacity(0.15), desc: "Transformed suffering into identity and power. Every wound becomes art.", sampleHeadline: "I paint myself because I am the subject I know best.", sampleBody: "Your pain is material. It is color on your palette. Use it. Paint what happened and it will stop haunting you the moment it becomes yours."),
            ]
        ),
        // MARK: - The Strategists (20-24)
        VoicePack(
            id: "strategists",
            name: "The Strategists",
            subtitle: "Power, Persuasion & Getting Ahead",
            icon: "\u{2694}\u{FE0F}",
            color: Color(hex: 0xC9A84C),
            bgGradient: LinearGradient(colors: [Color(hex: 0x2A2210), Color(hex: 0x1A1A20)], startPoint: .topLeading, endPoint: .bottomTrailing),
            accent: Color(hex: 0xC9A84C).opacity(0.15),
            productID: "com.endlessrumination.pack.strategists",
            voices: [
                VoicePackVoice(id: 20, name: "Dale Carnegie", years: "1888\u{2013}1955", emoji: "\u{1F91D}", color: Color(hex: 0xC9A84C), bgColor: Color(hex: 0xC9A84C).opacity(0.15), desc: "The master of human relations. Turns your worry into a lesson on winning friends and defusing conflict.", sampleHeadline: "You're worrying about the wrong side of this conversation.", sampleBody: "People will forgive almost anything if you make them feel important. The remedy isn't the apology -- it's what you say next."),
                VoicePackVoice(id: 21, name: "Machiavelli", years: "1469\u{2013}1527", emoji: "\u{1F40D}", color: Color(hex: 0x8B4513), bgColor: Color(hex: 0x8B4513).opacity(0.15), desc: "Cold strategic reframing. Every interpersonal problem is a power dynamics puzzle.", sampleHeadline: "Your error was not the email -- it was showing your hand.", sampleBody: "A prince who reveals displeasure gives others power over his emotions. The remedy is to become so formidable that this person will one day wish they had acted differently."),
                VoicePackVoice(id: 22, name: "Sun Tzu", years: "544\u{2013}496 BC", emoji: "\u{1F3EF}", color: Color(hex: 0xD4A843), bgColor: Color(hex: 0xD4A843).opacity(0.15), desc: "Every worry reframed as a battlefield. Ancient strategy applied to modern problems.", sampleHeadline: "The battle is lost. Withdraw and prepare the next campaign.", sampleBody: "The wise general does not reinforce failure. Study what intelligence you gathered from this defeat. The next battle will be fought on ground of your choosing."),
                VoicePackVoice(id: 23, name: "Benjamin Franklin", years: "1706\u{2013}1790", emoji: "\u{1FA81}", color: Color(hex: 0x6E9FFF), bgColor: Color(hex: 0x6E9FFF).opacity(0.15), desc: "The original life-hacker. Pragmatic wit meets systematic self-improvement.", sampleHeadline: "I once made a list of my virtues and failed every one by Tuesday.", sampleBody: "Take a fresh sheet and draw a line down the middle. On the left, every consequence you fear. On the right, the probability of each. Your imagination has been a far crueler correspondent than reality."),
                VoicePackVoice(id: 24, name: "P.T. Barnum", years: "1810\u{2013}1891", emoji: "\u{1F3AA}", color: Color(hex: 0xFF6B9D), bgColor: Color(hex: 0xFF6B9D).opacity(0.15), desc: "The greatest showman. Every disaster is just the opening act of a better story.", sampleHeadline: "My dear friend, you haven't failed -- you've created a spectacle!", sampleBody: "The public loves a comeback more than they ever loved a smooth beginning. Every great success I ever had began with a moment that looked exactly like this one."),
            ]
        ),
        // MARK: - The Philosophers (30-34)
        VoicePack(
            id: "philosophers",
            name: "The Philosophers",
            subtitle: "Deep Thinking on the Human Condition",
            icon: "\u{1F989}",
            color: Color(hex: 0xB08AFF),
            bgGradient: LinearGradient(colors: [Color(hex: 0x1A1530), Color(hex: 0x1A1A20)], startPoint: .topLeading, endPoint: .bottomTrailing),
            accent: Color(hex: 0xB08AFF).opacity(0.15),
            productID: "com.endlessrumination.pack.philosophers",
            voices: [
                VoicePackVoice(id: 30, name: "Immanuel Kant", years: "1724\u{2013}1804", emoji: "\u{1F4D0}", color: Color(hex: 0xB08AFF), bgColor: Color(hex: 0xB08AFF).opacity(0.15), desc: "The categorical imperative applied to your problems. Rigorous moral reasoning meets daily worry.", sampleHeadline: "Could you universalize sending that email? Then you must not.", sampleBody: "Your own reason tells you this was wrong, and that recognition is itself the proof of your moral capacity. Act now from duty, not inclination."),
                VoicePackVoice(id: 31, name: "Nietzsche", years: "1844\u{2013}1900", emoji: "\u{26A1}", color: Color(hex: 0xFF6B9D), bgColor: Color(hex: 0xFF6B9D).opacity(0.15), desc: "Life-affirming through suffering. Challenges weakness of spirit with fierce love.", sampleHeadline: "Amor fati -- love your fate, including this humiliation.", sampleBody: "You are suffering because you glimpsed who you became in that moment and it revolted you. This revulsion is the sign of ascending life, not declining."),
                VoicePackVoice(id: 32, name: "Kierkegaard", years: "1813\u{2013}1855", emoji: "\u{1F630}", color: Color(hex: 0x4A7CFF), bgColor: Color(hex: 0x4A7CFF).opacity(0.15), desc: "THE philosopher of anxiety. Wrote the book on dread. Deeply relevant to rumination.", sampleHeadline: "Your anxiety is not a symptom -- it is the dizziness of your freedom.", sampleBody: "This dread you feel is not punishment. It is the proof that you are a self in the process of becoming. Only those who choose wrongly and feel the wound can choose rightly next time."),
                VoicePackVoice(id: 33, name: "Epictetus", years: "50\u{2013}135 AD", emoji: "\u{26D3}\u{FE0F}", color: Color(hex: 0x40DFB0), bgColor: Color(hex: 0x40DFB0).opacity(0.15), desc: "Stoicism forged in slavery. Not armchair philosophy -- wisdom from lived suffering.", sampleHeadline: "You are disturbed not by the email but by your judgment of it.", sampleBody: "What remains in your control? Your response to this moment. That is the entirety of your domain. Stop rehearsing a past you cannot reach."),
                VoicePackVoice(id: 34, name: "Lao Tzu", years: "~6th c. BC", emoji: "\u{262F}\u{FE0F}", color: Color(hex: 0x8A8690), bgColor: Color(hex: 0x8A8690).opacity(0.12), desc: "Taoist non-action. The paradoxical wisdom of going with the flow.", sampleHeadline: "The reed that bends in the wind does not break.", sampleBody: "Your path forward is not to fight the current of regret -- it is to stop swimming upstream and let the river carry you to where you are meant to go."),
            ]
        ),
    ]

    static func voice(at index: Int) -> VoicePackVoice? {
        for pack in all {
            if let voice = pack.voices.first(where: { $0.id == index }) {
                return voice
            }
        }
        return nil
    }

    static func pack(forVoiceIndex index: Int) -> VoicePack? {
        all.first { $0.voices.contains(where: { $0.id == index }) }
    }

    static func pack(byProductID productID: String) -> VoicePack? {
        all.first { $0.productID == productID }
    }
}
