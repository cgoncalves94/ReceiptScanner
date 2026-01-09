"use client";

import { useQuery } from "@tanstack/react-query";

// Currency symbols to ISO codes mapping
const CURRENCY_MAP: Record<string, string> = {
  "€": "EUR",
  "£": "GBP",
  "$": "USD",
  "¥": "JPY",
  "CHF": "CHF",
  "A$": "AUD",
  "C$": "CAD",
};

// Reverse mapping
const ISO_TO_SYMBOL: Record<string, string> = {
  EUR: "€",
  GBP: "£",
  USD: "$",
  JPY: "¥",
  CHF: "CHF",
  AUD: "A$",
  CAD: "C$",
};

export const SUPPORTED_CURRENCIES = [
  { code: "EUR", symbol: "€", name: "Euro" },
  { code: "GBP", symbol: "£", name: "British Pound" },
  { code: "USD", symbol: "$", name: "US Dollar" },
];

// Convert currency symbol to ISO code
export function symbolToCode(symbol: string): string {
  return CURRENCY_MAP[symbol] || symbol;
}

// Convert ISO code to symbol
export function codeToSymbol(code: string): string {
  return ISO_TO_SYMBOL[code] || code;
}

interface ExchangeRates {
  base: string;
  rates: Record<string, number>;
  date: string;
}

// Fetch exchange rates from Frankfurter API (free, no API key)
async function fetchExchangeRates(baseCurrency: string): Promise<ExchangeRates> {
  const response = await fetch(
    `https://api.frankfurter.app/latest?from=${baseCurrency}`
  );
  if (!response.ok) {
    throw new Error("Failed to fetch exchange rates");
  }
  return response.json();
}

// Hook to get exchange rates for a base currency
export function useExchangeRates(baseCurrency: string) {
  return useQuery({
    queryKey: ["exchangeRates", baseCurrency],
    queryFn: () => fetchExchangeRates(baseCurrency),
    staleTime: 1000 * 60 * 60, // Cache for 1 hour
    gcTime: 1000 * 60 * 60 * 24, // Keep in cache for 24 hours
  });
}

// Convert amount from one currency to another
export function convertAmount(
  amount: number,
  fromCurrency: string,
  toCurrency: string,
  rates: ExchangeRates | undefined
): number {
  if (!rates) return amount;

  const fromCode = symbolToCode(fromCurrency);
  const toCode = symbolToCode(toCurrency);

  // If same currency, no conversion needed
  if (fromCode === toCode) return amount;

  // If base currency matches target, use rate directly
  if (rates.base === fromCode && rates.rates[toCode]) {
    return amount * rates.rates[toCode];
  }

  // If base currency matches source, divide by rate
  if (rates.base === toCode && rates.rates[fromCode]) {
    return amount / rates.rates[fromCode];
  }

  // Cross-rate conversion (from -> base -> to)
  if (rates.rates[fromCode] && rates.rates[toCode]) {
    const amountInBase = amount / rates.rates[fromCode];
    return amountInBase * rates.rates[toCode];
  }

  return amount;
}

// Convert and sum multiple amounts in different currencies to a target currency
export function convertAndSum(
  items: { amount: number; currency: string }[],
  targetCurrency: string,
  rates: ExchangeRates | undefined
): number {
  return items.reduce((sum, item) => {
    const converted = convertAmount(item.amount, item.currency, targetCurrency, rates);
    return sum + converted;
  }, 0);
}
