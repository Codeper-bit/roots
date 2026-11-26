# Roots frontend: notes and backend gaps

## Run it
    npm install
    cp .env.example .env.local   # optional
    npm run dev                  # backend must be running on 127.0.0.1:8000
    npm run typecheck && npm run build

## CORS (needs a decision)
`backend/app/main.py` has no CORS middleware, so a browser on localhost:5173 cannot call
http://127.0.0.1:8000. Pick one:
1. Add `CORSMiddleware` (allow origin http://localhost:5173) to the backend, or
2. Set `VITE_API_BASE_URL=/api` in `.env.local`. `vite.config.js` proxies `/api` to the backend.

## Temporary identity
There is no auth and no users endpoint, yet stories need `owner_id`, edits need `created_by`, and
reviews need `reviewer_id`, all FKs to `users.id`. The app asks for an existing user UUID
(header chip), stored in localStorage. Replace `src/lib/identity.ts` when Supabase Auth lands.

## Integrated endpoints
GET /health; POST/GET /stories, GET /stories/{id}; POST /participants, GET /stories/{id}/participants;
POST /consents, GET /participants/{id}/consents, POST /consents/{id}/withdraw;
POST /audio-assets/upload (multipart, with progress), GET /audio-assets/{id};
POST /transcriptions; POST /content-versions, GET /stories/{id}/content-versions;
POST /content-reviews, GET /content-reviews/version/{id};
POST /story-questions, GET /stories/{id}/questions, PATCH /story-questions/{id}/status;
GET /processing-jobs/story/{id}.

## Waiting on the backend
| Need | Effect today |
|---|---|
| Download / signed URL for audio | Recording plays only in the tab that recorded it; not after refresh |
| List audio assets | Dashboard "Recent recordings" is an honest note; audio ids come from the session or processing jobs |
| Segments, timestamps, speakers, word confidence | Transcript is one text, split into display segments; no speaker labels, timeline sync or uncertain-word highlights |
| Translation endpoint | Panel shows "not available yet"; a person can write one (stored as a `translation` content version) |
| Question generation and answers | Only manually added questions; no answers |
| Cross-story content list | Review dashboard fetches versions per story (N+1, first 40 stories) |
| Language list endpoint | Seeded yo/ha/ig plus manual ISO code |
| Anything that updates `stories.status` | Status stays "draft"; review counts come from content versions instead |
| Users / auth | See Temporary identity. Not production-secure. |

## Details worth knowing
* Recorded blobs are re-typed to `audio/webm` (no `;codecs=`), because the DB constraint rejects it.
* Transcription provider limit is 25 MB (upload limit is 50 MB); the UI warns.
* `POST /transcriptions` is synchronous: "Processing" means the request is in flight. After a refresh the page
  polls `/processing-jobs/story/{id}` while a job is queued or running.
* Corrections create a new `human_edited` version; AI drafts are never overwritten.
* A small History-API router (`src/lib/router.tsx`) replaces react-router; icons are local SVGs.
