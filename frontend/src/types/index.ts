// API Response Types - matching backend schemas

// Payment method enum matching backend
export type PaymentMethod =
  | "cash"
  | "credit_card"
  | "debit_card"
  | "mobile_payment"
  | "other";

export const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  cash: "Cash",
  credit_card: "Credit Card",
  debit_card: "Debit Card",
  mobile_payment: "Mobile Payment",
  other: "Other",
};

export interface Category {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface CategoryCreate {
  name: string;
  description?: string | null;
}

export interface CategoryUpdate {
  name?: string | null;
  description?: string | null;
}

export interface ReceiptItem {
  id: number;
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  currency: string;
  category_id: number | null;
  receipt_id: number;
  total_cost: number;
  created_at: string;
  updated_at: string;
}

export interface ReceiptItemUpdate {
  name?: string | null;
  quantity?: number | null;
  unit_price?: number | null;
  total_price?: number | null;
  currency?: string | null;
  category_id?: number | null;
}

export interface ReceiptItemCreate {
  name: string;
  quantity: number;
  unit_price: number;
  currency: string;
  category_id?: number | null;
}

export interface Receipt {
  id: number;
  store_name: string;
  total_amount: number;
  currency: string;
  purchase_date: string;
  image_path: string;
  created_at: string;
  updated_at: string;
  items: ReceiptItem[];
  // Metadata fields
  notes: string | null;
  tags: string[];
  payment_method: PaymentMethod | null;
  tax_amount: number | null;
}

export interface ReceiptUpdate {
  store_name?: string | null;
  total_amount?: number | null;
  currency?: string | null;
  purchase_date?: string | null;
  // Metadata fields
  notes?: string | null;
  tags?: string[] | null;
  payment_method?: PaymentMethod | null;
  tax_amount?: number | null;
}

// Scan result from AI analysis
export interface ScanResult {
  receipt: Receipt;
  confidence?: number;
}

// API Error response
export interface ApiError {
  detail: string;
}

// Receipt filter parameters for search/filtering
export interface ReceiptFilters {
  search?: string;
  store?: string;
  after?: string; // ISO 8601 date string
  before?: string; // ISO 8601 date string
  category_ids?: number[];
  min_amount?: number;
  max_amount?: number;
}

// PDF export options
export interface PdfExportOptions {
  includeImages: boolean;
}

// Analytics Types - Multi-currency support
// Backend returns amounts grouped by original currency
// Frontend converts to display currency using exchange rates

export interface CurrencyAmount {
  currency: string;
  amount: string; // Decimal serialized as string
}

export interface SpendingSummary {
  totals_by_currency: CurrencyAmount[];
  receipt_count: number;
  top_category: string | null;
  top_category_amounts: CurrencyAmount[] | null;
  year: number;
  month: number | null;
}

export interface SpendingTrend {
  date: string;
  totals_by_currency: CurrencyAmount[];
  receipt_count: number;
}

export interface SpendingTrendsResponse {
  trends: SpendingTrend[];
  period: "daily" | "weekly" | "monthly";
  start_date: string;
  end_date: string;
}

export interface StoreVisit {
  store_name: string;
  visit_count: number;
  totals_by_currency: CurrencyAmount[];
}

export interface TopStoresResponse {
  stores: StoreVisit[];
  year: number;
  month: number | null;
}

export interface CategorySpending {
  category_id: number;
  category_name: string;
  item_count: number;
  totals_by_currency: CurrencyAmount[];
}

export interface CategoryBreakdownResponse {
  categories: CategorySpending[];
  totals_by_currency: CurrencyAmount[];
  year: number;
  month: number | null;
}

// Auth Types

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}
