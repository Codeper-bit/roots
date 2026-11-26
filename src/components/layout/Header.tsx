import { useState } from 'react'
import { useUserId } from '../../lib/identity'
import { Link } from '../../lib/router'
import { shortId } from '../../utils/uuid'
import { Icon, Wordmark } from '../ui/Icon'
import { Modal } from '../ui/Modal'
import { ApiStatus } from './ApiStatus'
import { IdentityForm } from './IdentityForm'

export function Header() {
  const userId = useUserId()
  const [open, setOpen] = useState(false)
  return (
    <header className="topbar">
      <Link to="/" className="topbar__brand" aria-label="Roots home">
        <Wordmark size={20} />
      </Link>
      <div className="topbar__spacer" />
      <ApiStatus />
      <button type="button" className="identity-chip" onClick={() => setOpen(true)}>
        <Icon name="user" size={16} />
        <span>{userId ? `User ${shortId(userId)}…` : 'Choose user'}</span>
      </button>
      <Modal open={open} title="Workspace user" onClose={() => setOpen(false)}>
        <IdentityForm onDone={() => setOpen(false)} />
      </Modal>
    </header>
  )
}
