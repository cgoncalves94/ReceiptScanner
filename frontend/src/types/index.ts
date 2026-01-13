// API Response Types - matching backend schemas

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
}

export interface ReceiptUpdate {
  store_name?: string | null;
  total_amount?: number | null;
  currency?: string | null;
  purchase_date?: string | null;
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
