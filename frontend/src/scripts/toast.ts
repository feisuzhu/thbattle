import { reactive } from "vue";

export type Message = string | {
  title?: string
  content: string
  subTitle?: string
}

export const errors = reactive<Message[]>([])
export const warnings = reactive<Message[]>([])
export const infos = reactive<Message[]>([])

export const error = (m: Message) => errors.push(m)

export const warn = (m: Message) => warnings.push(m)

export const info = (m: Message) => infos.push(m)


export default {
  error,
  warn,
  info
}
