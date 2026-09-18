# KOT7K WebUI

Next.js, React, TypeScript and Carbon.

Run `npm ci`, then `npm run dev` from this directory. The development server uses http://localhost:10000 and connects to http://localhost:10001/api by default. Set `NEXT_PUBLIC_API_BASE_URL` to override the API origin.

Validation: `npm run lint`, `npx tsc --noEmit --incremental false`, and `npm run build`. Serve the production build with `npm start`.
