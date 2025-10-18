import { HStack, Button, Menu, Portal, Icon, Text } from "@chakra-ui/react";
import { ChevronDown } from "lucide-react";
import { useCallback } from "react";

type Props = { onChange?: (filters: Record<string, string>) => void };
type Option = { value: string; label: string };

function FilterMenu({
    label,
    options,
    onSelectValue,
    flex = 1,
}: {
    label: string;
    options: Option[];
    onSelectValue: (value: string) => void;
    flex?: number;
}) {
    const handleSelect = useCallback(
        (details: { value: string }) => onSelectValue(details.value),
        [onSelectValue]
    );

    return (
        <Menu.Root onSelect={handleSelect}>
            <Menu.Trigger asChild>
                <Button
                    h="12"
                    w="100%"
                    flex={flex}
                    bg="white"
                    color="#373645"
                    border="none"
                    borderRadius="full"
                    px="5"
                    justifyContent="space-between"
                    boxShadow="none"
                    _hover={{ bg: "white", color: "grey.800" }}
                    _active={{ bg: "white", boxShadow: "none" }}
                    _focus={{ outline: "none", boxShadow: "none" }}
                    _focusVisible={{ outline: "none", boxShadow: "none" }}
                >
                    <Text color="#373645">{label}</Text>
                    <Icon as={ChevronDown} aria-hidden color="grey.500" />
                </Button>
            </Menu.Trigger>

            <Portal>
                <Menu.Positioner>
                    <Menu.Content
                        bg="white"
                        border="none"                 // ← без бордера
                        borderRadius="xl"
                        shadow="none"                 // ← без тени
                        minW="var(--reference-width)" // ширина ≈ кнопке
                    >
                        {options.map((o) => (
                            <Menu.Item
                                key={o.value}
                                value={o.value}
                                color="grey.700"
                                _hover={{ bg: "grey.100" }}
                            >
                                {o.label}
                            </Menu.Item>
                        ))}
                    </Menu.Content>
                </Menu.Positioner>
            </Portal>
        </Menu.Root>
    );
}

export function UsersFilters({ onChange }: Props) {
    const setFilter = (key: string) => (value: string) => onChange?.({ [key]: value });

    return (
        <HStack gap={4} w="100%">
            <FilterMenu
                label="Отдел"
                options={[
                    { value: "any", label: "Любой" },
                    { value: "it", label: "ИТ" },
                    { value: "hr", label: "HR" },
                ]}
                onSelectValue={setFilter("department")}
            />
            <FilterMenu
                label="Сектор"
                options={[
                    { value: "any", label: "Любой" },
                    { value: "s1", label: "S1" },
                    { value: "s2", label: "S2" },
                ]}
                onSelectValue={setFilter("sector")}
            />
            <FilterMenu
                label="Команда"
                options={[
                    { value: "any", label: "Любая" },
                    { value: "lab260", label: "lab260" },
                ]}
                onSelectValue={setFilter("team")}
            />
            <FilterMenu
                label="Офис"
                options={[
                    { value: "any", label: "Любой" },
                    { value: "techno", label: "Технополис" },
                ]}
                onSelectValue={setFilter("office")}
            />
        </HStack>
    );
}
