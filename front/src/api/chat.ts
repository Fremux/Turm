import axios from 'axios'

export type SessionDto = { session_id: string; name: string }

export function getSessions(user_id: string | number) {
  return axios.get<SessionDto[]>('/api/v1/auth/sessions', {
    params: { user_id },
  })
}

export function postChatStream(opts: {
  session_id: string
  user_id: string | number
  use_react_agent?: boolean
  content: string
}) {
  const { session_id, user_id, use_react_agent = true, content } = opts

  const url =
    `/api/v1/chatbot/chat/stream` +
    `?session_id=${encodeURIComponent(session_id)}` +
    `&user_id=${encodeURIComponent(String(user_id))}` +
    `&use_react_agent=${use_react_agent ? 'true' : 'false'}`

  return fetch(url, {
    method: 'POST',
    headers: {
      accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages: [{ role: 'user', content }],
    }),
  })
}
