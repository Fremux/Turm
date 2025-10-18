import { Box, Heading, Flex, Card } from "@chakra-ui/react";
import { DataTable } from "./components/DataTable";
import { UsersToolbar } from "./components/UsersToolbar";
import { UsersFilters } from "./components/UsersFilters";
import { useGetUsers } from "./lib/useGetUsers";
import { useState } from "react";
import { CreateUserModal } from "./components/CreateUserModal";

export default function UsersPage() {
  const { clients } = useGetUsers();
  const [open, setOpen] = useState(false);

  return (
    <Flex h="100%" w="100%" direction="column" p="30px" gap="18px">
      <Heading size="2xl">Выберите пользователя, чтобы войти</Heading>

      <UsersToolbar onCreate={() => setOpen(true)} />

      <UsersFilters onChange={() => { }} />

      <Card.Root border="none" boxShadow="none" bg="white" borderRadius="2xl">
        <Card.Body p={0}>
          <Box>
            <DataTable data={clients ?? []} />
          </Box>
        </Card.Body>
      </Card.Root>

      <CreateUserModal
        open={open}
        onClose={() => setOpen(false)}
        onSubmit={(payload) => {
          console.log("create user:", payload);
        }}
      />
    </Flex>
  );
}
