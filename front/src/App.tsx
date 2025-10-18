import { lazy, Suspense } from "react";
import { Box, Center, Spinner, Text } from "@chakra-ui/react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
// import { Layout } from "./shared/ui/Layout";

const Users = lazy(() => import("./pages/Users/Users"));
const Chat = lazy(() => import("./pages/Chat/Chat"));

export default function App() {
  return (
    <BrowserRouter>
      {/* <Layout> */}
        <Suspense
          fallback={
            <Box p={8}>
              <Spinner size="xl" />
            </Box>
          }
        >
          <Routes>
            <Route path="/" element={<Users />} />
            <Route path="/chat/:id" element={<Chat />} />
            <Route
              path="*"
              element={
                <Center>
                  <Text>404 страница</Text>
                </Center>
              }
            />
          </Routes>
        </Suspense>
      {/* </Layout> */}
    </BrowserRouter>
  );
}
