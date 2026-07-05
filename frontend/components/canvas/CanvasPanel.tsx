"use client";

import StarterKit from "@tiptap/starter-kit";
import { EditorContent, useEditor } from "@tiptap/react";
import { useEffect } from "react";

import { useStore } from "@/lib/store";

/**
 * Tiptap editor bound to the shared-state document key. Agent edits arrive as
 * STATE_SNAPSHOT and STATE_DELTA through the store and are applied here live,
 * and the editor stays user-editable during a run.
 */
export function CanvasPanel() {
  const doc = useStore((s) => s.doc);

  const editor = useEditor({
    extensions: [StarterKit],
    content: doc.content,
    immediatelyRender: false,
  });

  useEffect(() => {
    if (!editor) return;
    if (editor.getText() !== doc.content) {
      editor.commands.setContent(doc.content, false);
    }
  }, [editor, doc.content]);

  return (
    <div className="canvas-panel">
      <div className="canvas-header">
        <input value={doc.title} readOnly aria-label="Document title" />
      </div>
      <div className="canvas-body">
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}
