/**
 * localStorage-based storage for cost split reports.
 * Mirrors the API of storage.py using browser localStorage.
 */

const STORAGE_PREFIX = "cost_splitter:";

/**
 * Generate a URL-safe slug from a report name.
 * @param {string} name
 * @returns {string}
 */
function slugify(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

/**
 * Save a report to localStorage.
 * @param {Object} report
 */
function saveReport(report) {
  report.slug = slugify(report.name);
  localStorage.setItem(
    STORAGE_PREFIX + report.slug,
    JSON.stringify(report)
  );
}

/**
 * Load a report from localStorage by slug.
 * @param {string} slug
 * @returns {Object}
 * @throws {Error} if report not found
 */
function loadReport(slug) {
  const data = localStorage.getItem(STORAGE_PREFIX + slug);
  if (!data) {
    throw new Error(`Report '${slug}' not found`);
  }
  return JSON.parse(data);
}

/**
 * List all report slugs in localStorage.
 * @returns {string[]}
 */
function listReports() {
  const slugs = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key.startsWith(STORAGE_PREFIX)) {
      slugs.push(key.slice(STORAGE_PREFIX.length));
    }
  }
  return slugs.sort();
}

/**
 * Delete a report from localStorage by slug.
 * @param {string} slug
 */
function deleteReport(slug) {
  localStorage.removeItem(STORAGE_PREFIX + slug);
}

/**
 * Create a new report object.
 * @param {string} name
 * @param {string[]} participants
 * @returns {Object}
 */
function createReport(name, participants) {
  return {
    name,
    slug: slugify(name),
    participants,
    spendings: [],
    createdAt: new Date().toISOString(),
  };
}

/**
 * Create a new spending object.
 * @param {string} description
 * @param {number} amount
 * @param {string} paidBy
 * @param {string[]} participants
 * @param {Object.<string, number>|null} customAmounts
 * @returns {Object}
 */
function createSpending(description, amount, paidBy, participants, customAmounts) {
  return {
    description,
    amount,
    paidBy,
    participants,
    customAmounts: customAmounts || null,
    createdAt: new Date().toISOString(),
  };
}

export {
  slugify,
  saveReport,
  loadReport,
  listReports,
  deleteReport,
  createReport,
  createSpending,
};
