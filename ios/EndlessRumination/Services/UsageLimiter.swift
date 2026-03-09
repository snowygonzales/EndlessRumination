import Foundation
import os

/// Rate-limits submissions to prevent chatbot abuse and enforce free-tier caps.
///
/// Two independent limit systems:
/// 1. **Anti-abuse** (all users): 8 per 30 min, 15 min cooldown
/// 2. **Free-tier cap** (free only): 2 per day OR 10 per month, whichever hits first
///
/// Timestamps stored in UserDefaults and persist across app restarts.
enum UsageLimiter {

    private static let log = Logger(subsystem: "com.endlessrumination", category: "UsageLimiter")

    // MARK: - Anti-Abuse Configuration

    /// Max submissions allowed within the rolling window (all users).
    private static let burstMax = 8

    /// Rolling window in seconds (30 minutes).
    private static let burstWindowSeconds: TimeInterval = 30 * 60

    /// Cooldown duration in seconds (15 minutes).
    private static let cooldownSeconds: TimeInterval = 15 * 60

    // MARK: - Free-Tier Configuration

    /// Max submissions per calendar day for free users.
    static let freeDailyLimit = 2

    /// Max submissions per rolling 30-day window for free users.
    static let freeMonthlyLimit = 10

    // MARK: - UserDefaults Keys

    private static let timestampsKey = "usage_limiter_timestamps"
    private static let cooldownUntilKey = "usage_limiter_cooldown_until"

    // MARK: - Limit Result

    enum LimitResult {
        case allowed
        case burstCooldown(CooldownInfo)
        case dailyLimitReached
        case monthlyLimitReached
    }

    struct CooldownInfo {
        let remainingSeconds: Int

        var displayText: String {
            let minutes = remainingSeconds / 60
            let seconds = remainingSeconds % 60
            if minutes > 0 {
                return "\(minutes)m \(seconds)s"
            }
            return "\(seconds)s"
        }
    }

    // MARK: - Public API

    /// Check whether the user can submit right now.
    /// Pass `isPro: true` to skip free-tier limits.
    static func checkLimit(isPro: Bool) -> LimitResult {
        let now = Date()

        // 1. Anti-abuse burst check (all users)
        if let cooldownUntil = activeCooldownEnd(), cooldownUntil > now {
            let remaining = cooldownUntil.timeIntervalSince(now)
            log.info("Burst cooldown active — \(Int(remaining))s remaining")
            return .burstCooldown(CooldownInfo(remainingSeconds: Int(remaining)))
        }

        // Clear expired cooldown
        if activeCooldownEnd() != nil {
            UserDefaults.standard.removeObject(forKey: cooldownUntilKey)
        }

        let burstTimestamps = recentTimestamps(within: burstWindowSeconds, from: now)
        if burstTimestamps.count >= burstMax {
            let cooldownEnd = now.addingTimeInterval(cooldownSeconds)
            UserDefaults.standard.set(cooldownEnd.timeIntervalSince1970, forKey: cooldownUntilKey)
            log.warning("Burst limit hit — \(burstMax) in \(Int(burstWindowSeconds/60))min")
            return .burstCooldown(CooldownInfo(remainingSeconds: Int(cooldownSeconds)))
        }

        // 2. Free-tier daily/monthly check (free users only)
        if !isPro {
            let todayCount = submissionsToday()
            if todayCount >= freeDailyLimit {
                log.info("Free daily limit reached — \(todayCount)/\(freeDailyLimit)")
                return .dailyLimitReached
            }

            let monthCount = submissionsThisMonth()
            if monthCount >= freeMonthlyLimit {
                log.info("Free monthly limit reached — \(monthCount)/\(freeMonthlyLimit)")
                return .monthlyLimitReached
            }
        }

        return .allowed
    }

    /// Record a new submission timestamp. Call AFTER a successful submission.
    static func recordSubmission() {
        var timestamps = allTimestamps()
        timestamps.append(Date().timeIntervalSince1970)

        // Prune timestamps older than 31 days to keep storage small
        let cutoff = Date().timeIntervalSince1970 - (31 * 24 * 60 * 60)
        timestamps = timestamps.filter { $0 > cutoff }

        UserDefaults.standard.set(timestamps, forKey: timestampsKey)

        let today = submissionsToday()
        let month = submissionsThisMonth()
        log.info("Submission recorded — today: \(today)/\(freeDailyLimit), month: \(month)/\(freeMonthlyLimit)")
    }

    // MARK: - Free-Tier Usage Info

    /// Number of submissions used today (calendar day).
    static func submissionsToday() -> Int {
        let startOfDay = Calendar.current.startOfDay(for: Date())
        let cutoff = startOfDay.timeIntervalSince1970
        return allTimestamps().filter { $0 >= cutoff }.count
    }

    /// Number of submissions in the last 30 days.
    static func submissionsThisMonth() -> Int {
        let cutoff = Date().timeIntervalSince1970 - (30 * 24 * 60 * 60)
        return allTimestamps().filter { $0 > cutoff }.count
    }

    /// Free submissions remaining today.
    static var freeDailyRemaining: Int {
        max(0, freeDailyLimit - submissionsToday())
    }

    /// Free submissions remaining this month.
    static var freeMonthlyRemaining: Int {
        max(0, freeMonthlyLimit - submissionsThisMonth())
    }

    // MARK: - Private

    private static func allTimestamps() -> [TimeInterval] {
        UserDefaults.standard.array(forKey: timestampsKey) as? [TimeInterval] ?? []
    }

    private static func recentTimestamps(within window: TimeInterval, from date: Date) -> [TimeInterval] {
        let cutoff = date.timeIntervalSince1970 - window
        return allTimestamps().filter { $0 > cutoff }
    }

    private static func activeCooldownEnd() -> Date? {
        let raw = UserDefaults.standard.double(forKey: cooldownUntilKey)
        guard raw > 0 else { return nil }
        return Date(timeIntervalSince1970: raw)
    }
}
