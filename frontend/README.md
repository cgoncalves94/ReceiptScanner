# Receipt Scanner Frontend

Next.js 16 frontend for the Receipt Scanner application.

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **UI**: React 19, Tailwind CSS, shadcn/ui
- **State**: TanStack Query (server state), Zustand (client state)
- **Forms**: React Hook Form + Zod validation
- **Charts**: Recharts

## Development

```bash
# Install dependencies
pnpm install

# Start dev server (requires backend at localhost:8000)
pnpm dev

# Build for production
pnpm build

# Run production build
pnpm start

# Lint
pnpm lint
```

## Project Structure

```text
src/
├── app/                    # App Router pages
│   ├── (app)/              # Authenticated routes
│   │   ├── page.tsx        # Dashboard
│   │   ├── receipts/       # Receipt list & detail
│   │   ├── categories/     # Category management
│   │   ├── analytics/      # Spending charts
│   │   └── scan/           # Receipt scanning
│   └── layout.tsx          # Root layout
├── components/
│   └── ui/                 # shadcn/ui components
├── hooks/                  # TanStack Query hooks
│   ├── use-receipts.ts     # Receipt CRUD
│   ├── use-categories.ts   # Category CRUD
│   └── use-currency.ts     # Currency conversion
├── lib/
│   ├── api/client.ts       # API client
│   └── format.ts           # Formatters
└── types/                  # TypeScript types
```

## Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Docker

```bash
# Build image
docker build -t receipt-frontend .

# Run container
docker run -p 3000:3000 receipt-frontend
```

Or use docker-compose from root:

```bash
make up  # Starts db, backend, and frontend
```
