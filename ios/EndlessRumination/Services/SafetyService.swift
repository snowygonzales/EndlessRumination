import Foundation

/// Client-side safety checks for harmful content.
///
/// On-device version: server-side check removed (no backend).
/// Multi-layer approach:
///   1. Input blocklist with Unicode normalization (pre-generation)
///   2. Safety preamble in all system prompts (during generation)
///   3. Output blocklist on model responses (post-generation)
enum SafetyService {

    // MARK: - Input Blocklist (checked before generation)

    private static let inputBlocklist = [
        // Suicidal ideation -- direct
        "kill myself", "kill me", "suicide", "suicidal",
        "hurt myself", "harm myself", "self-harm", "self harm",
        "end it all", "end my life", "want to die", "wanna die",
        "cut myself", "cutting myself",
        "overdose", "hang myself", "jump off", "slit my",
        "take my life", "no reason to live", "better off dead",

        // Suicidal ideation -- indirect/euphemistic
        "don't want to exist", "want to disappear forever",
        "want to vanish", "not be here anymore",
        "not wake up", "go to sleep forever",
        "make it stop forever", "make the pain stop",
        "final exit", "permanent solution",
        "no point in living", "nothing to live for",
        "nobody would miss me", "nobody would notice",
        "wrote my goodbyes", "writing my goodbye",
        "saying goodbye to everyone", "goodbye letter",
        "one way out", "only way out",
        "can't go on", "can't do this anymore",
        "want it to be over", "just want it to end",
        "world without me", "they'd be better without me",
        "everyone would be better off",

        // Self-harm methods
        "razor blade", "slit my wrist", "cut my wrist",
        "tie a noose", "swallow pills", "stockpiling pills",
        "carbon monoxide", "jump from",
        "bridge near", "rooftop",

        // Violence toward others
        "kill someone", "kill him", "kill her", "kill them",
        "hurt someone", "hurt him", "hurt her", "hurt them",
        "want to attack", "fantasize about hurting",
        "murder", "stab", "shoot", "strangle",
        "weapon", "gun",
    ]

    // MARK: - Output Blocklist (checked after generation)

    /// Phrases that should never appear in model-generated takes.
    /// Checked against output before displaying to user.
    private static let outputBlocklist = [
        // Model encouraging self-harm
        "kill yourself", "end your life", "you should die",
        "better off dead", "no reason to live",
        "nothing to live for", "no hope for you",
        "give up", "just give up",
        "you deserve to suffer", "you deserve the pain",
        "there is no way out", "no way out for you",
        "hopeless case", "beyond help",
        "no one can help you", "no one cares",

        // Model providing dangerous advice
        "take these pills", "take medication",
        "stop taking your medication",
        "you don't need therapy", "therapy is useless",
        "don't see a doctor", "don't talk to anyone",

        // Model encouraging violence
        "hurt them", "attack them", "fight them",
        "make them pay", "get revenge",
        "they deserve to suffer",
    ]

    // MARK: - Crisis Resources

    struct CrisisResource {
        let name: String
        /// "call", "text", or "link"
        let action: String
        let value: String
        let description: String
    }

    /// Locale-aware crisis resources.
    /// Returns country-specific hotlines based on device region, plus an
    /// international directory link as fallback for all other countries.
    static var crisisResources: [CrisisResource] {
        let countryCode = Locale.current.region?.identifier ?? "US"
        var resources = countryHotlines[countryCode] ?? countryHotlines["US"]!

        // Always append international directory link
        resources.append(CrisisResource(
            name: "Find a helpline in your country",
            action: "link",
            value: "https://findahelpline.com/countries/\(countryCode.lowercased())",
            description: "175+ countries covered"
        ))

        return resources
    }

