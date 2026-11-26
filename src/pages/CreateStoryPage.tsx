import { useState, type FormEvent } from 'react'
import { createStory } from '../api/stories'
import { ApiError } from '../api/client'
import { RequireIdentity } from '../components/layout/RequireIdentity'
import { Button } from '../components/ui/Button'
import { Input, Select, Textarea } from '../components/ui/Field'
import { PageHeader } from '../components/ui/PageHeader'
import { Notice } from '../components/ui/States'
import { useToast } from '../components/ui/Toast'
import { navigate } from '../lib/router'
import { updateWorkflow } from '../lib/workflow'
import type { StoryVisibility } from '../types'
import { describeError } from '../utils/errors'
import { LANGUAGE_CODE_PATTERN, SEEDED_LANGUAGES } from '../utils/languages'

export function CreateStoryPage() {
  return (
    <div className="stack stack--lg narrow">
      <PageHeader
        eyebrow="Step 1 of 6"
        title="Start a story"
        description="Give the story a name and tell us the language it will be told in."
      />
      <RequireIdentity>{(ownerId) => <CreateStoryForm ownerId={ownerId} />}</RequireIdentity>
    </div>
  )
}

function CreateStoryForm({ ownerId }: { ownerId: string }) {
  const toast = useToast()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [language, setLanguage] = useState<string>(SEEDED_LANGUAGES[0].code)
  const [customLanguage, setCustomLanguage] = useState('')
  const [visibility, setVisibility] = useState<StoryVisibility>('private')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const usingCustom = language === '__other'
  const languageCode = usingCustom ? customLanguage.trim().toLowerCase() : language

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (submitting) return
    const next: Record<string, string> = {}
    if (!title.trim()) next.title = 'Give your story a title.'
    else if (title.trim().length > 200) next.title = 'Keep the title under 200 characters.'
    if (!LANGUAGE_CODE_PATTERN.test(languageCode)) next.source_language = 'Enter a 2–3 letter language code, such as yo.'
    if (description.length > 5000) next.description = 'Keep the description under 5,000 characters.'
    setErrors(next)
    setFormError(null)
    if (Object.keys(next).length > 0) return

    setSubmitting(true)
    try {
      const story = await createStory({
        owner_id: ownerId,
        title: title.trim(),
        source_language: languageCode,
        description: description.trim() ? description.trim() : null,
        visibility,
      })
      updateWorkflow({ storyId: story.id })
      toast.success('Story created.')
      navigate(`/stories/${story.id}/participant`)
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fieldErrors).length > 0) setErrors(err.fieldErrors)
      setFormError(describeError(err))
      setSubmitting(false)
    }
  }

  return (
    <form className="card card--pad stack" onSubmit={submit} noValidate>
      <Input
        label="Story title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        error={errors.title}
        maxLength={200}
        placeholder="How my grandmother crossed the river"
        required
      />
      <Select
        label="Language of the story"
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
        error={usingCustom ? undefined : errors.source_language}
        hint="The language the storyteller will speak."
        required
      >
        {SEEDED_LANGUAGES.map((l) => (
          <option key={l.code} value={l.code}>
            {l.name} ({l.native})
          </option>
        ))}
        <option value="__other">Another language…</option>
      </Select>
      {usingCustom && (
        <Input
          label="Language code"
          value={customLanguage}
          onChange={(e) => setCustomLanguage(e.target.value)}
          error={errors.source_language}
          maxLength={3}
          hint="A 2–3 letter ISO 639 code. It must already exist in the database’s languages table."
          required
        />
      )}
      <Textarea
        label="Description (optional)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        error={errors.description}
        rows={4}
        maxLength={5000}
        hint="Who is telling it, where and when. This stays with the story."
      />
      <Select
        label="Who can see this story"
        value={visibility}
        onChange={(e) => setVisibility(e.target.value as StoryVisibility)}
        error={errors.visibility}
      >
        <option value="private">Private — only me</option>
        <option value="family">Family</option>
      </Select>
      {formError && (
        <Notice tone="error" title="The story couldn’t be created">
          {formError}
        </Notice>
      )}
      <div className="row">
        <Button type="submit" size="lg" iconRight="arrowRight" loading={submitting}>
          Continue
        </Button>
      </div>
    </form>
  )
}
