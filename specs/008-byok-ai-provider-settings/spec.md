# Feature Specification: BYOK AI Provider Settings

**Feature Branch**: `013-byok-ai-keys`

**Created**: 2026-07-14

**Status**: Draft

**Input**: User description: "BYOK (Bring Your Own Key) AI provider settings: users can save their own AI provider (Anthropic, Gemini, or an OpenAI-compatible endpoint) and API key on a new account settings page. When a user has a key configured, all of their CV-tailoring requests are routed through their own provider and key instead of the platform's shared key. Users without a configured key keep using the platform's shared key as a free tier, exactly as today — no behavior change for them. The key is validated with a live test call before being saved (an invalid key is rejected immediately with an actionable error, not silently stored). Saved keys are stored encrypted at rest and are never exposed back to the client in plaintext — only a masked last-4 preview plus provider/model/base_url are returned. Users can remove their saved key at any time, which reverts them to the platform free tier. This is BYOK only — no wallet, no billing, no Stripe, no usage metering in this feature; a platform-managed pay-as-you-go wallet is an explicitly separate, later feature that this work must not block."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Save a working AI key and get reliable tailoring (Priority: P1)

A user who is frustrated with the platform's shared AI tier (rate limits, inconsistent
quality) goes to a settings page, picks their provider, pastes in their own API key,
and saves it. From then on, every CV they tailor is generated using their own
provider and key, giving them the reliability and model quality they already know
that key provides.

**Why this priority**: This is the entire point of the feature — it is the only story
that actually solves the reliability problem motivating the work. Without it, nothing
else matters.

**Independent Test**: Can be fully tested by saving a valid key for a supported
provider, then tailoring a CV, and confirming (via that provider's own usage
dashboard or logs) that the request was made with the user's key rather than the
platform's.

**Acceptance Scenarios**:

1. **Given** a user with no AI key configured, **When** they open the settings page,
   **Then** they see that they are using the platform's shared free tier.
2. **Given** a user on the settings page, **When** they select a provider, enter a
   valid API key, and save, **Then** the system confirms the key works and shows it
   saved (masked, e.g. `sk-…a4f9`) with its provider and model.
3. **Given** a user with a saved, valid key, **When** they tailor a CV, **Then** the
   request is generated using their own provider and key, not the platform's.

---

### User Story 2 - Invalid key is rejected immediately, not silently stored (Priority: P2)

