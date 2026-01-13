import type {
  Category,
  CategoryBreakdownResponse,
  CategoryCreate,
  CategoryUpdate,
  Receipt,
  ReceiptUpdate,
  ReceiptItemUpdate,
  SpendingSummary,
  SpendingTrendsResponse,
  TopStoresResponse,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = `${API_BASE_URL}/api/v1`;

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_V1}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    // Handle 204 No Content (empty response)
    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  // ============================================================================
  // Receipts
  // ============================================================================

  async getReceipts(): Promise<Receipt[]> {
    return this.request<Receipt[]>("/receipts");
  }

  async getReceipt(id: number): Promise<Receipt> {
    return this.request<Receipt>(`/receipts/${id}`);
  }

  async scanReceipt(file: File): Promise<Receipt> {
    const formData = new FormData();
    formData.append("image", file);

    const response = await fetch(`${API_V1}/receipts/scan`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async updateReceipt(id: number, data: ReceiptUpdate): Promise<Receipt> {
    return this.request<Receipt>(`/receipts/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteReceipt(id: number): Promise<void> {
    await this.request<void>(`/receipts/${id}`, {
      method: "DELETE",
    });
  }

  // ============================================================================
  // Receipt Items
  // ============================================================================

  async updateReceiptItem(
    receiptId: number,
    itemId: number,
    data: ReceiptItemUpdate
  ): Promise<Receipt> {
    return this.request<Receipt>(`/receipts/${receiptId}/items/${itemId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // Categories
  // ============================================================================

  async getCategories(): Promise<Category[]> {
    return this.request<Category[]>("/categories");
  }

  async getCategory(id: number): Promise<Category> {
    return this.request<Category>(`/categories/${id}`);
  }

  async createCategory(data: CategoryCreate): Promise<Category> {
    return this.request<Category>("/categories", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateCategory(id: number, data: CategoryUpdate): Promise<Category> {
    return this.request<Category>(`/categories/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteCategory(id: number): Promise<void> {
    await this.request<void>(`/categories/${id}`, {
      method: "DELETE",
    });
  }

  async getCategoryItems(
    categoryId: number,
    skip = 0,
    limit = 100
  ): Promise<import("@/types").ReceiptItem[]> {
    return this.request(`/receipts/category/${categoryId}/items?skip=${skip}&limit=${limit}`);
  }

  // ============================================================================
  // Health
  // ============================================================================

  async healthCheck(): Promise<{ status: string; database: string }> {
    const response = await fetch(`${API_BASE_URL}/healthcheck`);
    return response.json();
  }

  // ============================================================================
  // Analytics
  // Note: Backend returns data grouped by original currency.
  // Frontend converts to display currency using exchange rates.
  // ============================================================================

  async getAnalyticsSummary(
    year: number,
    month?: number
  ): Promise<SpendingSummary> {
    const params = new URLSearchParams({
      year: year.toString(),
    });
    if (month !== undefined) {
      params.set("month", (month + 1).toString()); // Convert 0-indexed to 1-indexed
    }
    return this.request<SpendingSummary>(`/analytics/summary?${params}`);
  }

  async getAnalyticsTrends(
    start: Date,
    end: Date,
    period: "daily" | "weekly" | "monthly" = "monthly"
  ): Promise<SpendingTrendsResponse> {
    const params = new URLSearchParams({
      start: start.toISOString(),
      end: end.toISOString(),
      period,
    });
    return this.request<SpendingTrendsResponse>(`/analytics/trends?${params}`);
  }

  async getTopStores(
    year: number,
    month?: number,
    limit = 10
  ): Promise<TopStoresResponse> {
    const params = new URLSearchParams({
      year: year.toString(),
      limit: limit.toString(),
    });
    if (month !== undefined) {
      params.set("month", (month + 1).toString()); // Convert 0-indexed to 1-indexed
    }
    return this.request<TopStoresResponse>(`/analytics/top-stores?${params}`);
  }

  async getCategoryBreakdown(
    year: number,
    month?: number
  ): Promise<CategoryBreakdownResponse> {
    const params = new URLSearchParams({
      year: year.toString(),
    });
    if (month !== undefined) {
      params.set("month", (month + 1).toString()); // Convert 0-indexed to 1-indexed
    }
    return this.request<CategoryBreakdownResponse>(`/analytics/category-breakdown?${params}`);
  }
}

export const api = new ApiClient();
