import Foundation

struct Problem: Identifiable, Codable {
    let id: UUID
    let text: String
    let createdAt: Date
    var takes: [Take]

    enum CodingKeys: String, CodingKey {
        case id, text, takes
        case createdAt = "created_at"
    }
}
