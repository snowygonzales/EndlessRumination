import Foundation

enum SafetyService {
    private static let blocklist = [
        "kill myself", "kill me", "suicide", "suicidal",
        "hurt myself", "harm myself", "self-harm", "self harm",
        "end it all", "end my life", "want to die",
        "cut myself", "cutting myself",
        "weapon", "gun", "shoot",
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
    static func clientSideCheck(_ text: String) -> Bool {
        let lowered = text.lowercased()
        return !blocklist.contains(where: { lowered.contains($0) })
    }

    /// Server-side safety check via Claude classification.
    static func serverSideCheck(_ text: String) async throws -> Bool {
        let response = try await APIClient.shared.checkSafety(problem: text)
        return response.safe
    }
}