A user pastes a mistyped or revoked API key. Instead of saving it and finding out it's
broken the next time they try to tailor a resume (which would look identical to the
platform-tier flakiness they're trying to escape), the system tests the key
immediately and tells them it didn't work.

**Why this priority**: Directly prevents the failure mode this feature exists to fix
from reappearing in a new place. Without this, a bad save is indistinguishable from
provider flakiness, defeating the purpose.

**Independent Test**: Can be fully tested by submitting a deliberately invalid API key
and confirming the save is rejected with an actionable message, and that no key was
persisted.

**Acceptance Scenarios**:

1. **Given** a user on the settings page, **When** they submit an invalid or revoked
   API key, **Then** the save is rejected with a clear, actionable error and nothing
   is stored.
2. **Given** a save was rejected, **When** the user checks their settings again,
   **Then** they still show as using the platform free tier (no partial/broken key on
   file).

---

### User Story 3 - Remove a saved key and revert to the free tier (Priority: P3)

A user who saved a key later wants to stop using it (e.g., they cancelled that
provider account) and go back to the platform's shared tier.

**Why this priority**: Necessary for the feature to be safe and reversible, but it's a
simpler, secondary path relative to saving and validating a key.

**Independent Test**: Can be fully tested by removing a previously saved key and
confirming subsequent tailoring requests use the platform's shared key again.

**Acceptance Scenarios**:

1. **Given** a user with a saved key, **When** they choose to remove it, **Then** the
   settings page shows them back on the platform free tier.
2. **Given** a key was just removed, **When** the user tailors a CV, **Then** the
   request uses the platform's shared key, with no error or interruption.

---

### Edge Cases

- What happens when a user's previously valid key is later revoked or expires on the
  provider's side (not caught at save time, since it was valid then)? The tailoring
  request must fail with a clear, actionable message pointing the user back to
  settings — not the platform's generic "temporarily unavailable" error, since this is
  actionable by the user and the other is not.
- What happens when a user configures an OpenAI-compatible endpoint with an
  unreachable or malformed `base_url`? The live validation check at save time must
  catch this the same way it catches an invalid key.
- What happens if a user submits the settings form twice in quick succession (double
  submit)? The second save must not leave the key in a partially-updated state; the
  saved key at rest is always the last successfully validated submission.
- What happens to a user's saved key if their account is deleted? The key record must
  be removed along with the rest of their account data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to view whether they currently have their own AI
  provider key configured, or are using the platform's shared free tier.
- **FR-002**: Users MUST be able to choose one of the platform's supported AI
  providers (Anthropic, Gemini, or a custom OpenAI-compatible endpoint) and submit
  their own API key (plus model, and endpoint URL when applicable) for that provider.
- **FR-003**: The system MUST verify a submitted key actually works, with a real
  request to the chosen provider, before saving it.
- **FR-004**: The system MUST reject a submission whose key fails verification, with
  a message that tells the user their key didn't work, and MUST NOT persist anything
  from a rejected submission.
- **FR-005**: Once a user has a verified key saved, the system MUST use that user's
  own provider and key for all of that user's CV-tailoring requests going forward.
- **FR-006**: Users without a saved key MUST continue to have their CV-tailoring
  requests served by the platform's shared key, with no change in behavior from
  today.
- **FR-007**: The system MUST NOT ever return a user's API key in plaintext once
  saved; a saved key's provider, model, endpoint (if applicable), and a masked
  preview (e.g. last 4 characters) MAY be shown back to the user, but never the full
  key.
- **FR-008**: Saved API keys MUST be stored encrypted at rest.
- **FR-009**: Users MUST be able to remove their saved key at any time, after which
  their CV-tailoring requests revert immediately to the platform's shared key.
- **FR-010**: If a user's saved key later fails during an actual tailoring request
  (e.g., revoked after being saved), the system MUST surface an actionable message
  distinguishing "your key stopped working" from a generic platform-side failure.
- **FR-011**: This feature MUST NOT introduce any billing, credit balance, usage
  metering, or payment flow — those are explicitly out of scope and reserved for a
  separate future feature.

### Key Entities

- **AI Provider Setting**: A single user's configuration for bringing their own AI
  key — which provider, which model, an optional custom endpoint, and their key
  (stored encrypted, never exposed in full). At most one per user; absence means that
  user is on the platform's shared free tier.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user with a supported provider account can go from "no key
  configured" to "tailoring a CV with their own key" in under 2 minutes, without
  contacting support.
- **SC-002**: 100% of invalid-key submissions are rejected at save time with an
  actionable message; 0% result in a silently stored broken key.
- **SC-003**: Users who never configure a key see no change in behavior, latency, or
  output quality of the tailoring feature compared to before this feature existed.
- **SC-004**: When a user's saved key becomes invalid after being saved, the resulting
  error message is distinguishable (by the user, without technical knowledge) from a
  generic "platform is down" message, and tells them what to do next.
- **SC-005**: A user can fully remove their saved key and confirm they're back on the
  shared tier in under 30 seconds.

## Assumptions

- Supported providers for BYOK in this feature are the same three the platform
  already integrates with: Anthropic, Gemini, and any OpenAI-compatible endpoint
  (self-hosted or hosted). Adding further providers is out of scope here.
- "Encrypted at rest" means the platform operator cannot recover a usable plaintext
  key by reading the database directly; it does not require a customer-managed
  encryption key or hardware security module in this iteration.
- One AI provider configuration per user (not per-CV or per-application) — matches
  how the platform's own shared key already applies uniformly across a user's
  tailoring requests.
- The platform's shared free tier continues to exist indefinitely as the default for
  users who don't configure their own key; this feature does not deprecate or rate-
  limit that tier beyond its current behavior.
- Removing a saved key is immediate and does not require re-confirming the user's
  identity beyond their existing authenticated session.
- A platform-managed pay-as-you-go wallet/billing tier is a distinct, separate
  feature and is explicitly not designed or scheduled by this specification.
