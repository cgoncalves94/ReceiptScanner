import { create } from "zustand";

interface UIState {
  // Sidebar state
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  // Scan modal state
  scanModalOpen: boolean;
  openScanModal: () => void;
  closeScanModal: () => void;

  // Selected receipt for detail view
  selectedReceiptId: number | null;
  selectReceipt: (id: number | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
  // Sidebar
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  // Scan modal
  scanModalOpen: false,
  openScanModal: () => set({ scanModalOpen: true }),
  closeScanModal: () => set({ scanModalOpen: false }),

  // Selected receipt
  selectedReceiptId: null,
  selectReceipt: (id) => set({ selectedReceiptId: id }),
}));
