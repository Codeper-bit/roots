# Roots: Product Requirements Document

**Status:** Draft v0.1 · **Project type:** 16-day solo build · **Platform:** Full-stack web application

## How to read this document

Every statement falls into one of three categories, marked where it matters:

- **[Decided]**: a confirmed product decision.
- **[Assumption]**: a working assumption used to keep scope moving. It may be revised.
- **[Open]**: an unresolved question. See Section 10.

Anything unmarked is a requirement that follows from a decided principle.

---

## 1. Product overview

**Name:** Roots
**Tagline:** *Keep the story. Keep the language.* **[Assumption: tagline is a placeholder]**
**Guiding principle [Decided]:** *"AI helps preserve the story. The storyteller decides what is true."*

### Problem statement
Grandparents hold family history, proverbs and cultural knowledge in spoken form, often in languages their grandchildren speak poorly or not at all. When these stories are recorded at all, they sit unlabeled in phone galleries or chat apps, with no transcript, no translation and no explanation of the cultural meaning. Generic translation tools tend to flatten idioms, names, proverbs and context, and they present machine output as if it were fact.

### Proposed solution
Roots lets a family record or upload a grandparent's story in its original language, keeps that audio untouched, and generates a draft transcript and draft translation. It also drafts cultural explanations of terms and references that a reader from outside the culture might miss. Family members review and correct the drafts. **Cultural interpretations are marked "confirmed" only when a person explicitly approves them.** The app can then suggest follow-up questions to ask the storyteller next, which keeps the preservation process going.

### Product vision
A family archive where the original voice is always primary, every machine-made layer is clearly labeled as such, and the storyteller or their family has the final word on meaning. Over time, Roots could support more languages and richer family collaboration. The MVP proves one thing: a family can turn a spoken story into a trustworthy, bilingual, human-reviewed record.

### Non-goals **[Decided]**
Roots is not a social network, a public story platform, a general-purpose translation tool, or an analytics product. Roots does not claim to support every language, and it does not claim to be the first product of its kind.

---

## 2. Target users

### Primary users
| User | Needs | Difficulties |
|---|---|---|
| **Storyteller** (grandparent or elder) | Tell stories naturally in their own language. Have the meaning of their words represented correctly. Control what is recorded and kept. | May be unfamiliar with apps, may have hearing or vision difficulty, may be uncomfortable with being recorded or with AI. Often cannot read the English translation to check it. |
| **Family archivist** (typically a grandchild or adult child who operates the app) | Capture stories quickly, get a usable transcript and translation, correct errors, and keep everything in one place. | Limited fluency in the original language, so they cannot always judge transcript accuracy. Often recording in noisy home environments on a phone with variable connectivity. |

### Secondary users
| User | Needs | Difficulties |
|---|---|---|
| **Other family members** (siblings, cousins, relatives) | Read and listen to stories. May help correct the transcript if they speak the language. | May disagree with the archivist or with each other about details. |
| **Future generations** | Access stories years later with context intact. | Rely entirely on the quality and honesty of what was preserved. |

**[Assumption]** For the MVP, the archivist is the main person operating the app, and the storyteller participates by speaking and, where possible, by approving cultural interpretations with the archivist present or relaying the approval.

---

## 3. Core user journey

1. **Record or upload.** The archivist creates a story entry (title, storyteller name, language, date) and either records audio in the browser or uploads an existing audio file. Consent is recorded before the story is saved (see 4.1).
2. **Preserve the original audio.** The original file is stored unmodified. Any playback or processing copy is separate.
3. **Transcribe.** The app produces a draft transcript in the original language. It is labeled as AI-generated and unreviewed.
4. **Translate.** The app produces a draft translation (initially English **[Assumption]**) aligned to the transcript. It is labeled as AI-generated and unreviewed.
5. **Review and correct.** The archivist or a family member listens to the audio and edits the transcript and translation. Edits are tracked and the original generated version is preserved.
6. **Confirm cultural interpretations.** The app proposes short explanations for culturally significant terms, proverbs, names or customs. Each can be approved, edited, or rejected. Only explicit approval earns a "Confirmed" status, and the approver is recorded.
7. **Generate follow-up questions.** From the story content, the app suggests questions to ask the storyteller next. The user can keep, edit or discard them.
8. **Save and retrieve.** The story is saved with its audio, transcript, translation, interpretations and questions. Users can find it again through a library list and basic search, and play it back with its text.

