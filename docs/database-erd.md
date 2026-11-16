
erDiagram
    LANGUAGES ||--o{ STORIES : identifies
    LANGUAGES ||--o{ CONTENT_VERSIONS : identifies

    USERS ||--o{ STORIES : owns
    USERS o|--o{ STORY_PARTICIPANTS : may_be
    STORIES ||--o{ STORY_PARTICIPANTS : has

    STORY_PARTICIPANTS ||--o{ CONSENT_RECORDS : gives

    STORIES ||--o{ AUDIO_ASSETS : contains
    STORIES ||--o{ CONTENT_VERSIONS : has
    CONTENT_VERSIONS ||--o{ CONTENT_REVIEWS : receives
    USERS ||--o{ CONTENT_REVIEWS : writes

    STORIES ||--o{ PROCESSING_JOBS : has
    AUDIO_ASSETS o|--o{ PROCESSING_JOBS : uses

    STORIES ||--o{ STORY_QUESTIONS : has