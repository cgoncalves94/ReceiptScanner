/**
 * Format a date string to relative time (e.g., "2 hours ago")
 */
export function formatDistanceToNow(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return "just now";
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`;
  }

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours}h ago`;
  }

  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) {
    return `${diffInDays}d ago`;
  }

  // Format as date for older items
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

// ISO code to symbol mapping
const ISO_TO_SYMBOL: Record<string, string> = {
  EUR: "€",
  GBP: "£",
  USD: "$",
  JPY: "¥",
  CHF: "CHF",
  AUD: "A$",
  CAD: "C$",
};

/**
 * Format currency with symbol.
 * Converts ISO codes (EUR, GBP, USD) to symbols (€, £, $) for display.
 */
export function formatCurrency(amount: number, currency: string = "EUR"): string {
  const symbol = ISO_TO_SYMBOL[currency.toUpperCase()] || currency;
  return `${symbol}${amount.toFixed(2)}`;
}

/**
 * Format date for display
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}
