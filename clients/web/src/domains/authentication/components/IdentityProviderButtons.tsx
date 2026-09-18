import type { ComponentProps } from "react"

import { Button, Stack } from "@carbon/react"

import type { PublicIdentityProvider }
  from "@/domains/authentication/services/providers"

type IdentityProviderButtonsProps = {
  providers: PublicIdentityProvider[]
  disabled?: boolean
  onSelect: (provider: PublicIdentityProvider) => void
}

type ProviderIconProps = ComponentProps<"svg"> & {
  size?: number
}


function MicrosoftIcon({
  size = 16,
  ...props
}: ProviderIconProps) {
  const half = size * 0.4375
  const gap = size * 0.125

  return (
    <svg
      {...props}
      width={size}
      height={size}
      viewBox="0 0 16 16"
      aria-hidden="true"
    >
      <rect x="0" y="0" width={half} height={half} fill="#f25022" />
      <rect x={half + gap} y="0" width={half} height={half} fill="#7fba00" />
      <rect x="0" y={half + gap} width={half} height={half} fill="#00a4ef" />
      <rect
        x={half + gap}
        y={half + gap}
        width={half}
        height={half}
        fill="#ffb900"
      />
    </svg>
  )
}


function GoogleIcon({
  size = 16,
  ...props
}: ProviderIconProps) {
  return (
    <svg
      {...props}
      width={size}
      height={size}
      viewBox="0 0 16 16"
      aria-hidden="true"
    >
      <text
        x="8"
        y="12"
        textAnchor="middle"
        fontFamily="Arial, sans-serif"
        fontSize="14"
        fontWeight="700"
        fill="#4285f4"
      >
        G
      </text>
    </svg>
  )
}


function AppleIcon({ size = 16, ...props }: ProviderIconProps) {
  return (
    <svg {...props} width={size} height={size} viewBox="0 0 16 16" aria-hidden="true">
      <path fill="currentColor" d="M11.7 8.5c0-1.9 1.6-2.8 1.7-2.9-.9-1.3-2.3-1.5-2.8-1.5-1.2-.1-2.3.7-2.9.7-.6 0-1.5-.7-2.5-.7-1.3 0-2.5.8-3.2 1.9-1.4 2.4-.4 6 1 8 .7 1 1.5 2 2.6 2 1 0 1.4-.6 2.6-.6 1.2 0 1.5.6 2.6.6s1.8-1 2.4-1.9c.8-1.1 1.1-2.2 1.1-2.3-.1 0-2.6-1-2.6-3.3ZM9.8 2.9C10.3 2.2 10.7 1 10.6 0 9.7 0 8.5.6 7.9 1.3c-.5.6-1 1.8-.9 2.8 1 .1 2.1-.5 2.8-1.2Z" />
    </svg>
  )
}


export default function IdentityProviderButtons({
  providers,
  disabled = false,
  onSelect,
}: IdentityProviderButtonsProps) {
  return (
    <Stack gap={3}>
      {providers.map((provider) => (
        <Button
          key={provider.key}
          type="button"
          kind="tertiary"
          size="lg"
          renderIcon={
            provider.provider_type === "microsoft"
              ? MicrosoftIcon
              : provider.provider_type === "google"
                ? GoogleIcon
                : provider.provider_type === "apple"
                  ? AppleIcon
                  : undefined
          }
          disabled={disabled}
          onClick={() => onSelect(provider)}
          style={{ width: "100%", maxWidth: "none" }}
        >
          {provider.provider_type === "webauthn"
            ? "Continua amb una passkey"
            : `Continua amb ${provider.name}`}
        </Button>
      ))}
    </Stack>
  )
}
