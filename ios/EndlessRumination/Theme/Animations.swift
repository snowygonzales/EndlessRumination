import SwiftUI

enum ERAnimations {
    static let takeTransition = Animation.easeOut(duration: 0.3)
    static let goneForever = Animation.easeOut(duration: 1.2)
    static let wordCounter = Animation.easeInOut(duration: 0.3)
    static let bob = Animation.easeInOut(duration: 2.0).repeatForever(autoreverses: true)
    static let spin = Animation.linear(duration: 0.8).repeatForever(autoreverses: false)
    static let pulse = Animation.easeInOut(duration: 1.5).repeatForever(autoreverses: true)
}
