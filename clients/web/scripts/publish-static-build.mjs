import {
  access,
  mkdir,
  readFile,
  writeFile,
  rename,
  rm,
} from "node:fs/promises"
import { constants } from "node:fs"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"


const scriptDirectory = dirname(
  fileURLToPath(import.meta.url),
)
const uiDirectory = resolve(scriptDirectory, "..")
const buildDirectory = resolve(uiDirectory, "out")
const targetDirectory = resolve(uiDirectory, "../../api/ui_dist")
const previousDirectory = resolve(uiDirectory, "../../api/ui_dist.previous")

// Validate the export before moving the currently published build.
for (const file of ["index.html", "404.html", "authentication/login.html",
  "authentication/front-channel-logout", "authentication/signed-out",
  "auth/front-channel-logout.js", "auth/signed-out.js"]) {
  await access(resolve(buildDirectory, file), constants.R_OK)
}

// Static exports do not serve the Response headers. Carry the logout policies
// into an Nginx include, using the same build-time API origin as the HTML.
const quote = (value) => JSON.stringify(value).replaceAll("$", "\\$")
const locations = []
const uiHeaders = {}
for (const name of ["front-channel-logout", "signed-out"]) {
  const { headers } = JSON.parse(await readFile(
    resolve(uiDirectory, `.next/server/app/authentication/${name}.meta`), "utf8",
  ))
  uiHeaders[`authentication/${name}`] = Object.fromEntries(
    ["cache-control", "referrer-policy", "content-security-policy"].map((key) => [key, headers[key]]),
  )
  const directives = ["cache-control", "referrer-policy", "content-security-policy"]
    .map((header) => {
      if (!headers[header]) throw new Error(`Missing ${header} for ${name}`)
      return `    add_header ${header} ${quote(headers[header])} always;`
    })
  locations.push(`location = /authentication/${name} {
    default_type text/html;
    charset utf-8;
    try_files $uri =404;
${directives.join("\n")}
}`)
}
await writeFile(resolve(buildDirectory, ".ui-headers.json"), JSON.stringify(uiHeaders, null, 2) + "\n")
await mkdir(resolve(buildDirectory, ".nginx"), { recursive: true })
await writeFile(resolve(buildDirectory, ".nginx/logout.conf"), locations.join("\n\n") + "\n")
await rm(previousDirectory, { recursive: true, force: true })

let previousBuildMoved = false

try {
  try {
    await rename(targetDirectory, previousDirectory)
    previousBuildMoved = true
  } catch (error) {
    if (error?.code !== "ENOENT") throw error
  }

  await rename(buildDirectory, targetDirectory)
} catch (error) {
  if (previousBuildMoved) {
    try {
      await rename(previousDirectory, targetDirectory)
    } catch {
      // Preserve the original error; the backup remains available on disk.
    }
  }
  throw error
}

await rm(previousDirectory, { recursive: true, force: true })

process.stdout.write(`UI publicada a ${targetDirectory}\n`)
