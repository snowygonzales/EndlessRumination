import SwiftUI

struct LicensesView: View {

    var body: some View {
        ZStack {
            ERColors.background.ignoresSafeArea()

            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    Text("This app uses the following open-source software.")
                        .font(.system(size: 13))
                        .foregroundStyle(ERColors.secondaryText)
                        .padding(.bottom, 4)

                    licenseSection(title: "ON-DEVICE AI MODEL", items: modelItems)
                    licenseSection(title: "MACHINE LEARNING", items: mlItems)
                    licenseSection(title: "APPLE OPEN SOURCE", items: appleItems)
                    licenseSection(title: "OTHER", items: otherItems)

                    Spacer(minLength: 40)
                }
                .padding(.horizontal, 24)
                .padding(.top, 12)
            }
        }
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .principal) {
                Text("OPEN SOURCE LICENSES")
                    .font(.system(size: 10, weight: .medium, design: .monospaced))
                    .tracking(2)
                    .foregroundStyle(ERColors.dimText)
            }
        }
        .toolbarBackground(ERColors.background, for: .navigationBar)
    }

    // MARK: - Section Builder

    private func licenseSection(title: String, items: [LicenseItem]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.system(size: 10, weight: .medium, design: .monospaced))
                .tracking(2)
                .foregroundStyle(ERColors.dimText)

            ForEach(items) { item in
                LicenseRow(item: item)
            }
        }
    }

    // MARK: - Data

    private var modelItems: [LicenseItem] {
        [
            LicenseItem(
                name: "Qwen 3.5 4B",
                description: "On-device language model for generating perspectives",
                licenseType: .apache2,
                copyright: "Copyright 2025-2026 Alibaba Cloud"
            ),
        ]
    }

    private var mlItems: [LicenseItem] {
        [
            LicenseItem(
                name: "mlx-swift",
                description: "Machine learning framework for Apple Silicon",
                licenseType: .mit,
                copyright: "Copyright (c) 2023 ml-explore"
            ),
            LicenseItem(
                name: "mlx-swift-lm",
                description: "Language model inference for Apple Silicon",
                licenseType: .mit,
                copyright: "Copyright (c) 2024 ml-explore"
            ),
            LicenseItem(
                name: "swift-transformers",
                description: "Tokenizers and model loading from Hugging Face",
                licenseType: .apache2,
                copyright: "Copyright 2022 Hugging Face SAS"
            ),
            LicenseItem(
                name: "swift-jinja",
                description: "Jinja template engine for prompt formatting",
                licenseType: .apache2,
                copyright: "Copyright 2022 Hugging Face SAS"
            ),
        ]
    }

    private var appleItems: [LicenseItem] {
        [
            LicenseItem(
                name: "swift-collections",
                description: "Additional Swift collection types",
                licenseType: .apache2,
                copyright: "Copyright Apple Inc."
            ),
            LicenseItem(
                name: "swift-numerics",
                description: "Numerical computing support",
                licenseType: .apache2,
                copyright: "Copyright Apple Inc."
            ),
            LicenseItem(
                name: "swift-crypto",
                description: "Cryptographic operations",
                licenseType: .apache2,
                copyright: "Copyright Apple Inc."
            ),
            LicenseItem(
                name: "swift-asn1",
                description: "ASN.1 encoding and decoding",
                licenseType: .apache2,
                copyright: "Copyright Apple Inc."
            ),
        ]
    }

    private var otherItems: [LicenseItem] {
        [
            LicenseItem(
                name: "yyjson",
                description: "High-performance JSON parsing",
                licenseType: .mit,
                copyright: "Copyright (c) 2020 YaoYuan"
            ),
            LicenseItem(
                name: "Google Mobile Ads SDK",
                description: "Advertising framework",
                licenseType: .apache2,
                copyright: "Copyright 2021 Google LLC"
            ),
            LicenseItem(
                name: "Google UMP SDK",
                description: "User consent management",
                licenseType: .apache2,
                copyright: "Copyright 2021 Google LLC"
            ),
        ]
    }
}

// MARK: - License Item Model

private struct LicenseItem: Identifiable {
    let id = UUID()
    let name: String
    let description: String
    let licenseType: LicenseType
    let copyright: String
}

private enum LicenseType: String {
    case mit = "MIT"
    case apache2 = "Apache 2.0"

    var fullText: String {
        switch self {
        case .mit: return LicenseTexts.mit
        case .apache2: return LicenseTexts.apache2
        }
    }
}

// MARK: - License Row

private struct LicenseRow: View {
    let item: LicenseItem
    @State private var isExpanded = false

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Button {
                withAnimation(.easeInOut(duration: 0.2)) {
                    isExpanded.toggle()
                }
            } label: {
                HStack {
                    VStack(alignment: .leading, spacing: 3) {
                        Text(item.name)
                            .font(.system(size: 14, weight: .medium))
                            .foregroundStyle(ERColors.primaryText)

                        Text(item.description)
                            .font(.system(size: 11))
                            .foregroundStyle(ERColors.secondaryText)
                    }

                    Spacer()

                    Text(item.licenseType.rawValue)
                        .font(.system(size: 10, weight: .medium, design: .monospaced))
                        .foregroundStyle(ERColors.accentCool)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(ERColors.accentCool.opacity(0.12))
                        .clipShape(RoundedRectangle(cornerRadius: 4))

                    Image(systemName: "chevron.right")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundStyle(ERColors.dimText)
                        .rotationEffect(.degrees(isExpanded ? 90 : 0))
                }
            }
            .buttonStyle(.plain)
            .padding(.vertical, 10)

            if isExpanded {
                VStack(alignment: .leading, spacing: 8) {
                    Text(item.copyright)
                        .font(.system(size: 11, weight: .medium))
                        .foregroundStyle(ERColors.secondaryText)

                    Text(item.licenseType.fullText)
                        .font(.system(size: 9, design: .monospaced))
                        .foregroundStyle(ERColors.dimText)
                        .lineSpacing(3)
                }
                .padding(.bottom, 12)
                .transition(.opacity.combined(with: .move(edge: .top)))
            }

            Rectangle()
                .fill(ERColors.border)
                .frame(height: 1)
        }
    }
}

// MARK: - License Full Texts

private enum LicenseTexts {

    static let mit = """
        MIT License

        Permission is hereby granted, free of charge, to any person obtaining a copy \
        of this software and associated documentation files (the "Software"), to deal \
        in the Software without restriction, including without limitation the rights \
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell \
        copies of the Software, and to permit persons to whom the Software is \
        furnished to do so, subject to the following conditions:

        The above copyright notice and this permission notice shall be included in all \
        copies or substantial portions of the Software.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR \
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, \
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE \
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER \
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, \
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE \
        SOFTWARE.
        """

    static let apache2 = """
        Apache License, Version 2.0

        Licensed under the Apache License, Version 2.0 (the "License"); \
        you may not use this file except in compliance with the License. \
        You may obtain a copy of the License at

            http://www.apache.org/licenses/LICENSE-2.0

        Unless required by applicable law or agreed to in writing, software \
        distributed under the License is distributed on an "AS IS" BASIS, \
        WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. \
        See the License for the specific language governing permissions and \
        limitations under the License.
        """
}
