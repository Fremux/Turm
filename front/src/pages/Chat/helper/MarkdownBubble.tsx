import * as React from "react";
import { chakra } from "@chakra-ui/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";
import { C } from "./c";

type CodeRendererProps = React.ComponentPropsWithoutRef<"code"> & {
    inline?: boolean;
    node?: unknown;
    className?: string;
    children?: React.ReactNode;
};

const mdComponents = {
    p: (props: React.HTMLAttributes<HTMLParagraphElement>) => (
        <chakra.p color={C.text} mb="8px" {...props} />
    ),

    h3: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
        <chakra.h3 fontWeight="700" mb="8px" {...props} />
    ),

    strong: (props: React.HTMLAttributes<HTMLElement>) => (
        <chakra.strong fontWeight="700" {...props} />
    ),
    em: (props: React.HTMLAttributes<HTMLElement>) => (
        <chakra.em fontStyle="italic" {...props} />
    ),

    ul: (props: React.HTMLAttributes<HTMLUListElement>) => (
        <chakra.ul display="grid" rowGap="6px" pl="18px" mb="8px" {...props} />
    ),
    ol: (props: React.HTMLAttributes<HTMLOListElement>) => (
        <chakra.ol display="grid" rowGap="6px" pl="18px" mb="8px" {...props} />
    ),
    li: (props: React.LiHTMLAttributes<HTMLLIElement>) => (
        <chakra.li color={C.text} {...props} />
    ),

    a: (props: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
        <chakra.a
            color={C.blue}
            textDecoration="underline"
            target="_blank"
            rel="noreferrer"
            {...props}
        />
    ),

    hr: () => <chakra.hr h="1px" bg={C.bubbleBorder} border="0" my="10px" />,

    table: (props: React.TableHTMLAttributes<HTMLTableElement>) => (
        <chakra.table w="full" borderCollapse="collapse" mb="10px" {...props} />
    ),
    th: (props: React.ThHTMLAttributes<HTMLTableCellElement>) => (
        <chakra.th
            fontWeight="700"
            borderBottom={`1px solid ${C.bubbleBorder}`}
            p="6px"
            textAlign="left"
            {...props}
        />
    ),
    td: (props: React.TdHTMLAttributes<HTMLTableCellElement>) => (
        <chakra.td borderBottom={`1px solid ${C.bubbleBorder}`} p="6px" {...props} />
    ),

    code: ({ inline, children, ...rest }: CodeRendererProps) =>
        inline ? (
            <chakra.code
                bg="#F2F4F8"
                borderRadius="6px"
                px="6px"
                py="2px"
                color={C.text}
                {...rest}
            >
                {children}
            </chakra.code>
        ) : (
            <chakra.pre
                bg="#0B1426"
                color="#E6EDF3"
                p="12px"
                borderRadius="10px"
                overflowX="auto"
                mb="10px"
                {...rest}
            >
                <chakra.code>{children}</chakra.code>
            </chakra.pre>
        ),
} satisfies Components;

export function MarkdownBubble({ md }: { md: string }) {
    return (
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
            {md}
        </ReactMarkdown>
    );
}
