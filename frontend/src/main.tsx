import React from "react";
import ReactDOM from "react-dom/client";
import { Theme } from "@radix-ui/themes";
import "@radix-ui/themes/styles.css";
import App from "./App";
import "./styles.css";

/** Statt weißem Fenster: Fehlertext sichtbar (enrich-Lehre — im
    WKWebView gibt es keinen Inspector). */
class Fehlerfang extends React.Component<
  { children: React.ReactNode }, { fehler: string | null }> {
  state = { fehler: null as string | null };
  static getDerivedStateFromError(e: unknown) {
    return { fehler: e instanceof Error
      ? `${e.message}\n${e.stack ?? ""}` : String(e) };
  }
  render() {
    if (this.state.fehler) {
      return <pre style={{ padding: 24, whiteSpace: "pre-wrap",
                           fontSize: 12 }}>{this.state.fehler}</pre>;
    }
    return this.props.children;
  }
}

/** Hell/Dunkel folgt dem System (wie PrepareMedia: prefers-color-scheme),
    live beim Umschalten. Radix bekommt `appearance`, das <html> die
    Klasse `dark`, damit auch body/Scrollleisten (ausserhalb des
    Theme-Elements) die Dunkelpalette nehmen. */
function ThemeWurzel({ children }: { children: React.ReactNode }) {
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  const [dunkel, setDunkel] = React.useState(mq.matches);
  React.useEffect(() => {
    const h = (e: MediaQueryListEvent) => setDunkel(e.matches);
    mq.addEventListener("change", h);
    return () => mq.removeEventListener("change", h);
  }, [mq]);
  React.useEffect(() => {
    document.documentElement.classList.toggle("dark", dunkel);
    document.documentElement.style.colorScheme = dunkel ? "dark" : "light";
  }, [dunkel]);
  return (
    <Theme accentColor="indigo" grayColor="slate" radius="medium"
           appearance={dunkel ? "dark" : "light"}
           style={{ minHeight: "100vh" }}>
      {children}
    </Theme>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeWurzel>
      <Fehlerfang><App /></Fehlerfang>
    </ThemeWurzel>
  </React.StrictMode>,
);
