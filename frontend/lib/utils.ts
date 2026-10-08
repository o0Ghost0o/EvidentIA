import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

const customTwMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      "font-size": [
        "text-display-xl",
        "text-display-lg",
        "text-heading-md",
        "text-label",
        "text-body-md",
        "text-body-sm",
        "text-mono",
        "text-caption",
      ],
      "text-color": [
        "text-on-primary",
        "text-ink",
        "text-ink-muted",
        "text-hairline",
        "text-canvas",
        "text-surface",
        "text-surface-sunken",
        "text-primary",
        "text-primary-deep",
        "text-primary-soft",
        "text-accent",
        "text-success",
        "text-warning",
        "text-error",
        "text-info",
      ],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return customTwMerge(clsx(inputs));
}
