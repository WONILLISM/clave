import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Star } from "lucide-react";

interface SelectionState {
  text: string;
  messageUuid: string | null;
  /** Viewport coordinates (fixed positioning) — top-left anchor of the button */
  x: number;
  y: number;
}

interface Props {
  /** selection 이 이 컨테이너 내부일 때만 toolbar 가 뜸 */
  containerRef: React.RefObject<HTMLElement | null>;
  onSave: (args: { text: string; messageUuid: string | null }) => void;
}

/**
 * 메시지 영역에서 드래그 선택 → 선택 위에 "하이라이트" 플로팅 버튼 표시.
 * 클릭 시 onSave 호출, selection 해제 시 자동 닫힘.
 */
export function HighlightSelectionToolbar({ containerRef, onSave }: Props) {
  const [sel, setSel] = useState<SelectionState | null>(null);
  const suppressRef = useRef(false);

  useEffect(() => {
    function compute() {
      if (suppressRef.current) return;
      const selection = window.getSelection();
      if (!selection || selection.isCollapsed || selection.rangeCount === 0) {
        setSel(null);
        return;
      }
      const range = selection.getRangeAt(0);
      const container = containerRef.current;
      if (!container) {
        setSel(null);
        return;
      }
      // 선택 영역이 컨테이너 내부인지 확인
      const anchor = selection.anchorNode;
      if (!anchor || !container.contains(anchor)) {
        setSel(null);
        return;
      }
      const text = selection.toString().trim();
      if (!text) {
        setSel(null);
        return;
      }
      const rect = range.getBoundingClientRect();
      if (rect.width === 0 && rect.height === 0) {
        setSel(null);
        return;
      }

      // anchor node 기준으로 가장 가까운 message article 의 uuid
      const anchorEl: Element | null =
        anchor.nodeType === Node.ELEMENT_NODE
          ? (anchor as Element)
          : anchor.parentElement;
      const msgEl = anchorEl?.closest<HTMLElement>("[data-message-uuid]");
      const messageUuid = msgEl?.dataset.messageUuid ?? null;

      setSel({
        text,
        messageUuid,
        x: rect.left + rect.width / 2,
        y: rect.top - 8,
      });
    }

    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setSel(null);
        window.getSelection()?.removeAllRanges();
      }
    }

    document.addEventListener("selectionchange", compute);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("selectionchange", compute);
      document.removeEventListener("keydown", onKey);
    };
  }, [containerRef]);

  if (!sel) return null;

  return createPortal(
    <button
      // 선택 영역을 잃지 않게 mousedown 기본동작 차단
      onMouseDown={(e) => {
        e.preventDefault();
      }}
      onClick={() => {
        onSave({ text: sel.text, messageUuid: sel.messageUuid });
        // 저장 직후 선택 해제 + 중복 트리거 방지
        suppressRef.current = true;
        window.getSelection()?.removeAllRanges();
        setSel(null);
        // 다음 tick 에서 해제
        setTimeout(() => {
          suppressRef.current = false;
        }, 50);
      }}
      style={{
        position: "fixed",
        left: `${sel.x}px`,
        top: `${sel.y}px`,
        transform: "translate(-50%, -100%)",
        zIndex: 50,
      }}
      className="flex items-center gap-1.5 rounded-xs border border-outline-variant/40 bg-surface-container-highest px-2.5 py-1 text-xs text-on-surface shadow-lg backdrop-blur-md transition-colors hover:border-primary hover:bg-primary/10 hover:text-primary"
    >
      <Star size={12} />
      하이라이트
    </button>,
    document.body,
  );
}
