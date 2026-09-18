"use client"

import Image from "next/image"

import {
  useState,
  type FormEvent,
} from "react"

import {
  Button,
  Form,
  InlineNotification,
  Link,
  PasswordInput,
  Stack,
  TextInput,
} from "@carbon/react"

import { ArrowRight }
  from "@carbon/icons-react"

import {
  login,
  startGoogleLogin,
  startCertificateLogin,
  startMicrosoftLogin,
  startAppleLogin,
  startPasskeyLogin,
  startGenericOIDCLogin,
}
  from "@/domains/authentication/services/authentication"
import IdentityProviderButtons
  from "@/domains/authentication/components/IdentityProviderButtons"

import type { PublicIdentityProvider }
  from "@/domains/authentication/services/providers"

import type { LoginResponse }
  from "@/domains/authentication/types/authentication"


type LoginFormProps = {
  providers: PublicIdentityProvider[]
  onAuthenticated: (
    response: LoginResponse,
  ) => void
}


export default function LoginForm({
  providers,
  onAuthenticated,
}: LoginFormProps) {
  const [
    step,
    setStep,
  ] = useState<1 | 2>(1)

  const [
    email,
    setEmail,
  ] = useState("")

  const [
    password,
    setPassword,
  ] = useState("")

  const [
    isSubmitting,
    setIsSubmitting,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  )

  const localLoginEnabled = providers.some(
    (provider) => provider.provider_type === "local" || provider.provider_type === "ldap",
  )
  const externalProviders = providers.filter(
    (provider) => provider.provider_type !== "local" && provider.provider_type !== "ldap",
  )


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault()

    if (step === 1) {
      if (!email.trim()) {
        setError(
          "Has d'introduir el correu electrònic.",
        )

        return
      }

      setError(null)
      setStep(2)

      return
    }

    if (!password) {
      setError(
        "Has d'introduir la contrasenya.",
      )

      return
    }

    try {
      setIsSubmitting(true)
      setError(null)

      const response =
        await login({
          email:
            email.trim().toLowerCase(),
          password,
        })

      onAuthenticated(
        response,
      )
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : (
              "No s'ha pogut "
              + "iniciar la sessió."
            ),
      )
    } finally {
      setIsSubmitting(false)
    }
  }


  function handleChangeUser():
    void {
    setStep(1)
    setPassword("")
    setError(null)
  }


  async function handleProviderSelection(
    provider: PublicIdentityProvider,
  ): Promise<void> {
    if (provider.provider_type === "x509") {
      try {
        setIsSubmitting(true)
        setError(null)
        await startCertificateLogin(provider.key)
      } catch (caughtError) {
        setError(
          caughtError instanceof Error
            ? caughtError.message
            : "No s'ha pogut iniciar l'accés amb certificat.",
        )
        setIsSubmitting(false)
      }
      return
    }

    if (provider.provider_type === "webauthn") {
      try {
        setIsSubmitting(true)
        setError(null)
        onAuthenticated(await startPasskeyLogin(provider.key))
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : "No s'ha pogut iniciar l'accés amb passkey.")
        setIsSubmitting(false)
      }
      return
    }

    if (provider.provider_type === "microsoft") {
      try {
        setIsSubmitting(true)
        setError(null)
        await startMicrosoftLogin(provider.key)
      } catch (caughtError) {
        setError(
          caughtError instanceof Error
            ? caughtError.message
            : "No s'ha pogut iniciar l'accés amb Microsoft.",
        )
        setIsSubmitting(false)
      }
      return
    }

    if (provider.provider_type === "apple") {
      try {
        setIsSubmitting(true)
        setError(null)
        await startAppleLogin(provider.key)
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : "No s'ha pogut iniciar l'accés amb Apple.")
        setIsSubmitting(false)
      }
      return
    }

    if (provider.provider_type === "oidc") {
      try {
        setIsSubmitting(true)
        setError(null)
        await startGenericOIDCLogin(provider.key)
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : "No s'ha pogut iniciar l'accés OpenID Connect.")
        setIsSubmitting(false)
      }
      return
    }

    try {
      setIsSubmitting(true)
      setError(null)
      await startGoogleLogin(provider.key)
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "No s'ha pogut iniciar l'accés amb Google.",
      )
      setIsSubmitting(false)
    }
  }


  return (
    <Form
      aria-label="Inici de sessió"
      onSubmit={(event) => {
        void handleSubmit(event)
      }}
    >
      <Stack gap={7}>
        <Image
          src={
            "/images/logos/"
            + "kot7k-login.png"
          }
          alt="KOT7K"
          width={2086}
          height={754}
          priority
          style={{
            display: "block",
            width: "100%",
            maxWidth: "23rem",
            height: "auto",
            margin: "0 auto 2rem",
          }}
        />


        <div>
        </div>


        {error && (
          <InlineNotification
            kind="error"
            lowContrast
            hideCloseButton
            title={
              "No s'ha pogut "
              + "iniciar la sessió"
            }
            subtitle={error}
          />
        )}

        <Stack gap={5}>
          {localLoginEnabled && <TextInput
            id="login-email"
            name="email"
            type="email"
            labelText="Correu electrònic"
            placeholder={
              "Introdueix el teu correu electrònic"
            }
            value={email}
            readOnly={step === 2}
            disabled={
              isSubmitting
            }
            autoComplete="email"
            autoFocus={step === 1}
            onChange={(event) => {
              setEmail(
                event.target.value,
              )
            }}
          />}


          {localLoginEnabled && step === 1 ? (
            <>
              <Button
                type="submit"
                kind="primary"
                size="lg"
                renderIcon={
                  ArrowRight
                }
                disabled={
                  isSubmitting
                }
                style={{
                  width: "100%",
                  maxWidth: "none",
                }}
              >
                Continua
              </Button>

              {externalProviders.length > 0 && <div
                role="separator"
                aria-label="Altres opcions d’accés"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--cds-spacing-04)",
                  color: "var(--cds-text-secondary)",
                  fontSize: "var(--cds-label-01-font-size)",
                }}
              >
                <span
                  aria-hidden="true"
                  style={{
                    flex: 1,
                    borderTop: "1px solid var(--cds-border-subtle-01)",
                  }}
                />
                <span>O continua amb</span>
                <span
                  aria-hidden="true"
                  style={{
                    flex: 1,
                    borderTop: "1px solid var(--cds-border-subtle-01)",
                  }}
                />
              </div>}

              <IdentityProviderButtons
                providers={externalProviders}
                disabled={isSubmitting}
                onSelect={(provider) => {
                  void handleProviderSelection(provider)
                }}
              />
            </>
          ) : localLoginEnabled ? (
            <>
              <PasswordInput
                id="login-password"
                name="password"
                labelText="Contrasenya"
                placeholder={
                  "Introdueix la teva contrasenya"
                }
                value={password}
                disabled={
                  isSubmitting
                }
                autoComplete={
                  "current-password"
                }
                autoFocus
                onChange={(event) => {
                  setPassword(
                    event.target.value,
                  )
                }}
              />


              <Button
                type="submit"
                kind="primary"
                size="lg"
                renderIcon={
                  ArrowRight
                }
                disabled={
                  isSubmitting
                }
                style={{
                  width: "100%",
                  maxWidth: "none",
                }}
              >
                {isSubmitting
                  ? "Iniciant sessió..."
                  : "Inicia sessió"}
              </Button>


              <Button
                type="button"
                kind="ghost"
                size="sm"
                disabled={
                  isSubmitting
                }
                onClick={
                  handleChangeUser
                }
                style={{
                  alignSelf:
                    "flex-start",
                  paddingLeft: 0,
                }}
              >
                Canvia d’usuari
              </Button>
            </>
          ) : (
            <IdentityProviderButtons
              providers={externalProviders}
              disabled={isSubmitting}
              onSelect={(provider) => {
                void handleProviderSelection(provider)
              }}
            />
          )}
        </Stack>


        <div
          style={{
            paddingTop:
              "var(--cds-spacing-05)",
            borderTop:
              "1px solid "
              + "var(--cds-border-subtle-01)",
          }}
        >
          <span
            style={{
              color:
                "var(--cds-text-secondary)",
            }}
          >
            Necessites ajuda?{" "}
          </span>

          <Link href="#">
            Contacta amb el suport
          </Link>
        </div>
      </Stack>
    </Form>
  )
}
