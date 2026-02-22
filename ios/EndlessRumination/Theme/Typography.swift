import SwiftUI

enum ERTypography {
    static let appTitle = Font.custom("NewYork-Bold", size: 38, relativeTo: .largeTitle)
    static let screenTitle = Font.custom("NewYork-Bold", size: 28, relativeTo: .title)
    static let headline = Font.custom("NewYork-Semibold", size: 24, relativeTo: .title2)
    static let body = Font.system(size: 13.5, weight: .light)
    static let ui = Font.system(size: 16, weight: .regular)
    static let button = Font.system(size: 16, weight: .bold)
    static let counter = Font.system(size: 12, design: .monospaced)
    static let caption = Font.system(size: 11, weight: .regular)
    static let smallCaps = Font.system(size: 12, weight: .bold)
        .width(.standard)
    static let badge = Font.system(size: 12, weight: .bold)

    static func serifHeadline(size: CGFloat = 24) -> Font {
        .system(size: size, design: .serif).weight(.semibold)
    }

    static func serifTitle(size: CGFloat = 28) -> Font {
        .system(size: size, design: .serif).weight(.bold)
    }

    static func serifLargeTitle(size: CGFloat = 38) -> Font {
        .system(size: size, design: .serif).weight(.bold)
    }
}
