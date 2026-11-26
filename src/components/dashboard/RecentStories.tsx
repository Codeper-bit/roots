import type { ReviewStatus, Story } from '../../types'
import { StoryCard } from './StoryCard'

export function RecentStories({
  stories,
  reviewByStory,
}: {
  stories: Story[]
  reviewByStory: Map<string, ReviewStatus | null>
}) {
  return (
    <div className="card-grid">
      {stories.map((story) => (
        <StoryCard
          key={story.id}
          story={story}
          transcriptReview={reviewByStory.has(story.id) ? reviewByStory.get(story.id) : undefined}
        />
      ))}
    </div>
  )
}
