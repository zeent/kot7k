export const siteConfig = {
  name: process.env.NEXT_PUBLIC_APP_NAME ?? "KOT7K by ZeroEntropy",
  description: "IAM & IAG made simple",
  links: {
    home: "/",
    administration: "/administration",
  },
} as const

export type SiteConfig = typeof siteConfig
