import Foundation

actor APIClient {
    static let shared = APIClient()

    #if DEBUG
    private let baseURL = "http://localhost:8000"
    #else
    private let baseURL = "https://backend-production-5537.up.railway.app"
    #endif

    private var authToken: String?

    func setAuthToken(_ token: String?) {
        authToken = token
    }

    // MARK: - Auth

    func register(deviceId: String) async throws -> AuthResponse {
        let body: [String: Any] = ["device_id": deviceId]
        return try await post("/api/v1/auth/register", body: body)
    }

    func login(deviceId: String) async throws -> AuthResponse {
        let body: [String: Any] = ["device_id": deviceId]
        return try await post("/api/v1/auth/login", body: body)
    }

    // MARK: - Safety

    struct SafetyCheckResponse: Codable {
        let safe: Bool
        let category: String?
        let resources: [[String: String]]?
    }

    func checkSafety(problem: String) async throws -> SafetyCheckResponse {
        let body: [String: Any] = ["problem": problem]
        return try await post("/api/v1/safety-check", body: body)
    }

    // MARK: - Takes (SSE Streaming)

    func generateBatch(problem: String, lensIndices: [Int] = Array(0..<20), ownedPackIDs: [String] = []) -> AsyncThrowingStream<Take, Error> {
        AsyncThrowingStream { continuation in
            Task {
                do {
                    let body: [String: Any] = [
                        "problem": problem,
                        "lens_indices": lensIndices,
                        "owned_pack_ids": ownedPackIDs,
                    ]
                    let bodyData = try JSONSerialization.data(withJSONObject: body)

                    var request = URLRequest(url: URL(string: "\(baseURL)/api/v1/generate-batch")!)
                    request.httpMethod = "POST"
                    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                    if let token = authToken {
                        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
                    }
                    request.httpBody = bodyData

                    let (bytes, response) = try await URLSession.shared.bytes(for: request)

                    guard let httpResponse = response as? HTTPURLResponse,
                          httpResponse.statusCode == 200 else {
                        let statusCode = (response as? HTTPURLResponse)?.statusCode ?? 0
                        continuation.finish(throwing: APIError.httpError(statusCode))
                        return
                    }

                    for try await line in bytes.lines {
                        guard line.hasPrefix("data: ") else { continue }
                        let payload = String(line.dropFirst(6))

                        if payload == "[DONE]" {
                            break
                        }

                        guard let data = payload.data(using: .utf8) else { continue }
                        let take = try JSONDecoder().decode(Take.self, from: data)
                        continuation.yield(take)
                    }

                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }

    // MARK: - Single Take

    func generateTake(problem: String, lensIndex: Int) async throws -> Take {
        let body: [String: Any] = [
            "problem": problem,
            "lens_index": lensIndex,
        ]
        return try await post("/api/v1/generate-take", body: body)
    }

    // MARK: - Helpers

    private func post<T: Decodable>(_ path: String, body: [String: Any]) async throws -> T {
        let url = URL(string: "\(baseURL)\(path)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard 200..<300 ~= httpResponse.statusCode else {
            throw APIError.httpError(httpResponse.statusCode)
        }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return try decoder.decode(T.self, from: data)
    }
}

enum APIError: LocalizedError {
    case invalidResponse
    case httpError(Int)
    case decodingError

    var errorDescription: String? {
        switch self {
        case .invalidResponse: return "Invalid response from server"
        case .httpError(let code): return "HTTP error: \(code)"
        case .decodingError: return "Failed to decode response"
        }
    }
}
