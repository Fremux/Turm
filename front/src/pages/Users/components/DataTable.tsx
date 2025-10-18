import { Badge, Box, Text, Table } from "@chakra-ui/react";
import {
    flexRender,
    getCoreRowModel,
    getSortedRowModel,
    useReactTable,
    createColumnHelper,
} from "@tanstack/react-table";
import type { ColumnDef, SortingState } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

type AnyRow = Record<string, unknown>;

function toTitle(key: string) {
    return key
        .replace(/_/g, " ")
        .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
        .replace(/\s+/g, " ")
        .trim()
        .replace(/^./, (c) => c.toUpperCase());
}

function stringifyValue(v: unknown) {
    if (v === null || v === undefined) return "";
    if (typeof v === "object") return JSON.stringify(v);
    return String(v);
}

export function DataTable({ data }: { data: AnyRow[] }) {
    const [sorting, setSorting] = useState<SortingState>([]);
    const navigate = useNavigate();

    const columns: ColumnDef<AnyRow, unknown>[] = useMemo(() => {
        if (!data?.length) return [];
        const keys = Object.keys(data[0]);
        const helper = createColumnHelper<AnyRow>();

        return keys.map((key) =>
            helper.accessor((row) => row[key], {
                id: key,
                header: toTitle(key),
                cell: (ctx) => {
                    const value = ctx.getValue();
                    const isBadge =
                        typeof value === "string" &&
                        /team|команда|lab|tag|label/i.test(ctx.column.id);
                    if (isBadge) {
                        return (
                            <Badge borderRadius="full" px="3" py="1" variant="subtle" colorPalette="violet">
                                {value}
                            </Badge>
                        );
                    }

                    const headerId = ctx.column.id || "";
                    const isFio =
                        /fio|name|фио/i.test(headerId) || /full.?name/i.test(headerId);

                    return <Text fontWeight={isFio ? "semibold" : "normal"}>{stringifyValue(value)}</Text>;
                },
            })
        );
    }, [data]);

    const table = useReactTable({
        data: data ?? [],
        columns,
        state: { sorting },
        onSortingChange: setSorting,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
    });

    if (!data?.length) {
        return (
            <Box p={8}>
                <Text color="grey.500">Нет данных</Text>
            </Box>
        );
    }

    const colCount = table.getAllColumns().length;

    return (
        <Table.Root
            size="lg"
            w="100%"
            border="none"
            boxShadow="none"
            bg="transparent"
        >
            {/* Шапка: без фона/бордеров */}
            <Table.Header bg="transparent">
                {table.getHeaderGroups().map((hg) => (
                    <Table.Row key={hg.id}>
                        {hg.headers.map((header) => (
                            <Table.ColumnHeader
                                key={header.id}
                                cursor="default"
                                userSelect="none"
                                fontWeight="semibold"
                                color="grey.600"
                                py="4"
                            >
                                {flexRender(header.column.columnDef.header, header.getContext())}
                            </Table.ColumnHeader>
                        ))}
                    </Table.Row>
                ))}
                {/* разделитель под шапкой */}
                <Table.Row>
                    <Table.ColumnHeader colSpan={colCount} p="0">
                        <Box h="1px" bg="grey.200" mx="2" />
                    </Table.ColumnHeader>
                </Table.Row>
            </Table.Header>

            <Table.Body bg="transparent">
                {table.getRowModel().rows.map((row) => {
                    // безопасно достаём id
                    const rid =
                        (row.original as AnyRow)?.id ??
                        (row.getAllCells().find((c) => c.column.id === "id")?.getValue() as unknown);

                    return (
                        <Box as={Table.Row}
                            key={row.id}
                            // кликабельная строка
                            onClick={() => (rid != null ? navigate(`/chat/${rid}`) : null)}
                            cursor={rid != null ? "pointer" : "default"}
                            _hover={{ bg: "transparent" }}
                            border="none"
                        >
                            {row.getVisibleCells().map((cell) => (
                                <Table.Cell key={cell.id} py="5" border="none">
                                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                </Table.Cell>
                            ))}
                            {/* разделитель строки */}
                            <Table.Cell colSpan={colCount} p="0" border="none">
                                <Box h="1px" bg="grey.200" mx="2" />
                            </Table.Cell>
                        </Box>
                    );
                })}
            </Table.Body>
        </Table.Root>
    );
}
