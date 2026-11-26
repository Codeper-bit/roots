// Types mirror backend/app/schemas/*.py. Datetimes and UUIDs arrive as strings.

export type UUID = string

export type StoryStatus = 'draft' | 'processing' | 'in_review' | 'completed'
export type StoryVisibility = 'private' | 'family'

export type ParticipantRole =
  | 'storyteller'
  | 'interviewer'
  | 'family_member'
  | 'translator'
  | 'reviewer'
  | 'other'

export type ConsentPurpose =
  | 'audio_storage'
  | 'transcription'
  | 'translation'
  | 'cultural_interpretation'
  | 'family_sharing'
export type ConsentStatus = 'granted' | 'declined' | 'withdrawn'
export type ConsentDecision = 'granted' | 'declined'

export type AudioUploadStatus = 'pending' | 'uploaded' | 'failed'

export type ContentType = 'transcript' | 'translation' | 'interpretation'
export type ContentOrigin = 'ai_generated' | 'human_created' | 'human_edited'
export type ReviewStatus = 'unreviewed' | 'approved' | 'rejected' | 'changes_requested'
export type ReviewDecision = 'approved' | 'rejected' | 'changes_requested'

export type ProcessingJobType =
  | 'transcription'
  | 'translation'
  | 'interpretation'
  | 'question_generation'
export type ProcessingJobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled'

export type StoryQuestionStatus = 'suggested' | 'asked' | 'dismissed'

// ---- Stories -------------------------------------------------------------
export interface StoryCreate {
  owner_id: UUID
  title: string
  source_language: string
  description?: string | null
  visibility?: StoryVisibility
}
export interface Story {
  id: UUID
  owner_id: UUID
  title: string
  description: string | null
  source_language: string
  status: StoryStatus
  visibility: StoryVisibility
  deleted_at: string | null
  created_at: string
  updated_at: string
}
export interface StoryList {
  stories: Story[]
  total: number
}

// ---- Participants --------------------------------------------------------
export interface ParticipantCreate {
  story_id: UUID
  user_id?: UUID | null
  display_name: string
  role: ParticipantRole
}
export interface Participant {
  id: UUID
  story_id: UUID
  user_id: UUID | null
  display_name: string
  role: ParticipantRole
  created_at: string
  updated_at: string
}

// ---- Consents ------------------------------------------------------------
export interface ConsentCreate {
  participant_id: UUID
  purpose: ConsentPurpose
  status: ConsentDecision
}
export interface Consent {
  id: UUID
  participant_id: UUID
  purpose: ConsentPurpose
  status: ConsentStatus
  granted_at: string | null
  withdrawn_at: string | null
  created_at: string
  updated_at: string
}
export interface ConsentList {
  consents: Consent[]
}

// ---- Audio ---------------------------------------------------------------
export interface AudioAsset {
  id: UUID
  story_id: UUID
  storage_key: string
  mime_type: string
  size_bytes: number | null
  duration_ms: number | null
  checksum: string | null
  upload_status: AudioUploadStatus
  created_at: string
  updated_at: string
}

// ---- Transcription / content --------------------------------------------
export interface TranscriptionCreate {
  participant_id: UUID
  story_id: UUID
  audio_asset_id: UUID
  language_code: string
  created_by?: UUID | null
}

export interface ContentVersionCreate {
  story_id: UUID
  content_type: ContentType
  language_code: string
  content: string
  origin: ContentOrigin
  based_on_version_id?: UUID | null
  created_by?: UUID | null
}
export interface ContentVersion {
  id: UUID
  story_id: UUID
  content_type: ContentType
  language_code: string
  version_number: number
  content: string
  origin: ContentOrigin
  based_on_version_id: UUID | null
  created_by: UUID | null
  review_status: ReviewStatus
  created_at: string
  updated_at: string
}

export interface ContentReviewCreate {
  content_version_id: UUID
  reviewer_id: UUID
  decision: ReviewDecision
  comment?: string | null
}
export interface ContentReview {
  id: UUID
  content_version_id: UUID
  reviewer_id: UUID
  decision: ReviewDecision
  comment: string | null
  created_at: string
}

// ---- Processing jobs -----------------------------------------------------
export interface ProcessingJob {
  id: UUID
  story_id: UUID
  audio_asset_id: UUID | null
  job_type: ProcessingJobType
  status: ProcessingJobStatus
  attempts: number
  error_message: string | null
  created_at: string
  updated_at: string
  completed_at: string | null
}

// ---- Story questions -----------------------------------------------------
export interface StoryQuestion {
  id: UUID
  story_id: UUID
  question: string
  status: StoryQuestionStatus
  created_at: string
  updated_at: string
}
export interface StoryQuestionList {
  questions: StoryQuestion[]
}

export interface HealthResponse {
  status: string
  database: string
}
