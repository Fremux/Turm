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
                    const isFio = /fio|name|фио/i.test(headerId) || /full.?name/i.test(headerId);
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

    const rows = table.getRowModel().rows;

    return (
        <Box bg="white" borderRadius="2xl" overflow="hidden" h='70vh'>
            <Table.Root size="lg" w="100%" border="none" boxShadow="none" bg="transparent" tableLayout="fixed">
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
                                    borderBottomWidth="3px"
                                    borderColor="#D7D5E9"
                                >
                                    {flexRender(header.column.columnDef.header, header.getContext())}
                                </Table.ColumnHeader>
                            ))}
                        </Table.Row>
                    ))}
                </Table.Header>

                <Table.Body bg="transparent">
                    {rows.map((row, idx) => {
                        const last = idx === rows.length - 1;
                        const rid =
                            (row.original as AnyRow)?.id ??
                            (row.getAllCells().find((c) => c.column.id === "id")?.getValue() as unknown);

                        return (
                            <Table.Row
                                key={row.id}
                                onClick={() => (rid != null ? navigate(`/chat/${rid}`) : undefined)}
                                cursor={rid != null ? "pointer" : "default"}
                                _hover={{ bg: "#F5F4FC" }}
                                borderBottomWidth={last ? "0px" : "1px"}
                                borderColor="grey.200"
                            >
                                {row.getVisibleCells().map((cell) => (
                                    <Table.Cell key={cell.id} py="5" border="none">
                                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                    </Table.Cell>
                                ))}
                            </Table.Row>
                        );
                    })}
                </Table.Body>
            </Table.Root>
        </Box>
    );
}
