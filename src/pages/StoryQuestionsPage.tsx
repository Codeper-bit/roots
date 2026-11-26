import { StoryScope } from '../components/layout/StoryScope'
import { StoryQuestions } from '../components/story/StoryQuestions'
import { useParams } from '../lib/router'

export function StoryQuestionsPage() {
  const { storyId } = useParams()
  return (
    <StoryScope storyId={storyId} step="story">
      {({ story }) => (
        <div className="stack narrow-wide">
          <h2 className="section-title">Follow-up questions</h2>
          <StoryQuestions storyId={story.id} />
        </div>
      )}
    </StoryScope>
  )
}
