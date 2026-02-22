import Foundation

enum SubscriptionTier: String, Codable {
    case free
    case pro
}

struct User: Codable {
    let id: UUID
    let deviceId: String
    let email: String?
    let subscriptionTier: SubscriptionTier
    let dailyTakesUsed: Int
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id, email
        case deviceId = "device_id"
        case subscriptionTier = "subscription_tier"
        case dailyTakesUsed = "daily_takes_used"
        case createdAt = "created_at"
    }
}

struct AuthResponse: Codable {
    let token: String
    let user: User
}
