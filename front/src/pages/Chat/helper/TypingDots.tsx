import { Flex } from "@chakra-ui/react"
import { C } from "./c"

export function TypingDots() {
  return (
    <Flex gap="6px" align="center">
      {Array.from({ length: 3 }).map((_, i) => (
        <Flex
          key={i}
          w="8px"
          h="8px"
          borderRadius="full"
          bg={C.sub}
          // sx={{
          //   animation: 'typing 1.4s infinite ease-in-out',
          //   animationDelay: `${i * 0.15}s`,
          //   '@keyframes typing': {
          //     '0%, 80%, 100%': { opacity: 0.2, transform: 'translateY(0)' },
          //     '40%': { opacity: 1, transform: 'translateY(-3px)' },
          //   },
          // }}
        />
      ))}
    </Flex>
  )
}
