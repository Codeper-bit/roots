import { useState, type FormEvent } from 'react'
import { createStoryQuestion, listStoryQuestions, updateStoryQuestionStatus } from '../../api/storyQuestions'
import { useAsync } from '../../hooks/useAsync'
import type { StoryQuestion, StoryQuestionStatus } from '../../types'
import { describeError } from '../../utils/errors'
import { formatDate } from '../../utils/formatDate'
import { QuestionBadge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Textarea } from '../ui/Field'
import { EmptyState, ErrorState, LoadingState, Notice } from '../ui/States'
import { useToast } from '../ui/Toast'

export function StoryQuestions({ storyId }: { storyId: string }) {
  const toast = useToast()
  const state = useAsync((signal) => listStoryQuestions(storyId, signal), [storyId])
  const [text, setText] = useState('')
  const [adding, setAdding] = useState(false)
  const [fieldError, setFieldError] = useState<string | undefined>()
  const [busyId, setBusyId] = useState<string | null>(null)

  async function add(e: FormEvent) {
    e.preventDefault()
    if (adding) return
    if (!text.trim()) {
      setFieldError('Write a question first.')
      return
    }
    setAdding(true)
    setFieldError(undefined)
    try {
      await createStoryQuestion(storyId, text.trim())
      setText('')
      toast.success('Question added.')
      state.reload()
    } catch (err) {
      setFieldError(describeError(err))
    } finally {
      setAdding(false)
    }
  }

  async function setStatus(q: StoryQuestion, status: StoryQuestionStatus) {
    if (busyId) return
    setBusyId(q.id)
    try {
      await updateStoryQuestionStatus(q.id, status)
      state.reload()
    } catch (err) {
      toast.error(describeError(err))
    } finally {
      setBusyId(null)
    }
  }

  const questions = state.data?.questions ?? []

  return (
    <div className="stack">
      <Notice tone="info" title="How questions work today">
        Roots keeps a list of follow-up questions for each story. Questions are not generated
        automatically yet, so only the ones added here appear. Recording an answer isn’t supported by
        the backend yet; ask the question in person, then mark it as asked.
      </Notice>

      {state.loading && !state.data ? (
        <LoadingState label="Loading questions…" />
      ) : state.error && !state.data ? (
        <ErrorState error={state.error} onRetry={state.reload} title="Couldn’t load questions" />
      ) : questions.length === 0 ? (
        <EmptyState icon="message" title="No questions yet">
          Add something you’d like to ask the storyteller next time you talk.
        </EmptyState>
      ) : (
        <ul className="question-list">
          {questions.map((q) => (
            <li key={q.id} className={`question${q.status === 'dismissed' ? ' question--dismissed' : ''}`}>
              <div className="question__main">
                <p className="question__text">{q.question}</p>
                <p className="muted small row row--wrap">
                  <QuestionBadge status={q.status} /> added {formatDate(q.created_at)}
                </p>
              </div>
              <div className="row row--wrap">
                {q.status !== 'asked' && (
                  <Button size="sm" variant="secondary" onClick={() => setStatus(q, 'asked')} disabled={busyId !== null}>
                    Mark as asked
                  </Button>
                )}
                {q.status !== 'dismissed' ? (
                  <Button size="sm" variant="ghost" onClick={() => setStatus(q, 'dismissed')} disabled={busyId !== null}>
                    Dismiss
                  </Button>
                ) : (
                  <Button size="sm" variant="ghost" onClick={() => setStatus(q, 'suggested')} disabled={busyId !== null}>
                    Restore
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <form className="card card--pad stack" onSubmit={add} noValidate>
        <Textarea
          label="Add a follow-up question"
          value={text}
          rows={2}
          maxLength={1000}
          onChange={(e) => {
            setText(e.target.value)
            setFieldError(undefined)
          }}
          error={fieldError}
          hint="For example: Who taught you this song?"
        />
        <div>
          <Button type="submit" icon="plus" loading={adding}>
            Add question
          </Button>
        </div>
      </form>
    </div>
  )
}
