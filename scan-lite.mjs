// scan-lite.mjs
import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'

const ROOT = process.argv[2] ? path.resolve(process.argv[2]) : process.cwd()
const OUTPUT_FILE = path.join(ROOT, 'project-scan-lite.md')

const INCLUDE_DIRS = [
  'app',
  'src',
  'features',
  'services',
  'lib',
  'db',
  'components',
  'docs',
  'infra',
  'scripts',
  'prisma',
  'migrations',
  '.github/workflows',
]

const INCLUDE_ROOT_FILES = [
  'README.md',
  'package.json',
  'tsconfig.json',
  'next.config.ts',
  'next.config.js',
  'next.config.mjs',
  'tailwind.config.ts',
  'tailwind.config.js',
  'middleware.ts',
  'docker-compose.yml',
  'docker-compose.yaml',
  '.env.example',
  '.env.sample',
  'pnpm-workspace.yaml',
  'turbo.json',
  'pyproject.toml',
  'requirements.txt',
  'alembic.ini',
]

const IGNORE_SUBDIRS = new Set([
  'node_modules',
  '.next',
  '.git',
  'dist',
  'build',
  '__tests__',
  'test',
  'tests',
  'coverage',
  '.turbo',
  '.vercel',
  '.idea',
  '.vscode',
  '.venv',
  'venv',
  '__pycache__',
  '.pytest_cache',
  'site-packages',
  'ui',
])

const IGNORE_FILES = new Set([
  'package-lock.json',
  'yarn.lock',
  'pnpm-lock.yaml',
  'bun.lockb',
  '.DS_Store',
  'project-scan-lite.md',
])

const ALWAYS_INCLUDE_FILENAMES = new Set([
  'Dockerfile',
  'README.md',
  'requirements.txt',
  'pyproject.toml',
  '.env.example',
  '.env.sample',
])

const VALID_EXTENSIONS = new Set([
  '.ts',
  '.tsx',
  '.js',
  '.jsx',
  '.mjs',
  '.cjs',
  '.py',
  '.sql',
  '.json',
  '.md',
  '.yml',
  '.yaml',
  '.toml',
  '.sh',
])

const MAX_FILE_LINES = 350
const MAX_FILE_CHARS = 18000

let output = ''
let fileCount = 0
const capturedFiles = []

function normalizeRel(relPath) {
  return relPath.split(path.sep).join('/')
}

function getLang(filePath) {
  const base = path.basename(filePath)
  const ext = path.extname(filePath).toLowerCase()

  if (base === 'Dockerfile') return 'dockerfile'

  const map = {
    '.ts': 'typescript',
    '.tsx': 'tsx',
    '.js': 'javascript',
    '.jsx': 'jsx',
    '.mjs': 'javascript',
    '.cjs': 'javascript',
    '.py': 'python',
    '.json': 'json',
    '.sql': 'sql',
    '.md': 'markdown',
    '.yml': 'yaml',
    '.yaml': 'yaml',
    '.toml': 'toml',
    '.sh': 'bash',
  }

  return map[ext] || 'text'
}

function isIgnoredDir(entryName, relDir) {
  if (IGNORE_SUBDIRS.has(entryName)) return true

  const rel = normalizeRel(relDir)
  if (rel.includes('/components/ui')) return true
  if (rel.includes('/coverage/')) return true
  if (rel.includes('/dist/')) return true
  if (rel.includes('/build/')) return true

  return false
}

function isIgnoredFile(entryName) {
  if (IGNORE_FILES.has(entryName)) return true
  if (entryName === '.env') return true
  if (entryName.startsWith('.env.') && !entryName.endsWith('.example') && !entryName.endsWith('.sample')) return true
  if (/\.(test|spec)\.(ts|tsx|js|jsx|py)$/.test(entryName)) return true
  return false
}

function shouldIncludeFile(entryName) {
  if (isIgnoredFile(entryName)) return false
  if (ALWAYS_INCLUDE_FILENAMES.has(entryName)) return true

  const ext = path.extname(entryName).toLowerCase()
  return VALID_EXTENSIONS.has(ext)
}

function appendFile(fullPath, rel) {
  try {
    const raw = fs.readFileSync(fullPath, 'utf-8')
    if (!raw.trim()) return

    const lang = getLang(fullPath)
    const lines = raw.replace(/\r\n/g, '\n').split('\n')
    let content = raw.trim()
    let truncated = false

    if (lines.length > MAX_FILE_LINES) {
      content = lines.slice(0, MAX_FILE_LINES).join('\n')
      truncated = true
    }

    if (content.length > MAX_FILE_CHARS) {
      content = content.slice(0, MAX_FILE_CHARS)
      truncated = true
    }

    output += `\n## \`${rel}\`\n`
    output += `- Linhas originais: ${lines.length}\n`
    output += `- Truncado: ${truncated ? 'sim' : 'não'}\n`
    if (truncated) {
      output += `- Observação: conteúdo truncado para manter o scan legível.\n`
    }
    output += `\n\`\`\`${lang}\n${content}\n\`\`\`\n`

    capturedFiles.push(rel)
    fileCount++
  } catch {
    // ignora binários ou arquivos ilegíveis
  }
}

function readDir(dir) {
  let entries
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true })
  } catch {
    return
  }

  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    const fullPath = path.join(dir, entry.name)
    const rel = normalizeRel(path.relative(ROOT, fullPath))

    if (entry.isDirectory()) {
      if (isIgnoredDir(entry.name, rel)) continue
      readDir(fullPath)
      continue
    }

    if (shouldIncludeFile(entry.name)) {
      appendFile(fullPath, rel)
    }
  }
}

for (const name of INCLUDE_ROOT_FILES) {
  const fullPath = path.join(ROOT, name)
  if (fs.existsSync(fullPath)) {
    appendFile(fullPath, normalizeRel(name))
  }
}

for (const dir of INCLUDE_DIRS) {
  const fullPath = path.join(ROOT, dir)
  if (fs.existsSync(fullPath)) {
    readDir(fullPath)
  }
}

const capturedList = capturedFiles.length
  ? capturedFiles.map((f) => `- \`${f}\``).join('\n')
  : '_Nenhum arquivo capturado._'

const header = `# Project Scan (lite) — ${path.basename(ROOT)}

> Raiz escaneada: \`${normalizeRel(ROOT)}\`
> Gerado em: ${new Date().toLocaleString('pt-BR')}
> Arquivos capturados: ${fileCount}
> Pastas-alvo: ${INCLUDE_DIRS.join(', ')}
> Regras: ignora testes, build artifacts, lockfiles, \`.env\` real e \`components/ui\`

---

## Como interpretar este arquivo
- Este scan é uma evidência forte da estrutura do projeto.
- Ele não prova comportamento em runtime.
- Ausência de algo no scan não prova ausência no repositório.
- Presença no scan é forte indício de implementação existente.

## Arquivos capturados
${capturedList}

---
`

fs.writeFileSync(OUTPUT_FILE, header + output, 'utf-8')

const sizeKB = (fs.statSync(OUTPUT_FILE).size / 1024).toFixed(1)

console.log('✅ Scan lite completo!')
console.log(`📄 Arquivo: ${OUTPUT_FILE}`)
console.log(`📦 Tamanho: ${sizeKB} KB`)
console.log(`🗂️  Arquivos: ${fileCount}`)
console.log(`📍 Raiz: ${ROOT}`)