import { Flex } from '@chakra-ui/react'
import type { ReactNode } from 'react'

export const Layout = ({ children }: { children: ReactNode }) => (
    <Flex
        w="100vw"
        h="100vh"
        direction="column"
        justify="center"
        align="center"
        style={{ position: 'relative', overflow: 'hidden' }}
        backgroundColor={'gray.100'}
        zIndex={0}
    >
        <div
            style={{
                position: 'absolute',
                bottom: '-5%',
                right: '-5%',
                width: '252px',
                height: '252px',
                background: '#BCD9FF',
                filter: 'blur(70px)',
                zIndex: 0,
            }}
        />
        {/* <div
      style={{
        position: 'absolute',
        bottom: '+30%',
        right: '+15%',
        width: '252px',
        height: '252px',
        background: '#FFD2ED',
        filter: 'blur(70px)',
        zIndex: -1,
      }}
    /> */}
        {children}
    </Flex>
)