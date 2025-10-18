import { useEffect, useMemo, useRef, useState } from 'react'
import { postChatStream, type SessionDto } from '../../../api/chat'

export type ChatMsg = {
  id: string
  role: 'user' | 'assistant'
  content: string
  ts: number
}

export function useChat(userId?: string | number, session?: SessionDto | null) {
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const streamAbort = useRef<AbortController | null>(null)

  useEffect(() => {
    return () => {
      streamAbort.current?.abort()
    }
  }, [userId, session?.session_id])

  const send = (text: string) => {
    console.log(text)
    if (!userId || !session || !text.trim() || isStreaming) return
    console.log(text)
    // добавляем своё сообщение + пустой ассистент
    const userMsg: ChatMsg = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      ts: Date.now(),
    }
    const assistantId = crypto.randomUUID()
    const assistantMsg: ChatMsg = {
      id: assistantId,
      role: 'assistant',
      content: '',
      ts: Date.now(),
    }
    setMessages((m) => [...m, userMsg, assistantMsg])

    setIsStreaming(true)
    const ctrl = new AbortController()
    streamAbort.current = ctrl

    postChatStream({
      session_id: session.session_id,
      user_id: userId,
      content: text,
    })
      .then(async (res) => {
        const reader = res.body?.getReader()
        if (!reader) return

        const dec = new TextDecoder()
        let buffer = ''
        let done = false
        while (!done) {
          const chunk = await reader.read()
          if (chunk.done) break
          buffer += dec.decode(chunk.value, { stream: true })

          const lines = buffer.split('\n')
          // последняя строка может быть неполной – оставим её в буфере
          buffer = lines.pop() ?? ''

          lines.forEach((line) => {
            const idx = line.indexOf('data:')
            if (idx === -1) return
            const json = line.slice(idx + 5).trim()
            if (!json) return

            const obj = JSON.parse(json) as { content?: string; done?: boolean }
            if (obj.done) {
              done = true
              return
            }
            if (typeof obj.content === 'string' && obj.content.length) {
              setMessages((m) =>
                m.map((msg) =>
                  msg.id === assistantId
                    ? { ...msg, content: msg.content + obj.content }
                    : msg
                )
              )
            }
          })
        }
      })
      .catch(() => {
        // опционально можно добавить системное сообщение об ошибке
        console.warn('стрим чата не получен')
      })
      .finally(() => {
        setIsStreaming(false)
        streamAbort.current = null
      })
  }

  const api = useMemo(
    () => ({ messages, send, isStreaming }),
    [messages, isStreaming]
  )

  return api
}
