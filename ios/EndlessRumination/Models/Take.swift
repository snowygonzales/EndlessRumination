import Foundation

struct Take: Identifiable, Codable {
    var id: UUID = UUID()
    let lensIndex: Int
    let headline: String
    let body: String

    enum CodingKeys: String, CodingKey {
        case lensIndex = "lens_index"
        case headline
        case body
    }

    init(lensIndex: Int, headline: String, body: String) {
        self.lensIndex = lensIndex
        self.headline = headline
        self.body = body
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.lensIndex = try container.decode(Int.self, forKey: .lensIndex)
        self.headline = try container.decode(String.self, forKey: .headline)
        self.body = try container.decode(String.self, forKey: .body)
    }
}
