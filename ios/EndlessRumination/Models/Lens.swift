import SwiftUI

struct Lens: Identifiable {
    let id: Int
    let name: String
    let emoji: String
    let color: Color
    let bgColor: Color

    var index: Int { id }
}

extension Lens {
    static let all: [Lens] = [
        Lens(id: 0,  name: "The Comedian",        emoji: "\u{1F602}",  color: Color(hex: 0xFF6B9D), bgColor: Color(hex: 0xFF6B9D).opacity(0.15)),
        Lens(id: 1,  name: "The Stoic",            emoji: "\u{1F3DB}",  color: Color(hex: 0xC9A84C), bgColor: Color(hex: 0xC9A84C).opacity(0.15)),
        Lens(id: 2,  name: "The Nihilist",          emoji: "\u{1F573}",  color: Color(hex: 0x8A8690), bgColor: Color.white.opacity(0.06)),
        Lens(id: 3,  name: "The Optimist",          emoji: "\u{2600}\u{FE0F}",  color: Color(hex: 0x3ECF8E), bgColor: Color(hex: 0x3ECF8E).opacity(0.15)),
        Lens(id: 4,  name: "The Pessimist",         emoji: "\u{26C8}",   color: Color(hex: 0xFF4757), bgColor: Color(hex: 0xFF4757).opacity(0.15)),
        Lens(id: 5,  name: "Your Best Friend",      emoji: "\u{1FAC2}",  color: Color(hex: 0x4A7CFF), bgColor: Color(hex: 0x4A7CFF).opacity(0.15)),
        Lens(id: 6,  name: "The Poet",              emoji: "\u{1FAB6}",  color: Color(hex: 0x9B6DFF), bgColor: Color(hex: 0x9B6DFF).opacity(0.15)),
        Lens(id: 7,  name: "A Five-Year-Old",       emoji: "\u{1F9F8}",  color: Color(hex: 0xF0C832), bgColor: Color(hex: 0xF0C832).opacity(0.15)),
        Lens(id: 8,  name: "The CEO",               emoji: "\u{1F4CA}",  color: Color(hex: 0xF0ECE4), bgColor: Color(hex: 0xF0ECE4).opacity(0.08)),
        Lens(id: 9,  name: "The Therapist",         emoji: "\u{1FAB7}",  color: Color(hex: 0x00D4AA), bgColor: Color(hex: 0x00D4AA).opacity(0.15)),
        Lens(id: 10, name: "Your Grandma",          emoji: "\u{1F36A}",  color: Color(hex: 0xE8653A), bgColor: Color(hex: 0xE8653A).opacity(0.15)),
        Lens(id: 11, name: "The Alien",             emoji: "\u{1F47D}",  color: Color(hex: 0x4AFFB4), bgColor: Color(hex: 0x4AFFB4).opacity(0.12)),
        Lens(id: 12, name: "The Historian",          emoji: "\u{1F4DC}",  color: Color(hex: 0xD4A843), bgColor: Color(hex: 0xD4A843).opacity(0.12)),
        Lens(id: 13, name: "The Philosopher",        emoji: "\u{1F989}",  color: Color(hex: 0xB08AFF), bgColor: Color(hex: 0xB08AFF).opacity(0.12)),
        Lens(id: 14, name: "Future You",             emoji: "\u{231B}",   color: Color(hex: 0x6E9FFF), bgColor: Color(hex: 0x6E9FFF).opacity(0.12)),
        Lens(id: 15, name: "Drill Sergeant",         emoji: "\u{1F396}",  color: Color(hex: 0xC8C0B4), bgColor: Color(hex: 0xC8C0B4).opacity(0.10)),
        Lens(id: 16, name: "The Monk",               emoji: "\u{1F9D8}",  color: Color(hex: 0x40DFB0), bgColor: Color(hex: 0x40DFB0).opacity(0.10)),
        Lens(id: 17, name: "The Scientist",          emoji: "\u{1F52C}",  color: Color(hex: 0x5A8CFF), bgColor: Color(hex: 0x5A8CFF).opacity(0.12)),
        Lens(id: 18, name: "Conspiracy Theorist",    emoji: "\u{1F53A}",  color: Color(hex: 0xE8B830), bgColor: Color(hex: 0xE8B830).opacity(0.12)),
        Lens(id: 19, name: "Your Dog",               emoji: "\u{1F415}",  color: Color(hex: 0xF0A070), bgColor: Color(hex: 0xF0A070).opacity(0.12)),
    ]

    static func lens(at index: Int) -> Lens {
        all[index % all.count]
    }
}
