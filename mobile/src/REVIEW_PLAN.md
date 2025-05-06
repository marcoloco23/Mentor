# Codebase Review & Action Plan

## 1. Structure & Modularity
- UI components (`components/`), screens (`screens/`), API logic (`api/`), and utilities (`utils/`) are well-separated.
- All modules use TypeScript with clear interfaces and types.

## 2. Components
- **ChatBubble**
  - Uses semantic theme object for all colors.
  - All `Pressable` elements have `accessibilityLabel` and are accessible.
  - Haptic feedback on mount for user/assistant messages.
  - Uses `expo-clipboard` for Expo compatibility.
  - `allowFontScaling={true}` on `Text`.
  - **Note:** Snackbar logic for copy/timestamp toast should be present if desired.
- **Composer**
  - Theming and accessibility best practices.
  - `allowFontScaling={true}` on `TextInput`.
  - Grows up to 6 lines, robust against measurement errors.
- **MessageList**
  - Uses `KeyboardAwareFlatList` for keyboard handling.
  - Passes accessibility and theming to `ChatBubble`.

## 3. Screens
- **ChatScreen**
  - Uses idiomatic React state for messages, input, typing, and test mode.
  - Handles keyboard dismissal on send, scroll, and drag.
  - Haptic feedback on send.
  - All backgrounds and text use the theme object.
  - Test mode toggle is accessible.
  - **Note:** `onBubblePress` uses `navigator.clipboard` (web only). For mobile, use `expo-clipboard` in `ChatBubble`.

## 4. API & Utilities
- **mentorApi.ts**: Typed, robust, error-handled API and streaming logic.
- **apiBaseUrl.ts**: Platform-aware base URL logic. Consider env vars for production.
- **theme.ts**: Semantic, extensible, ready for design tokens.
- **chatReducer.ts / chatReducer.test.ts**: Pure reducer logic, fully unit tested with Jest.

## 5. Best Practices & Modern Patterns
- Third-party imports first, internal after.
- All major functions and components have docstrings.
- All styles in `StyleSheet.create` or composed with theme.
- All interactive elements are accessible and labeled.
- Font scaling supported everywhere.
- Reducer logic covered by Jest.

---

## Actionable Recommendations

- [ ] **Snackbar/Tooltip for Copy/Time:** Ensure Snackbar logic is present in `ChatBubble` for copy/timestamp feedback.
- [ ] **Clipboard on Web vs Mobile:** In `ChatScreen`, use `expo-clipboard` for mobile, not `navigator.clipboard`.
- [ ] **API Base URL:** Use environment variables or config for production API base URL.
- [ ] **E2E Testing:** Add Detox or similar for E2E coverage if not already present.
- [ ] **Security:** All message text is rendered as plain text, so XSS is not a risk.

---

## Next Steps
- Address actionable recommendations above.
- Continue with launch prep and QA.
- Review and polish as needed before release. 