---

## 4. Functional requirements

### 4.1 Accounts, consent and story creation
- Users can sign up, sign in and sign out. **[Assumption: simple email-based auth; method to be chosen at build time.]**
- Each story belongs to a family workspace or account and is private by default. **[Decided: no public stories.]**
- Before saving a recording, the user must record the storyteller's consent: that they agree to the recording and to AI processing, and who gave consent and when. Consent can be given verbally on the recording and noted in the form. **[Assumption]**
- Story metadata: title, storyteller name, original language, recording date, optional notes.

### 4.2 Audio capture and upload
- Record audio in the browser with start, pause, resume, stop and playback-before-save.
- Upload common audio formats (for example MP3, M4A, WAV, WebM). **[Assumption: final list depends on provider support.]**
- Enforce a maximum file length and size, shown to the user before upload. **[Open: limits]**
- Show clear upload progress and failure states.

### 4.3 Original audio preservation
- The original uploaded or recorded file is stored as-is and is never overwritten, re-encoded in place, trimmed or deleted by any processing step.
- Any derived copy (for example for transcription) is stored separately and labeled as derived.
- The user can play the original at any time and download it. **[Assumption]**

### 4.4 Transcription
- Generate a draft transcript in the story's original language using the selected speech recognition provider **[Open: provider]**.
- Processing is asynchronous. The user sees status (queued, processing, ready, failed) and can leave and return.
- On failure, the user sees a plain explanation and a retry action. The audio is never lost.
- The transcript is marked "AI-generated, unreviewed" until a human edits it.

### 4.5 Translation
- Generate a draft translation of the transcript into the target language (English at launch **[Assumption]**).
- Translation is tied to a specific transcript version, so the user can tell if the transcript changed after translation.
- Users can re-run translation after correcting the transcript. Re-running does not erase human edits without confirmation.
- The translation is marked "AI-generated, unreviewed" until a human edits it.

### 4.6 Review and correction
- Side-by-side view of original-language transcript and translation, with audio playback.
- Users can edit both texts, and can mark each text as "Reviewed" once they have checked it. **[Assumption: "Reviewed" is distinct from "Confirmed", see Section 6.]**
- The system keeps the original AI-generated version, and each human edit records who made it and when.
- Users can see what changed and restore an earlier version.

### 4.7 Cultural interpretation
- The app proposes cultural explanations for selected terms or passages, each linked to a place in the transcript.
- Each interpretation is shown as **Proposed** until a person acts on it. Available actions: **Approve**, **Edit then approve**, **Reject**.
- Approved interpretations show a **Confirmed** label with the approver's name and date.
- Users can also add their own interpretation manually. A manual note is clearly labeled as human-authored.
- Rejected interpretations are kept out of the default view but retained for the record. **[Assumption]**

### 4.8 Follow-up questions
- Generate a small set of open-ended follow-up questions from the story content, in the original language where the provider supports it, otherwise in English. **[Open]**
- Users can edit, delete, or mark a question as "asked", and attach the question to the next recording session. **[Assumption: linking is light, for example a note field]**
- Questions are suggestions only and carry no verification status.

### 4.9 Library, search and retrieval
- A library lists the family's stories with title, storyteller, language, date, and processing and review status.
- Basic text search across titles, transcripts, translations and confirmed interpretations.
- A story page shows audio, transcript, translation, interpretations and questions together.
- Users can delete a story and all of its related data. Deletion is explicit and confirmed. **[Decided: privacy requirement, see 5.1]**

---

## 5. Non-functional requirements

