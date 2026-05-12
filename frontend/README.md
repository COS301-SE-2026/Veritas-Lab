## Getting Started

First, run the frontend development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Frontend File Structure

```
frontend/
├── public/ # Next.js application
├── src/ # API/server code, if separate
│   ├── api/ # API calls
│   ├── app/ # Pages
│   │   ├── page.tsx # Root/landing page "/"
│   │   ├── layout.tsx # Layout wraping all the pages (Stuff like navbars)
│   │   ├── login/ # Login page (The subpages in here represent the structures of the other pages)
│   │   │   ├── page.tsx # Routed page for the login page "/login"
│   │   │   └── layout.tsx # Layout wrapper for the login page (This is an example)
│   │   ├── signup/ # Signup page
│   │   └── dashboard/ # Dashboard page
│   ├── assets/ # Icons, fonts, etc 
│   ├── components/ # Reusable components
│   ├── hooks/ # Custom react hooks
│   ├── styles/ # CSS and stylings
│   └── types/ # Custom interfaces/types to used
├── .gitignore
├── eslint.config.mjs
├── next.config.ts
├── package.json
├── postcss.config.mjs
├── README.md
└── tsconfig.json
```
