import axios from "axios";


export function getUsers() {
  return axios.get('/api/v1/auth/users')
}