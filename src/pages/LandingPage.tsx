import { ButtonLink } from '../components/ui/Button'
import { Icon, Wordmark, type IconName } from '../components/ui/Icon'
import { Link } from '../lib/router'

const STEPS: Array<{ icon: IconName; title: string; text: string }> = [
  { icon: 'users', title: 'Begin with the storyteller', text: 'Name the story and the person telling it, in the language they think in.' },
  { icon: 'shield', title: 'Ask permission first', text: 'Nothing is recorded or transcribed until the storyteller says yes, one purpose at a time.' },
  { icon: 'mic', title: 'Record the voice', text: 'Record on the spot or upload an existing recording. The original audio is kept as it was.' },
  { icon: 'fileAudio', title: 'Write it down', text: 'A speech-to-text draft appears next to the recording. It is a draft, not the truth.' },
  { icon: 'edit', title: 'Correct and confirm', text: 'The storyteller fixes the words and decides when the text is right.' },
  { icon: 'heart', title: 'Keep it for the family', text: 'The approved story, its recording and its translations stay together.' },
]

export function LandingPage() {
  return (
    <div className="landing">
      <header className="landing__nav">
        <Wordmark />
        <nav aria-label="Main" className="row">
          <Link to="/dashboard" className="link">
            Your stories
          </Link>
        </nav>
      </header>

      <section className="hero">
        <div className="hero__copy">
          <p className="eyebrow">A family archive for voices and languages</p>
          <h1 className="hero__title">Keep the story. Keep the language.</h1>
          <p className="hero__lead">
            Roots helps you record an older relative telling a story in their own language, keep the
            original voice safe, and turn it into text they can read, correct and approve themselves.
          </p>
          <div className="row row--wrap">
            <ButtonLink to="/stories/new" size="lg" iconRight="arrowRight">
              Preserve a Story
            </ButtonLink>
            <ButtonLink to="/dashboard" size="lg" variant="secondary">
              Explore Stories
            </ButtonLink>
          </div>
        </div>
        <div className="hero__art" aria-hidden="true">
          <svg viewBox="0 0 420 420" role="presentation">
            <defs>
              <linearGradient id="heroBg" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor="#E8DDBF" />
                <stop offset="1" stopColor="#A8B9A0" />
              </linearGradient>
            </defs>
            <rect width="420" height="420" rx="36" fill="url(#heroBg)" />
            <g fill="none" stroke="#183D32" strokeOpacity="0.25">
              {[40, 70, 100, 130, 160, 190].map((r) => (
                <circle key={r} cx="210" cy="230" r={r} />
              ))}
            </g>
            <g fill="none" stroke="#183D32" strokeWidth="5" strokeLinecap="round">
              <path d="M210 420 C214 340 196 300 214 240" />
              <path d="M212 340 C250 326 270 300 300 290" />
              <path d="M208 310 C170 300 150 270 120 262" />
              <path d="M214 240 C212 200 236 176 270 168" />
              <path d="M214 240 C214 204 190 180 156 172" />
            </g>
            <circle cx="214" cy="236" r="9" fill="#C6A66B" />
          </svg>
        </div>
      </section>

      <section className="principle">
        <blockquote>
          AI helps preserve the story.
          <br />
          <strong>The storyteller decides what is true.</strong>
        </blockquote>
      </section>

      <section className="process" aria-labelledby="process-title">
        <h2 id="process-title" className="section-title">
          How a story is preserved
        </h2>
        <ol className="process__list">
          {STEPS.map((s, i) => (
            <li key={s.title} className="process__item">
              <span className="process__num">{i + 1}</span>
              <span className="process__icon">
                <Icon name={s.icon} size={22} />
              </span>
              <h3 className="process__title">{s.title}</h3>
              <p className="muted">{s.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <footer className="landing__foot">
        <Wordmark size={18} />
        <p className="muted small">
          Early version. Sign-in is not built yet, so Roots is not ready to hold private family
          recordings in production.
        </p>
      </footer>
    </div>
  )
}
