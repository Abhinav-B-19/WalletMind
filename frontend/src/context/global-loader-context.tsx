import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { PropsWithChildren } from "react";
import { LoaderCircle } from "lucide-react";

type GlobalLoaderContextValue = {
  showLoader: (message?: string) => void;
  hideLoader: () => void;
};

const DEFAULT_MESSAGE = "Loading WalletMind workspace...";
const MIN_VISIBLE_MS = 320;

const GlobalLoaderContext = createContext<GlobalLoaderContextValue | undefined>(
  undefined,
);

export function GlobalLoaderProvider({ children }: PropsWithChildren) {
  const [isVisible, setIsVisible] = useState(false);
  const [message, setMessage] = useState(DEFAULT_MESSAGE);
  const shownAtRef = useRef<number | null>(null);
  const hideTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (hideTimeoutRef.current !== null) {
        window.clearTimeout(hideTimeoutRef.current);
      }
    };
  }, []);

  const showLoader = useCallback((nextMessage?: string) => {
    if (hideTimeoutRef.current !== null) {
      window.clearTimeout(hideTimeoutRef.current);
      hideTimeoutRef.current = null;
    }

    setMessage(nextMessage ?? DEFAULT_MESSAGE);
    shownAtRef.current = Date.now();
    setIsVisible(true);
  }, []);

  const hideLoader = useCallback(() => {
    const shownAt = shownAtRef.current;
    const elapsed = shownAt ? Date.now() - shownAt : MIN_VISIBLE_MS;
    const remaining = Math.max(0, MIN_VISIBLE_MS - elapsed);

    if (hideTimeoutRef.current !== null) {
      window.clearTimeout(hideTimeoutRef.current);
    }

    hideTimeoutRef.current = window.setTimeout(() => {
      setIsVisible(false);
      setMessage(DEFAULT_MESSAGE);
      shownAtRef.current = null;
      hideTimeoutRef.current = null;
    }, remaining);
  }, []);

  const contextValue = useMemo(
    () => ({ showLoader, hideLoader }),
    [hideLoader, showLoader],
  );

  return (
    <GlobalLoaderContext.Provider value={contextValue}>
      {children}
      <div
        aria-hidden={!isVisible}
        className={`fixed inset-0 z-[120] grid place-items-center bg-[rgba(5,10,20,0.62)] px-4 backdrop-blur-sm transition-opacity duration-[var(--duration-normal)] ${
          isVisible
            ? "pointer-events-auto opacity-100"
            : "pointer-events-none opacity-0"
        }`}
      >
        <section
          role="status"
          aria-live="polite"
          className="w-full max-w-sm rounded-[var(--radius-lg)] border border-[var(--border)] bg-[color:rgba(18,31,52,0.96)] p-6 text-center shadow-[var(--shadow-md)]"
        >
          <div className="mx-auto grid h-11 w-11 place-items-center rounded-xl bg-[var(--primary)] text-sm font-bold text-[var(--bg)] shadow-[var(--shadow-sm)]">
            WM
          </div>
          <h2 className="mt-4 text-base font-semibold tracking-tight text-[var(--text)]">
            WalletMind
          </h2>
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            AI Financial Concierge
          </p>
          <div className="mt-4 inline-flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2 text-sm text-[var(--text-muted)]">
            <LoaderCircle className="h-[var(--icon-md)] w-[var(--icon-md)] animate-spin text-[var(--primary)]" />
            <span>{message}</span>
          </div>
        </section>
      </div>
    </GlobalLoaderContext.Provider>
  );
}

export function useGlobalLoader(): GlobalLoaderContextValue {
  const context = useContext(GlobalLoaderContext);
  if (!context) {
    throw new Error(
      "useGlobalLoader must be used within a GlobalLoaderProvider",
    );
  }
  return context;
}
