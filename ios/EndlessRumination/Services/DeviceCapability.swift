import Foundation

/// Device capability checks for on-device model inference.
enum DeviceCapability {

    /// Device physical RAM in bytes.
    static var physicalMemory: UInt64 {
        ProcessInfo.processInfo.physicalMemory
    }

    /// Device physical RAM in GB.
    static var ramGB: Double {
        Double(physicalMemory) / 1_073_741_824
    }

    /// Whether this device can run the optimized 4B model (~2.0 GB at 4-bit).
    /// Requires 6 GB+ RAM with `increased-memory-limit` entitlement.
    static var canRunModel: Bool {
        ramGB >= 5.5 // 6 GB devices report ~5.5 GB usable
    }

    /// Actual available memory right now (accounts for system pressure).
    static var availableMemoryGB: Double {
        Double(os_proc_available_memory()) / 1_073_741_824
    }

    /// Human-readable diagnostics string.
    static var info: String {
        String(format: "RAM: %.1f GB | Available: %.1f GB | Can run: %@",
               ramGB, availableMemoryGB, canRunModel ? "YES" : "NO")
    }
}
