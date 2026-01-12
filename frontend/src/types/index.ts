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