### 5.1 Privacy and security
- Stories are private by default. Only authenticated members of the owning account can access them.
- All traffic is encrypted in transit, and stored audio and text are encrypted at rest through the hosting platform. **[Assumption]**
- Audio and transcripts are sent to third-party AI providers only for processing. The provider's data retention and training-use terms must be reviewed before launch. **[Open]**
- Users are told plainly, before first use, which third parties process their data.
- Users can delete their stories and account data on request. **[Decided]**
- No audio or story content is placed in logs or error reports.

### 5.2 Reliability
- Uploads recover from interruption: a failed or partial upload can be resumed or retried without re-recording where feasible. **[Assumption: simple retry in the MVP; chunked resume is a stretch goal.]**
- A recording remains available in the browser until its upload is confirmed successful. **[Assumption]**
- Long-running AI steps are asynchronous, with visible status and retry.
- A failure in transcription, translation, interpretation or question generation never blocks access to the saved audio or the other parts of the story.

### 5.3 Performance
Targets are initial and **[Assumption]**, to be validated against the chosen provider.
- Library and story pages load within 3 seconds on a typical mobile connection.
- Draft transcript and translation for a 5-minute recording are ready within 5 minutes under normal conditions, with progress shown.
- UI remains responsive while processing runs in the background.

### 5.4 Accessibility
- Meets WCAG 2.1 AA as a target for core flows.
- Fully keyboard-operable, with visible focus and labeled controls.
- Large, readable text with a user-adjustable text size. Strong contrast.
- Audio controls are accessible and do not autoplay.
- Language is declared on text in the original language so screen readers pronounce it correctly where possible.
- The recording flow is simple enough for a first-time, older user to complete with help, using few steps and plain wording.

### 5.5 Mobile responsiveness
- Mobile-first layout, usable from small phone screens upward. **[Decided: stories are most likely recorded on phones.]**
- Recording works in current mobile browsers (iOS Safari and Android Chrome at minimum). **[Assumption: verify early, since browser audio capture varies.]**
- Touch targets are comfortably large, and the review view stacks transcript and translation on narrow screens.

### 5.6 Maintainability
- Keep the architecture simple: one web app, one backend, one database, one file store, and AI providers behind a thin interface so they can be swapped.
- Provider calls are isolated in one place, so changing the speech provider or the language does not ripple through the app.
- Core flows are covered by automated tests, and the acceptance criteria in Section 8 map to test cases.
- Configuration and secrets are kept out of source code.
- Documentation covers setup, environment variables and deployment.

---

## 6. Human-in-the-loop requirements

These are hard requirements. They override convenience.

1. **AI output is never treated as verified.** Every generated transcript, translation, interpretation and question is labeled as AI-generated, and carries no verified or confirmed state by default.
2. **Only explicit approval confers "Confirmed."** The Confirmed status applies to cultural interpretations only, and can be set only by a user action of approving that specific interpretation. No bulk auto-approval, no default approval, no approval as a side effect of editing, saving or viewing.
3. **Editing resets status.** If an approved interpretation's text is changed, it returns to Proposed until approved again.
4. **Attribution.** Every Confirmed interpretation records who approved it and when. The UI shows this.
5. **Original audio is immutable.** No feature may modify, replace or silently delete it. Deleting a story is the only way original audio is removed, and it requires explicit confirmation.
6. **Corrections are preserved.** The original AI-generated text and each human revision are retained with author and timestamp. Re-running AI generation never overwrites human edits without explicit confirmation, and keeps the prior version.
7. **Distinct states.** The UI visibly separates *AI-generated*, *human-edited*, *Reviewed* (text checked by a person) and *Confirmed* (interpretation approved). "Reviewed" never implies "Confirmed."
8. **Uncertainty is shown.** Where the provider supplies low-confidence markers, they are surfaced instead of hidden. Where it does not, the interface still states that drafts may contain errors.
9. **Who may confirm.** The product principle says the storyteller decides. The MVP must record the approver's role (storyteller or family member) so a family-confirmed item is not presented as storyteller-confirmed. **[Open: exact rules, see Section 10.]**

