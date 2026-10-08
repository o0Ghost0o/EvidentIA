import type { Config } from "tailwindcss";

// EvidentIA design system — tokens defined in assets/css/tailwind.css, spec in DESIGN.md.
export default <Partial<Config>>{
  darkMode: "class",
  content: [
    "./components/**/*.{vue,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./app.vue",
  ],
  theme: {
    extend: {
      colors: {
        // Structural
        border: "hsl(var(--border))",
        hairline: "hsl(var(--hairline))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        canvas: "hsl(var(--canvas))",
        surface: {
          DEFAULT: "hsl(var(--surface))",
          sunken: "hsl(var(--surface-sunken))",
        },
        // Text
        ink: {
          DEFAULT: "hsl(var(--ink))",
          muted: "hsl(var(--ink-muted))",
        },
        // Brand
        primary: {
          DEFAULT: "hsl(var(--primary))",
          deep: "hsl(var(--primary-deep))",
          soft: "hsl(var(--primary-soft))",
          foreground: "hsl(var(--on-primary))",
        },
        "on-primary": "hsl(var(--on-primary))",
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        // State / semantic
        success: "hsl(var(--success))",
        warning: "hsl(var(--warning))",
        error: "hsl(var(--error))",
        info: "hsl(var(--info))",
        // shadcn-compat aliases
        secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        serif: ["'Source Serif 4'", "Lora", "Georgia", "serif"],
        display: ["'Source Serif 4'", "Lora", "Georgia", "serif"],
        mono: ["'IBM Plex Mono'", "'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      fontSize: {
        // role: [size, { lineHeight, letterSpacing, fontWeight }]
        "display-xl": ["32px", { lineHeight: "1.15", letterSpacing: "-0.4px", fontWeight: "600" }],
        "display-lg": ["24px", { lineHeight: "1.2", letterSpacing: "-0.2px", fontWeight: "600" }],
        "heading-md": ["18px", { lineHeight: "1.3", fontWeight: "600" }],
        label: ["13px", { lineHeight: "1.3", letterSpacing: "0.6px", fontWeight: "600" }],
        "body-md": ["16px", { lineHeight: "1.55", fontWeight: "400" }],
        "body-sm": ["14px", { lineHeight: "1.5", fontWeight: "400" }],
        mono: ["13px", { lineHeight: "1.5", fontWeight: "450" }],
        caption: ["12px", { lineHeight: "1.4", letterSpacing: "0.2px", fontWeight: "500" }],
      },
      borderRadius: {
        sm: "6px",
        md: "8px",
        lg: "12px",
      },
      boxShadow: {
        "ev-1": "0 1px 2px rgba(19,35,58,0.06)",
        "ev-2": "0 4px 12px rgba(19,35,58,0.08)",
        "ev-3": "0 12px 32px rgba(19,35,58,0.14)",
      },
      maxWidth: {
        container: "1120px",
      },
    },
  },
};
