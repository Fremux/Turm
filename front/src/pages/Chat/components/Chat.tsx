import { useParams } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { Flex, Text, Input, Button, Icon } from "@chakra-ui/react";
import { Send } from "lucide-react";
import { useSessions } from "../lib/useSessions";
import { useChat } from "../lib/useChat";
import { C } from "../helper/c";
import { MarkdownBubble } from "../helper/MarkdownBubble";
import { TypingDots } from "../helper/TypingDots";




export function ChatUI() {
    const { id } = useParams<{ id: string }>();
    const userId = id ? Number(id) : undefined;

    const { sessions } = useSessions(userId);
    const session = sessions[0] ?? null;
    const { messages, send, isStreaming } = useChat(userId, session);

    const [val, setVal] = useState("");
    const inputRef = useRef<HTMLInputElement>(null);
    const endRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages.length, isStreaming]);

    const submit = () => {
        const v = val.trim();
        if (!v || !session) return;
        send(v);
        setVal("");
        inputRef.current?.focus();
    };
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    //@ts-expect-error
    const onKey = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault?.();
            submit();
        }
    };

    return (
        <Flex h="90vh" w="100%" p="24px" zIndex={1}>
            {/* белый контейнер чата */}
            <Flex direction="column" flex="1" minW={0} bg={C.white} borderRadius="24px" p="20px">
                {/* Лента сообщений — узкая колонка по центру, скролл внутри */}
                <Flex direction="column" align="center" flex="1" minH="0">
                    <Flex
                        direction="column"
                        gap="20px"
                        w="100%"
                        flex="1"
                        overflowY="auto"
                        pr="4px"
                        pb="16px"
                    >
                        {messages.map((m) => {
                            const isUser = m.role === "user";
                            return (
                                <Flex
                                    key={m.id}
                                    direction="column"
                                    align={isUser ? "flex-end" : "flex-start"}
                                    gap="6px"
                                    w="100%"
                                >
                                    <Flex
                                        maxW="75%"
                                        bg={C.bubble}
                                        border={`1px solid ${C.bubbleBorder}`}
                                        borderRadius="16px"
                                        px="16px"
                                        py="12px"
                                        alignSelf={isUser ? "flex-end" : "flex-start"}
                                        direction='column'
                                    >
                                        {isUser ? (
                                            <Text color={C.text} whiteSpace="pre-wrap">{m.content}</Text>
                                        ) : m.content ? (
                                            <MarkdownBubble md={m.content} />
                                        ) : isStreaming ? (
                                            <TypingDots />
                                        ) : null}
                                    </Flex>
                                    <Text fontSize="12px" color={C.time} pr={isUser ? "6px" : 0}>
                                        {new Date(m.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                                    </Text>
                                </Flex>
                            );
                        })}
                        <div ref={endRef} />
                    </Flex>

                    {/* Composer — как на макете: тонкая рамка, синяя кнопка c иконкой */}
                    <Flex direction="row" w="100%" gap="12px" pt="8px">
                        <Input
                            ref={inputRef}
                            placeholder="Напишите сообщение…"
                            value={val}
                            onChange={(e) => setVal(e.target.value)}
                            onKeyDown={onKey}
                            bg={C.white}
                            borderRadius="14px"
                            border={`1px solid ${C.inputBorder}`}
                            h="56px"
                            px="16px"
                            color={C.text}
                            _placeholder={{ color: C.sub }}
                            _hover={{ borderColor: C.inputBorder }}
                            _focusVisible={{ outline: "none", borderColor: C.blue }}
                            flex="1"
                            disabled={!session}
                        />
                        <Button
                            onClick={submit}
                            h="56px"
                            px="18px"
                            minW="56px"
                            borderRadius="14px"
                            bg={C.blue}
                            _hover={{ bg: C.blueHover }}
                            _active={{ bg: C.blueHover }}
                            color={C.white}
                            disabled={!session || isStreaming}
                            aria-label="Отправить"
                        >
                            <Icon as={Send} />
                        </Button>
                    </Flex>
                </Flex>
            </Flex>
        </Flex>
    );
}
