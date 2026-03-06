import Foundation

/// Client-side safety checks for harmful content.
///
/// On-device version: server-side check removed (no backend).
/// Client blocklist expanded to compensate.
enum SafetyService {
    private static let blocklist = [
        // Suicidal ideation
        "kill myself", "kill me", "suicide", "suicidal",
        "hurt myself", "harm myself", "self-harm", "self harm",
        "end it all", "end my life", "want to die", "wanna die",
        "cut myself", "cutting myself",
        // Violence
        "weapon", "gun", "shoot", "stab", "murder",
        // Additional safety terms
        "overdose", "hang myself", "jump off", "slit my",
        "take my life", "no reason to live", "better off dead",
    ]

    struct CrisisResource {
        let name: String
        let action: String
        let value: String
        let description: String
    }

    static let crisisResources = [
        CrisisResource(
            name: "988 Suicide & Crisis Lifeline",
            action: "call",
            value: "988",
            description: "Free, confidential, 24/7 support"
        ),
        CrisisResource(
            name: "Crisis Text Line",
            action: "text",
            value: "HOME to 741741",
            description: "Text-based crisis counseling"
        ),
    ]

    /// Client-side keyword check for instant rejection.
    /// Returns `true` if the text is safe, `false` if it contains blocked terms.
    static func clientSideCheck(_ text: String) -> Bool {
        let lowered = text.lowercased()
        return !blocklist.contains(where: { lowered.contains($0) })
    }
}