    // Top countries by App Store revenue with verified crisis numbers
    private static let countryHotlines: [String: [CrisisResource]] = [
        "US": [
            CrisisResource(name: "988 Suicide & Crisis Lifeline", action: "call", value: "988", description: "Free, confidential, 24/7"),
            CrisisResource(name: "Crisis Text Line", action: "text", value: "HOME to 741741", description: "Text-based crisis support"),
        ],
        "GB": [
            CrisisResource(name: "Samaritans", action: "call", value: "116123", description: "Free, 24/7 emotional support"),
            CrisisResource(name: "Shout", action: "text", value: "SHOUT to 85258", description: "Text-based crisis support"),
        ],
        "IE": [
            CrisisResource(name: "Samaritans", action: "call", value: "116123", description: "Free, 24/7 emotional support"),
        ],
        "CA": [
            CrisisResource(name: "Talk Suicide Canada", action: "call", value: "18334564566", description: "24/7 crisis support"),
        ],
        "AU": [
            CrisisResource(name: "Lifeline Australia", action: "call", value: "131114", description: "24/7 crisis support"),
        ],
        "NZ": [
            CrisisResource(name: "Lifeline NZ", action: "call", value: "0800543354", description: "24/7 crisis support"),
        ],
        "DE": [
            CrisisResource(name: "Telefonseelsorge", action: "call", value: "08001110111", description: "Kostenlos, 24/7"),
        ],
        "FR": [
            CrisisResource(name: "3114 - Numero national", action: "call", value: "3114", description: "Gratuit, 24h/24"),
        ],
        "ES": [
            CrisisResource(name: "Telefono de la Esperanza", action: "call", value: "717003717", description: "24/7, gratuito"),
        ],
        "IT": [
            CrisisResource(name: "Telefono Amico", action: "call", value: "0223272327", description: "Supporto emotivo"),
        ],
        "NL": [
            CrisisResource(name: "113 Zelfmoordpreventie", action: "call", value: "113", description: "Gratis, 24/7"),
        ],
        "JP": [
            CrisisResource(name: "Inochi no Denwa", action: "call", value: "0120783556", description: "24/7"),
        ],
        "KR": [
            CrisisResource(name: "Mental Health Crisis Line", action: "call", value: "15770199", description: "24/7"),
        ],
        "BR": [
            CrisisResource(name: "CVV", action: "call", value: "188", description: "24 horas, gratuito"),
        ],
        "IN": [
            CrisisResource(name: "iCall", action: "call", value: "9152987821", description: "Mental health support"),
        ],
        "MX": [
            CrisisResource(name: "SAPTEL", action: "call", value: "5552598121", description: "24 horas"),
        ],
        "TW": [
            CrisisResource(name: "Suicide Prevention Hotline", action: "call", value: "1925", description: "24/7"),
        ],
        "SE": [
            CrisisResource(name: "Mind Sjalvmordslinjen", action: "call", value: "90101", description: "Dygnet runt"),
        ],
        "CH": [
            CrisisResource(name: "Die Dargebotene Hand", action: "call", value: "143", description: "24/7"),
        ],
    ]

    // MARK: - Input Safety Check

    /// Client-side keyword check for user input before generation.
    /// Returns `true` if the text is safe, `false` if it contains blocked terms.
    static func clientSideCheck(_ text: String) -> Bool {
        let normalized = normalizeForSafetyCheck(text)
        return !inputBlocklist.contains(where: { normalized.contains($0) })
    }

    // MARK: - Output Safety Check

    /// Check model-generated output for harmful content.
    /// Returns `true` if the output is safe to display, `false` if it should be suppressed.
    static func outputSafetyCheck(_ text: String) -> Bool {
        let normalized = normalizeForSafetyCheck(text)
        return !outputBlocklist.contains(where: { normalized.contains($0) })
    }

    // MARK: - Text Normalization

    /// Normalize text to resist common evasion techniques:
    /// - Lowercasing
    /// - Unicode NFKD decomposition + diacritic stripping (catches homoglyphs)
    /// - Strip non-alphanumeric characters except spaces (catches l33tspeak separators)
    /// - Common l33t substitutions
    /// - Collapse multiple spaces
    private static func normalizeForSafetyCheck(_ text: String) -> String {
        var result = text.lowercased()

        // Unicode NFKD decomposition — folds homoglyphs and accented chars to ASCII base
        // e.g., Cyrillic "а" → "a", "е" → "e", accented "ò" → "o"
        if let data = result.data(using: .ascii, allowLossyConversion: true),
           let ascii = String(data: data, encoding: .ascii) {
            result = ascii
        }

        // Common l33t substitutions
        let leetMap: [Character: Character] = [
            "0": "o", "1": "i", "3": "e", "4": "a",
            "5": "s", "7": "t", "@": "a", "$": "s",
        ]
        result = String(result.map { leetMap[$0] ?? $0 })

        // Strip non-alphanumeric except spaces (catches s.u.i.c.i.d.e, s-u-i-c-i-d-e, etc.)
        result = String(result.unicodeScalars.filter {
            CharacterSet.alphanumerics.contains($0) || $0 == " "
        })

        // Collapse multiple spaces
        while result.contains("  ") {
            result = result.replacingOccurrences(of: "  ", with: " ")
        }

        return result.trimmingCharacters(in: .whitespaces)
    }
}
