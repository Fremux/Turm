import { useEffect, useMemo, useState } from "react"
import { getUsers } from "../../../api/users"


export const useGetUsers = () => {
  const [clients, setClients] = useState([])

  useEffect(() => {
    getUsers()
      .then(({ data }) => {
        setClients(data.users)
      })
      .catch(() => {
        console.warn('не получили пользователей')
      })
  }, [])

  const data = useMemo(() => {
    return { clients }
  }, [clients])

  return data
}