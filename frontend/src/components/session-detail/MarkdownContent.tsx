import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import type { Components } from "react-markdown";

const components: Components = {
  // Code blocks
  pre({ children }) {
    return (
      <pre className="overflow-x-auto rounded border border-outline-variant/20 bg-surface-container-lowest p-3 font-mono text-sm leading-relaxed">
        {children}
      </pre>
    );
  },
  code({ className, children, ...props }) {
    const isBlock = className?.startsWith("hljs") || className?.startsWith("language-");
    if (isBlock) {
      return (
        <code className={`${className ?? ""} text-sm`} {...props}>
          {children}
        </code>
      );
    }
    // Inline code
    return (
      <code
        className="rounded border border-outline-variant/20 bg-surface-container-lowest px-1.5 py-0.5 font-mono text-sm text-primary-dim"
        {...props}
      >
        {children}
      </code>
    );
  },
  // Block elements
  p({ children }) {
    return <p className="text-md leading-relaxed text-on-surface">{children}</p>;
  },
  h1({ children }) {
    return <h1 className="text-lg font-bold text-on-surface">{children}</h1>;
  },
  h2({ children }) {
    return <h2 className="text-md font-bold text-on-surface">{children}</h2>;
  },
  h3({ children }) {
    return <h3 className="text-md font-semibold text-on-surface">{children}</h3>;
  },
  // Lists
  ul({ children }) {
    return <ul className="list-disc space-y-1 pl-5 text-md text-on-surface">{children}</ul>;
  },
  ol({ children }) {
    return <ol className="list-decimal space-y-1 pl-5 text-md text-on-surface">{children}</ol>;
  },
  li({ children }) {
    return <li className="leading-relaxed">{children}</li>;
  },
  // Blockquote
  blockquote({ children }) {
    return (
      <blockquote className="border-l-2 border-primary/40 pl-4 text-on-surface-variant italic">
        {children}
      </blockquote>
    );
  },
  // Table
  table({ children }) {
    return (
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">{children}</table>
      </div>
    );
  },
  th({ children }) {
    return (
      <th className="border border-outline-variant/20 bg-surface-container-highest px-3 py-1.5 text-left font-mono text-xs font-semibold text-on-surface-variant">
        {children}
      </th>
    );
  },
  td({ children }) {
    return (
      <td className="border border-outline-variant/20 px-3 py-1.5 text-on-surface">
        {children}
      </td>
    );
  },
  // Links
  a({ href, children }) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-primary underline decoration-primary/30 underline-offset-2 hover:decoration-primary"
      >
        {children}
      </a>
    );
  },
  // Horizontal rule
  hr() {
    return <hr className="border-outline-variant/20" />;
  },
  // Strong / em
  strong({ children }) {
    return <strong className="font-semibold text-on-surface">{children}</strong>;
  },
};

interface Props {
  content: string;
}

export const MarkdownContent = memo(function MarkdownContent({ content }: Props) {
  return (
    <div className="space-y-3">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
});
