import { HStack, Button, Input, Box, Icon, Text } from "@chakra-ui/react";
import { Search, Plus } from "lucide-react";
import { useState, type ChangeEvent } from "react";

type Props = {
    onCreate?: () => void;
    onSearchChange?: (value: string) => void;
};

export function UsersToolbar({ onCreate, onSearchChange }: Props) {
    const [value, setValue] = useState("");

    const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
        const v = e.target.value;
        setValue(v);
        onSearchChange?.(v);
    };

    return (
        <HStack gap={6}>
            <Box position="relative" flex="1">
                <Icon
                    as={Search}
                    aria-hidden
                    boxSize="5"          
                    color="grey.500"
                    position="absolute"
                    left="4"
                    top="50%"
                    transform="translateY(-50%)"
                    pointerEvents="none"
                    zIndex={1}
                />
                <Input
                    placeholder="Поиск по пользователям…"
                    value={value}
                    onChange={handleChange}
                    bg="white"
                    border="none"
                    borderRadius="full"
                    h="12"        
                    pl="50px"        
                    _hover={{ bg: "white" }}
                    _focusVisible={{ outline: "none" }}
                />
            </Box>

            <Button
                onClick={onCreate}
                bg="white"
                color="blue.600"
                border="none"
                borderRadius="full"
                h="12"          // одинаковая высота
                px="5"
                _hover={{ bg: "white", color: "blue.700" }}
                _active={{ bg: "white" }}
            >
                <Icon as={Plus} mr="2" />
                <Text fontWeight="semibold">Создать пользователя</Text>
            </Button>
        </HStack>
    );
}
