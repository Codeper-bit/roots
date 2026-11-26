import { AppLayout } from './components/layout/AppLayout'
import { ToastProvider } from './components/ui/Toast'
import { Routes, usePathname, type RouteDef } from './lib/router'
import { ConsentPage } from './pages/ConsentPage'
import { CreateStoryPage } from './pages/CreateStoryPage'
import { DashboardPage } from './pages/DashboardPage'
import { LandingPage } from './pages/LandingPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { ParticipantPage } from './pages/ParticipantPage'
import { RecordingPage } from './pages/RecordingPage'
import { ReviewPage } from './pages/ReviewPage'
import { ReviewsPage } from './pages/ReviewsPage'
import { StoryDetailPage } from './pages/StoryDetailPage'
import { StoryQuestionsPage } from './pages/StoryQuestionsPage'
import { TranscriptionPage } from './pages/TranscriptionPage'

// Static paths must come before /stories/:storyId.
const APP_ROUTES: RouteDef[] = [
  { path: '/dashboard', element: <DashboardPage /> },
  { path: '/stories/new', element: <CreateStoryPage /> },
  { path: '/stories/:storyId', element: <StoryDetailPage /> },
  { path: '/stories/:storyId/participant', element: <ParticipantPage /> },
  { path: '/stories/:storyId/consent', element: <ConsentPage /> },
  { path: '/stories/:storyId/record', element: <RecordingPage /> },
  { path: '/stories/:storyId/transcribe', element: <TranscriptionPage /> },
  { path: '/stories/:storyId/review', element: <ReviewPage /> },
  { path: '/stories/:storyId/questions', element: <StoryQuestionsPage /> },
  { path: '/reviews', element: <ReviewsPage /> },
]

export function App() {
  const pathname = usePathname()
  return (
    <ToastProvider>
      {pathname === '/' ? (
        <LandingPage />
      ) : (
        <AppLayout>
          <Routes routes={APP_ROUTES} fallback={<NotFoundPage />} />
        </AppLayout>
      )}
    </ToastProvider>
  )
}
