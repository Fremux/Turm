import { Flex } from "@chakra-ui/react";
import { ChatUI } from "./components/Chat";


export default function ChatPage() {

  return (
    <Flex w='100vw' h='100vh' alignItems='center' >
      <ChatUI />
    </Flex>
  )
}
