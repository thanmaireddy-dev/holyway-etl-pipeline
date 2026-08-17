/**
 * extractFirestore.mjs
 *
 * HolyWay Data Engineering Pipeline — Step 1: Firestore → Raw JSON
 *
 * This script performs a READ-ONLY extraction of the `churches` collection
 * from the HolyWay Firebase Firestore project (holy-way-9800e).
 *
 * It produces a faithful raw snapshot of every document with:
 *   - Firestore document IDs preserved
 *   - Original field names preserved
 *   - Nested objects (e.g. massTimings) preserved
 *   - Arrays (e.g. languages, imageUrls, searchKeywords) preserved
 *   - Timestamps serialized as ISO 8601 strings
 *
 * No data is cleaned, normalized, deduplicated, renamed, or flattened.
 * No Firestore documents are created, updated, or deleted.
 *
 * Output:
 *   raw/firestore/churches.json           — array of raw church documents
 *   raw/firestore/_extraction_metadata.json — extraction run metadata
 *
 * Usage:
 *   1. Copy .env.example to .env and fill in Firebase configuration.
 *   2. npm install
 *   3. npm run extract
 */

import 'dotenv/config';
import { initializeApp } from 'firebase/app';
import { getFirestore, collection, getDocs, Timestamp } from 'firebase/firestore';
import { writeFile, mkdir } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

// ---------------------------------------------------------------------------
// 1. Validate environment
// ---------------------------------------------------------------------------

const REQUIRED_ENV_VARS = [
  'FIREBASE_API_KEY',
  'FIREBASE_AUTH_DOMAIN',
  'FIREBASE_PROJECT_ID',
  'FIREBASE_STORAGE_BUCKET',
  'FIREBASE_MESSAGING_SENDER_ID',
  'FIREBASE_APP_ID',
];

const missing = REQUIRED_ENV_VARS.filter((key) => !process.env[key]);
if (missing.length > 0) {
  console.error(
    '\n❌  Missing required environment variables:\n' +
      missing.map((k) => `   • ${k}`).join('\n') +
      '\n\nCreate a .env file from .env.example and fill in all values.\n'
  );
  process.exit(1);
}

// ---------------------------------------------------------------------------
// 2. Firebase configuration (loaded entirely from .env)
// ---------------------------------------------------------------------------

const firebaseConfig = {
  apiKey: process.env.FIREBASE_API_KEY,
  authDomain: process.env.FIREBASE_AUTH_DOMAIN,
  projectId: process.env.FIREBASE_PROJECT_ID,
  storageBucket: process.env.FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.FIREBASE_APP_ID,
};

// ---------------------------------------------------------------------------
// 3. Paths
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = join(__dirname, '..', '..');
const OUTPUT_DIR = join(PROJECT_ROOT, 'raw', 'firestore');
const OUTPUT_FILE = join(OUTPUT_DIR, 'churches.json');
const METADATA_FILE = join(OUTPUT_DIR, '_extraction_metadata.json');

const COLLECTION_NAME = 'churches';

// ---------------------------------------------------------------------------
// 4. Serialization helpers
// ---------------------------------------------------------------------------

/**
 * Recursively convert Firestore-specific types into plain JSON-safe values.
 *
 * - Firestore Timestamps → ISO 8601 string + original { seconds, nanoseconds }
 * - All other values pass through unchanged.
 */
function serializeValue(value) {
  if (value === null || value === undefined) {
    return value;
  }

  // Firestore Timestamp
  if (value instanceof Timestamp) {
    const date = value.toDate();
    return {
      _type: 'timestamp',
      iso: date.toISOString(),
      _seconds: value.seconds,
      _nanoseconds: value.nanoseconds,
    };
  }

  // Firestore Timestamp-like plain objects (from the Web SDK these sometimes
  // arrive as plain objects with seconds/nanoseconds keys)
  if (
    typeof value === 'object' &&
    !Array.isArray(value) &&
    typeof value.seconds === 'number' &&
    typeof value.nanoseconds === 'number' &&
    Object.keys(value).length === 2
  ) {
    const date = new Timestamp(value.seconds, value.nanoseconds).toDate();
    return {
      _type: 'timestamp',
      iso: date.toISOString(),
      _seconds: value.seconds,
      _nanoseconds: value.nanoseconds,
    };
  }

  // Arrays — recurse into each element
  if (Array.isArray(value)) {
    return value.map(serializeValue);
  }

  // Plain objects — recurse into each key
  if (typeof value === 'object') {
    const result = {};
    for (const [k, v] of Object.entries(value)) {
      result[k] = serializeValue(v);
    }
    return result;
  }

  // Primitives (string, number, boolean) — pass through
  return value;
}

// ---------------------------------------------------------------------------
// 5. Main extraction
// ---------------------------------------------------------------------------

async function main() {
  const extractionStart = new Date();

  console.log('');
  console.log('═══════════════════════════════════════════════════');
  console.log('  HolyWay Data Pipeline — Firestore Extraction');
  console.log('═══════════════════════════════════════════════════');
  console.log('');
  console.log(`  Project ID : ${process.env.FIREBASE_PROJECT_ID}`);
  console.log(`  Collection : ${COLLECTION_NAME}`);
  console.log(`  Output     : ${OUTPUT_DIR}`);
  console.log('');

  // --- Initialize Firebase ---
  console.log('🔌  Connecting to Firestore…');
  const app = initializeApp(firebaseConfig);
  const db = getFirestore(app);

  // --- Read collection ---
  console.log(`📖  Reading collection "${COLLECTION_NAME}"…`);
  const snapshot = await getDocs(collection(db, COLLECTION_NAME));

  if (snapshot.empty) {
    console.warn(`\n⚠️  Collection "${COLLECTION_NAME}" is empty or inaccessible.\n`);
    process.exit(0);
  }

  // --- Serialize documents ---
  const documents = [];
  for (const doc of snapshot.docs) {
    const data = doc.data();
    documents.push({
      _firestoreId: doc.id,
      ...serializeValue(data),
    });
  }

  console.log(`✅  Retrieved ${documents.length} document(s).`);

  // --- Ensure output directory ---
  await mkdir(OUTPUT_DIR, { recursive: true });

  // --- Write churches.json ---
  await writeFile(OUTPUT_FILE, JSON.stringify(documents, null, 2), 'utf-8');
  console.log(`💾  Wrote ${OUTPUT_FILE}`);

  // --- Write extraction metadata ---
  const extractionEnd = new Date();
  const metadata = {
    extractionTimestamp: extractionStart.toISOString(),
    extractionCompletedAt: extractionEnd.toISOString(),
    durationMs: extractionEnd - extractionStart,
    firebaseProjectId: process.env.FIREBASE_PROJECT_ID,
    firestoreCollection: COLLECTION_NAME,
    documentCount: documents.length,
  };

  await writeFile(METADATA_FILE, JSON.stringify(metadata, null, 2), 'utf-8');
  console.log(`📋  Wrote ${METADATA_FILE}`);

  console.log('');
  console.log('───────────────────────────────────────────────────');
  console.log(`  Extraction complete: ${documents.length} document(s)`);
  console.log('───────────────────────────────────────────────────');
  console.log('');
}

main().catch((err) => {
  console.error('\n❌  Extraction failed:\n');
  // Do not log the full error object — it may contain config details.
  console.error(`   ${err.message || err}`);
  process.exit(1);
});
