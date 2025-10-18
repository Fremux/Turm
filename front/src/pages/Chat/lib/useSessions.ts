import { useEffect, useMemo, useState } from 'react'
import { getSessions, type SessionDto } from '../../../api/chat'

export function useSessions(userId?: string | number) {
  const [sessions, setSessions] = useState<SessionDto[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!userId) return
    setLoading(true)
    getSessions(userId)
      .then(({ data }) => setSessions(data ?? []))
      .catch(() => {
        console.warn('не получили сессии')
      })
      .finally(() => setLoading(false))
  }, [userId])

  const data = useMemo(() => ({ sessions, loading }), [sessions, loading])

  return data
}
