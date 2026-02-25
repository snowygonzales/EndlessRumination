import SwiftUI

struct Lens: Identifiable {
    let id: Int
    let name: String
    let emoji: String
    let color: Color
    let bgColor: Color

    var index: Int { id }

    /// Free-tier users see the first 5 lenses only
    static let freeLensCount = 5

    /// These lens indices use Sonnet ("Wise") even for free-tier users
    static let wiseLensIndices: Set<Int> = [1, 9]

    /// Whether this lens is available to free-tier users
    var isFree: Bool { id < Self.freeLensCount }

    /// Whether this lens is powered by Sonnet (shown as "Wise")
    var isWise: Bool { Self.wiseLensIndices.contains(id) }
}

extension Lens {
    static let all: [Lens] = [
        Lens(id: 0,  name: "The Comedian",        emoji: "😂",  color: Color(hex: 0xFF6B9D), bgColor: Color(hex: 0xFF6B9D).opacity(0.15)),
        Lens(id: 1,  name: "The Stoic",            emoji: "🏛",  color: Color(hex: 0xC9A84C), bgColor: Color(hex: 0xC9A84C).opacity(0.15)),
        Lens(id: 2,  name: "The Nihilist",          emoji: "🕳",  color: Color(hex: 0x8A8690), bgColor: Color.white.opacity(0.06)),
        Lens(id: 3,  name: "The Optimist",          emoji: "☀️",  color: Color(hex: 0x3ECF8E), bgColor: Color(hex: 0x3ECF8E).opacity(0.15)),
        Lens(id: 4,  name: "The Pessimist",         emoji: "⛈",   color: Color(hex: 0xFF4757), bgColor: Color(hex: 0xFF4757).opacity(0.15)),
        Lens(id: 5,  name: "Your Best Friend",      emoji: "🫂",  color: Color(hex: 0x4A7CFF), bgColor: Color(hex: 0x4A7CFF).opacity(0.15)),
        Lens(id: 6,  name: "The Poet",              emoji: "🪶",  color: Color(hex: 0x9B6DFF), bgColor: Color(hex: 0x9B6DFF).opacity(0.15)),
        Lens(id: 7,  name: "A Five-Year-Old",       emoji: "🧸",  color: Color(hex: 0xF0C832), bgColor: Color(hex: 0xF0C832).opacity(0.15)),
        Lens(id: 8,  name: "The CEO",               emoji: "📊",  color: Color(hex: 0xF0ECE4), bgColor: Color(hex: 0xF0ECE4).opacity(0.08)),
        Lens(id: 9,  name: "The Therapist",         emoji: "🪷",  color: Color(hex: 0x00D4AA), bgColor: Color(hex: 0x00D4AA).opacity(0.15)),
        Lens(id: 10, name: "Your Grandma",          emoji: "🍪",  color: Color(hex: 0xE8653A), bgColor: Color(hex: 0xE8653A).opacity(0.15)),
        Lens(id: 11, name: "The Alien",             emoji: "👽",  color: Color(hex: 0x4AFFB4), bgColor: Color(hex: 0x4AFFB4).opacity(0.12)),
        Lens(id: 12, name: "The Historian",          emoji: "📜",  color: Color(hex: 0xD4A843), bgColor: Color(hex: 0xD4A843).opacity(0.12)),
        Lens(id: 13, name: "The Philosopher",        emoji: "🦉",  color: Color(hex: 0xB08AFF), bgColor: Color(hex: 0xB08AFF).opacity(0.12)),
        Lens(id: 14, name: "Future You",             emoji: "⌛",   color: Color(hex: 0x6E9FFF), bgColor: Color(hex: 0x6E9FFF).opacity(0.12)),
        Lens(id: 15, name: "Drill Sergeant",         emoji: "🎖",  color: Color(hex: 0xC8C0B4), bgColor: Color(hex: 0xC8C0B4).opacity(0.10)),
        Lens(id: 16, name: "The Monk",               emoji: "🧘",  color: Color(hex: 0x40DFB0), bgColor: Color(hex: 0x40DFB0).opacity(0.10)),
        Lens(id: 17, name: "The Scientist",          emoji: "🔬",  color: Color(hex: 0x5A8CFF), bgColor: Color(hex: 0x5A8CFF).opacity(0.12)),
        Lens(id: 18, name: "Conspiracy Theorist",    emoji: "🔺",  color: Color(hex: 0xE8B830), bgColor: Color(hex: 0xE8B830).opacity(0.12)),
        Lens(id: 19, name: "Your Dog",               emoji: "🐕",  color: Color(hex: 0xF0A070), bgColor: Color(hex: 0xF0A070).opacity(0.12)),
    ]

    static let freeLenses: [Lens] = Array(all.prefix(freeLensCount))

    static func lens(at index: Int) -> Lens {
        all[index % all.count]
    }

    /// Unified display info for both base lenses (0-19) and pack voices (20-39).
    static func displayInfo(at index: Int) -> (name: String, emoji: String, color: Color, bgColor: Color) {
        if index < all.count {
            let l = all[index]
            return (l.name, l.emoji, l.color, l.bgColor)
        }
        if let v = VoicePack.voice(at: index) {
            return (v.name, v.emoji, v.color, v.bgColor)
        }
        // Fallback
        return ("Unknown", "?", ERColors.dimText, ERColors.inputBackground)
    }
}
