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
