import { useState, type FormEvent } from 'react'
import { clearUserId, getUserId, setUserId } from '../../lib/identity'
import { isUuid } from '../../utils/uuid'
import { Button } from '../ui/Button'
import { Input } from '../ui/Field'

/**
 * Temporary stand-in for sign-in. The backend requires an existing users.id
 * for owner_id / created_by / reviewer_id and has no auth or user endpoints.
 */
export function IdentityForm({ onDone }: { onDone?: () => void }) {
  const [value, setValue] = useState(getUserId() ?? '')
  const [error, setError] = useState<string | undefined>()

  function submit(e: FormEvent) {
    e.preventDefault()
    if (!isUuid(value)) {
      setError('Enter a valid user ID, e.g. 3f2b8c1e-5d4a-4c8e-9b7a-1a2b3c4d5e6f')
      return
    }
    setUserId(value)
    setError(undefined)
    onDone?.()
  }

  return (
    <form onSubmit={submit} className="stack" noValidate>
      <p className="muted">
        Roots does not have sign-in yet. The backend needs the ID of an existing row in its{' '}
        <code>users</code> table to own stories and sign off reviews. Paste one here. It is stored
        only in this browser and sent with requests as <code>owner_id</code>, <code>created_by</code>{' '}
        and <code>reviewer_id</code>.
      </p>
      <Input
        label="Workspace user ID"
        value={value}
        onChange={(e) => {
          setValue(e.target.value)
          setError(undefined)
        }}
        error={error}
        placeholder="00000000-0000-0000-0000-000000000000"
        autoComplete="off"
        spellCheck={false}
        required
      />
      <div className="row">
        <Button type="submit">Save</Button>
        {getUserId() && (
          <Button
            variant="ghost"
            onClick={() => {
              clearUserId()
              setValue('')
              onDone?.()
            }}
          >
            Forget this ID
          </Button>
        )}
      </div>
    </form>
  )
}
