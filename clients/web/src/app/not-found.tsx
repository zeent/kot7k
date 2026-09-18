import Link from "next/link"
import { getRequestMessages } from "@/i18n/server"

export default async function NotFound() {
  const messages = await getRequestMessages()

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "1rem",
        }}
      >
        <h1
          style={{
            margin: 0,
            paddingRight: "1rem",
            borderRight: "1px solid #d1d1d1",
            fontSize: "1.5rem",
          }}
        >
          404
        </h1>

        <div>
          <p style={{ margin: 0 }}>
            {messages.notFound.message}
            {" "}
            <Link
              href="/"
              style={{
                display: "inline-block",
                textDecoration: "underline",
              }}
            >
              {messages.notFound.returnHome}
            </Link>
          </p>
        </div>
      </div>
    </main>
  )
}
