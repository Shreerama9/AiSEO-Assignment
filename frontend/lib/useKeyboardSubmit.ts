"use client";

import { useEffect } from "react";

/**
 * Calls `onSubmit` when Cmd+Enter (Mac) or Ctrl+Enter (Win/Linux) is pressed.
 * Only fires when `enabled` is true.
 */
export function useKeyboardSubmit(onSubmit: () => void, enabled: boolean) {
  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && enabled) {
        e.preventDefault();
        onSubmit();
      }
    }
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onSubmit, enabled]);
}