---

## 7. MVP scope

### Essential for MVP **[Decided unless marked]**
- Simple accounts, with each story private to its account
- Story creation with metadata and a recorded consent step
- Browser audio recording and audio file upload
- Immutable original audio storage and playback
- Draft transcription in **one** initial language **[Open: language]**
- Draft translation to English **[Assumption]**
- Side-by-side review and editing with preserved version history
- Cultural interpretation proposals with approve, edit and reject, plus Confirmed status and approver record
- Follow-up question generation, with edit and delete
- Story library, story detail page and basic search
- Story and data deletion
- Mobile-responsive, accessible core flows
- Clear failure and retry states for long-running steps

### Future improvements (not in MVP)
- Additional languages and target languages
- Chunked resumable uploads and fuller offline support
- Audio-synchronized transcript (click text to jump to audio)
- Multiple family members with roles and invitations
- Speaker separation for multi-person recordings
- Export as PDF or printable book
- Tagging, themes and timelines
- Glossary of confirmed terms reused across stories
- Notifications and reminders to record
- Native mobile apps

### Explicitly excluded **[Decided]**
Graph databases, social networking features, public story feeds, and elaborate analytics.

---

## 8. Acceptance criteria

Each item should be verifiable by a manual or automated test.

**Accounts and privacy**
- A signed-out visitor cannot view any story, audio or transcript by direct URL.
- A signed-in user cannot access another account's stories.
- A story cannot be saved without a recorded consent confirmation.

**Recording and upload**
- A user can record, pause, resume, stop, play back and save audio on current iOS Safari and Android Chrome.
- A supported audio file uploads and appears in the story. An unsupported or oversized file is rejected with a clear message before upload starts.
- If the network drops during upload, the user sees an error and can retry without losing the recording.

**Original audio preservation**
- After transcription, translation and any edits, the stored original audio is byte-identical to what was uploaded (verified by checksum).
- No UI action or API route can replace or alter the original audio. Deleting a story requires explicit confirmation.

**Transcription**
- Submitting a story produces a draft transcript, or a visible failure with a working retry.
- The transcript is labeled AI-generated and unreviewed until edited.
- A provider failure leaves the audio and metadata intact.

**Translation**
- A draft translation is produced from the current transcript and labeled AI-generated and unreviewed.
- Re-running translation after a transcript edit asks before replacing human-edited translation text, and keeps the previous version.

**Review and correction**
- A user can edit transcript and translation, and the edits persist after reload.
- The original AI-generated version remains viewable. Each revision shows author and timestamp.
- A user can restore an earlier version.

**Cultural interpretation**
- Newly generated interpretations show as Proposed, never Confirmed.
- Approving an interpretation sets Confirmed and records approver and time.
- Editing a Confirmed interpretation returns it to Proposed.
- No API call or UI path produces a Confirmed status without an explicit approval action (covered by a test that attempts to create one without it).
- Rejected interpretations are hidden from the default view.

**Follow-up questions**
- A set of questions is produced for a processed story. They can be edited, deleted and marked asked, and none carry a verified status.

**Library and retrieval**
- Saved stories appear in the library with correct metadata and status.
- Search returns stories matching words in the title, transcript, translation or confirmed interpretations.
- The story page shows audio, transcript, translation, interpretations and questions together.
- Deleting a story removes its audio, text, interpretations and questions.

**Non-functional**
- Core flows pass an automated accessibility check with no critical violations and can be completed by keyboard alone.
- Core flows are usable at a 360px-wide viewport.
- A transcription failure does not prevent playing the audio or reading the other parts of the story.

---

## 9. Risks and assumptions

