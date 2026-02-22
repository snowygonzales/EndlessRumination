import XCTest
@testable import EndlessRumination

final class EndlessRuminationTests: XCTestCase {

    func testAllLensesDefined() {
        XCTAssertEqual(Lens.all.count, 20)
    }

    func testLensIndicesSequential() {
        for (i, lens) in Lens.all.enumerated() {
            XCTAssertEqual(lens.id, i)
        }
    }

    @MainActor
    func testWordCount() {
        let state = AppState()
        state.problemText = ""
        XCTAssertEqual(state.wordCount, 0)

        state.problemText = "one two three"
        XCTAssertEqual(state.wordCount, 3)

        state.problemText = "  spaces   everywhere   "
        XCTAssertEqual(state.wordCount, 2)
    }

    @MainActor
    func testCanSubmitRequires20Words() {
        let state = AppState()
        state.problemText = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen"
        XCTAssertFalse(state.canSubmit)

        state.problemText += " twenty"
        XCTAssertTrue(state.canSubmit)
    }

    func testSafetyClientSideCheck() {
        XCTAssertTrue(SafetyService.clientSideCheck("I'm worried about my job interview"))
        XCTAssertFalse(SafetyService.clientSideCheck("I want to hurt myself"))
        XCTAssertFalse(SafetyService.clientSideCheck("I have thoughts of suicide"))
    }

    func testTakeDecoding() throws {
        let json = """
        {"lens_index": 0, "headline": "Test headline", "body": "Test body text"}
        """
        let data = json.data(using: .utf8)!
        let take = try JSONDecoder().decode(Take.self, from: data)
        XCTAssertEqual(take.lensIndex, 0)
        XCTAssertEqual(take.headline, "Test headline")
        XCTAssertEqual(take.body, "Test body text")
    }

    @MainActor
    func testReceiveTake() {
        let state = AppState()
        state.currentScreen = .loading

        let take = Take(lensIndex: 0, headline: "H", body: "B")
        state.receiveTake(take)

        XCTAssertEqual(state.takes.count, 1)
        XCTAssertEqual(state.currentScreen, .takes)
    }

    @MainActor
    func testReceiveTakeNoDuplicates() {
        let state = AppState()
        let take = Take(lensIndex: 0, headline: "H", body: "B")
        state.receiveTake(take)
        state.receiveTake(take)
        XCTAssertEqual(state.takes.count, 1)
    }

    @MainActor
    func testReset() {
        let state = AppState()
        state.problemText = "some text"
        state.currentTakeIndex = 5
        state.takes = [Take(lensIndex: 0, headline: "H", body: "B")]

        state.reset()

        XCTAssertEqual(state.problemText, "")
        XCTAssertEqual(state.currentTakeIndex, 0)
        XCTAssertTrue(state.takes.isEmpty)
    }
}
