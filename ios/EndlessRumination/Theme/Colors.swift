import SwiftUI

enum ERColors {
    static let background = Color(hex: 0x0A0A0C)
    static let inputBackground = Color(hex: 0x1A1A20)
    static let primaryText = Color(hex: 0xF0ECE4)
    static let secondaryText = Color(hex: 0x8A8690)
    static let dimText = Color(hex: 0x4A4650)
    static let border = Color.white.opacity(0.06)
    static let accentWarm = Color(hex: 0xE8653A)
    static let accentGold = Color(hex: 0xC9A84C)
    static let accentCool = Color(hex: 0x4A7CFF)
    static let accentGreen = Color(hex: 0x3ECF8E)
    static let accentPurple = Color(hex: 0x9B6DFF)
    static let accentPink = Color(hex: 0xFF6B9D)
    static let accentCyan = Color(hex: 0x00D4AA)
    static let accentRed = Color(hex: 0xFF4757)

    static let warmGradient = LinearGradient(
        colors: [Color(hex: 0xE8653A), Color(hex: 0xD44A2A)],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let logoGradient = LinearGradient(
        colors: [Color(hex: 0xE8653A), Color(hex: 0x9B6DFF)],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let proGradient = LinearGradient(
        colors: [Color(hex: 0xC9A84C), Color(hex: 0xE8653A)],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let titleGradient = LinearGradient(
        colors: [Color(hex: 0xF0ECE4), Color(hex: 0xC9A84C)],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )
}

extension Color {
    init(hex: UInt, alpha: Double = 1.0) {
        self.init(
            .sRGB,
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255,
            opacity: alpha
        )
    }
}