| Risk | Impact | Mitigation |
|---|---|---|
| **Transcription quality.** Speech recognition for many Nigerian languages, dialects and code-switched speech is often weaker than for major languages. Elderly speakers, background noise and phone microphones add errors. | Poor draft transcripts, which makes review slow and discouraging. | Evaluate providers on real sample audio before committing. Pick the initial language partly on measured quality. Make editing fast. Never present drafts as accurate. |
| **Translation accuracy.** Machine translation can miss idioms, proverbs, names, tone and tonal or diacritic meaning, and can produce fluent but wrong text. | Misleading meaning that looks trustworthy. | Human review is required to reach Reviewed. Label all drafts. Keep the original transcript and audio always available beside the translation. |
| **Cultural interpretation errors.** Generated explanations may be invented, generic or wrong. | Spreading incorrect cultural claims. | The Proposed vs Confirmed model in Section 6. Interpretations are suggestions only. |
| **Consent.** A storyteller may not understand AI processing or may not freely agree. Others may appear in the story. | Ethical and trust harm. | Consent step in plain language, recorded with the story. Easy deletion. **[Open: consent wording and its legal review.]** |
| **Privacy.** Voice recordings and family histories are sensitive, and third-party AI providers will process them. | Exposure or misuse of personal data. | Private by default. Review provider retention and training terms before launch. Minimal logging. Deletion support. |
| **Unreliable networks.** Large audio uploads over weak or intermittent connections may fail. | Lost recordings and frustration. | Keep local recording until upload succeeds, retry, show clear status, cap file size. Fuller offline support is future work. |
| **Browser recording differences.** Audio capture formats and permissions vary across mobile browsers. | Recording fails on some devices. | Test on iOS and Android early. Offer file upload as a fallback. |
| **Scope and time.** Sixteen days, one developer. | Unfinished core flow. | Strict MVP scope in Section 7, a single language, thin provider abstraction, and cuts made from the future list first. |
| **Provider cost and limits.** AI services may charge per minute and rate limit. | Unexpected cost or throttling. | Length caps, async processing, and cost checked during provider evaluation. |

### Assumptions (summary)
1. English is the translation target at launch.
2. The archivist operates the app on a phone or laptop, and the storyteller may not use it directly.
3. A simple email-based sign-in is sufficient.
4. Recordings are typically a few minutes to roughly 15 minutes long.
5. Hosting provides encryption at rest and managed file storage.
6. One language is supported at launch, and the interface itself is in English.

---

## 10. Open questions

| # | Question | Why it matters | Needed by |
|---|---|---|---|
| 1 | **Which language is the initial language?** (Not selected. Roots does not assume support for every Nigerian language.) | Drives provider choice, quality expectations, test data and the family or storyteller used for validation. | Day 1 to 2 |
| 2 | **Which speech recognition provider?** | Determines supported languages, accuracy, pricing, audio limits, data retention, and whether confidence scores exist. | Day 1 to 2, alongside Q1 |
| 3 | Which services handle translation, cultural interpretation drafts and follow-up question generation? Can one provider cover them? | Affects cost, privacy review and how many integrations the solo build needs. | Day 2 to 3 |
| 4 | **Who may confirm an interpretation** when the storyteller is unavailable or has passed away? Is a family-confirmed state allowed, and how is it labeled? | Core to the principle "the storyteller decides what is true." | Before building the review flow |
| 5 | Is English the only translation target for the MVP? | Scope of translation and review UI. | Day 2 |
| 6 | Maximum audio length and file size? | Cost, upload reliability, processing time. | Day 2 to 3 |
| 7 | Consent wording and format (verbal on recording, checkbox, or both)? Does anyone need to review the wording? | Ethical and legal exposure. | Before any real family recordings |
| 8 | Provider data retention and model-training terms: acceptable for family recordings? | Privacy commitments the product can honestly make. | Before launch |
| 9 | Authentication method and the account model (single family account vs invited members). | Affects scope of the MVP's access control. | Day 2 |
| 10 | Should the original-language transcript be editable by people who do not speak the language? | Risk of well-meaning corrections introducing errors. | Before the review flow |
| 11 | Hosting and storage choice, and approximate budget. | Encryption, cost and deployment effort. | Day 2 to 3 |
| 12 | Final tagline and visual identity. | Branding only, not blocking. | Any time |
