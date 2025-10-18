import {
    Dialog,
    Portal,
    DialogBackdrop as Backdrop,
    DialogContent as Content,
    DialogTitle as Title,
    DialogCloseTrigger as CloseTrigger,
    Button,
    Input,
    HStack,
    Stack,
    IconButton,
} from "@chakra-ui/react";
import { X } from "lucide-react";
import { useState, type ChangeEvent } from "react";

type Props = {
    open: boolean;
    onClose: () => void;
    onSubmit?: (payload: Record<string, string>) => void;
};

export function CreateUserModal({ open, onClose, onSubmit }: Props) {
    const [form, setForm] = useState({ fullName: "", username: "" });

    const handle = (k: keyof typeof form) => (e: ChangeEvent<HTMLInputElement>) =>
        setForm((s) => ({ ...s, [k]: e.target.value }));

    const submit = () => {
        onSubmit?.(form);
        onClose();
    };

    return (
        <Dialog.Root open={open} onOpenChange={(e) => !e.open && onClose()}>
            <Portal>
                <Backdrop />
                <Dialog.Positioner>
                    <Content
                        bg="white"
                        borderRadius="2xl"
                        shadow="none"           // без тени
                        border="none"           // без бордера
                        p="6"
                        w="full"
                        maxW="520px"
                    >
                        <HStack justify="space-between" mb="4">
                            <Title fontSize="xl" fontWeight="semibold">Создать пользователя</Title>
                            <CloseTrigger asChild>
                                <IconButton aria-label="Закрыть" variant="ghost" borderRadius="full">
                                    <X />
                                </IconButton>
                            </CloseTrigger>
                        </HStack>

                        <Stack gap="3">
                            <Input
                                placeholder="ФИО"
                                value={form.fullName}
                                onChange={handle("fullName")}
                                bg="white" border="1px solid" borderColor="grey.200" borderRadius="lg"
                            />
                            <Input
                                placeholder="Username"
                                value={form.username}
                                onChange={handle("username")}
                                bg="white" border="1px solid" borderColor="grey.200" borderRadius="lg"
                            />
                        </Stack>

                        <HStack justify="flex-end" gap="3" mt="6">
                            <Button variant="ghost" onClick={onClose}>Отмена</Button>
                            <Button colorPalette="blue" onClick={submit}>Создать</Button>
                        </HStack>
                    </Content>
                </Dialog.Positioner>
            </Portal>
        </Dialog.Root>
    );
}
